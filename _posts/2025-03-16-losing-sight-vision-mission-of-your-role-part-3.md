---
layout: post
title: "Losing Sight and Vision of Your Mission and Culture: Part 3"
author: "Joshua Rogers"
categories: personal
---

_Part two can be found [here](https://joshua.hu/losing-sight-vision-mission-of-your-role-part-2)._

You: You're a developer for a website which offers various functionality to paid, logged-in users. One day, you're tasked with making sure your website is secure from hackers. After reading about how to protect from malicious activity, you think to yourself, well golly, I'll just configure my state-of-the-art Web Application Firewall (WAF) that will block unwanted traffic. Even better, you see an option called "Super Bot Fight Mode" and enable it immediately! Super Fighting Protection™! Now when those hackers, bots, and malicious actors try to connect to your website, they'll have to go through Cloudflare's Turnstile! That'll show 'em!

![Cloudflare Turnstile](https://cf-assets.www.cloudflare.com/zkvhlag99gkb/10LzRAr38KzxAANQIVxwZT/0fe5ec0867c70f8217a6deff4b244f9b/image2.gif)

---

Me: I'm a run-of-the-mill, normal user, utilizing a website I've paid to use. One day, the website completely stops working! While loading the website, the main page loads, but none of the buttons do anything! So, I ask my son -- who is always able to fix the home internet when needed (by turning it off and on). He explains that the website has stopped working because Cloudflare (whatever that is) thinks I'm a bot, and every time I access the website, it tries to access https://api.example.com/ in the background, resulting in the Cloudflare Turnstile -- I can't see the turnstile, because it's in the background, so how do I tell them I'm not a bot?!

Me: I think to myself, "well, can't I just access the API manually by navigating to https://api.example.com/, "verifying I'm a human", then using the main website again?" Again, my son explains that that won't work, because the cookies (yum!) that Cloudflare set are not sent with the requests to the API, both due to the server not responding with `Access-Control-Allow-Credentials: true`, and because the requests are sent with `fetch()` without the `credentials: 'include'` option enabled.

Me: Oh well, I guess I'll just contact support, and they'll fix this issue for me! As I go to the support form and write my problem, the website crashes when I click submit. My son says complaints are sent via the same https://api.example.com/ website, which thinks I'm a bot, and doesn't allow me to prove I'm not one. Go figure.
