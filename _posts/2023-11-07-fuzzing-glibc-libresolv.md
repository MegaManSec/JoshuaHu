---
layout: post
title: "Fuzzing glibc's libresolv's res_init()"
author: "Joshua Rogers"
categories: security
---

Looking back at the issue I [had with libresolv nearly 10 years ago](https://joshua.hu/revisiting-my-old-blog), I decided it might be interesting to fuzz glibc's [res_init()](https://man7.org/linux/man-pages/man3/res_init.3.html) to see if we can find any bugs.

Most of the processing of `res_init()` happens when `/etc/resolv.conf` is parsed, so we're just going to make a program that creates `/etc/resolv.conf` and fills it with data and calls `res_init()`.

No need to trash our harddrive, so let's use a ram disk:
```bash
mkdir -p /tmp/fuzz
mount -t tmpfs -o size=100M tmpfs /tmp/fuzz
```

We're going to `chroot` into `/tmp/fuzz/*` in order to not destroy anything on our server, too,

```C
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <resolv.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>

__AFL_FUZZ_INIT();
int main(int argc, char **argv) {
  char chroot_dir_base[] = "/tmp/fuzz/";
  char resolv_conf_path[] = "/etc/resolv.conf";

  int dir_suffix = 1;
  char chroot_dir[256];

  while (1) { // find a new /tmp/fuzz/[number]/ directory to use for our chroot.
    snprintf(chroot_dir, sizeof(chroot_dir), "%s%d/", chroot_dir_base, dir_suffix);
    if (access(chroot_dir, F_OK) != 0) {
      if (mkdir(chroot_dir, 0755) != 0) {
        dir_suffix++;
        continue;
      } else {
        break;
      }
    }

    dir_suffix++;
  }

  if (chroot(chroot_dir) != 0) { //chroot into /tmp/fuzz/[number]/
    perror("chroot");
    return 1;
  }

  if (access("/etc/", F_OK) != 0) { //create /etc/
    if (mkdir("/etc/", 0755) != 0) {
      perror("mkdir 2");
      return 1;
    }
  }

  __AFL_INIT();
  unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;
  while (__AFL_LOOP(1000000)) {
    int len = __AFL_FUZZ_TESTCASE_LEN;
    FILE *resolv_conf = fopen(resolv_conf_path, "w"); //create /etc/resolv.conf
    if (resolv_conf == NULL) {
      perror("fopen?");
      continue;
    }

    fprintf(resolv_conf, "%s\n", buf);
    fclose(resolv_conf);

    if (res_init() != 0) { //res_init should always return 0t
      abort();
    }
  }

  return 0;
}
```

We create different numbers /tmp/fuzz/ folders for each chroot because there will be a race condition if all of the fuzzers are writing /tmp/fuzz/etc/resolv.conf at the same time.

Compiling it with afl-fuzz, we find two unique issues within about 5 seconds.

---

### Infinite loop in sortlist handling
The first issue is related to the _sortlist_ directive. _sortlist_ is an obsolete directive which allows for networks or subnets to be prefered if [multiple addresses are received from a dns query](https://docstore.mik.ua/orelly/networking_2ndEd/dns/ch06_01.htm#dns4-CHP-6-SECT-1.5.html). The C code for parsing this directive looks like:
```C
while (true)
  {
    while (*cp == ' ' || *cp == '\t')
      cp++;
    if (*cp == '\0' || *cp == '\n' || *cp == ';')
      break;
      
    char *net = cp;
    while (*cp && !is_sort_mask (*cp) && *cp != ';'
           && isascii (*cp) && !isspace (*cp))
      cp++;
    char separator = *cp;
    *cp = 0;
    struct resolv_sortlist_entry e;
    if (__inet_aton (net, &a))
      {
        [..]
      }
    *cp = separator;
  }
```
Cycling through the line until the value for for the _sortlist_ directive is found, _separator_ is any character which is not: _;_ _[space]_ _[ascii]_ _&_ or _/_. Once a separator (or the end of the buffer) is found, everything before then is assumed to be some type of address and a null byte is placed at the separator. However, if `__inet_aton()` fails, the "separator" is placed back where it was in the _cp_ buffer, meaning the loop will continue. The loop will continue forever in the case of the character being not the aforementioned _;_ _[space]_ _[ascii]_ _&_ or _/_.

Therefore, if we print, say, `\x321 ` into a value for _sortlist_, this will loop forever. `printf "sortlist 192.0\3212.0" >> /etc/resolv.conf ; ping example.com` will hang forever. I can imagine embedded devices which allow you to set `/etc/resolv.conf` could be completely bricked by this, as anything using glibc's libresolv when any function that calls `res_init()` (AKA all libresolv functions) will simply hang forever. Reported in [31025](https://sourceware.org/bugzilla/show_bug.cgi?id=31025).

### Reachable assertion in resolv_conf.c:570: update_from_conf: Assertion `resolv_conf_matches (resp, conf)' failed.

Another less interesting issue was an assert in the _search_ directive. The technical details are boring, but I'm surprised nobody has noticed this before:
```
echo "search example.org example.com example.net corp.corp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.examcorp.exam" >> /etc/resolv.conf
# ping example.com
ping: resolv_conf.c:570: update_from_conf: Assertion `resolv_conf_matches (resp, conf)' failed.
Aborted
```

Basically if the directive for _search_ is greater than 255 characters, an assertion. Reported in [31026](https://sourceware.org/bugzilla/show_bug.cgi?id=31026).

---

Has nobody fuzzed glibc before? How strange.
