---
layout: post
title: "Debugging failures of HTTP/2 in Burp, mitmproxy, and browsers"
author: "Joshua Rogers"
categories: security
---


## Burp Chromium Error

During some recent work, I had to use Burp Suite's proxy to browse a website which relied on around one-hundred different javascript resources, which were hosted on an nginx server. When accessing the webpage and trying to use its functionality, the website would not function, as the javascript resources could not be loaded properly. The debug console offered some, albeit little support:

```
Refused to execute script from '[/9185.c9932aa8d.js](/9185.c9932aa8d.js)' because its MIME type ('text/html') is not executable, and strict MIME type checking is enabled. /:1 Refused to execute script from '[/9185.c9932aa8d.js](/9185.c9932aa8d.js)' because its MIME type ('text/html') is not executable, and strict MIME type checking is enabled.
```

Navigating to `/9185.c9932aa8d.js` didn't help: it showed the correct file contents, and the MIME type was correct (`text/javascript`). Looking at the network tab revealed that for some reason, the request initiated by the webpage (instead of when I manually navigated) resulted in the response

```
# Burp Suite Professional

# Error

Stream failed to close correctly
```

While that explains why the MIME type was wrong, it doesn't explain why that resource couldn't be retrieved. And why could I retrieve it perfectly fine by navigating to the page manually?

In addition to this, when browsing the website, the scripts which exhibited this behavior changed every refresh: one request it was the aforementioned `/9185.c9932aa8d.js`, and on another it was a different one. Burp's "proxy" tab showed no information other than that the request to retrieve the resource was sent, but with no indication of a response being received. In the "event log", two errors were shown of "Type: Error" and "Source: Proxy":

* [1] Stream failed to close correctly
* [1] Communication error: domain.com

Burp does not provide a way to view verbose logs, so there is no way to know what's going on, on the side of the proxy. I worked out that the browser<-->proxy connection was fine, but the proxy<-->website connection was the issue. I couldn't reproduce the issue at all on Firefox, and while I could in a non-proxied Chromium instance, it was so rare that reliably debugging was impossible.

After considering the options of "where it's going wrong", I tried disabling HTTP/2 in Burp. Success! The resources were always loaded properly, and no errors were encountered. While that's a great way to _avoid_ the problem, **I'm not happy with workarounds**. So, I looked through the nginx configuration (which was **massive**) for anything that could be causing some rate-limiting, bot-detection, or anything like this. I found nothing useful.

## Calling mitmproxy to the secure

My next idea was to ditch Burp because it's useless for debugging as it's closed source, and move to mitmproxy. And luckily enough, that exhibited the exact same behavior!

mitmproxy provides much greater debugging capabilities, and I was able to find the HTTP/2 error message corresponding to the request to the to the file which could not be retrieved:

```
HTTP/2 connection closed: <ConnectionTerminated error_code:0, last_stream_id:199, additional_data:None>
[..]
HTTP/2 protocol error: Invalid ConnectionInputs.RECV_HEADERS in state ConnectionState.CLOSED
```

Great! Something is wrong, but we're still not sure certain _what_. So, let's see what's really happening over the wire with Wireshark. Since all HTTP/2 traffic is encrypted, we use:

```
SSLKEYLOGFILE=/tmp/keys mitmproxy  --set proxy_debug=true
```

