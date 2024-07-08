---
layout: post
title: "Encrypted NTP using NTS and chrony on FreeBSD"
author: "Joshua Rogers"
categories: security
---

By default, FreeBSD uses the standard `ntpd(8)` daemon that is built with the FreeBSD world. This daemon only supports symmetric keys for encryption which must be configured per client/server duo, and thus cannot at-scale guarantee authenticity of the data received from the Network Time Protocol (NTP) server. [Recent developments like RFC 8915/Network Time Security (NTS)](https://fedoramagazine.org/secure-ntp-with-nts/) have allowed for the automatic establishment of those keys over TLS. With a focus on both authenticity (so an attacker on-the-wire cannot set your clock forwards/backwards) and privacy (so a passive attacker cannot identify systems when they change networks), NTS seems to be the way forward, so let's use it on a FreeBSD machine.

---

There are two main options for utilizing NTS on FreeBSD: `ntpsec(8)` and `chrony(8)`. Recently, a rust implementation seems to be getting popular ([ntpd-rs](https://github.com/pendulum-project/ntpd-rs)). There is also `chrony-lite(8)`, but this is literally `chrony(8)` [_without_ NTS support](https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=252584). So we go for `chrony(8)`.

Beginning by either building the `net/chrony` port or installing the `chrony` pkg, the default configuration is found in `/usr/local/etc/chrony.conf`.

First we need to disable the plaintext NTP server being used, by commenting out
```
pool 0.freebsd.pool.ntp.org iburst
```
by adding a `!` at the front:
```
! pool 0.freebsd.pool.ntp.org iburst
```

---

There are not so many public NTS servers available, but they are [documented on jauderho/nts-servers](https://github.com/jauderho/nts-servers) on GitHub. I chose one from Netnod, Cloudflare, and an independent in Switzerland. In the configuration file, we simply add:
```
server ntp.3eck.net iburst nts
server nts.netnod.se iburst nts
server time.cloudflare.com iburst nts
```

The `nts` at the end of each of those lines ensures that the time from each of the servers will only be used if it is properly authenticated.

---

We restart chrony and confirm the servers are being communicated to:
```
$ service chronyd onerestart
Stopping chronyd.
Waiting for PIDS: 34158 34395
Starting chronyd.

$ chronyc -Na sources 
MS Name/IP address         Stratum Poll Reach LastRx Last sample               
===============================================================================
^+ ntp.3eck.net                  3   6    17    62   -971us[ -971us] +/-   24ms
^+ nts.netnod.se                 1   6    17    62  -3319us[-3319us] +/-   37ms
^* time.cloudflare.com           3   6    17    64  -1501us[-1699us] +/-   22ms

```
---

Finally, we need to disable the main `ntp(8)` daemon from starting on boot, and enable `chrony(8)` to start, too:
```
$ sysrc ntpdate_enable="NO"
ntpdate_enable: YES -> NO
$ sysrc ntpd_enable="NO"
ntpd_enable: YES -> NO
$ sysrc chronyd_enable="YES"
chronyd_enable: NO -> YES
```
will do that.

---

Using tcpdump, we can confirm the key exchange is happening on port 4460, too.
