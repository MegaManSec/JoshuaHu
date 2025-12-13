---
layout: post
title: "Feedburner's Caching Problem"
description: "Google Feedburner's lack of caching support wastes bandwidth. A look at how broken ETag/If-Modified-Since handling affects bots and RSS feeds."
categories: journal
---

I'm a big fan of minimizing the work required to perform a task correctly (without reducing quality), whether it be technical or otherwise. In today's case, I'm talking about retrieving RSS/Atom feeds from Google's Feedburner, and caching is seemingly not supported.

Some authors, like Rachel Kroll, have [talked extensively about RSS readers](https://rachelbythebay.com/w/2024/08/17/hash/), and how poor implementations do not correctly check whether feeds have _changed_ using the `If-Modified-Since` and `If-None-Match` HTTP request headers. Feed servers usually provide a mechanism to inform readers/clients whether a feed has changed since the last visit: the idea is that a client shouldn't download the large feed if anything hasn't actually changed. The reader can constantly poll the server simply asking the question, "do you have anything new for me?" instead of retrieving everything over-and-over, despite no data changing since the last hundreds of visits.

Two major mechanisms are available to achieve this:

1. The `If-Modified-Since` _request_ header. When the server responds to a request for a feed, it includes a `Last-Modified` header containing something like `Fri, 31 Jan 2025 16:09:50 GMT`. The next time the client requests the feed, it can send a header such as `If-Modified-Since: Fri, 31 Jan 2025 16:09:50 GMT`. If nothing has changed on the feed from that date, the server simply responds with a `304 Not Modified` header, with no data -- nothing has changed, so simply inform the client "nothing new!" If something _had_ changed, the server would response with a full response, with a new `Last-Modified` header accompanied with the feed.
2. The `If-None-Match` _request_ header. When the server responds to a request for a feed, it includes an `ETag` header containing something like `33a64df551425fcc55e4d42a148795d9f25f89d4`. The idea is that this is a unique identifier for the specific version of the content that has just been retrieved. Subsequent visits by the client can set a request header of `If-None-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"` to basically ask the server, "only show me the feed if it isn't what you've previously identified as `33a64df551425fcc55e4d42a148795d9f25f89d4`". Once again, if the feed hasn't changed and the server still considers it `33a64df551425fcc55e4d42a148795d9f25f89d4`, a `304 Not Modified` header would be replied-with, with no data.


These techniques save a lot of bandwidth for both servers and clients, as it ensures that unnecessary data is not transferred: the work is minimized, but the task is still performed correctly.

So, why does Feedburner not support either of these?

I noticed this while updating my Chromium Checker Bot ([CCBot](https://github.com/MegaManSec/CCBot)) script, which polls Chrome's release blog for new updates containing security fixes. [This blog](https://chromereleases.googleblog.com/) is seemingly the only public feed of security-related fixes concerning Chrome and Chromium, and they make it difficult fairly difficult to parse this information (formatting is not consistent, security releases are not categorized, incorrect tags are sometimes used, and some so on).  The blog provides an RSS feed, and an Atom feed:

1. https://www.blogger.com/feeds/8982037438137564684/posts/default -- An RSS feed.
2. https://chromereleases.googleblog.com/feeds/posts/default (which redirects to https://feeds.feedburner.com/GoogleChromeReleases) -- An Atom feed, hosted on feedburner.

While using CCBot, it was noticed that the RSS feed could serve old results for up-to 24 hours. I am not sure whether this is a caching issue on their side, but this delay ended up being unacceptable. No stale feed was noticed in the Atom feed (in the end, I updated the script to use both and combine the results.) The RSS feed supports both the `If-Modified-Since` and `If-None-Match` headers:

```shell
$ hcurl -H "if-modified-since: Mon, 20 Jan 2035 10:39:12 GMT"  "https://www.blogger.com/feeds/8982037438137564684/posts/default"
HTTP/2 304 
sunset: Mon, 30 Sep 2024 23:59:59 GMT
link: <https://developers.google.com/blogger/docs/2.0/developers_guide>;rel="sunset";type="text/html"
p3p: CP="This is not a P3P policy! See https://www.google.com/support/accounts/bin/answer.py?hl=en&answer=151657 for more info."
expires: Sat, 01 Feb 2025 07:52:48 GMT
date: Sat, 01 Feb 2025 07:52:48 GMT
etag: W/"a0014dabaeb0c06f31c5ef584786f51ab208ca995b2004b582cd6db292955e7f"
```

Since no modifications have happened since 2035 ([the future](https://www.youtube.com/watch?v=1acWg-c5Buo)), the server rightfully responses with the 304 header. But what's that `sunset` and `link`? Well, it seems this type of feed will be removed sometime in the future. At the moment, the documentation states that:

> The version 2.0 GData API URLs are used as feed URLs. Will such feeds be unavailable too?
> -   We continue to serve feeds for such URLs. But the response is the same as [blogspot.com](http://blogspot.com) feeds like https://{your_subdomain}.blogspot.com/feeds/posts/default and can be slightly different from the original.

So, this is considered the outdated way of retrieving the RSS feed. What about the Atom feed, then?

```shell
$ hcurl -H "if-modified-since: Mon, 20 Jan 2035 10:39:12 GMT"  "https://feeds.feedburner.com/GoogleChromeReleases"
HTTP/2 200 
content-type: text/xml; charset=utf-8
feedburnerv2: 
last-modified: Fri, 31 Jan 2025 16:09:50 GMT
cache-control: no-cache, no-store, max-age=0, must-revalidate
pragma: no-cache
expires: Mon, 01 Jan 1990 00:00:00 GMT
date: Sat, 01 Feb 2025 08:01:31 GMT
```

For some reason, Google really doesn't want clients/feedreaders to save data. No ETag is available, and the server does not take into consideration the `If-Modified-Since` header. As far as I can tell, there is no way to enduce a `304 Not Modified` header from the feedburner service. Why would they do this? I have no idea. Feedburner is generally considered dead, but clearly Google themselves are using it for their blog. Do they want to waste bandwidth deliberately? Waste users' bandwidth in the hope that they move off Feedburner? Or maybe it's just a bug nobody noticed.
