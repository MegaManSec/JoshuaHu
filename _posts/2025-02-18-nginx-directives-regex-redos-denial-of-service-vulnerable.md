---
layout: post
title: "Can Nginx Configurations Be Vulnerable to ReDoS Expressions?"
description: "Can Nginx configurations be DDoSed? Exploring ReDoS vulnerabilities in regex directives and how to crash a server with simple request strings."
categories: security
---

[Betteridge's law of headlines](https://en.wikipedia.org/wiki/Betteridge%27s_law_of_headlines) fails again! The answer is yes.

---

Looking more and more at nginx configuration issue, I thought about being creative in the issues I can identify. So, I wanted to see if it was possible to denial-of-service attack a server which uses regular expressions in any of its directives. The idea is if any of the regexs are vulnerable to [ReDoS](https://en.wikipedia.org/wiki/ReDoS), we could kill the server with very few connections.

This type of attack is not theoretical, malicious or not. Cloudflare was downed [in 2019](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/) due to this issue, as was [StackExchange in 2016](https://web.archive.org/web/20160720211311/http://stackstatus.net/post/147710624694/outage-postmortem-july-20-2016).

Consider for example the following completely made-up example of an nginx configuration:

```
server {
   [..]

   location ~ /^(a|aa|aaa|aaaa)+$ {
       default_type text/plain;
       return 200 "";
   }
   [..]
}
```

According to [this checker](https://devina.io/redos-checker) (which uses [recheck](https://makenowjust-labs.github.io/recheck/) from makenowjust-labs), the regex's complexity is exponential, and suffers from a potential ReDoS issue with an attack-string as simple as:

```
aaaaaaaaaaaaaaaaaaaaaaaaaaa....
```

But how bad can it really be, and does nginx somehow defend again this? Let's test:

```shell
# curl -i https://localhost/aaaaaaaaaaaaaaaaaaaaaab
HTTP/2 500
server: nginx
[..]

500 Internal Server Error
```

So, it takes 22 `a` characters with one non-`a` (which is required to to make the [catastrophic backtracking](https://www.regular-expressions.info/catastrophic.html) occur).

On the server-side, the error log appears:

```
pcre2_match() failed: -47 on "/aaaaaaaaaaaaaaaaaaaaaab" using /^(a|aa|aaa|aaaa)+$
```

Not the most useful error message, but checking the source code we work out that return code -47 corresponds to [PCRE2_ERROR_MATCHLIMIT](https://github.com/PCRE2Project/pcre2/blob/master/src/pcre2.h.in#L410). This error "limits the amount of backtracking that can take place". Great, so the library limits the amount of backtracking. But just how much does it defend against ReDoS in this case?

```
# ab -n 1000 -c 50 https://localhost/aaaaaaaaaaaaaaaaaaaaaab &>/dev/null &
# time curl https://localhost/ >/dev/null
real    9.978s
```

So with just 50 concurrent requests, it's possible to bring the server to a standstill. All nginx threads run at 100% CPU utilization during this attack.

---

How can we detect this automatically? Well, we can use a tool to check whether a regular expression used it vulnerable to ReDoS, but it seems the only good checker, [recheck](https://github.com/makenowjust-labs/recheck/), is only available in Scala and JavaScript, and DoyenSec's [regexploit](https://github.com/doyensec/regexploit) fails to catch the above (very simple) example. In the long-term, I would like to add something to [Gixy-Next](https://gixy.io/), but it's not so obvious how that's going to be possible.


