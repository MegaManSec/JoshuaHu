---
layout: post
title: "Comparing different versions of AWK with WebAssembly"
author: "Joshua Rogers"
categories: security
---

After releasing [SSH-Snake](https://github.com/MegaManSec/SSH-Snake), I quickly received a bug report: when the script ran on Debian Jessie systems, the script wouldn't function properly due to the awk script which ran at the beginning of the script not being compatible with the system's awk program.
I had extensively tested the script on old Ubuntu servers -- so what was going on?

As it turns out, older versions of Debian used _mawk_ for awk -- AKA "mawk, Mike Brennan's AWK". Ubuntu, however, used "gawk" -- GNU AWK. I'd tested my awk script on various versions of gawk and a newer version of mawk, but not the old version of mawk. (There's lots of different AWK versions. [this document](https://www.gnu.org/software/gawk/manual/html_node/Other-Versions.html) and [this superuser post](https://superuser.com/questions/75875/awk-mawk-nawk-gawk-what) details all about that.)

The fix was simple. I hand to change the awk script from `if ($0 ~ "^[[:space:]]*" funcs[i]) {` to `if ($0 ~ "^[ \t]*" funcs[i]) {`. `[[:space:]]` (meaning a space, tab, or newline) isn't supported in the old version of mawk, so I had to specify a space or tab specifically.

---

Finally having the time to work on it, I decided to build a dashboard where I can enter an awk script with some data, and compare the results between the versions.

So, [awk-compare](https://megamansec.github.io/awk-compare/) is born. The source is available [on Github](https://github.com/MegaManSec/awk-compare).

I used emscripten to compile each versions of AWK to WebAssembly which was easy enough.
On my FreeBSD machine, I booted up an Ubuntu VM and installed the emsdk and then just built the AWKs as normal.
There were some issues with every one except gawk, mostly related to the fact that the building process normally involves building a separate program which is then executed by the build process, in order to generate a new .c file.
Anyways with that dealt with, I simply used `emcmake` which built two files: `awk` and `awk.wasm`.
The former is a javascript file, and the latter is the WebAssembly bytecode. I renamed `awk` to `awk.js`.

emscripten's emcmake/emcc performs some static analysis and can automatically determine which runtime methods need to be used by the exported wasm and script (e.g. filesystem). So in this case, it automatically determined that we have a main function to be called (AWK's C `main(argc, argv)` function, and some FS interaction. YMMV with other programs.

Actually "running" awk was a bit more annoying to work out. The basic JS boils down to the following:

```js
  Module = {
    onRuntimeInitialized: function() {
      if (data)
        FS.writeFile('/data.txt', data);
      if (script)
        FS.writeFile('/script.awk', script);
    },
    'print':  function(text) { console.log(text); },
    'printErr':  function(text) { console.log(text); },
    'arguments': ["-f", "script.awk", "input.txt"],
  };
  var s = document.createElement('script');
  s.setAttribute('src', `awk.js`);
  document.body.appendChild(s);  
```

The secret here is that the the `awk.js` file needs to be loaded after the `Module` object is set. `onRuntimeInitialized` is run _"when compiled code is safe to run, which is after any asynchronous startup operations have completed"_.
By default, the program (the `main()` function) is run automatically. To disable that, you can set `'noInitialRun': true`, and call `Module.callMain(args)` (or [ccall](https://emscripten.org/docs/api_reference/preamble.js.html#ccall)) when you want to. Just make sure you're calling these after `onRuntimeInitialized()` has been called, otherwise some internal state or operations may not be finished/ready yet.

---

Anyways, the website itself isn't too fancy. It reminded me that I hate CSS. "_The answer to many CSS formatting problems seems to be "add another <div>!"_" indeed.. [Or this comment](https://stackoverflow.com/questions/526035/how-can-i-position-my-div-at-the-bottom-of-its-container#comment339220_526035).

I added some examples. The most interesting example for me is that `\s` will be the character `s` in all versions except for gawk, where it matches a space. Seems like an interesting gotcha.



