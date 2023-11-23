---
layout: post
title: "More fun with bash: bash, ssh, and ssh-keygen version quirks"
author: "Joshua Rogers"
categories: security
---

Continuing the journey with bash, ssh, and so on, I hit some more fun facts and/or pitfalls of the trade.

Version numbers/ranges here aren't accurate, but the versions I've tested on.

---
### bash writes files to the disk for larger here-document operations:
How much can you get away with while having zero disk space? Surprisingly a lot. Most of the operations in bash happen in memory or read-only. In some cases however, here-documents will use disk space. 
```bash
$ sudo mount -t tmpfs -o size=1M none "/dev/shm/empty"
$ dd if=/dev/zero of=/dev/shm/empty/1 bs=1
$ TMPDIR=/dev/shm/empty/ cat <<< "$(perl -e "print 'X' x 65536")"
-bash: cannot create temp file for here-document: No space left on device
```
65536 is one byte larger than the default maximum pipe size on Linux. The bash source code explains:
```
  /* Try to use a pipe internal to this process if the document is shorter
     than the system's pipe capacity (computed at build time). We want to
     write the entire document without write blocking. */
```

---
###  bash <= 4.3 considers empty arrays as unset:
```bash
#!/bin/bash
set -o nounset

ignored_users=()

for i in "${ignored_users[@]}"; do # bash: ignored_users[@]: unbound variable
  echo "$i"
done
```

---
### bash > 4 expands in-variable array keys:
```bash
#!/bin/bash
declare -A my_array
un='$anything'

[[ -v my_array["$un"] ]] && return 1
```

This results is the error `line 4: my_array: bad array subscript`. Basically, _\$un_ gets expanded to _\$anything_ which gets expanded to nothing, thus making the script effectively run `[[ -v my_array[] ]]` which is invalid. We can see it when using bash's -x flag:
```bash
$ bash -x t.sh  # Bash 4.3
+ declare -A my_array
+ un='$anything'
+ [[ -v my_array[$anything] ]]
t.sh: line 5: my_array: bad array subscript
```

---
### bash > 4 expands AND executes in-variable array keys:
```bash
$ declare -A my_array
$ un='$(huh)'
$ [[ -v my_array["$un"] ]] && return 1
-bash: huh: command not found
-bash: my_array: bad array subscript
```

Arbitrary command execution if our variable(!) is `$(..)` the command will be executed! Great.. This issue is documented [here](https://mywiki.wooledge.org/BashPitfalls#A.5B.5B_-v_hash.5B.24key.5D_.5D.5D).

---
### ssh-keygen <= 6.6.1 can only display MD5 fingerprint hashes:
```bash
$ ssh-keygen -E md5 -lf .ssh/authorized_keys
unknown option -- E
usage: ssh-keygen [options]
```
Because why would anybody ever need anything other than MD5?!

---
### ssh <= 6.6.1 does not allowing appending to HostbasedKeyTypes or KexAlgorithms:
```bash
$ ssh -oHostkeyAlgorithms=+ssh-rsa -oKexAlgorithms=+diffie-hellman-group1-sha1 host
command-line line 0: Bad protocol 2 host key algorithms '+ssh-rsa'.
```

---
### ssh-keygen <= 6.6.1 does not differentiate between invalid passphrase and invalid format:
```bash
$ ssh-keygen
Generating public/private rsa key pair.
Enter file in which to save the key (/home/sdev/.ssh/id_rsa):
Enter passphrase (empty for no passphrase): 
Enter same passphrase again: 
Your identification has been saved in .ssh/id_rsa.
Your public key has been saved in .ssh/id_rsa.pub.
The key fingerprint is:
a7:60:50:03:8b:84:28:02:91:d4:f7:63:91:8b:c4:d2
The key's randomart image is:
+--[ RSA 2048]----+
|*=o +.o .        |
|*. + E +         |
|o . * o o        |
|     o =         |
|      + S .      |
|     . . o       |
|        .        |
|                 |
|                 |
+-----------------+
$ ssh-keygen -P test -y -f .ssh/id_rsa
load failed
$ ssh-keygen -P test -y -f /etc/passwd
load failed
```

Newer versions print "incorrect passphrase supplied to decrypt private key" and "invalid format" respectively.

---
### ssh-keygen <= 6.6.1 cannot convert unprotected ssh private keys into their respective public key hashes:
```bash
$ rm .ssh/id_rsa.pub ; ssh-keygen -lf .ssh/id_rsa
key_read: uudecode PRIVATE KEY----- failed
key_read: uudecode PRIVATE KEY----- failed
.ssh/id_rsa is not a public key file.
```

---
### ssh-keygen <= 6.6.1 cannot convert a private key to a public key if the permissions are too public and a passphrase is not provided (even if the key doesn't have a passphrase):
```bash
$ chmod 777 ./ssh/id_rsa
$ ssh-keygen -y -f ./ssh/id_rsa 
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0777 for './ssh/id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
bad permissions: ignore key: ./ssh/id_rsa
Enter passphrase: 
```

I couldn't imagine why it asks for a passphrase at all.

---
###  ssh-keygen > 6.6.1 CAN convert unprotected ssh private keys into their respective public key hash even if they are too public:
```bash
$ chmod 777 ./ssh/id_rsa
$ ssh-keygen -E md5 -lf .ssh/id_rsa
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0777 for 'id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
8192 MD5:a7:60:50:03:8b:84:28:02:91:d4:f7:63:91:8b:c4:d2 no comment (RSA)
```

The hash is printed to stdout and the rest to stderr. The return code is 0.

---
### ssh-keygen <= 6.6.1 AND > 6.6.1 CAN convert an unprotected private key into a private key and then convert the public key into a hash:

```bash
$ ssh-keygen -lf /dev/stdin <<<$(ssh-keygen -yf .ssh/id_rsa)
8192 MD5:a7:60:50:03:8b:84:28:02:91:d4:f7:63:91:8b:c4:d2 no comment (RSA)
```

But if you need to do that fileless, you have to:

```bash
$ ssh-keygen -lf <( (cat .ssh/id_rsa))
8192 MD5:a7:60:50:03:8b:84:28:02:91:d4:f7:63:91:8b:c4:d2 no comment (RSA)
```

However, unfortunately, that's also not possible for all versions of ssh-keygen:

```bash
$ ssh-keygen -lf <( (cat .ssh/id_rsa))
/dev/fd/63 is not a public key file
```
