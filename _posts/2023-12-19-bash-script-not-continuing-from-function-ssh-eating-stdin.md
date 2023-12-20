---
layout: post
title: "Bash and SSH fun: SSH is eating my stdin! Or: why does my Bash script not continue after returning from a function?"
author: "Joshua Rogers"
categories: security
---

Another day, another bash and ssh discovery.

I've been working on a script which, in its most minimal state, does the following:

```bash
fun() {
  ssh -i key user@host 'true'
  return
}
echo before
fun
echo after
```


Assuming the key exists and `true` will indeed run on the foreign server, what will the output be when running this script? As it turns out, it depends on how you run it:

```bash
$ bash ./test.sh
before
after
```

```bash
$ cat ./test.sh | bash
before
```

Huh? Why isn't bash executing the second `echo`?

In fact, it seems that the script just completely finishes after the `fun()` function returns. We see this when running the script in :

```bash
cat test.sh | bash -x
+ echo before
before
+ fun
+ ssh -i key user@host true
+ return
```

After some time reading the ssh manpage, I noticed:

```
-n      Redirects stdin from /dev/null (actually, prevents reading from stdin).  This must be used when ssh is run in the background.
```

Right. ssh by default reads from stdin unless disabled. Since the script is being read from stdin line by line, when the `fun()` function is actually _executed_, stdin still contains `echo after`, and as such, `ssh` reads it or effectively eats it.

---

There are a few flags you can use to disable the reading of stdin by default, like the aforementioned `-n`, but also `-f`. Alternatively, you can feed `/dev/null` into it, as such:

```bash
fun() {
  ssh -i key user@host 'true' < /dev/null
  return
}
echo before
fun
echo after
```
