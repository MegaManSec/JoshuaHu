---
layout: post
title: "Some Thoughts on \"Fixing Security Issues\""
author: "Joshua Rogers"
categories: security
---

_This post was inspired by [upcoming hardening in PHP](https://dustri.org/b/upcoming-hardening-in-php.html)._

---

One of my more unorthodox takes on security is that *the goal* for many focuses too much on simply finding bugs and subsequently fixing them or covering them up. Well duh, obviously it's about fixing security holes -- but let me explain the issue I see.

Find a buffer overflow? Report it, and the developer will stop it from overflow! Find an XSS? Report it, and the developer will stop the execution of the arbitrary script! Find a way to access some data that shouldn't be accessed? Report it to the owner and they'll stop you from accessing it!

But in my mind, while you've fixed one bug, you haven't fixed *the security issue*. *The issue* is that the bug is possible in the first place as well as the collective outcome of theoretical **exploitation**. Fixing a bug may be part of the solution, but it doesn't **solve** the issue.

Teaching developers about common pitfalls, security issues, and best practises is great, but people make mistakes, and tomorrow's vulnerabilities and vulnerability classes are not always understood today. Of course, I'm not the first person [to note that "bug finding is not the answer"](https://owasp.org/www-chapter-boulder/zz_presentations_2021_05.pdf). Indeed, in Google's [Building Secure and Reliable Systems](https://google.github.io/building-secure-and-reliable-systems/raw/ch12.html), the authors also note that: _"In theory, you can create secure and reliable software by carefully writing application code that maintains these invariants. However, as the number of desired properties and the size of the codebase grows, this approach becomes almost impossible. It’s unreasonable to expect any developer to be an expert in all these subjects, or to constantly maintain vigilance when writing or reviewing code. [..] This approach is also imperfect—manual code reviews won’t find every issue, and no reviewer will catch every security issue that an attacker could potentially exploit."_ 

That's where we get to posts like the one this was written with inspiration from, [upcoming hardening in PHP](https://dustri.org/b/upcoming-hardening-in-php.html). In that post, the author discusses securing hardening which takes (paraphrasing) "PHP's ridiculously soft target of a memory heap" and attempts to *fix* the security issues that make PHP so easy to exploit when a vulnerability is discovered. However, the author also details attempts to *fix* the **exploitation** of vulnerabilities, too. [Safe-stack](https://clang.llvm.org/docs/SafeStack.html), [shadow stacks](https://clang.llvm.org/docs/ShadowCallStack.html), or any other related protections attempt to stop exploitation of stack-smashing vulnerabilities, since we've decided that smashing the stack for fun and profit is not going away; so let's make the *exploitation* go away, instead.

It's not only memory-related vulnerabilities that the author looked to "fix", though. They also took liberty to attempt to kill the commonly-used exploitation method of using PHP filters: where hundreds or thousands of filters are used to discern file contents. In the real world, there is unlikely to ever be a real use-case for using more than one or two filters at the same time. So, by simply disallowing thousands of filters to be used (by forcing a maximum of three), they've successfully *fixed* the issue: until the next exploitation class/method is discovered -- because the issue is that a bug can be turned into an exploit; that is, until a new exploitation method is discovered (which will then demand a fix as well).

Indeed, as the post concludes, _I find it fascinating that people are putting so much efforts optimizing exploitation techniques, yet ~nobody bothers fixing them, even if it only takes a couple of lines of code and 20 minutes._. I do too; but I'm not necessarily surprised. These are low-hanging fruit to fix, but since people are more interested in finding bugs and covering them up, these fixes are never developed.

---

Historically (if I remember correctly, and I may be way off), PHP suffered from so many memory-safety related vulnerabilities in `unserialize()`, that they came out saying, "this function is not safe at all, so use it only with trusted data". Then, of course, there's the whole object instantiation being abused to execute code if arbitrary data is passed to that function, too.

The Pike scripting language also has serialization and unserialization capabilities. However, unlike PHP, it uses a safe-by-default option, stopping the object instantiation issue that PHP faces [and execution of arbitrary code is not possible unless the protection is specifically turned off](https://pike.lysator.liu.se/generated/manual/modref/ex/predef_3A_3A/decode_value.html)

In my mind (as somebody that hasn't done any real PHP development since PHP5), "fixing a security issue" in this case could be to alter PHP's `unserialize()` to by-default NOT handle "_object instantiation and autoloading_". This post does not intend to discuss specific vulnerability classes in specific languages, or attempts at fixing them, though.

It's probably interesting to note that Wordpress explicitly attempts to *fix* the issue of PHP object injection in their codebase. They know that extensions are never going to be secure: so they try to *fix* the issue such that if `unserialize()` is called with arbitrary data, an attacker has no way to perform remote-code-execution (at least using Wordpress' base code) -- in theory, a vulnerability turns into a bug. There are of course times when POP chains in Wordpress' code are discovered such as [here](https://www.wordfence.com/blog/2023/12/psa-critical-pop-chain-allowing-remote-code-execution-patched-in-wordpress-6-4-2/), where it was noted that "_While WordPress Core currently does not have any known object injection vulnerabilities, they are rampant in other plugins and themes_".

My final thought is that: if an XSS can be used to take over your site and network, or an open redirect can be used to steal OAuth tokens, then you should be focusing on fixing the exploitation more than the bug.
