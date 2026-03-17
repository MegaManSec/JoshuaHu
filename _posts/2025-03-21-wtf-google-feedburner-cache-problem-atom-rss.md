---
layout: post
title: "wtf Google: cacheable rss feeds are dead, and Atom feeds are delayed"
tags: [rss_feeds, web_platform]
description: "Update: Google kills RSS support and breaks Atom feeds. How Feedburner's continued caching failures and stale data affect aggregators."
---

In a [previous post](/google-feedburner-broken-caching-if-modified-since), I outlined how Google's Feedburner refuses to serve `304 Not Modified` for cached Atom feeds. I also outlined how rss feeds were serving stale results, resulting in delays of new posts of up to a few days. After sending that post to Feedburner's support contact in the hopes that they would fix the delayed rss feed results and respect attempts at caching, they instead... completely got rid of the rss feed, and started serving stale results in the Atom feed. Nice!

Of course, who knows whether this change was a direct consequence of me contacting their support -- Google doesn't reply to support emails of course (yay, asymmetric communication) -- but the change is evident nonetheless. The response when attempting to retrieve the rss feed for [the Google Chrome Releases blog](https://chromereleases.googleblog.com/) is a simple 302 redirect to the Atom feed:

```shell
$ hcurl 'https://www.blogger.com/feeds/8982037438137564684/posts/default'
HTTP/2 302
location: http://feeds.feedburner.com/GoogleChromeReleases
```

The Chrome Releases blog source code still has in its source:

```
<link rel="alternate" type="application/atom+xml" title="Chrome Releases - Atom" href="https://chromereleases.googleblog.com/feeds/posts/default" />
<link rel="alternate" type="application/rss+xml" title="Chrome Releases - RSS" href="https://chromereleases.googleblog.com/feeds/posts/default?alt=rss" />
<link rel="service.post" type="application/atom+xml" title="Chrome Releases - Atom" href="https://www.blogger.com/feeds/8982037438137564684/posts/default" />
```

All of these redirect to the [https://feeds.feedburner.com/GoogleChromeReleases](https://feeds.feedburner.com/GoogleChromeReleases).

Alright; so the Atom feed -- which doesn't respect any attempts at client caching -- is now the only way to retrieve some type of feed from the blog. Whatever; the bandwidth isn't important, it's the principal of not retrieving unnecessary data.

But the results of the feed? Well..

```shell
$ date
Sun Feb 23 22:33:37 AEDT 2025
$ curl --silent "https://feeds.feedburner.com/GoogleChromeReleases" | grep -o '2025-02-..' | sort -n | head -n5
2025-02-16
2025-02-13
2025-02-13
2025-02-13
2025-02-13
```

Oh, great. They've not only forced the non-cacheable Atom feed, but they've introduced the exact same bug that the rss feed had -- the results are stale!

Due to this, [CCBot](https://www.github.com/MegaManSec/CCBot) (my bot which checks and reports on newly released Chromium versions with security fixes) now reports newly fixed security issues with delayed results. I haven't checked whether other Atom (or rss) feeds are affected by the new information detailed in this post, but I assume they are.

Again, my understanding is that Feedburner is dead, so any development time going into it is probably a single person with effort that comes from passion, not a paycheck (aka the best kind of effort; been there, done that).

---

In any case, I've updated CCBot recently to:

- Garbage collect old blog posts,
- Use Docker,
- Use Python Virtual Environments,
- Force UTF-8 (a post in Feburary 2025 contained some UTF-8 characters, resulting in CCBot crashing as it expected ASCII-only),
- Retry links/posts which result in failures (like network problems).

I recommend updating, if you're using it.

At least one of the large Chromium-based browsers (still) uses CCBot to alert on these security releases. There is no collaborative effort between Chromium-based browsers to coordinate patches; Google does not provide an internal / private channel for these updates, either; this is one of the reasons that Chromium-based browsers receive security updates so late, compared to Chrome. By serving stale results on their feed, they make it even worse. Wtf, Google?

---

By the way, there's something interesting  on the Chrome Release blog. The Chrome Releases Blogger profile's author is listed as [Ben Mason](https://www.blogger.com/profile/03020057964049649634) (team lead of Chrome Browser Release Team), with an associated [test blog](https://bentest-chrome.blogspot.com/). I'm surprised that this Blogger profile, which hosts the release blog, is just somebody's personal Blogger personal. :).
