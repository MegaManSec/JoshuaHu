---
layout: post
title: "Fixing Google's Feedburner problem: ?redirect=false, and caching that half works"
tags: [rss_feeds, web_platform]
description: "Blogger's ?redirect=false skips the stale Feedburner copy of the Chrome Releases feed. ETags work with gzip; If-Modified-Since only works via a one-second cache."
---

In a [previous post](https://joshua.hu/wtf-google-feedburner-cache-problem-atom-rss), I talked about how Google's [Chrome Release blog](https://chromereleases.googleblog.com/) was serving stale results on its Atom feed, and had set up a redirect from its RSS feed (which was serving up-to-date results) to ... the stale Atom feed. This meant results were a up to a few days old. This was particuarly annoying because my [CCBot](https://joshua.hu/ccbot-chrome-checker-bot-googlechromereleases-chromium-updates), which parsed the blog's feed to notify me (Opera!) about Chromium vulnerabilities which were fixed. When I wrote that post, the Atom feed was days behind:

```console?prompt=$,#
$ date
Sun Feb 23 22:33:37 AEDT 2025
$ curl --silent "https://feeds.feedburner.com/GoogleChromeReleases" | grep -o '2025-02-..' | sort -n | head -n5
2025-02-16
2025-02-13
2025-02-13
2025-02-13
2025-02-13
```

And the RSS feed (which historically was serving fresh results) was redirecting to the Atom feed:

```console?prompt=$,#&output=http
$ hcurl 'https://www.blogger.com/feeds/8982037438137564684/posts/default'
HTTP/2 302
location: http://feeds.feedburner.com/GoogleChromeReleases
```

Well, lo and behold, a few days ago I came to discover that the RSS feed could still be accessed, if you added a secret parameter, `?redirect=false`:

```console?prompt=$,#&output=http
$ hcurl 'https://www.blogger.com/feeds/8982037438137564684/posts/default?redirect=false'
HTTP/2 200
cross-origin-resource-policy: cross-origin
server: blogger-renderd
x-content-type-options: nosniff
x-xss-protection: 0
x-frame-options: SAMEORIGIN
date: Sat, 21 Nov 2026 22:20:58 GMT
expires: Sat, 21 Nov 2026 22:20:59 GMT
cache-control: public, must-revalidate, proxy-revalidate, max-age=1
last-modified: Sat, 21 Nov 2026 14:45:03 GMT
content-type: application/atom+xml; charset=UTF-8
age: 0
alt-svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000
accept-ranges: none
vary: Accept-Encoding
```

It looks like this parameter has been available forever, it's just undocumented.

Since we can now pull in fresh results from the Chrome Release blog, it means that CCBot can start working properly again. Its source is still [on GitHub](https://github.com/MegaManSec/CCBot), and I'm sure Opera still uses it (lol).

In terms of the [feed caching problem](https://joshua.hu/google-feedburner-broken-caching-if-modified-since) I also previously wrote about, where both the RSS feed and the Feedburner Atom feed refused any caching techniques which RSS feeds typically allow to be utilized, it turns out the `redirect=false` feed supports them. Sort of.

Feedburner itself hasn't changed at all. It still doesn't send an `ETag`, it still ignores `If-Modified-Since`, and it still tells everybody not to cache anything:

```console?prompt=$,#&output=http
$ hcurl -H 'if-modified-since: Mon, 20 Jan 2035 10:39:12 GMT' 'https://feeds.feedburner.com/GoogleChromeReleases'
HTTP/2 200
content-type: text/xml; charset=utf-8
feedburnerv2:
last-modified: Sat, 21 Nov 2026 15:27:08 GMT
cache-control: no-cache, no-store, max-age=0, must-revalidate
pragma: no-cache
expires: Mon, 01 Jan 1990 00:00:00 GMT
date: Sat, 21 Nov 2026 22:35:16 GMT
```

It's also still slow. On the 30th of October, a post published at 07:58 PT was still missing from the Feedburner feed nearly two hours later.

The `redirect=false` feed, on the other hand, does respond with `304 Not Modified`. Sometimes. Here's the same request, with an `If-Modified-Since` in the future, made twelve times in a row:

```console?prompt=$,#
$ URL='https://www.blogger.com/feeds/8982037438137564684/posts/default?redirect=false'
$ for i in $(seq 12); do hcurl -H 'if-modified-since: Mon, 20 Jan 2035 10:39:12 GMT' "$URL" | tr -d '\r' | grep -iE '^(http|date|age)' | paste -sd ' ' -; done
HTTP/2 200  date: Sat, 21 Nov 2026 22:35:17 GMT
HTTP/2 200  date: Sat, 21 Nov 2026 22:35:18 GMT
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:18 GMT age: 0
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:18 GMT age: 0
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:18 GMT age: 0
HTTP/2 200  date: Sat, 21 Nov 2026 22:35:19 GMT
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:19 GMT age: 0
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:19 GMT age: 0
HTTP/2 200  date: Sat, 21 Nov 2026 22:35:20 GMT
HTTP/2 200  date: Sat, 21 Nov 2026 22:35:21 GMT
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:21 GMT age: 0
HTTP/2 304  date: Sat, 21 Nov 2026 22:35:21 GMT age: 0
```

Look at the `date` and `age` headers. The first request in each second gets a full `200`, and every request after it in that same second gets a `304` with an `age: 0` header.

`age` is the header a cache adds when it answers with its own stored copy instead of asking the server behind it. The feed is served with `cache-control: public, must-revalidate, proxy-revalidate, max-age=1`, so whatever sits in front of Blogger's `blogger-renderd` server (presumably some Google frontend) is allowed to keep a copy for one second. While that copy is fresh, the cache handles the `If-Modified-Since` itself, correctly, and replies with a `304`. Once it has expired, the request goes through to `blogger-renderd`, which ignores `If-Modified-Since` completely and sends back the whole feed.

Adding a junk parameter to the URL makes every request miss the cache, and then it's a `200` every single time:

```console?prompt=$,#
$ for i in $(seq 10); do curl -s -o /dev/null -w '%{http_code} ' -H 'if-modified-since: Mon, 20 Jan 2035 10:39:12 GMT' "$URL&nocache=$RANDOM"; done; echo
200 200 200 200 200 200 200 200 200 200
```

So for anything that polls the feed every few minutes, the one-second copy will always have expired by the time the next request comes in, and `If-Modified-Since` never gets a `304`.

That's different to what I found in my original post. Back then, the blogger.com URL was still served by the old GData API (that's what the `sunset` and `link` headers in that post were about), and it answered `If-Modified-Since` with a `304`. Those headers are gone now, and the responses come from `server: blogger-renderd`, which is the same server that handles the blog's own feeds on chromereleases.googleblog.com, redirect included:

```console?prompt=$,#&output=http
$ hcurl 'https://chromereleases.googleblog.com/feeds/posts/default'
HTTP/2 302
server: blogger-renderd
location: http://feeds.feedburner.com/GoogleChromeReleases
```

That's probably also the real reason for the redirect in my last post. The documentation I quoted in my original post said that the old GData feed URLs would keep working, but that "the response is the same as blogspot.com feeds". The Chrome Releases blog's own feeds were already redirecting to Feedburner at the time (that's Blogger's "Post feed redirect URL" setting), so once the GData API was finally switched off, the blogger.com URL started redirecting too. So it probably wasn't me emailing Feedburner's support after all.

`redirect=false` is how you get around that setting, and it's not quite as undocumented as I thought: a [Feedburner help page about Google Webmaster Tools](https://support.google.com/feedburner/answer/97090) mentions `http://mybloggerblog.blogspot.com/feeds/posts/default?redirect=false` as a feed URL format that "should always work" for Blogger users.

---

`If-None-Match` does work on the `redirect=false` feed. The catch is that you only get an `ETag` if you ask for a compressed response. Without `Accept-Encoding: gzip`, there's no `ETag` at all:

```console?prompt=$,#&output=http
$ hcurl "$URL"
HTTP/2 200
server: blogger-renderd
cache-control: public, must-revalidate, proxy-revalidate, max-age=1
last-modified: Sat, 21 Nov 2026 22:21:34 GMT
content-type: application/atom+xml; charset=UTF-8
vary: Accept-Encoding
```

With it, there is:

```console?prompt=$,#&output=http
$ hcurl --compressed "$URL"
HTTP/2 200
content-encoding: gzip
server: blogger-renderd
content-length: 57817
cache-control: public, must-revalidate, proxy-revalidate, max-age=1
last-modified: Sat, 21 Nov 2026 22:21:34 GMT
etag: W/"19973aaeb10ce867051869871443ee4e1f782e6a97a91bff8e8b5422e5f7f357"
content-type: application/atom+xml; charset=UTF-8
vary: Accept-Encoding
```

Asking for only `br` or `zstd` doesn't help either: the server doesn't support them, so it sends the feed uncompressed, without an `ETag`.

Once you have the `ETag`, sending it back in `If-None-Match` gets a `304` every time, even with the cache-busting parameter (so these all come from `blogger-renderd` itself), and with or without `--compressed`:

```console?prompt=$,#
$ for i in $(seq 10); do curl -s --compressed -o /dev/null -w '%{http_code} ' -H 'if-none-match: W/"19973aaeb10ce867051869871443ee4e1f782e6a97a91bff8e8b5422e5f7f357"' "$URL&nocache=$RANDOM"; done; echo
304 304 304 304 304 304 304 304 304 304
```

The `ETag` follows the content, not the URL: it's the same with the junk parameter added, and different for `&max-results=24`.

This saves quite a bit. The full feed is 1,725,860 bytes uncompressed and 57,817 bytes gzipped, and a `304` is nothing. Feedburner sends 55,792 gzipped bytes (1,615,960 uncompressed) every single time.

Oh, and the "RSS feed" I've been talking about in these posts is actually an Atom feed (`content-type: application/atom+xml`). The real RSS version is `?alt=rss&redirect=false`, which behaves exactly the same way, on both blogger.com and chromereleases.googleblog.com.

---

One more thing. Every one of the blog's feed URLs redirects to `http://feeds.feedburner.com/GoogleChromeReleases`, not https, and Feedburner happily serves the feed over plain HTTP:

```console?prompt=$,#&output=http
$ hcurl 'http://feeds.feedburner.com/GoogleChromeReleases'
HTTP/1.1 200 OK
Content-Type: text/xml; charset=utf-8
```

So anything subscribed to one of the Chrome Releases blog's own feed links gets Chrome's security release announcements over cleartext, where anybody in the middle can change them. Nice!

So, to sum it all up:

| URL | `If-Modified-Since` | `If-None-Match` | Up to date? |
|---|---|---|---|
| `feeds.feedburner.com/GoogleChromeReleases` | Ignored | No `ETag` | Not always (hours, or days, behind) |
| `/feeds/posts/default` and `?alt=rss`, on chromereleases.googleblog.com or blogger.com | n/a (302 to Feedburner, over HTTP) | n/a | n/a |
| The same URLs with `redirect=false` | Only from the one-second cache | Works, if you ask for gzip to get the `ETag` | Yes |

If you're polling a Blogger feed that's redirected to Feedburner, use `?redirect=false`, ask for gzip, keep the `ETag`, and send it back as `If-None-Match`. Python's `requests` already asks for gzip by default, so it's only the last two you need to do yourself.
