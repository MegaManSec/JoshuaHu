---
layout: post
title: "Fuzzing scripting languages and interpreters natively using AFL++ to find memory corruption and more"
author: "Joshua Rogers"
categories: personal
---

Fuzzing applications needs no introduction, and I have written about some interesting problems related to fuzzing in the past [0](https://joshua.hu/fuzzing-multiple-servers-parallel-aflplusplus-nfs)[1](https://joshua.hu/fuzzing-glibc-libresolv)[2](https://joshua.hu/fuzzing-with-memfd-createfd-fmemopen-syscall-function)[3](https://joshua.hu/aflplusplus-generate-fuzzing-campaign-commands-options-secondary-fuzzers). At scale, fuzzing has traditionally focused on compiled binaries and detecting crashes and other memory corruption issues. In this blog, we'll be looking at how you can easily fuzz _scripting_ languages whether it be php, perl, ruby, python, or even lisp, using the fuzzing software traditionally built for binaries. We'll also look at some interesting bug classes which can be caught this way.

---

Many scripting languages/interpreters are, at their core, written in C or C++, meaning their security is directly coupled to the C/C++ codebase underneath the hood. As such, we're effectively going to be fuzzing the native code underlying the scripting language's interpreter.

For ease-of-use, we'll be using the [AFL++](https://github.com/AFLplusplus/AFLplusplus) fuzzer. We'll be attacking the [Pike](https://pike.lysator.liu.se/) scripting language, which is written in C; Pike being something I've also [written about previously](https://joshua.hu/pikeproof-wycheproof-pike-checks).

---

The general idea is simple: instead of attempting (and miserably failing) to add fuzzing harnesses into Pike's internal C code to fuzz individual C functions, we instead just make use of what Pike is: a scripting language! So, we create some new _Pike scripting functions_ inside the C codebase, which we can then call via a _Pike script_. Then, instead of fuzzing C functions in the Pike codebase directly, we instead just write a Pike script and fuzz the Pike scripting functions as if the fuzzer was natively integrated into the Pike language (which, in a way, it is).

Normally when using AFL++ to fuzz C code, you call the `__AFL_LOOP()` macro to loop through each of the fuzzing payloads. AFL++'s [afl-cc.c](https://github.com/AFLplusplus/AFLplusplus/blob/36db3428ab16156dd72196213d2a02a5eadaed11/src/afl-cc.c#L1560) outlines how this macro is expanded into, among other things, a call to the `__afl_persistent_loop(unsigned int max_cnt)` function. This function continuously reads inputs, and copies them into a char buffer. As such, it is as simple as creating an inbuilt Pike function which calls this C function, which will be available when Pike is built using AFL++'s compiler:

```C
extern int __afl_persistent_loop(unsigned int count);
PIKEFUN int AFL_LOOP(unsigned int i)
{
  RETURN __afl_persistent_loop(i);
}
```

This code is added to Pike's [src/builtin.cmod](https://github.com/pikelang/Pike/blob/1af958923b31838ea1ee95767f2eb4a9b88306b6/src/builtin.cmod#L740) file, which is used to define some of the inbuilt functions of the scripting language.

In order for AFL++ to notice that we are using persistent mode, we also need to include a constant in the code that the fuzzer will find. That is as simple as adding to [src/main.c](https://github.com/pikelang/Pike/blob/1af958923b31838ea1ee95767f2eb4a9b88306b6/src/main.c#L302):

```C
static volatile char AFL_PERSISTENT[] = "##SIG_AFL_PERSISTENT##";
```

Basically, `afl-fuzz` uses this constant to ensure that the binary was compiled with the correct compiler and macro, so we have to add it manually.

---

In theory, we could also add a function (and constant) for AFL++'s deferred forkserver mode, which in C are characterized by:
```C
static volatile char AFL_DEFER_FORKSVR[] = "##SIG_AFL_DEFER_FORKSRV##";
void                 __afl_manual_init();
```
however I didn't do this with Pike: I found that some type of internal state was being corrupted when this was used, and didn't bother investigating why (the speedup is minimal due to our use of persistent mode).

---

In addition to the main AFL++ loop function, I also added internal Pike functions for selectively enabling and disabling coverage, so we can focus the fuzzing on specific functionality and not flood the AFL++ bitmap. By adding `__AFL_COVERAGE_START_OFF();`, fuzzing coverage is not collected until coverage is specifically turned on. Selective instrumentation [is documented here](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.instrument_list.md#2-selective-instrumentation-with-_afl_coverage-directives). Once again in `src/builtins.cmod`:

```C
__AFL_COVERAGE();
__AFL_COVERAGE_START_OFF();
extern void __afl_coverage_on();
extern void __afl_coverage_off();
PIKEFUN void AFL_BEGIN_COVERAGE()
{
  __AFL_COVERAGE_ON();
}
PIKEFUN void AFL_END_COVERAGE()
{
  __AFL_COVERAGE_OFF();
}
```

---

Now we need to build the interpreter. For Pike, this ended up being more difficult than expected, due to its antiquated build system. Specifically, compiling the interpreter without `-O1` would not allow AFL++'s llvm module to correctly use LTO. And forget about any type of parallelized building, either:
```bash
export CC=afl-clang-lto
export CXX=afl-clang-lto++
CFLAGS='-O1 -fcf-protection=none -flto -fno-common -fno-inline' CPPFLAGS='-O1 -fcf-protection=none -flto -fno-common -fno-inline' AFL_HARDEN=1 make CONFIGUREARGS='--without-dynamic-modules --without-copt --without-machine-code --without-fuse'
```

---

Pike is now built and we can now create a Pike _script_ to start fuzzing the internal functions of the language (or we could simply fuzz whatever Pike/scripting code we have and find non-memory-related bugs). We have a lot to choose from: image decoders, JSON parsers, BSON parsers, and so on. In this case, we'll look at Pike's serializer and deserializer: [encode_value](https://pike.lysator.liu.se/generated/manual/modref/ex/predef_3A_3A/encode_value.html) and [decode_value](https://pike.lysator.liu.se/generated/manual/modref/ex/predef_3A_3A/decode_value.html#decode_value).

Our Pike script looks like this:
```C
int main() {
        while(__builtin.AFL_LOOP(10000)) { // Read 10,000 fuzzing payloads before restarting.
                string data = Stdio.stdin.read(); // Read fuzzing payload from stdin.
                __builtin.AFL_BEGIN_COVERAGE(); // Starts coverage. This line is _required_ before fuzzing happens, otherwise there will be no coverage data at all.
                array error = catch { // Catch any errors.
                      mixed decoded = decode_value(data, -1);
                };
                __builtin.AFL_END_COVERAGE(); //Ends coverage.
        }
        return 0;
}
```
In the code, just like using AFL++ with a C codebase, we loop by calling the `builtin.AFL_LOOP()` function, read data from stdin, begin the coverage collection for coverage-guided fuzzing, and then finally pass the fuzzing payload to the function we want to fuzz: `decode_value`. Note: the second parameter of `decode_value` is outlined in the documentation: `Decoding a coded_value that you have not generated yourself is a security risk that can lead to execution of arbitrary code, unless codec is specified as -1.` This is important because if `decode_value` causes some type of crash when it's called in this "safe mode", then it is by definition a security issue.

We start fuzzing as normal: `afl-fuzz -t 1000 -i inputs/ -o output/ -M Main ./build/linux-x86_64/pike fuzzing_script.pike` and away the fuzzer goes.

---

Fuzzing scripting languages is not only about finding memory-related crashes in the base C code. I found some interesting bugs using this fuzzing technique of the Pike scripting language.

---

In the aforementioned looping of fuzzing payloads, the interpreter has a pre-defined path of execution: 1) begin, 2) perform actions, 3) exit. But what if something goes wrong during this path and the interpreter doesn't behave as expected? That's something that was discovered. In the following code, calling `do_something(data)` should never make the interpreter cease execution, since any errors should be caught:

```C
int main() {
        while(__builtin.AFL_LOOP(10000)) {
                string data = Stdio.stdin.read();
                __builtin.AFL_BEGIN_COVERAGE();
                array error = catch { mixed var = do_something(data); };
                __builtin.AFL_END_COVERAGE();
        }
        return 0;
}
```

To prove this, I changed Pike's interpreter to abort when exiting normally, by editing the final line of (reachable) code in [src/main.c](https://github.com/pikelang/Pike/blob/7d99ae0328982c37436f15db1caaa453acd09563/src/main.c#L692) to `abort();`. Then in the Pike script, `return 0;` was replaced with `_exit(0);` (which calls the [C code `exit`](https://pike.roxen.se/generated/manual/modref/ex/predef_3A_3A/_exit.html#_exit) directly).

As it turned out, there was a bug in the `do_something` function which, given a specific input, resulted in Pike simply "walking away from its responsibilities, and exiting the interpreter". Not great, for things running as a daemon especially.

---

When fuzzing the aforementioned `decode_value` function, hundreds of empty files were being created in the directory that the fuzzer was running. Since this wasn't causing any type of crash, determining which fuzzing inputs were causing the files to appear required first retrieving a count of files in the current directory, calling the fuzzed function, then again retrieving a count of the files in the current directory: if there was a new file, then we forcefully crashed:

```C
int main() {
        while(__builtin.AFL_LOOP(10000)) {
                string data = Stdio.stdin.read();
                array file_count = get_dir(); // return an array corresponding to all of the files in the current directory

                __builtin.AFL_BEGIN_COVERAGE();
                array error = catch { mixed var = decode_value(data, -1); };

                array second_file_count = get_dir();
                if(sizeof(file_count) != sizeof(second_file_count))
                    crash();

                __builtin.AFL_END_COVERAGE();
        }
        return 0;
}
```

---

Testing for "correctness" of functions also proved to be quite helpful with some bugs found. That involves doing something like:

```C
int main() {
        while(__builtin.AFL_LOOP(10000)) {
                string data = Stdio.stdin.read();
                __builtin.AFL_BEGIN_COVERAGE();
                array error = catch { mixed var = do_something(data); };
                if(!error) {
	                      var = undo_something(var);
	                      if (var != data)
	                              crash();
	              }
                __builtin.AFL_END_COVERAGE();
        }
        return 0;
}
```

---

Lots of other testing can be done too. In late 2021, I submitted a patch to the AFL++ codebase to make [fuzzing for memory leaks possible](https://blogs.opera.com/security/2022/01/fuzzing-http-proxies-privoxy-part-3/), which a scripting language certainly shouldn't be doing either.

Likewise, AFL++ recently added preliminary support for [fuzzing for injections like SQLi, XSS, and and LDAPi](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.injections.md). This seems like a prime target for future research using the fuzzing method outlined in this blog post.

Even whole codebases can be fuzzed this way: if the code handles some arbitrary data, just start fuzzing it instead of sending random payloads, ensuring that the codebase will abort or raise some error which AFL++ will pick up (the environmental value `AFL_CRASH_EXITCODE` can be used to specify an [error code indicating an error](https://github.com/AFLplusplus/AFLplusplus/blob/stable/docs/env)_variables.md#4-settings-for-afl-fuzz).
