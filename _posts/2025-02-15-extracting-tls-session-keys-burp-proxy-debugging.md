---
layout: post
title: "Extracting TLS Session Keys in Burp Proxy à la SSLKEYLOGFILE"
description: "How to extract TLS session keys from Burp Suite to decrypt HTTP/2 traffic in Wireshark for better debugging and network analysis."
categories: security
---

In [my previous post](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium), I outlined how I discovered a bug in the handling of closing HTTP/2 keep-alive requests in Burp Suite, and how I had to debug the issue by using mitmproxy due to Burp's limited debugging capabilities.

One of the steps required to debug that issue was looking at the HTTP/2 packets over-the-wire between the proxy and the website. Many applications and libraries offer the ability to dump these keys with the `SSLKEYLOGFILE` environmental value, or with easy `LD_PRELOAD` tricks like OpenSSL. However, it seemed that wasn't possible with Burp. Online resources such as [this one](https://stackoverflow.com/questions/8152928/sniffing-https-ssl-traffic-with-burp-suite-proxy-in-combination-with-wireshark), [this one](https://forum.portswigger.net/thread/integrating-burp-and-wireshark-816abb78), and [this one](https://security.stackexchange.com/questions/277155/export-burp-certificate-to-wireshark-for-inspection), indicated that others had encountered the same pitfall.

As it turns out, it _is_ possible to extract the TLS session keys which are negotiated between the Burp proxy and websites visited. That is to say, in the chain (Browser <--> Burp Proxy <--> Website), we can extract the TLS keys used in the Burp Proxy <--> Website communication channel, allowing us to inspect the decrypted traffic in Wireshark (or otherwise).

---

Wireshark's [TLS wiki page](https://gitlab.com/wireshark/wireshark/-/wikis/tls#using-the-pre-master-secret) outlines how Java programs (which Burp is) can have their TLS keys extracted using a drop-in javaagent, such as [neykov/extract-tls-secrets](https://github.com/neykov/extract-tls-secrets).

Downloading the agent (or building it), you just need to run the Burp .jar file with the argument `-javaagent:extract-tls-secrets-4.0.0.jar=keys.txt`, which results in the TLS keys being saved to `keys.txt`. On Burp Suite Professional on MacOS, this can by done by running:

```shell
/Applications/Burp\ Suite\ Professional.app/Contents/Resources/jre.bundle/Contents/Home/bin/java \
  -javaagent:extract-tls-secrets-4.0.0.jar=keys \
  -jar /Applications/Burp\ Suite\ Professional.app/Contents/Resources/app/burpsuite_pro.jar
```

You then use Burp normally, and in Wireshark, specify the location of the keys in the Edit -> Preferences -> Protocols -> TLS, (Pre)-Master-Secret log filename preference.
