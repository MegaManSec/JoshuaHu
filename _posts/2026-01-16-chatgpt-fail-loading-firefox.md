---
layout: post
title: "wtf is NS_ERROR_INVALID_CONTENT_ENCODING? investigating shared dictionaries and ChatGPT breakage in Firefox"
tags: [browsers, firefox, web_platform, incident_investigation, ai]
description: "Investigating and diagnosing ChatGPT's outage for Firefox users, resulting in endless loading and inoperable buttons."
---

Today I learnt about the `NS_ERROR_INVALID_CONTENT_ENCODING` error (or "Content Encoding Error") in Firefox, which started popping up in my Network tab while trying to access ChatGPT. Indeed, while having access to ChatGPT has allowed me to keep up the charade that I actually know what I'm doing in (life\|work\|security\|etc), the service became completely inoperable in Firefox a few days ago. I couldn't find any analysis online, so I dug into it myself.

If you're looking for a fix for Firefox, your best bet is to simply open [about:config](about:config) and setting `network.http.dictionaries.enable` to **false**.

If you're interested in the technical details, read on.

---

## The "State Mismatch"

The ultimate cause of the problem is a "State Mismatch" where ChatGPT's HTTP server is:

1. Accepting a dictionary negotiation from the browser (`Accept-Encoding: dcb`),
2. Sending standard Brotli data (`Content-Encoding: br`) but including dictionary-management headers (`use-as-dictionary`),
3. Failing to provide a mandatory security headers required by the new standard.

I hadn't heard of `dcb` (Dictionary-Compressed Brotli) before, so I had to actually read something myself (instead of asking ~~my personal assistant~~ ChatGPT). It goes something like this.

## How Brotli Compression Usually Works

Standard Brotli is a compression algorithm that uses a pre-defined dictionary of [around 13,500 common strings](https://web.archive.org/web/20251027231523/https://gist.github.com/duskwuff/8a75e1b5e5a06d768336c8c7c370f0f3) which show up in standard pages viewed on the internet. Because both the server and the browser (which have Brotli support) have knowledge of this static dictionary, they can represent otherwise large amounts of text with a compressed form of that text.

For example, the string `http-equiv=\"Content-Type` is in that dictionary; instead of using 24-bytes for the whole string, it can use less than 1-byte to represent it (the dictionary reference for that string). Brotli in general is a bit more complicated than this (for example, it also uses the LZ77 algorithm to compress strings that reoccur in a data), but the important part today is this pre-defined dictionary.

## Shared Dictionaries

Dictionary-Compressed Brotli is a step up from this: It allows the server to use *previous* content from your browser's cache as the dictionary. Effectively, it turns a file update into a patch. The browser sends a request like:

```http
GET /cdn/assets/47edf3d1-lbmvrwb8eacezld4.js
Available-Dictionary: :EHe3uwunehosc6+MccCpqDMG88VW5mmyDLoRxd6EMOA=:
Accept-Encoding: gzip, br, dcb
```

This tells the server: "I have version 1 (`lbmvrwb8eacezld4`) of this file in my cache. Use it as a custom dictionary and just send me the differences!" If the server obliges and sends a delta (difference) it **MUST** respond with `content-encoding: dcb` in its HTTP response headers. The problem with ChatGPT is that it isn't doing this.

## Inconsistent Headers

When I captured the raw response with curl, I saw ChatGPT's server was responding with:

```http
HTTP/2 200 OK
content-encoding: br
use-as-dictionary: match="/cdn/assets/47edf3d1-*.js", id="assets/47edf3d1-lbmvrwb8eacezld4.js"
vary: Accept-Encoding
```

The data following these headers was actually standard, readable Javascript -- not a delta. The server had ignored the dictionary I offered and sent the full file, while also responding with the `use-as-dictionary` header despite the fact it refuses to actually obey my request for using `dcb` -- also note the `content-encoding: br`, indicating that the content was actually encoded with typical Brotli. So why did only Firefox choke on this and error out?

Within Firefox's HTTP transaction validation logic, the code checks the `Vary` header. Per [RFC 9842](https://www.rfc-editor.org/rfc/rfc9842.html) (the RFC for Compression Dictionary Transport), if a dictionary is being established or used, the server **MUST** include `available-dictionary` in the `Vary` header. Since ChatGPT only sends `Vary: Accept-Encoding` while sending `use-as-dictionary`, Firefox flags the response as establishing a dictionary, while incorrectly missing `use-as-dictionary` from the `Vary` header, resulting in the response being dropped. Chromium and friends ignore this requirement, for whatever reason, while Firefox throws `NS_ERROR_INVALID_CONTENT_ENCODING`.

## Broken Proxies and "Half-Dictionaries"

An astute reader may also notice that the `match` and `id` values in the `use-as-dictionary` response header differ: `match="/cdn/assets/..` versus `id="assets/`. So what's the deal with that? To be honest, I have no idea. But this mismatch suggests that the origin of this bug in ChatGPT's server is a configuration error in the proxies or CDNs serving ChatGPT's Javascript. One layer of the stack thinks the dictionary is at one path, while another layer expects a different one, leading to this buggy "half-dictionary" response.

## Temporary Fix

For now, the solution is to disable HTTP compression dictionaries in Firefox:

1. Open [about:config](about:config),
2. Search for `network.http.dictionaries.enable`, and set it to `false`.

That's even the quick fix that Mozilla went with, [here](https://github.com/mozilla-firefox/firefox/commit/c081f3f7d21922047379fe76320cfbc3abf7f2b3).
