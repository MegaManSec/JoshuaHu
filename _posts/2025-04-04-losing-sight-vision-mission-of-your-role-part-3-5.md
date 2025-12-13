---
layout: post
title: "Losing Sight and Vision of Your Mission and Culture: Part 3.5"
description: "How report-uri.com uses Cloudflare Turnstile to ironically block the very CSP violation reports it is designed to collect from browsers."
categories: personal
---

_Part three can be found [here](https://joshua.hu/losing-sight-vision-mission-of-your-role-part-3)._

This post is a minified version of part 3, as the exact same issue has occured.

You: You're a developer for a website/service (report-uri.com) which provides an endpoint for Content-Security-Policy (CSP) violation reports to be sent to, which are automatically sent by browsers (opaque to the user). One day, you configure your state-of-the-art Web Application Firewall (WAF) that will block unwanted traffic. Even better, you see an option called "Super Bot Fight Mode" and enable it immediately! Super Fighting Protection™! Now when those hackers, bots, and malicious actors try to connect to your website, they'll have to go through Cloudflare's Turnstile! That'll show 'em! Super Fighter!!!1! Tekkin Mortal Kormat Super FIIGGHHTTTEERRRR.

![Cloudflare Turnstile](https://cf-assets.www.cloudflare.com/zkvhlag99gkb/10LzRAr38KzxAANQIVxwZT/0fe5ec0867c70f8217a6deff4b244f9b/image2.gif)

---

Me: I'm a user who has just visited your website. My browser has detected a (CSP) violation. When my browser notices the CSP violation, it automatically sends the violation information to the `report-uri` endpoint specified in the Content-Security-Policy: a `report-uri.com` subdomain. The request is never succesful however, because Cloudflare thinks I'm a bot, and every time my browser to access the endpoint in the background, a Cloudflare Turnstile gets in the way -- I can't see the turnstile, because it's in the background, so how do I tell it I'm not a bot?!

![report-uri.com cloudflare captcha](/files/lolreporturi.png)

Hilarious. Their main product is to detect anomalous requests. Then they go and put a hidden, un-completeable captcha in front of the endpoint which is supposed to detect anomalous requests.
