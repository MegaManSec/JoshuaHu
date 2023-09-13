---
layout: post
title: "CVE-2023-4863: Fallout hits Facebook; probably much much more"
author: "Joshua Rogers"
categories: security
---

The news of a critical 0day fixed in Chrome has been getting quite a lot of attention the past few days. However, it's not just an issue in Chrome: it's a vulnerabilitry in the library Chrome uses to process [WebP](https://en.wikipedia.org/wiki/WebP) images: libwebp.

Now, the newest vulnerability affecting _libwebp_, tracked as CVE-2023-4863, has seemingly affected Facebook.

Users of Facebook's Messenger (at least the messenger.com and facebook.com websites) that attempt to upload large-ish images of the webp format are greeted with the following error:
```
Unable to Add Attachment

Your image couldn't be uploaded due to restrictions on image dimensions. Image should be less than 2048 pixels in any dimension.
```

Seemingly, this is because Facebook's systems which process uploaded images (whether it be its machine learning systems for classification, anti-spam/malicious, re-sizing, or compression) are vulnerable to CVE-2023-4863.

Most likely, in order to mitigate the risk of a user uploading a malicious image to pwn Facebook's image processing systems (which are inevitably completely segregated from anything else due to the plethora of image processing exploits), they have restricted the upload size to a maximum which they believe does not pose a risk.

Alternatively, this could be to protect Facebook's userbase from being attacked. Imagine being sent an image via Facebook and it infecting your phone (or at least your Facebook app).

---

CVE-2023-4863 is going to be so much more than just Chrome, Firefox, and other browsers. Any system or service which processes images or relies on libwebp is vulnerable. That includes:
- ffmpeg
- gd
- thunderbird
- imagemagick
- gimp
- photoshop?
- illustrator?
- premiere?
- libreoffice
- electron apps (slack, discord, microsoft teams, twitch, visual studio code, slack, skype)

And let's not forget content proxies which manipulate (for example for compression) image content:
- Cloudflare
- Akamai
- Cloudfront
- Fastly
- ...

Even game engines like Unreal and Unity use libwebp.

It would be naive to assume that other languages don't use libwebp, too. [PHP supports libwebp](https://www.php.net/manual/en/function.imagewebp.php).

I wouldn't be surprised if this is going to hit some proxies which also compress and scan webp images.
