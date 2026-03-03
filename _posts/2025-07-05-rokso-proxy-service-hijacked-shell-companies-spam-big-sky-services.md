---
layout: post
title: "Proxy Services, Hijacked Companies, and the Rabbit-Hole of Fake Hosting Companies and Big Sky Services"
tags: [proxy_abuse, security, incident_investigation]
description: "Investigating 'Big Sky Services': How hijacked shell companies and a massive proxy network flooded an Opera legacy endpoint with traffic."
---

One of the benefits of working for a large, albeit stuck-in-the-past technology company which has a whole range of strange services running to fit different decades' ideals -- like Opera -- is the ability to observe strange behavior and investigate it. You can find interesting things to investigate in every corner, whether that be due to concerns with security, or simply trying to work out "why is this happening?" At Opera, [another strange case](/iranian-browser-extension-addon-censorship-bypasses) caught my eye, and the story is one of my favorite from my time there.

Opera (for Opera Mini) hosts a special page on the internet, [https://echo.opera.com/](https://echo.opera.com/), which responds with the **exact** HTTP request that it received in both hex and text, as well as the IP address of the sender. This page has historically been used for many reasons, and traffic to this page is minimal. It's mostly used for debugging and everyday Opera Mini users generally do not hit this endpoint; however, it is not a secret page. Another page, `https://[redacted].opera.com/`, runs the exact same script -- but unlike the `echo` subdomain, this subdomain hasn't really been used for a very very long time -- it's kept online because there are some Opera Mini clients which .. haven't been updated in a very very long time :-). Traffic on this second host is even smaller -- just a few dozen requests per day, let's say -- and the minuscule resources assigned to this host were congruent to this.

To everybody's surprise, one day this second host went down: its memory was being exhausted for no good reason. After a quick investigation, it appeared that the web server was causing this exhaustion. Tens of thousands of different IP addresses, all from different ASNs, countries, companies, were sending requests to this page, overloading the server. But why? And how did they find this (extremely old, not on Google, but not secret) endpoint? Well, that was what I and my friend wanted to work out.

Upon first observation, the requests weren't deliberately crashing the server: the requests weren't being sent in spontaneous bursts: rather, it was the massive breadth and amount of IP addresses which made this interesting.

The first step was isolating some of the requests being sent, so we could analyze the requests, the responses, and the clients sending the requests. We noticed that some of these requests were sending `User-Agent` headers which corresponded to various browsers (none of them being Opera Mini) which simply did not exist (semi-valid formatted, but with non-existent versions). Taking a look at the packets from these requests, we discovered that the requests were generally normal, with the exception of the `X-Forwarded-For` header being set to random IP addresses; different for each request, and seemingly completely unrelated to the real host making the request.

Alright: so the `User-Agent` is fake, and a fake `X-Forwarded-For` header is set. We already know what the response will be: the exact HTTP request received, plus the IP address of the host which sent the request. Every request was to the index page with no exception. What can we learn about the client?

The next question was: how real are these users, anyway, given the fake HTTP headers? There's always a (tiny) chance there's some misconfigured application somewhere sending off requests to this server by accident. How could we find out? I wondered: will these clients -- whatever they actually are -- execute JavaScript if we ask them to? And if so, what can we learn? As it turns out, yes. Notably, we learnt that the clients:

- Were using Selenium with ChromeDriver,
- Would follow redirects.
- ... I don't remember what else.

There's [a million and one ways](https://coveryourtracks.eff.org/) to extract information about clients using JavaScript, with various APIs available at our disposal. We didn't bother too much with this, as all we needed to know was: were these real clients or not. The answer was no: they were headless Chrome instances, using Selenium to browse the page automatically.

The next question was: what are these hosts? We weren't just seeing random IP addresses from random ASNs. The IP addresses collated to whole /16 and /24 blocks -- and a /12 blocks too. Hundreds of different ranges, over dozens of registered ASNs, with the whole IP range being seen from our side over a long period of time. Those IP ranges are _expensive_ -- like, millions of dollars. We thought, there's no way somebody could have hacked a bunch of networking equipment and taken over all of these ranges unnoticed to the real owners. So what could be happening?

Typical reconnaissance of the IP addresses yielded no results: no TCP ports were open on any of them, Google searches didn't reveal any information about them, and none of them were on any the standard blocklists like Spamhaus et al. We looked into the true BGP routes and flow of some of the ranges (we had access to an [eyeball network](https://en.wikipedia.org/wiki/Eyeball_network)) and didn't find anything necessarily strange. Since we didn't actually know _what_ we were looking for, we just had to come up with some random actions to do, in the off chance we'd hit some information.

At this time, I had a suspicion that these IP addresses were being used to fuel a "proxy network" -- where somebody / some people were selling access to these IP addresses, so others could bypass blocks, rate limiting, whatever. Traditionally, proxy networks have used hacked systems for their IP addresses, but this isn't a requirement at all: it's just about who's doing it, the risks they want to take, and the money they want to spend. When developing my [RuneScape Account Bruteforcer](https://github.com/MegaManSec/RS-Account-Checker) (what idiot programs a bruteforcer .. in C?), I used a network called "AWM Proxy" which was [sued by Google](https://krebsonsecurity.com/2022/06/the-link-between-awm-proxy-the-glupteba-botnet/) some time ago, but there have been other famous ones over the years, like [VIP72, 911, LuxSocks, and SocksEscort](https://krebsonsecurity.com/2022/08/no-socks-no-shoes-no-malware-proxy-services/). Digressing for a moment, a quick search online indicates there are now hundreds of vendors offering this type of service, some of them not using malware or hacked systems, but semi-legitimate software which users _choose_ to download, where they semi-knowingly (it's in the description) turn their systems into proxies, like [Grass Lite Node](https://web.archive.org/web/20250627184520/https://chromewebstore.google.com/detail/grass-lite-node/ilehaonighjijnmpnagapkhpcdbhclfg?hl=en), which turns your browser into a proxy for somebody willing to pay for it: "Unlimited internet plan? Rent what you don't use". A cursory look indicates that most "free proxy" or "free VPN" software (both browser extensions and system executables) re-sell your network to people needing access to a "proxy network" with hundreds/thousands/millions of IP addresses at their disposal. 

In any case, this was clearly not legitimate traffic hitting our endpoint, and yet it wasn't intentionally malicious -- this seemed to fit the bill of somebody's proxy network, which used the endpoint to determine the IP address of the system. Other websites that print the IP address of the sender like `ifconfig.me`, `checkip.amazonaws.com`, and so on, eventually block bots (mostly because they're normally malware checking the IP address of the infected host, which also costs money to respond to). With this suspicion, I looked more into the ASNs of the networks we were seeing. I found that nearly all of the ASNs' contact details corresponded to companies all around the world, but which simply did not exist online, or existed but with generic "we are network X" homepages with no actual functionality on their website or way to contact the company. Some companies found _had_ websites but they were no longer operating. Various fake LinkedIn profiles, blog articles on random websites, and other junk which was all clearly planted or fake, were all discovered. We looked for company records for some of the ASNs, and they all lead to shell company after shell company.

Clearly, this was quite a large fradulent operation; hedging on a racket. Millions of dollars of IP addresses across dozens and dozens of different companies around the world, for which we couldn't find a single real human connected to.

Nothing is ever finished until I have an answer, so I continued looking, and eventually found the lead I needed. On _Google Scholar_, I found [a thesis](https://web.archive.org/web/20250705171222/https://researchcommons.waikato.ac.nz/server/api/core/bitstreams/8174898b-512a-40fd-96a5-481b9178ba8f/content) written in 2022 which named one of the companies we were seeing: "Intelligence Network Online, Inc." The thesis explained:

> [..] all related to a single spam operation that Spamhaus referred to as Big Sky Services, which specializes in acquiring address space and leasing it to spammers.
>
> One method they used to acquire address space was purchasing the assets of defunct companies and then maintaining the appearance that the company was still in operation.
>
>The abusers acquired an old legitimate ISP AS3502 (Intelligence Network Online, Inc.) that had legacy address space, and leased the prefixes to the spamming networks AS204472 and AS203999.

The thesis went on to explain that old, unused IPv4 addresses had been hijacked by these networks too. Indeed, Regional Internet Registries (RIRs) have been trying to [reclaim unused IPv4 addresses](https://web.archive.org/web/20231004162322/https://www.ipxo.com/blog/ip-legacy-space/) for some time. These ranges are ripe for BGP hijacking, since there's nobody to notice they've been hijacked, or complain.

Now with another name, "Big Sky Services", I was finally able to work out how this all operated. In a now-hidden _Register of Known Spam Operations_ (ROKSO) [article from Spamhaus](https://web.archive.org/web/20220517070559/https://www.spamhaus.org/rokso/evidence/ROK11571/big-sky-services-corespace-mark-wulff-liana-dunlap/main-info), _Big Sky Services_ operations were outlined:

> Big Sky Services is an operation which acquires large amounts of IP addresses through various means, which are then leased to spammers. Partner in spam with Michael Persaud, Michael Jenkins / Inbox Beyond.
>
> Some methods that Big Sky uses to obtain IP addresses are:
>
> Setting up fake "hosting" companies using false identities and Nevada PO boxes, and then justifying new IP allocations from ARIN for their non-existent "hosting" customers.
>
> Buying out the assets of defunct companies (including IP ranges) and then keeping up the appearance that the company is still in business, such as operating an old copy of the website, and impersonating the former owners.
>
> Apparently hijacking dead IP ranges by announcing them through one of the previously mentioned fake "hosting" companies.
>
> Apparently using a hijacked company's role accounts or domain to provide forged documents to upstream ISPs or RIRs when required. This is similar to how "Adconion Direct" is alleged to have operated, see: https://krebsonsecurity.com/2019/09/feds-allege-adconion-employees-hijacked-ip-addresses-for-spamming/
>
> Partnering with a Honduran individual or business that has the ability to obtain IP allocations directly from LACNIC, which are then used to spam.

The article lists various other companies which were registered at the helm of Big Sky Services. Afterwards, I discovered that a few of these were also still active, with their IP addresses hitting our server -- but since this hidden ROKSO article wasn't on Google, and for some reason the IP address not blocklisted by Spamhaus at the time, I didn't find this article earlier. The article also notes that in relation to "setting up fake companies", the US Government prosecuted somebody [for doing the exact same thing](https://www.justice.gov/usao-sc/pr/charleston-man-and-business-indicted-federal-court-over-9m-fraud): "_The indictment charges that, through this scheme, Golestan and Micfo obtained the rights to approximately 757,760 IP addresses, with a market value between $9,850,880.00 and $14,397,440.00._"

Finally, everything started to make sense: a mix of shell companies to look like real (older) companies, as well as purchased companies, all in the name of purchasing the rights to as many IPv4 addresses as possible, in order to be utilized by malicious networks (historically, spam). In addition to this, BGP hijacking of old, unused IPv4 addresses, which "nobody would notice have been hijacked".

Apparently, this operation has been going on for a long time. A really long time. This _might_ explain why requests were being sent to this endpoint of ours -- maybe it had been happening for a really long time, and way-back-when, the endpoint was actually commonly used, instead of `echo.opera.com`? We don't know, as we didn't have logging for so long (because we didn't need it).

Some questions still remain about this operation. Notably:

- Why were these hosts connecting to our page? (I suspect it was to confirm the IP address of the request.)
- Why were these hosts sending random `X-Forwarded-For` headers? (I suspect either it was not deliberate in its request to our service but rather it was intended for use later on when the host would connect to some other website for some purpose **or** it was an attempt to trick _our_ logging service (it didn't; who actually trusts that header anyway?))
- What were these hosts actually being used for? (I suspect there was no single answer: Big Sky Services seemed to simply resell their networks to malicious actors, no matter what they were doing. I suspect we were seeing a company whose sole business was proxies.)
- Why were these hosts using this _old_ subdomain specifically, and not the well-known `echo.opera.com` subdomain? (I don't know.)

On the topic of actually doing something about this from our side, some ideas arose:

- Block the requests completely,
- Serve incorrect results,
- Mine cryptocurrency using JavaScript,
- Redirect the client to somewhere they will have problems with,
- Contact and partner with Spamhaus,
- Sleep or delay the clients forever, for example with a forever `while()` loop, or a gzip/svg bomb.

In the end, we did nothing but give the server a bit more resources to handle the requests, which was probably the best thing to do.

---

On a final note, and on the topic of proxy networks, these things are .. funny in a way.

In 2024, [it was reported](https://krebsonsecurity.com/2024/05/stark-industries-solutions-an-iron-hammer-in-the-cloud/) that two weeks before Russia's full-scale invasion of Ukraine, a company utilized to DDoS Ukrainian and European networks was set up by the same group operating one of these networks:

>As detailed by researchers at Radware, NoName has effectively gamified DDoS attacks, recruiting hacktivists via its Telegram channel and offering to pay people who agree to install a piece of software called DDoSia.

Given the term _hacktivists_ here likely means "Russians supportive of the Russian regime", this is no different than Anonymous _hacktivists_ of the early 2010s, using Low Orbit Ion Cannon (LOIC) as a form of political intimidation. I'm not sure how I feel about the difference between these scenarios. A lot of people were arrested and [sentenced to real prison time](https://en.wikipedia.org/wiki/Christopher_Weatherhead) in the USA for using LOIC; despite their defence that "overloading the traffic of a company's website is no different than protesting outside of their office such that nobody can enter". Protests are, when we think about it, a form of political intimidation. That doesn't mean they're bad.

In any case, the full 2024 article is an interesting read. I highly recommend reading it from top to bottom. It also references similar activities to those of Big Sky Services, such as:

> A review of the Internet address ranges recently added to the network operated by Stark Industries Solutions offers some insight into its customer base, usage, and maybe even true origins.
>
> Those records indicate that the largest portion of the IP space used by Stark is in The Netherlands, followed by Germany and the United States. Stark says it is connected to roughly 4,600 Internet addresses that currently list their ownership as Comcast Cable Communications.
>
> A review of those address ranges at spur.us shows all of them are connected to an entity called Proxyline, which is a sprawling proxy service based in Russia that currently says it has more than 1.6 million proxies globally that are available for rent>
>
> Reached for comment, Comcast said the Internet address ranges never did belong to Comcast, so it is likely that Stark has been fudging the real location of its routing announcements in some cases.

In 2025, [it was reported](https://krebsonsecurity.com/2025/06/proxy-services-feast-on-ukraines-ip-address-exodus/) that:

> Ukraine has seen nearly one-fifth of its Internet space come under Russian control or sold to Internet address brokers since February 2022, a new study finds.
>
> The analysis indicates large chunks of Ukrainian Internet address space are now in the hands of shadowy proxy and anonymity services that are nested at some of America’s largest Internet service providers (ISPs).
>
> For example, Ukraine’s incumbent ISP Ukrtelecom is now routing just 29 percent of the IPv4 address ranges that the company controlled at the start of the war, Kentik found. Although much of that former IP space remains dormant, Ukrtelecom told Kentik’s Doug Madory they were forced to sell many of their address blocks “to secure financial stability and continue delivering essential services.”

That article (much shorter than the 2024 one) is valuable reading, too. Understanding this whole space is going to be useful in the future, I suspect.
