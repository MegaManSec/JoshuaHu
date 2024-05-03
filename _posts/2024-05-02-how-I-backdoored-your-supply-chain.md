---
layout: post
title: "Supply chain attacks and the many (other) different ways I've backdoored your dependencies"
author: "Joshua Rogers"
categories: security
---

I recently read a blog post by a [similar title as this one](https://kerkour.com/backdoored-dependencies-and-supply-chain-attacks), which outlined different supply chain attacks on CI/CD pipelines, and largely focused on software immeditely related to the deployment and development of products. Although the post contained a few well-known attacks, I thought I could expand on them with a greater focus on supply chains which may not be noticed by (especially) smaller organizations. Variations and combinations of each of these may also be a concern.

### Your hosting provider is easily socially-engineered

One day, your hosting provider receives a phone call appearing to come from _your_ number. _"Hello, my name is Archibald Tuttle. I have a few servers with you and have locked myself out of my account. How can I gain access back again?"_

After a quick chat where _Archibald_ exchanges some not-so-private information like date-of-birth, email address, and address, he is provided with a method to gain access to _your_ hosting account. The friendly support person even removes the 2-factor-authentication for you!

Quickly, _"you"_ use the remote administration tool provided by the hosting provider to gain root access to all of the servers and siphon off all the assets you'd ever want, either disppearing into thin-air after that, or performing some sort of defacement or whatever.

### Your hosting provider is vulnerable to ...

SQL Injection, IDOR, or even insecure random-number-generation for password resets, _you_ cannot know how secure your hosting provider is. An attacker could compromise your account by hacking the actual hosting provider itself, and either simply log in as you, or perform actions on your behalf: sometimes without your knowledge.

When your hosting company gets popped, [like Linode](https://www.exploit-db.com/papers/25306) (rip zee), you won't have a chance to even know you've been compromised because the hosting provider has the ability to do anything on its assets either through BMCs using `init=/bin/bash`, "management tools" that don't require any login for the system, or some tool to reset the root password otherwise. In some cases a reboot may happen, but would your first instinct be that "someone has hacked my hosting provider" if your server reboots unexpectedly? 

### Your domain registrar is vulnerable to ...

Like above, this one is more likely than one cares to think. Smaller domain registrars are really easy to hack (or social engineer).

Once an attacker has access to either your account or the whole infrastructure, they can simply change the DNS records (likely without you being any the wiser) and generate TLS certificates using Let's Encrypt. From there, they can set up a server or two to do ssl bridging (aka decrypt traffic then re-encrypt it) to monitor the traffic and sniff private information like logins, admin cookies, etc. More than that, you can also intercept mail, and other communication depending on the situation.

### Your BGP routes are hijacked; or a dependencies' routes

This happens more and more often these days for obvious reasons (cryptocurrency), and [BGP hijacking](https://www.kentik.com/blog/bgp-hijacks-targeting-cryptocurrency-services/) can be really profitable, with very few defenses available in many cases. It's not just _your_ BGP route that may be hijacked, it may also be your users' routes, or more interestingly, your dependencies' routes.

A few years ago, the South Korean KakaoTalk platform suffered a BGP hijacking where the attackers were focused on a single file: a javascript file that the platform hosted, which was inadvertently being used by a cryptocurrency exchange named KlaySwap. Since the javascript file was loaded on the exchange's website, when the route was hijacked, the attackers served a slightly altered version which siphoned off users' cryptocurrency when they visited the exchange's website. The attackers generated a valid tls certificate [the moment after hijacking the route](https://medium.com/s2wblog/post-mortem-of-klayswap-incident-through-bgp-hijacking-en-3ed7e33de600), so they could serve the file with a valid certificate, too.

What could KlaySwap do? Host its own version of KakaoTalk's SDK? Use subresource integrity and hope that KakaoTalk will communicate changes to the script in the future? (Perhaps a better system could in-fact use subresource integrity, and temporarily disable the functionality that the SDK provides the platform in case the hash changes, informing someone at KlaySwap that they should check the changes which have occured and update the resource hash if it looks reasonable; something that may be difficult or annoying if the script is minimized and obsfucated.)


### Your bug-bounty provider's support panel gets infiltrated

It's like an adversary's dream: a panel with a big list of vulnerabilities in your system, past and present, for any of the hundreds of support panel workers to view. It just takes one to be compromised for that RCE that can be used to take total control over your network -- which takes one month (!) to fix -- to be viewed and exploited by someone watching. Or they can get insights into the most vulnerable locations of your products, network, or whatever.

I doubt the people doing this are interested in receiving a measly few thousand dollars for taking over your network or exploiting your product.


---

In many of these cases, there's not many preventative measures you can really put in place to defend against an attack. However, the existence of these avenues of attack should at least be understood and realized.
