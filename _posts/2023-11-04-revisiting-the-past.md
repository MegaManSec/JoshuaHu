---
layout: post
title: "Revisiting the past: Security recommendations of a 17-year-old Joshua"
author: "Joshua Rogers"
categories: journal
#tags: [security work life]
#image: cutting.jpg
---

Do you ever experience huge coincidences that you wonder how it's possible that they can come to be? I do; fortunately or unfortunately, it constantly seems like the world is so small and time is so short. That's reigned true most recently while reading an email on the [oss-security mailing list](https://www.openwall.com/lists/oss-security/) -- which I re-subscribed to just a few weeks ago. In this case, it's a happy coincidence which has brought back quite fond memories. On the 24th of October, [an email discussing a security issue in Firefox](https://www.openwall.com/lists/oss-security/2023/10/24/2) came through. Let's go through it, and try to bring back even more memories

---

"_There was a recommendation to run firefox as a different user, e.g. firefox, some time ago: [https://seclists.org/fulldisclosure/2014/Jun/84](https://seclists.org/fulldisclosure/2014/Jun/84)_".  --- [Martin Hecht](https://www.openwall.com/lists/oss-security/2023/10/24/2).

The moment I read those words, I thought to myself.. "there's no way..." Browsing to the fulldisclosure mailing list that was posted, indeed revealed an email I wrote in 2014 titled "_Securing Ubuntu-Desktop From the Bad-Guys, and the Good-Guys_" where I outlined various techniques I was using to make my Ubuntu more secure. I was 17 at the time, and had good reason for wanting to protect my laptop as much as possible from both intruders over the network as well as intruders (think: police) in real life.

The guide was for Ubuntu 14.04. I first started using Ubuntu in 8.04 in 2009, dual-booted with Windows Vista. After that, I think I skipped 9 and 10, and went directly to Ubuntu 10.04 or possibly even 12.04. I still have screenshots from those times in a backup. At the time, I was using the Github account [JulianAssange](https://github.com/JulianAssange), which apparently I registered some time in 2010 when I was 13 (or possibly 12) years old. Some time around 2016 I switched to FreeBSD.

In the blog post, my recommendations were:
1. Disabling various firmware modules in Linux which may be used to dump memory via FireWire.
2. Hardening Firefox to use a separate user account in the OS.
3. Installing various addons in Firefox: an adblocker, HTTPS-Everywhere, BetterPrivacy, "User Agent Switcher".
4. Disabling all "plugins" in Firefox, disabling DNS prefetching, and disabling websockets (which at the time were not used anywhere).
5. Setting up a "mac changer" program to spoof your wlan's MAC address on each boot.
6. Installing ClamAV.
7. Installing DNSCrypt for DNS-over-HTTPS (or whatever was the flavor at the time).
8. Moving the Linux boot partition to a USB drive.
9. Setting an admin password for the BIOS, and disabling "Quickboot/Fastboot" such that memory is wiped on reboot.
10. Using "bleachbit" to overwrite the memory of files rather than using "rm" to simply remove the inode. 

Looking back, I have some comments.

---

Moving Firefox to a different user was an attempt to limit the damage if Firefox was hacked (AKA account separation). When it runs as your normal user, an attacker is then able to do anything that that user could do or access files that that user could access. As I noted at the time, it isn't as easy as just running Firefox as a different user, as you need to somehow establish a communication channel with X11. If you just allow the 'firefox' user X11 access, it can monitor and control all X11 activity of all users: this could include logging keystrokes, injecting keystrokes, or watching the screen. A more secure 'paranoid' option, however, disallowed copy-and-paste _from_ the browser into 'the real world' -- copying _into_ the browser, does work, however.

In my instructions, I also added 'firefox' to the audio group and made the firefox user a slave of the master Pulseaudio server. Looking back, it probably would have been possible to only allow Firefox to act as a speaker, meaning a compromised 'firefox' user couldn't listen to my microphone.

Reading back my comment "_I, like many of you probably do, like to play music in my browser._", all I can say is.. Cool story, bro.

ClamAV? We all make mistakes I suppose.

And I imagine that encrypted NTP wasn't a thing back then?

---

I ended that post stating that: "_After all, one could always torture you for access. [https://xkcd.com/538/](https://xkcd.com/538/)_". In the grand scheme of things, that prediction came to be quite true. In Australia, [you can be forced to reveal](https://ngm.com.au/3la-orders-crimes-act-1914/) your encryption keys or any passwords, or face 2 years in jail.

---

Seeing this email (which was just a copy-and-paste of a blog post I wrote) after so long brought back good memories. Most of all, I was happy that at least one person was using one of my recommendations (account separation for firefox). Even though Linux fails at being an OS for multi-tenant environments, this separation would certainly slow an attacker down. I was also happy that many of these features have since become standard for the general populous, and sandboxing in Firefox became a thing in 2016. This email has also made me go and check out my old blog, where I'll be writing something about all of the weird and interesting entries I wrote nearly a decade ago.
