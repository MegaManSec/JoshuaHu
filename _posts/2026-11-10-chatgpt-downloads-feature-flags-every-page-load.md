---
layout: post
title: "Annoying ChatGPT data usage"
tags: [web_platform, browsers, programming]
description: "Every reload of chatgpt.com downloads the full set of Statsig feature flags (around 780KB compressed, 5.7MB of JSON), because the client always asks for everything since time zero. It then tries to cache them in localStorage, runs out of space, and reports the error back to the server. Every time."
---

While investigating slow load times on ChatGPT, I noticed that every reload of chatgpt.com downloads a _lot_ of data, every single load.

Most of it is a single request to `https://ab.chatgpt.com/v1/initialize`, which is Statsig, the feature flag and experimentation service that OpenAI bought last year (because why not). On every page load, the response is around 1MB on the wire, and 5.7MB of JSON once decompressed. About 4.7MB of that is `dynamic_configs`.

The request body is JSON, base64-encoded, and then reversed (yes, really). Decoded, it contains (among other things):

```json
{
  "deltasResponseRequested": true,
  "sinceTime": 0,
  "partialUserMatchSinceTime": 1794316993881
}
```

`sinceTime: 0` means "give me everything since the beginning of time", so the server does. The client even knows when the flags last changed: `partialUserMatchSinceTime` is the exact `time` from the previous response. Two reloads a few minutes apart get exactly the same `time`, `company_lcut`, and `full_checksum` back, so nothing has changed, but we still download the full response every page load. Sometimes a single reload makes the request twice for some reason, too.

I'm currently on an island paying some exorbitant fee for internet, so this is pretty annoying. The server _does_ support doing this properly, though. Rewriting the request to include the previous `sinceTime` and `full_checksum`, the response is only a whopping 836 bytes.

Then (and perhaps related, but I haven't looked into it), the SDK tries to save the uncompressed response in `localStorage` as `statsig.cached.evaluations.<hash>`. But of course, it doesn't fit:

```text
QuotaExceededError: Failed to execute 'setItem' on 'Storage': Setting the value of 'statsig.cached.evaluations.3678146511' exceeded the quota.
```

The SDK does catch that and reports it to their `/v1/sdk_exception` endpoint (on every page load), but it wouldn't help even if it did fit, since handing the SDK a valid cache entry still isn't read back at startup for whatever reason.

On top of all of that, the HTML page for the homepage of ChatGPT includes around 700KB of.. the exact same flags, as bootstrap, and the page loads fine with just those.

So, on every page load, ChatGPT:

1. Downloads ~780KB of flags it already has,
2. Parses 5.7MB of JSON,
3. Serializes 5.65 million characters of it for `localStorage`,
4. Fails, and reports the failure.

Annoying!
