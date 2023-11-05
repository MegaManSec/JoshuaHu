---
layout: post
title: "Revisiting My Old Blog"
author: "Joshua Rogers"
categories: journal
---

While reminiscing about my blog posts from 2014, I decided to take a further look down memory lane at other blog posts from that time. Some I remembered completely, and some I'd totally forgotten about.

[[2014/05]](https://web.archive.org/web/20140529012212/http://blog.internot.info/2014/05/bcrypt-for-php.html) **bcrypt for PHP**: First posted in 2012, it outlined why bcrypt hashing should be used for passwords as well as information of how to start using bcrypt in the vBulletin forum software (which was used salted MD5 at the time). It also contained some statistics from hashcat I had taken using my multi-gpu hash-cracking rig at the time.

---

[[2014/05]](https://web.archive.org/web/20140527220316/http://blog.internot.info/2014/05/sql-injection-on-ebaycomau-subdomain.html) **SQL Injection on ebay.com.au**: It outlined an SQL injection vulnerability on eBay. This revealed that eBay's backend database was Microsoft SQL DB. Full account details were available as well as payment and order history.

---

[[2014/05]](https://web.archive.org/web/20140529012850/http://blog.internot.info/2014/05/facebook-skype-to-email-leak-3000-bounty.html) **Facebook-to-Skype Email Leak**: Outlined a vulnerability in Facebook which could be used to extract the email address of anybody whose Skype username you knew, regardless of whether the user had you added or not.

---

[[2014/06]](https://web.archive.org/web/20141110002053/http://blog.internot.info/2014/06/securing-ubuntu-desktop-from-bad-guys.html) **Securing Ubuntu Desktop From the Good and the Bad Guys**: Outlined how to harden Ubuntu from hackers and the police.

---

[[2014/06]](https://web.archive.org/web/20141016020023/http://blog.internot.info/2014/06/paypals-2-factor-authentication2fa-good.html) **PayPal 2-factor-authentication bypass**: Outlined a bypass of Paypal's 2-factor-authentication which I discovered. It was first reported on the 5th of June, 2014, and after it being not fixed for 2 months, I released it publicly. It was fixed 7 days later.

---

[[2014/07]](https://web.archive.org/web/20140811070231/http://blog.internot.info/2014/07/ptv-police-and-aftermath.html) **PTV: Police and the Aftermath**: Outlined what it's like when armed police show up at your doorstep with a search warrant. This was in response to [hacking the transportation office](http://www.wired.com/2014/01/teen-reported-security-hole) in Melbourne.

---

[[2014/09]](https://web.archive.org/web/20141101215526/http://blog.internot.info/2014/09/having-fun-with-passwords-in-ubuntu-re.html) **Having fun with passwords in Ubuntu and Police**: Where I detailed how to set up a "kill-switch password" in Ubuntu, which initiated a bash script to delete (overwrite) certain files and directories when somebody tries to login to the computer with the "kill-switch password". Basically, this was a secondary password which would succeed in logging the user in, but it would delete and edit some files (including the script itself). In addition to that, various photos of the "intruder" were taken, just for fun.

---

[[2014/11]](https://web.archive.org/web/20141109185045/http://blog.internot.info/2014/11/dpkg-format-string-vulnerability-cve.html ) **dpkg: a format string vulnerability**: Outlining a format string vulnerability that I had discovered in dpkg. At the time, I had only just learnt about format string vulnerabilities, and thought it was quite neat.

---

[[2014/11]](https://web.archive.org/web/20151006091259/http://blog.internot.info/2014/11/the-state-of-australian-infrastructure.html) **The State of Australia's Infrastructure Security**: Where I outlined that infrastructure and online security in Australia was in shambles. If you've followed the news in Australia in the past few years, it seems my predictions were right.

---

[[2015/01]](https://web.archive.org/web/20151005002923/http://blog.internot.info/2015/01/incorrect-volume-in-pulseaudio.html ) **PuleAudio: Incorrect Volume Slider**: Where I discussed the issue and the fix for PulseAudio not reporting the proper audio levels of my speaker.

---

[[2015/03]](https://web.archive.org/web/20151006091336/http://blog.internot.info/2015/03/specifying-dnsns-server-for-address.html) **Specifying DNS servers for address resolution using getaddrinfo in C**: Where I outlined how to use glibc's libresolv and change internal values to set non-specific DNS servers for resolving, including a bug in eglibc. At the time, eglibc was broken and res_init() did not correctly initialize the internal state of libresolv for resolving domains. res_init() is supposed to initialize the internal state of libresolv, and then subsequent calls to libresolv functions like getaddrinfo wouldn't need to initialize -- meaning if we changed the internal state in our program, res_init() wouldn't overwrite those changes. As it was, the first call to getaddrinfo would overwrite any changes made by the program, such as the dns server to use when querying domain data, meaning two getaddrinfo calls were needed to query a specific dns server.

---

[[2016/04]](https://web.archive.org/web/20160709071859/http://blog.internot.info/2016/04/monitoring-network-io-w-download-upload.html) **Monitoring network io using C on FreeBSD**: In 2016, I started using FreeBSD with the i3 tiled window manager and wasn't happy with i3status or i3pystatus so decided to build my own custom i3bar in C. Something I wanted on my i3bar was the network throughput. It used FreeBSD's ifmib(4) and if_data(9) to calculate the average upload and download speeds in kb/s over 2-second intervals. It also includes an example which has a stack overflow, however looking at my git repository, it seems this example was quite different from how I actually made my i3bar. I also noted that for some reason FreeBSD-10 had a bug which combined ifmd's tx and rx intio rx, meaning the "upload speed" was always 0 and "download speed" was a combination of download and upload. This was fixed in FreeBSD-11 and probably 10.x versions.

---

Two more blogs titled "**The Apt "buffer-overflow" - CVE-2014-6273 -- And why it isn't a real risk**" and "**Ethical Hacking: Responsibility & Ethics**" seem to not have been saved properly on archive.org.

There was an earlier version of this blog from 2012, and I can't say I enjoyed looking back at that one. [It's just cringe.](https://web.archive.org/web/20130202013711/http://www.internot.info/blog/)

---

Two of these posts are worth reminiscing about I think.

**Having fun with passwords in Ubuntu and Police**: Looking back, I would have done this a bit differently.

I would have made the whole script run as root, and I would have made it replace the .bash_history and other similar files with inconspicuous versions. I wouldn't have taken 30 frames from my webcam, because it would probably be _me_ writing the password – instead, I would make it wait for 15 seconds.

Some quotes from that post also include "_Arguably, forcing somebody to hand over encryption keys is undemocratic, and is comparable to the acts of the Stasi._" -- true; "_To maintain plausible deniability(a term created by another fascist government),_" -- calm down, Josh; "_Remember: It's not what they know. It's what they can prove_" -- true.

**Specifying DNS servers for address resolution using getaddrinfo in C**: At the time, debugging the issue which [eglibc](https://en.wikipedia.org/wiki/Glibc#Fork_and_variant) had introduced to libresolv's res_init() was fun, but unfortunately the issue was not ever directly fixed (Debian stopped using eglibc, and glibc rewrote much of the code which silently fixed the issue). The issue was more or less quite simple: res_init() initializes the internal lib_resolv state such that subsequent libresolv calls such as getaddrinfo won't need to.

In libresolv, you can set the internal _res.nsaddr_list variable with ip addresses where to resolve domain names. When res_init is run, _res.nsaddr is overwritten. Each libresolv function like getaddrinfo was checking whether /etc/resolv.conf had been updated since res_init had been run (either manually or by getaddrinfo), and if its modification date was different, it would re-run res_init.

The problem that I had discovered was that res_init did not set the state variable that contained the modification time of /etc/resolv.conf (because it was not set by res_init, but a function that calls res_init), meaning getaddrinfo would call "the function that calls res_init", setting the modification date and re-running res_init, wiping the change we made. Fun!

This also meant (and possibly still means) that there is an inherent race condition in setting custom name servers in libresolv: if /etc/resolv.conf had been modified between the time you set the variable and called getaddrinfo, whatever was in /etc/resolv.conf would be used.

---

Maybe in 10 years I'll be writing another blog post on a different website, just like this one, talking about this post. Hmm.
