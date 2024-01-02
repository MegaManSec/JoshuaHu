---
layout: post
title: "Fuzzing with memfd_create(2) and fmemopen(3)"
author: "Joshua Rogers"
categories: security
---

If you've done a fair amount of fuzzing, you've likely come across targets which are deeply dependent either on file descriptors or FILEs. Rewriting the whole codebase to accept a fuzzing harness from a buffer in shared memory is awfully cumbersome, so you're stuck with a slower fuzzing campaign than you'd hope. But then you hear about the `memfd_create(2)` syscall and the `fmemopen(3)` function.

1. _memfd_create()  creates an anonymous file and returns a file descriptor that refers to it.  The file behaves like a regular file, and so can be modified, truncated, memory-mapped, and so on.  However, unlike a regular file, it lives in RAM and has a volatile backing storage._
2. _The fmemopen() function opens a stream that permits the access specified by mode.  The stream allows I/O to be performed on the string or memory buffer pointed to by buf._

Basically, this syscall and this function can be used to create files which only exist in memory: and they can have arbitrary data from memory written to them. This post investigates the comparison of a fuzzing campaign's speed using them instead of traditional files on a tmpfs/ram-disk.

# Code

To create these benchmarks, we fuzz libxml2 with [aflplusplus](https://github.com/aflplusplus/aflplusplus). We compile with afl-clang-lto and no special hardening flags or optimization flags

We create four different programs.

## memfd_create(2)

```C
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <libxml/parser.h>


__AFL_FUZZ_INIT();
int main() {

  __AFL_INIT();
  unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;
  while (__AFL_LOOP(100000)) {
    int len = __AFL_FUZZ_TESTCASE_LEN;

    int memfd = memfd_create("xml_memory", 0);

    const char *xmlContent = buf;

    write(memfd, xmlContent, len);

    lseek(memfd, 0, SEEK_SET);

    xmlDocPtr doc = xmlReadFd(memfd, NULL, NULL, XML_PARSE_NOBLANKS);
    if (doc == NULL) {
        close(memfd);
        continue;
    }

    xmlFreeDoc(doc);
    xmlCleanupParser();
    close(memfd);
  }
    return 0;
}
```

## fmemopen(3)

As it turns out, you cannot call `fileno(3)` on a FILE which has been returned using `fmemopen(3)`. From the manpage: `There is no file descriptor associated with the file stream returned by this function (i.e., fileno(3) will return an error if called on the returned stream).`  Therefore, we proceed slightly differently.

```C
...
static int myRead(void *f, char *buf, int len) {
    return(fread(buf, 1, len, (FILE *) f));
}
static int myClose(void *context) {
    FILE *f = (FILE *) context;
    return(fclose(f));
}

__AFL_FUZZ_INIT();
int main() {

  __AFL_INIT();
  unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;
  while (__AFL_LOOP(100000)) {
    int len = __AFL_FUZZ_TESTCASE_LEN;

    FILE *memFile = fmemopen((void *)buf, len, "r");
    if (!memFile) {
        continue;
    }

    xmlDocPtr doc = xmlReadIO(myRead, myClose, memFile, NULL, NULL, XML_PARSE_NOBLANKS);
...
```

## stdin

```C
int main() {

  __AFL_INIT();
  while (__AFL_LOOP(100000)) {

    xmlDocPtr doc = xmlReadFd(STDIN_FILENO, NULL, NULL, XML_PARSE_NOBLANKS);
    if (doc == NULL) {
        fprintf(stderr, "Failed to parse XML from stdin\n");
        continue;
    }

    xmlFreeDoc(doc);
    xmlCleanupParser();
  }

    return 0;
}
```

## /dev/shm/file


```C
int main(int argc, char** argv) {

  __AFL_INIT();
  while (__AFL_LOOP(100000)) {

    xmlDocPtr doc = xmlReadFile(argv[1], NULL, XML_PARSE_NOBLANKS);
    if (doc == NULL) {
        continue;
    }

    xmlFreeDoc(doc);
    xmlCleanupParser();
  }

    return 0;
}
```



# Results

After fuzzing for one hour, the results show average executions per second:


|        | memfd_create(2) | fmemopen(3) | stdin | /dev/shm/file (tmpfs)
|--------|--------------|----------|-------|--------------|
| exec/s | 5548         | 9169        | 4626  | 2770         |


As we can see, the `fmemopen(3)` function is a clear winner. `memfs_create(2)` is second with `stdin` not far behind. Using files in a tmpfs comes dead last.

Why is `fmemopen(3)` so much faster than the others? Well if we use `strace(1)` to take a look at what's going on under the hood, we can see the various syscalls associated with each program:

## memfd_create(2)


```C
memfd_create("xml_memory", 0)           = 3
write(3, "<root><element>Content</element>"..., 39) = 39
lseek(3, 0, SEEK_SET)                   = 0
read(3, "<root><element>Content</element>"..., 4000) = 39
read(3, "", 4000)                       = 0
close(3)                                = 0
```

## fmemopen(3)

```C

```

## stdin

```C
read(0, "<root><element>Content</element>"..., 4000) = 40
read(0, "", 4000)                       = 0
```

## /dev/shm/file

```C
newfstatat(AT_FDCWD, "/dev/shm/file", {st_mode=S_IFREG|0664, st_size=39, ...}, 0) = 0
newfstatat(AT_FDCWD, "/dev/shm/file", {st_mode=S_IFREG|0664, st_size=39, ...}, 0) = 0
newfstatat(AT_FDCWD, "/dev/shm/file", {st_mode=S_IFREG|0664, st_size=39, ...}, 0) = 0
openat(AT_FDCWD, "/dev/shm/file", O_RDONLY) = 3
lseek(3, 0, SEEK_CUR)                   = 0
read(3, "<root><element>Content</element>"..., 8192) = 39
read(3, "", 8153)                       = 0
close(3)                                = 0
```

---

We can see that using a file in shared memory is slower because many more syscalls must be executed associated with the file permissions, opening the file, seeking to the beginning of the file, reading the file, and then closing the file.

Despite `memfd_create(2)` using more syscalls, it is in fact faster than stdin; I'm not sure why, but I would probably suggest that the two would converge on a much more similar exec/s if left fuzzing for longer.

The `fmemopen(3)` section is deliberately left blank. It uses no syscalls for reading the input and fuzzing. Everything is done in userland. Since there are no syscalls being called, the speed nearly doubles.

# Conclusion

Clearly, `fmemopen(3)` is a powerful tool in a fuzzer's toolkit. If you're indebted to FILEs, use it to your advantage -- don't bother reading files even if they're in a tmpfs; if you're stuck with file descriptors, then it seems using stdin doesn't make a huge difference in place of `memfd_create(2)` so just go with stdin.