to run mitmproxy while logging ssl session keys, which Wireshark can use to decrypt HTTP/2 packets (note: at the time of testing, I didn't know that it was possible to log session keys in Burp, too.)

## Wireshark traffic analysis

On the wire, for some reason, not all of the packets being sent to this server are filtered as HTTP/2. That's weird; and basically means that that the packets aren't being sent/received properly. Looking at the packets which _are_ being received properly, we see the packets identified as "GOAWAY" being received (and sent). 

![wireshark GOAWAY](/files/wireshark-debug.png)

What's that? [GOAWAY](https://webconcepts.info/concepts/http2-frame-type/0x7) is a frame which is used to indicate that a connection is being shutdown.

Looking at the position of the GOAWAY frame being sent in terms of the rest of the packets, it seems that as soon as the GOAWAY is received, the remaining packets are all TCP errors, RSTs, and other unidentifiable packets (likely something to do with HTTP/2 but which don't correspond to a fully encrypted/negotiated stream). This was enough for me to realize what was going on.

The aforementioned `<ConnectionTerminated error_code:0, last_stream_id:199, additional_data:None>` notes that `last_stream_id:199`, which corresponds to 100 stream requests, and 99 responses. The server is sending a GOAWAY frame because the connection has _just_ (with the 100th request) exhausted the maximum number of requests that can be sent through it, and the client needs to re-connect with a new connection. The problem is that neither mitmproxy nor Burp are able to handle this frame, and either bail, or attempt to send packets through a terminated connection.

## nginx keepalive_requests

Looking back at the nginx configuration, I discovered that the `keepalive_requests` directive was set to 100. That basically dictates that "if more than 100 keep-alive requests are sent within a keep-alive stream, send a [GOAWAY](https://webconcepts.info/concepts/http2-frame-type/0x7) frame". According to the nginx documentation, this [100 value was previously the default](https://nginx.org/en/docs/http/ngx_http_core_module.html#keepalive_requests), but not since [April 2021: it was changed to 1000](https://trac.nginx.org/nginx/ticket/2155) due to this exact issue.

Based on tests with all of the major and minor browsers, it seems no browser is able to handle the GOAWAY frame with great precision, and connections made after (or in parallel) to the GOAWAY frame being sent will fail.

## Proof of Concept

I tested this on my own nginx server using `keepalive_requests = 5`, and loading a page with [this source code](https://github.com/MegaManSec/MegaManSec.github.io/tree/main/img-serve). The source code loads as many images as the `num` parameter of the page visited (e.g. `/index.html?num=100`) specifies.

![Broken page](/files/broken-page.png)

Straight away, I got the exact same behavior that I was seeing in Burp and mitmproxy! Success! We've worked out what the problem is: the `keepalive_requests` is being exhausted, and the proxies aren't able to re-establish a connection after a GOAWAY frame is received.

## GOAWAY connection close suspicions

My **guess** is that the server sends a single GOAWAY frame in response to a single request and immediately closes the TCP stream. This results in all of the other uninitalized/pending requests on the same keep-alive connection to "fail" (seen as TCP RST or even refused connection).

Basically, while the client receives a GOAWAY from a single request (the "final request" in the maximum number of keep-alive requests), currently-opening connections are broken, as the tcp stream is closed. Clients are up to handle that to themselves, which Burp's proxy and mitmproxy fail at (or their HTTP/2 stacks, at least).

## Browsers

My understanding of [this comment](https://bugzilla.mozilla.org/show_bug.cgi?id=1050329#c8) and [this comment](https://bugzilla.mozilla.org/show_bug.cgi?id=1050329#c14) from a Firefox report seemingly confirms my suspicions, as does a net-export from Chromium (which first exhibits a [ERR\_HTTP2\_SERVER\_REFUSED\_STREAM](https://stackoverflow.com/questions/66572034/inconsistent-err-http2-server-refused-stream-error-on-page-load) error before being retried _once_):

![Chrome network debugging](/files/chrome-debug.png)

I imagine the reason browsers cannot simply "continuously try the connection again if it gets reset/closed on the same connection as a GOAWAY was received" is to avoid a [thundering herd problem](https://en.wikipedia.org/wiki/Thundering_herd_problem). Some browsers do try again _once_, though -- but if the second attempt results in the same problem, it gives up trying.

Based on my tests, Firefox is able to handle the problem the best, which I [believe is due to this commit](https://hg.mozilla.org/integration/autoland/rev/dd75cefee794) (which is [still in the src](https://github.com/mozilla/gecko-dev/blob/f3a243812e5b0c1452e307ec9c900479c7678dec/netwerk/protocol/http/Http2Session.cpp#L3290)) where any "busted http2 sessions" are retried in with HTTP/1.1 _once_ (unlike Chrome, [which retries with HTTP/2](https://chromium.googlesource.com/chromium/src.git/+/c4769d412d1b89724db8eb42577cd975fd85f559%5E!/#F2)).
