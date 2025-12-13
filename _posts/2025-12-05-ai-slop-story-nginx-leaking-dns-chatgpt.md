---
layout: post
title: "Another AI slop story: ChatGPT vs. Human"
description: "Incident response failure: How engineers trusted ChatGPT over technical evidence regarding a critical Nginx DNS data leak."
categories: security
---

In my [last](https://joshua.hu/ai-slop-okta-nextjs-0auth-security-vulnerability) two [posts](https://joshua.hu/gixy-ng-new-version-gixy-updated-checks#quality-degradation), I outlined different stories about my experiences dealing with developers that had offloaded their work to low-quality LLMs, resulting in frustrating performance degradation. Today, I'll be writing about a similar experience, wherein responding to a potential security incident, my professional expertise and technical analysis was disregarded due to ChatGPT stating that I was wrong -- only for it later to be proved that ChatGPT was wrong.

## Backstory

### nginx

Some time this year, I discovered that nginx does not by default respect DNS TTLs, meaning once nginx is started and an endpoint proxies upstream to for example `example.com`, the IP address of `example.com` is never re-resolved. Even if the IP address of `example.com` *does* change, nginx will continue attempting to proxy connections to the old IP address. I documented that issue in [this post](https://joshua.hu/nginx-dns-caching), with solutions. The impact of this problem can range drastically, depending on the purpose of the proxy.

### Amplitude

In the place I originally found out about nginx's resolution behavior, the proxying was being used to circumvent adblockers, by creating an endpoint `example.com/endpoint` which proxied upstream to the tracking endpoint of the Amplitude "digital analytics" service. Since every adblocker in the world will block all connections to Amplitude's tracking endpoints, this company created an endpoint on their own website which -- opaque to the browser -- forwarded the tracking data to Amplitude.

### Leaking to Amplitude and beyond

One day, Amplitude's website's IP addresses changed and some other websites picked up Amplitude's previous IP addresses (it was using AWS EC2, so rotating IPs are expected), resulting in ... unexpected data being sent to the web clients of users, causing various problems which I very quickly diagnosed to be this nginx server using the outdated DNS records for Amplitude ("it's always DNS"). Generally speaking, regardless of the whole DNS thing, these types of proxies are short-sighted, lazy, and unsafe: they ignore how browsers work (the proxies will forward all cookies upstream for example, and are considered same-origin and same-domain, so can execute arbitrary javascript). Imagine that: sending sensitive data like cookies to a _data tracking company_. I'm sure a data tracking company would never track the data being sent to their servers, am I right?! Anyways, since the company's proxying to external hosts was unknown to me, I asked, "where else are we doing this wrong?"

### Leaking everywhere

Eventually, I found five instances of this type of proxy being used, which included notable cases where:

- User authentication cookies (and other cookies) were being leaked upstream (to said tracking company, to "random IP addresses" (due to the outdated DNS records), and to some other proxied-to services),
- Personal data (residing in cookies) was being leaked upstream (as above),
- Tracking cookies and tracking data were being leaked upstream (as above).

### Incident response

The incident response team generally handled each of these cases as poorly as I expected: they seemed not to have any technical understanding of the issue, and seemed unable to grasp exactly what nginx even is or its purpose as a reverse proxy at all. Indeed, after around a month and the fourth leaking-proxy being found (but this single one not nginx! rather, a different proxying system; some software in Python), the incident owner linked a Python file unrelated to nginx at all, suggesting that _it_ somehow contained configuration which pertained to nginx ("it seems that your nginx file here ..."), despite _that_ problem ... not having a single thing to do with nginx (suggesting the person did not understand that nginx is a software, and that nginx is not synonymous with "reverse proxy"). I cannot overstate how stupid all of this was, to the point somebody could suggest they were being deliberately obtuse. I digress.

## AI slop

Alright, that's the back-story of this story, now let's talk about the actual AI slop.

I discovered a fifth instance of this proxying issue, again in nginx -- where the system owner didn't know that `proxy_pass` will use the initial IP address of the upstream host until nginx restart. Luckily, I wasn't part of the incident response procedure for this (only reporting it), and it was fully up to the incident response team to handle the issue. I say luckily, because otherwise we wouldn't have this funny story to tell today. In my report, I even included [documentation](https://web.archive.org/web/20250617053714/https://www.f5.com/company/blog/nginx/dns-service-discovery-nginx-plus) from nginx themselves that the configuration would result in the caching of the IP address. So, it could be handled easily, just like the other four nginx-related incidents, right?

The incident was closed as "not real", and no changes were made. I didn't get it, so I reached out to the incident owner, and he explained that:

- The incident response team investigated the issue (whatever that means),
- The system owner explained that nginx does not cache IP addresses, and that it was a misunderstanding of how nginx works to report this.
- The incident response team closed the issue, stating that it was a misunderstanding of how nginx works to report this.

This was, well, frustrating to say the least, and yet another eye-roll situation that I thought, "wow, these guys are truly incompetent and can't do anything themselves." That may seem like a derogatory thing to say from an outsider perspective, but when you have four (of the nginx) cases of the same issue being handled, and on the fourth one the team says "this is a misunderstanding of how nginx works" without asking the person who diagnosed and investigated the issue originally for their opinion (i.e. my opinion), you just have to wonder how effective these people will be in the case of a real, critical incident.

So, I reached out to the system owner: "how did you come to the conclusion this isn't a real issue?" He explained that the nginx documentation that I provided was outdated, and that he tested the server to see whether it worked the way I reported, and it didn't, "but thanks for the report anyways".

That was a lie. Of course it was a lie. I recorded a video demonstrating the issue in action by setting up a tiny nginx configuration to proxy somewhere, and used `tcpdump` to show that no DNS records were being retrieved after startup.

The system owner finally relented: "_**to be honest, I asked ChatGPT and it said that what you said was wrong. The documentation from nginx that you linked looked old, so I ignored it.**_"

All of just seemed to further support my poor opinion of the technical capabilities of the people handling the investigation/response into this issue. Not only did they seemingly not have the technical capabilities to investigate and solve the problem, they didn't even have the skills to discern fact from fiction (i.e. "human with examples and references to documentation" versus "what ChatGPT said"). I digress.

In the end, I got some meaningless apology, and the incident was reopened and handled accordingly.

I say accordingly, but in my opinion, the proper solution in this case was to simply retire this proxy. It was being used to create an endpoint `/giphy` on the webserver, which would proxy to Giphy's API endpoint. The reason?

> We prefer to keep it because it looks better

Ah yes, the most important thing in the world: how HTTP requests _look_. Because that ... matters?

## Final thoughts

One of the biggest problems in relation to AI and security that I am still trying to work out is: how can we even begin to _attempt_ to provide guardrails/guidelines for securely using AI to perform technical tasks like programming, to non-technical people? What training for non-technical people would actually provide meaningful results which create material benefits when it comes to security of the programs and systems they're "creating"?

Non-coders using AI to program are effectively non-technical people, equipped with the over-confidence of technical people. Proper training would turn those people into coders that are technical people. Traditional training techniques and material cannot work, as they are targeted and created with _technical people_ in mind.

What's more, as we are seeing more and more, coders using AI to program are effectively technical people equipped with their initial over-confidence, highly inflated by a sense of effortless capability. Before AI, developers were once (sometimes) forced to pause, investigate, and understand. Now, it's becoming easier and more natural simply _assume_ they grasp far more than they actually do. The result is seemingly an ever-growing gap between what they _believe_ they understand, versus what they genuinely understand. This gap will only grow larger, as AI's suggestions diverge from operators' true knowledge.

## Other Stories

For the people that enjoy reading these types of mind-numbingly stupid stories, [this situation](https://news.ycombinator.com/item?id=46039274) is a great read, with some golden quotes such as:

>   This humongous amount of code is hard to review, and very lightly tested. (You are only testing that basic functionality works.)
>
> I would disagree with you here. AI has a very deep understanding of how this code works. Please challenge me on this.

and

> To summarize, I love the new AI sausage and, having visited the sausage factory and done a thorough investigation, I’m not concerned with how the sausage is made. I won’t be forcing my sausage-making processes on anyone and will go make my own sausage!

and

>   Here's my question: why did the files that you submitted name Mark Shinwell as the author?
> Beats me. AI decided to do so and I didn't question it.

and

> May I bring some of your attention back to the facts that:
>
> [..]
>
> it looks well-written

Another amusing comment I read a few days ago was [this](https://news.ycombinator.com/item?id=46136867) and this [later](https://news.ycombinator.com/item?id=46137335) one on HN:

> [..]
>
> However, I was curious to see if github copilot can reverse engineer it based on the latest commits and seems that what it is saying aligns with both advisories
>
> While this analysis might be completely off, the simple fact that I could get even this information without much efforts is mind-boggling. With better setup it might be able to get more.
>
> [..]

Obviously, Copilot was wrong. "_the simple fact that I could get even this information without much efforts is mind-boggling_" is something quite hilarious to read: "look at this machine! I can ask it things and it can give me incorrect answers!"
