---
layout: post
title: "On Iranian Censorship, Bypasses, Browser Extensions, and Proxies"
author: "Joshua Rogers"
categories: security
---

# Rational Explanations: californiapetstore.com

One of the more interesting stories I have from my time working at Opera is when we discovered a "clone" of the [Opera Addon Store](https://web.archive.org/web/20250430044545/https://addons.opera.com/en/) on a completely foreign domain -- something completely random like californiapetstore.com which of course had nothing to do with Opera -- but the content was the exact same as the addon store. All functionality of the website worked exactly as the official addon store -- including searching the website. All links on the website "correctly" linked to californiapetstore.com instead of addons.opera.com, and there was no reference to opera.com in the HTML source code at all.

This came about because we had received some bug bounty submission related to some bullshit about the website accepting requests with TLS 1.1 encryption -- the horror! Initially, the report was closed by BugCrowd, but I was curious when I saw the title: "wtf does this have to do with Opera?" Digging into why (and how) this random californiapetstore.com website was seemingly cloning the addon store proved to be a general win: I discovered a small operation by Iranian dissidents that used esoteric proxy systems (a few of which I hadn't heard of before) to bypass the Iranian regime's censorship efforts throughout the country.

When first discovering californiapetstore.com, my colleagues associated with the Opera Addon store were quick to panic, suggesting that the backend source code had been leaked. "The backend systems like search are working! The page with the datetime is showing the correct time on every refresh! This is a P0 incident! How could they have gotten the source code?!" My colleagues in the security team were quick to panic, suggesting that the website was created in order to distribute malware in the form of extensions, which the Opera browser would use. The first thought of my boss was "they can use Opera in Iran? That's a sanctioned country! We need to get legal involved and block all Iranian users from using the browser!" (..seriously. what an atrocious first thought, and completely devoid of any understanding of sanctions or .. moral thought and empathy for the common people under an autocratic regime attempting to access software to view information on the internet.)

I had a much more simple solution: "_it's clearly a reverse-proxy to the addons store, right? I can make this website with one line in an nginx config_" (I had not checked whether the HTML source code used relative or absolute links), "_moreover, what benefit would anybody have from stealing the addon source code and hosting their own version of it on a random domain like californiapetstore.com? Opera doesn't allow you to (easily) install unsigned extensions, and there's no other functionality on the website which can be abused: sure they could serve malicious executable files for normal download, but they don't need to steal source code for that, and probably wouldn't be using a weird domain name like this. I wonder if it's being used to bypass some firewall._" (side-note: not to toot my own horn, but I generally consider myself a _rational person_ in the sense that I try to reason about what is happening, how things work, why they work, and more importantly: the motivation or stimulus that makes something happen. (side-side-note: I can sometimes seem like I'm doing irrational things, but that's because others don't see or know the full picture just yet.))

Funnily enough, I was able to find the owner of this domain. On a specific subdomain of the website, they had configured the HTTPS certificate with a Subject Alternative Name which pointed towards another website; the personal blog of somebody based in Tehran. I messaged them on LinkedIn a simple: "hey, I work for Opera, I found your website. I'm just curious why you set up a proxy to the addons store." In my mind, having identified that owner as Iranian, I sort of instantly knew it had to be about censorship (knowing how things work, the world, and so on, proves helpful once again).

A day later, I received an Instagram (lol) message. "Hello Joshua, I'm [name], head of [name]'s security team. You messaged our manager and asked about if we are using a site to reverse proxy to Opera. We use the site to bypass filtering and censorship. I want to know how you got our manager's name? If you can access this information, then the Iranian Government can too, and the identity of thousands of people who use this method in Iran is in danger of being leaked."

I went through how I discovered the owner's identity, and did a second pass to see if it was possible to find the owner's identity in any other way (there was one other way).

My suggestion in Opera was that we should actually make it _easier_ for this type of censorship bypassing to happen -- if we could do something to support the oppressed people under such restrictions, we should. Obviously, because doing something that is meaningful for the world (instead of just serving more shitty paid advertisements to more people) is too much to ask for, my suggestion was ignored.

# Browser Extensions and Censorship

So what censorship was happening which actually required a proxy to access the addon store? I was able to find a really interesting and detailed report from 2022 that outlined the internet shutdown and various censorship efforts in the country during the autumn 2022 protests, which included "Targeted Disruptions to Apps and Services", which included the "Blocking of Browser Extension Repositories". [The whole report](https://web.archive.org/web/20250306130239/https://ooni.org/post/2022-iran-technical-multistakeholder-report/) is an interesting read and goes into some technical detail about various protocols which were limited during this time. In terms of the addon store, the report noted that:

>Figure 21 aggregates OONI measurement coverage from the testing of the browser extension repository URLs for Firefox, Chrome, Microsoft Edge and Opera from multiple networks in Iran between 6th September 2022 to 5th October 2022. Most URLs from the figure lack testing coverage before 26th September 2022 because they were only added to the list of tested websites on that date. Given that access to addons.mozilla.org was blocked on 24th September 2022, it is possible that ISPs may have started blocking access to the other URLs on the same day (if they synchronized the blocking of browser extension repositories).

So basically, the Firefox Addon Store was blocked on the 24th of September, and it's probable (but unconfirmed, due to lack of data) that the Opera Addon Store was blocked at the same time. This is likely because various addons could be used to easily circumvent censorship efforts.

At the same time, all access to media apps like Messenger, Signal, WhatsApp, Instagram, Viber, LinkedIn, and so on, were all blocked. The Google Play Store and the Apple App Store were also blocked.

The Open Observatory of Network Interference (OONI) tracks and monitors this type of censorship, and all of their data is available for free, updated in real-time on their website, [https://ooni.org](https://ooni.org).

# Censorship Hardware

Historically, Iran has used technology from [Nokia, as well as homegrown solutions](https://web.archive.org/web/20250407012343/https://www.csmonitor.com/World/Middle-East/2010/0416/Haystack-gives-Iranian-opposition-hope-for-evading-Internet-censorship) for censorship of the internet. These days, it appear that Iran also uses (or used) products from the Canadian company _Sandvine_ to perform censorship or restrictions on the internet in the country. Sandvine's products are used in other countries, and has probably been most documented in use in [Egypt](https://web.archive.org/web/20250602122400/https://www.qurium.org/alerts/egypt/how-operators-use-sandvine-to-block-independent-media-in-egypt/). Their products can block certain content, [proxies and VPNs](https://web.archive.org/web/20250425111515/https://www.applogicnetworks.com/blog/hiding-the-internet-the-rise-of-vpns-global-internet-phenomena-spotlight), and even be used to inject malicious content or spyware content served on websites. This has been documented in many places, including CitizenLab's report, [Predator in the wires](https://web.archive.org/web/20250309124703/https://citizenlab.ca/2023/09/predator-in-the-wires-ahmed-eltantawy-targeted-with-predator-spyware-after-announcing-presidential-ambitions/).

In 2024, the USA [sanctioned Sandvine](https://web.archive.org/web/20250307090419/https://www.wired.com/story/sandvine-us-sanctions-egypt-internet-censorship/). In that linked article, some examples of friends of Sandvine were identified:

- "_used by the government in Azerbaijan to black out livestreaming services and social media sites during anti-corruption protests, and to later block access to a major opposition newspaper_"
- "_Sandvine’s tools had been used to deploy “nation-state spyware” onto users’ devices in Syria and Turkey._"
- "_Sandvine’s DPI tool was used to shut down the internet during anti-government protests in Belarus_"
- "_the company had been pursuing business in Russia, where the government has been rolling out a massive system of decentralized censorship_"
- "_Sandvine has provided a key tool in the government’s attempt to strangle independent voices, allegedly helping to block hundreds of sites, including Al-Manassa._

[Indeed](https://web.archive.org/web/20240227024305/https://www.iranintl.com/en/202312077744): "_the Iranian regime strictly controls internet access, frequently imposing blackouts during sensitive times, such as widespread protests, and has long restricted access to satellite TV through extensive jamming_". Today (18-06-2025), [Iran has shut off internet access in the country to the world](https://web.archive.org/web/20250618204737/https://www.wired.com/story/iran-internet-shutdown-israel/). This is because the Government knows their _censorship_ [efforts aren't perfect](https://web.archive.org/web/20250616001625/https://www.ynetnews.com/business/article/bjfpds3xlg), so instead of trying to filter content, they just unplug the internet for everybody. They have done this by withdrawing all BGP route advertisements; something Egypt famously did in 2011 during the Arab Spring. Iran did something similar in 2019 during protests, which resulted in 100-people being killed, and the whole world being real-time-blind to it (with no connection to the outside world, nobody could .. tell anybody what was happening). There's then the whole National Information Network (NIN) thing, that is effectively an [Iranian Intranet](https://en.wikipedia.org/wiki/National_Information_Network), designed to completely cut the country off from the rest of the world in "normal times" -- totally controlled by the Iranian Government.

Generally speaking, this is .. very sad.

# Censorship-bypassing proxies

Continuing the discussion with this guy from Instagram, I was interested in the technology that was actually being used on this site. It seemed to be a reverse proxy which could be configured to automatically rewrite URLs (including images, scripts, etc.) on the page to point towards the californiapetstore.com domain, to effectively swap any requests from the opera.com domain to the californiapetstore.com domain on-the-fly, bypassing any requests to blocked domains. Such a system would allow any domain (or other hostname, address, etc) to be configured to "replace" the blocked website with an unblocked equivalent.

I learnt that there are many methods which is used to bypass censorship in Iran:

- V2Ray
- Vless
- Hiddify
- ShadowSocks
- Reality
- VMess
- ShadowTLS
- Trojan (not the virus type, but [Trojan Proxies](https://www.anonymous-proxies.net/posts/what-is-trojan-proxy/))

Traditional methods of bypassing censorship, like OpenVPN, IKEv2, L2TP, SSTP, and so on, are blocked.

The californiapetstore.com website was using Reality.

# Opera VPNs and Proxies

Given that Opera actually provides (various) proxies and VPNs built-in to its various browsers, I was interested: do they work? Apparently not: they're all blocked.

Apparently there are some browser extensions which do work to bypass Iran's censorship. However, this is of course limited to only the browser, and cannot tunnel the entire network's traffic (of course, it would be possible to reverse engineer the extension and create a system-wide proxy).
