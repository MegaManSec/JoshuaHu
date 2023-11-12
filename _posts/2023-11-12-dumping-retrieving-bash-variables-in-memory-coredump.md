---
layout: post
title: "Dumping bash variable values from memory using gdb"
author: "Joshua Rogers"
categories: security
---

Dumping the memory of a binary process and examining variable contents is intuitive enough for normal programs. But how about retrieving the in-script variables and their current values of a bash script? Slightly less intuitive.

I've recently been working on a bash script which performs some continuous processing of information, with some of the processed information being appended to a string. Something like this:

```bash
while IFS= read -r line; do
  if [[ $line == "1:"* ]]; then
    str+="$line"
  fi
done < <(command)
```

I then ran my script for a considerable amount of time. However, I completely forgot to include any printf of `$str`. Instead of having to start over and lose all of the data I had already processed, I thought _why not just dump the memory and find the value of str?_ So let's do that.

---


First we make a coredump of the running bash _binary_ and load it into gdb:
```bash
$ ps ax | grep test
1234537 pts/2    S+     0:00 bash test.sh
# gcore -a 1234537
0x00007fe7db6803ce in read () from /lib/x86_64-linux-gnu/libc.so.6
warning: target file /proc/1234537/cmdline contained unexpected null characters
Saved corefile core.1234537
[Inferior 1 (process 1234537) detached]
$ gdb bash ./core.1234537 -ex 'set pagination off' -ex 'set print pretty on'
[..]
```

