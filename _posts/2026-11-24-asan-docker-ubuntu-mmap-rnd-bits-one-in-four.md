---
layout: post
title: "Why ASan crashes one run in four in Docker on Ubuntu"
tags: [linux, fuzzing, vuln_research]
description: "Older ASan runtimes reserve a fixed 4TiB heap at 0x600000000000. With Ubuntu's vm.mmap_rnd_bits=32, a PIE binary is loaded inside that range one run in four, and ASan maps its heap right over the program. Containers are where an old ASan meets a new kernel."
---

In my [post about sanitizers as an oracle](https://joshua.hu/lessons-using-sanitizers-oracle-llm-vulnerability-triage#b2-asan-in-docker), I noted that ASan inside Docker on Ubuntu hangs or crashes "about one run in four", and that the fix is `vm.mmap_rnd_bits=28` on the host. I also said that Ubuntu "randomize[s] more of the address space than ASan's shadow memory can live with". That last part turns out to be wrong, and I wanted to look more into why this happened, and why only one in four times.

Let's take a one-byte oob vulnerable code:

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
  char *p = malloc(8);
  printf("main=%p heap=%p\n", (void *)main, (void *)p);
  p[argc + 7] = 'x';
  free(p);
  return 0;
}
```

...

```console?prompt=$,#
$ gcc -g -fsanitize=address overflow.c -o of-gcc && ./of-gcc 2>&1 | head -3
=================================================================
==411033==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x7b979bbe0018 at pc 0x55c12fec82b1 bp 0x7ffc08c5de00 sp 0x7ffc08c5ddf0
WRITE of size 1 at 0x7b979bbe0018 thread T0
```

On an Ubuntu 26.04 host with `vm.mmap_rnd_bits=32` (Ubuntu's default), ASAN hits every time. Building the same file inside a set of docker instances, each ran 100 times, results in the following:

| Image | Compiler | Reported | Otherwise |
|---|---|---|---|
| `debian:bookworm` | gcc 12.2.0 | 69 | 31 hung, printing `AddressSanitizer:DEADLYSIGNAL` forever |
| `debian:bookworm` | clang 14.0.6 | 76 | 24 died with a plain `Segmentation fault` |
| `ubuntu:22.04` | gcc 11.4.0 | 100 | |
| `ubuntu:22.04` | clang 14.0.0 | 84 | 16 died with a plain `Segmentation fault` |
| `ubuntu:24.04` | gcc 13.3.0, clang 18.1.3 | 100 | |
| `debian:trixie` | gcc 14.2.0, clang 19.1.7 | 100 | |

The gcc failure looks like this, until something kills it:

```console?prompt=$,#
AddressSanitizer:DEADLYSIGNAL
AddressSanitizer:DEADLYSIGNAL
AddressSanitizer:DEADLYSIGNAL
AddressSanitizer:DEADLYSIGNAL
```

And the clang one is just:

```console?prompt=$,#
Segmentation fault
```

There are no ASAN reports at all, and in fact ASAN never even got to `main()`. Looking at what's going on, we need to look at how the binary is loaded when built with ASAN.

`vm.mmap_rnd_bits` is how many bits of randomness the kernel uses for mmap placement on x86-64, and the same number of bits also randomizes where a PIE executable is loaded. The executable's base starts at `0x555555554000` (two-thirds of the 47-bit address space), and gets up to 2<sup>bits</sup> pages added to it:

* With 28 bits, that's up to 1TiB, so the binary always lands somewhere in `0x555555554000`-`0x565555554000`.
* With 32 bits, that's up to 16TiB, so the binary lands anywhere up to `0x655555554000`.

`28` is the kernel's minimum (`CONFIG_ARCH_MMAP_RND_BITS_MIN`) and the upstream default; Ubuntu builds its kernels with `32`, the maximum, and has done since [early 2024](https://llbit.github.io/posts/2024-03-19-aslr-asan-problem.html):

```console?prompt=$,#
$ grep CONFIG_ARCH_MMAP_RND_BITS /boot/config-$(uname -r)
CONFIG_ARCH_MMAP_RND_BITS_MIN=28
CONFIG_ARCH_MMAP_RND_BITS_MAX=32
CONFIG_ARCH_MMAP_RND_BITS=32
```

Using `LD_SHOW_AUXV=1` to print each run's `AT_ENTRY` (the binary's entry point), we can see bookworm's results when run 200 times:

| Binary loaded at | gcc 12 | clang 14 |
|---|---|---|
| `0x55..` to `0x5f..` | 138 reported, 0 failed | 132 reported, 0 failed |
| `0x60..` to `0x63..` | 0 reported, 48 failed | 0 reported, 45 failed |
| `0x64..` to `0x65..` | 14 reported, 0 failed | 23 reported, 0 failed |

Every run where the binary was loaded between `0x600000000000` and `0x640000000000` failed, and every other run worked. So there's something going on inside there. But what, and why?

Older ASan runtimes put their heap at a hardcoded address: a 4TiB region starting at `0x600000000000` (`kAllocatorSpace` in compiler-rt). In a failing run, using `strace`, we can see the binary loaded with `AT_ENTRY` at `0x63decba3f2e0`, and then ASan does this:

```console?prompt=$,#
mmap(0x7fff7000, 268435456, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS|MAP_NORESERVE, -1, 0) = 0x7fff7000
mmap(0x2008fff7000, 15392894357504, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS|MAP_NORESERVE, -1, 0) = 0x2008fff7000
mmap(0x8fff7000, 2199023255552, PROT_NONE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS|MAP_NORESERVE, -1, 0) = 0x8fff7000
mmap(0x600000000000, 4398046519296, PROT_NONE, MAP_PRIVATE|MAP_FIXED|MAP_ANONYMOUS|MAP_NORESERVE, -1, 0) = 0x600000000000
--- SIGSEGV {si_signo=SIGSEGV, si_code=SEGV_ACCERR, si_addr=0x63decbadb321} ---
```

The first three are the shadow memory (and the inaccessible gap between its two halves), and they're fine, but the fourth reserves the heap: 4TiB of `PROT_NONE` at `0x600000000000`, with `MAP_FIXED`. `MAP_FIXED` doesn't fail when something is already mapped there; it silently replaces it. What was there was the program itself. The next instruction faults (`SEGV_ACCERR` at `0x63decbadb321`, inside the binary), because the program's own code is now an inaccessible reservation. With gcc 12's runtime, ASan's own signal handler catches the fault (which is what the `DEADLYSIGNAL` line is about), and the same fault comes straight back, forever. With clang 14's, the process just dies.

So it's not the shadow memory that can't live with the randomization (as I mentioned in the previous post), but rather the heap. And the one in four is just the proportion, since the binary is loaded somewhere in a 16TiB range, 4TiB of which is ASan's heap.

Also, all things considered:

* 31 bits works fine for ASAN, since 8TiB of randomization tops out at `0x5d5555554000`, short of `0x600000000000`
* `-no-pie` also works fine, since a non-PIE binary is loaded at `0x400000`, nowhere near the heap.

---

Then the question is also why did I hit this only in Docker?

As it turns out, it isn't really Docker, but rather an old ASAN runtime on a new kernel, which mixes the old ASAN with the host's `vm.mmap_rnd_bits`.

The fix for ASAN itself landed in [April 2023](https://lists.llvm.org/pipermail/llvm-commits/Week-of-Mon-20230410/1146796.html), when the heap was moved to `0x500000000000`. Since a PIE binary is never loaded below `0x555555554000`, it can no longer collide, regardless of the amount of bits used. We can also see which side of the commit (fix) we're on from the heap address in the report:

| Toolchain | Heap address in the report |
|---|---|
| bookworm gcc 12, clang 14 (bookworm and 22.04) | `0x602000000018` |
| 22.04 gcc 11, 24.04 gcc 13 / clang 18, trixie gcc 14 / clang 19 | `0x502000000018` |
| 26.04 gcc 15 / clang 21 | `0x7b979bbe0018` (no fixed address at all anymore) |

Also the odd one out is Ubuntu 22.04, whose gcc 11 has the fix (Ubuntu [patched it](https://bugs.launchpad.net/bugs/2058411)), but its clang 14 doesn't. So the same `ubuntu:22.04` container is fine or broken depending on `CC`.

So, the setting is the host's, and only the host can change it.

Also in reality, setting `vm.mmap_rnd_bits=31` would be fine just for ASAN, but TSAN and MSAN have their own (stricter) layout requirements, and 28 is what everything was built against anyway, so `vm.mmap_rnd_bits=28` it is.