Taking a look at bash's source code, we first look at the obvious [variables.c](https://github.com/bminor/bash/blob/2bb3cbefdb8fd019765b1a9cc42ecf37ff22fec6/variables.c#L119C14-L119C30). On the stack are the "global_variables" and "shell_variables" variables which store the bash variables for the bash session:
```C
/* The list of shell variables that the user has created at the global
   scope, or that came from the environment. */
VAR_CONTEXT *global_variables = (VAR_CONTEXT *)NULL;

/* The current list of shell variables, including function scopes */
VAR_CONTEXT *shell_variables = (VAR_CONTEXT *)NULL;
```

 The definition for VAR_CONTEXT is found in [variables.h](https://github.com/bminor/bash/blob/2bb3cbefdb8fd019765b1a9cc42ecf37ff22fec6/variables.h#L41):
 ```C
 typedef struct var_context {
  char *name;		/* empty or NULL means global context */
  int scope;		/* 0 means global context */
  int flags;
  struct var_context *up;	/* previous function calls */
  struct var_context *down;	/* down towards global context */
  HASH_TABLE *table;		/* variables at this scope */
} VAR_CONTEXT;
 ```

First we try to simply print `shell_variables` but that fails:
```
(gdb) p shell_variables
'shell_variables' has unknown type; cast it to its declared type
```

Since bash hasn't been built with debugging symbols, gdb can't pick up the _VAR_CONTEXT_ type. So, we need to build bash with debugging symbols and add the symbols in gdb.
```bash
$ apt-get source bash && \
 cd bash-* && \
 CFLAGS='-g' ./configure && \
 make -j32 && \
 cd ../
```

We then determine the text address location of the newly compiled bash binary and then load them into gdb:
```bash
$ readelf -WS ./bash-*/bash | grep .text | awk '{ print "0x"$5 }'
0x02fdd0

[..]

(gdb) add-symbol-file ./bash-5.1/bash 0x02fdd0
add symbol table from file "./bash-5.1/bash" at
        .text_addr = 0x2fdd0
(y or n) y
Reading symbols from ./bash-5.1/bash...
(gdb) p shell_variables
$1 = (VAR_CONTEXT *) 0x5652805cd150
(gdb) 
```
Taking a look again at the definition for _VAR_CONTEXT_, we see that _shell_variables_ is a double linked list, with the variables stored in a hash table of type _HASH_TABLE_. _HASH_TABLE_ is defined in [hashlib.h](https://github.com/bminor/bash/blob/2bb3cbefdb8fd019765b1a9cc42ecf37ff22fec6/hashlib.h#L46):
```C
typedef struct hash_table {
  BUCKET_CONTENTS **bucket_array;	/* Where the data is kept. */
  int nbuckets;			/* How many buckets does this table have. */
  int nentries;			/* How many entries does this table have. */
} HASH_TABLE;
```
and _BUCKET_CONTENTS_ too:
```C
typedef struct bucket_contents {
  struct bucket_contents *next;	/* Link to next hashed key in this bucket. */
  char *key;			/* What we look up. */
  void *data;			/* What we really want. */
  unsigned int khash;		/* What key hashes to */
  int times_found;		/* Number of times this item has been found. */
} BUCKET_CONTENTS;
```

So we go exploring:
```bash
(gdb) p *shell_variables
$21 = {
  name = 0x0 <nodel>,
  scope = 1,
  flags = 10,
  up = 0x0 <nodel>,
  down = 0x5652805ecde0,
  table = 0x5652805ffa40
}
(gdb) p *shell_variables->table
$22 = {
  bucket_array = 0x5652806416f0,
  nbuckets = 4,
  nentries = 1
}
(gdb) p shell_variables->table->bucket_array
$23 = (BUCKET_CONTENTS **) 0x5652806416f0
(gdb) p shell_variables->table->bucket_array[3]
$24 = (BUCKET_CONTENTS *) 0x5652805f6470
(gdb) p shell_variables->table->bucket_array[3].
data         key          khash        next         times_found  
(gdb) p shell_variables->table->bucket_array[3].next
$25 = (struct bucket_contents *) 0x0 <nodel>
(gdb) p shell_variables->table->bucket_array[3]key
A syntax error in expression, near `key'.
(gdb) p shell_variables->table->bucket_array[3]->key
$26 = 0x565280615620 "IFS"
(gdb) ptype ((SHELL_VAR *)shell_variables->table->bucket_array[3]->data)
type = struct variable {
    char *name;
    char *value;
    char *exportstr;
    sh_var_value_func_t *dynamic_value;
    sh_var_assign_func_t *assign_func;
    int attributes;
    int context;
} *
(gdb) p ((SHELL_VAR *)shell_variables->table->bucket_array[3]->data)->value
0x56528063a9a0: "\r\n"
```

Great success!

---

Putting it all together, we need to cycle through each of the var_context structs, then cycle through each of the buckets, working our way down each list until we get to the very end. Easy enough. We define a function:
```perl
define print_keys_vals
  set $current = shell_variables
  while $current != 0
    set $bucket = $current->table->bucket_array
    set $nbuckets = $current->table->nbuckets
    set $i = 0
    while $i < $nbuckets
      set $entry = $bucket[$i]
      while $entry != 0
        set $shell_var = (SHELL_VAR *)$entry->data
        printf "      Name: %s\n", $shell_var->name
        printf "      Value: %s\n", $shell_var->value
        set $entry = $entry->next
      end
      set $i = $i + 1
    end
    set $current = $current->down
  end
end
```

and run it:

```bash
(gdb) print_keys_vals
[...]
      Name: HISTCMD
      Value: (null)
      Name: BASH
      Value: /usr/bin/bash
      Name: MOTD_SHOWN
      Value: pam
      Name: str
      Value: 1: super secret string constructed in the bash script
      Name: s
      Value: sudo
      Name: LD_PRELOAD
      Value: /usr/libexec/coreutils/libstdbuf.so:/usr/libexec/coreutils/libstdbuf.so
      Name: BASH_VERSINFO
      Value:
      Name: BASHPID
      Value: (null)
[...]
```
And that's exactly what we were looking for (the environmental values we could have retrieved from `/proc/1234537/environ` already ofc, but not `str`). An all-in-one gdb script makes this a bit easier, and assumes that the bash binary built with debugging information is available in `./bash-5.1/bash`:

```
define add-symbol-file-bash
  shell echo set \$text_address=$(readelf -WS $arg0 | grep .text | awk '{ print "0x"$5 }') >/tmp/temp_gdb_text_address.txt
  source /tmp/temp_gdb_text_address.txt
  shell rm -f /tmp/temp_gdb_text_address.txt
  add-symbol-file $arg0 $text_address
end

add-symbol-file-bash ./bash-5.1/bash

define print_keys_vals
  set $current = shell_variables
  while $current != 0
    set $bucket = $current->table->bucket_array
    set $nbuckets = $current->table->nbuckets
    set $i = 0
    while $i < $nbuckets
      set $entry = $bucket[$i]
      while $entry != 0
        set $shell_var = (SHELL_VAR *)$entry->data
        printf "      Name: %s\n", $shell_var->name
        printf "      Value: %s\n", $shell_var->value
        set $entry = $entry->next
      end
      set $i = $i + 1
    end
    set $current = $current->down
  end
end


print_keys_vals
```

---

If you want to see the contents of associative arrays too, then you'll need to cast the value to the [ARRAY type](https://github.com/bminor/bash/blob/2bb3cbefdb8fd019765b1a9cc42ecf37ff22fec6/array.h#L41) and walk through the list, too:

```

define print_keys_vals
  set $current = shell_variables
  while $current != 0
    set $bucket = $current->table->bucket_array
    set $nbuckets = $current->table->nbuckets
    set $i = 0
    while $i < $nbuckets
      set $entry = $bucket[$i]
      while $entry != 0
        set $shell_var = (SHELL_VAR *)$entry->data
        printf "      Name: %s\n", $shell_var->name
        if ($shell_var->attributes & 0x4)
          set $array = ((ARRAY *)$shell_var->value)
          set $narray = $array->num_elements
          set $n = 0
          set $node = $array->head
          printf "      Value: "
          while $n < $narray
            set $n = $n + 1
            if $node != 0
              printf "%s, ", $node->value
              set $node = $node->next
            end
          end
          printf "\n"
        else
          printf "      Value: %s\n", $shell_var->value
        end   
        set $entry = $entry->next
      end
      set $i = $i + 1
    end
    set $current = $current->down
  end
end
```
