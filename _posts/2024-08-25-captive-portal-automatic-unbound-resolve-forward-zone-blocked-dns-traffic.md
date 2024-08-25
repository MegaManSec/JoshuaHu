---
layout: post
title: "An automatic captive-portal resolver and DNS white-lister for DNS over TLS with Unbound"
author: "Joshua Rogers"
categories: security
---

In my previous post [_encrypted DNS over TLS on FreeBSD_](https://joshua.hu/encrypted-dns-over-tls-unbound-mullvad-freebsd-block-unencrypted-dns-traffic), I mentioned that "_This setup, unsurprisingly, breaks captive portals and so on. But for my use-case, it’s fine_". That is because I block regular DNS traffic from my computer (unencrypted, over port 53 using UDP). This post details a script that can be, for example at cafes, hotels/hostels, airports, etc., which can automatically deal with captive portals.

The problem that needs to be solved is as follows:

1. When connecting to a public Wifi network, DNS is generally hijacked to force any http connections to be redirected to a captive page/landing page, accepting some terms&conditions or something similar.
2. Since we block any DNS requests over regular unencrypted DNS, we cannot resolve any host because we only allow DNS-over-TLS via unbound to Mullvad's servers (and, as if any public wifi's DNS server will support DoT anyways) -- and therefore cannot have our DNS hijacked.
3. Since we cannot have our DNS hijacked, we don't know how or where to connect to the landing page for the captive portal.
4. The captive portal may have (image or JS) dependencies which are not immediately obvious.

The easiest solution would of course to simply disable the firewall when connecting to the portal, changing the DNS server used to the same as provided by the DHCP server, then re-enabling it when the internet is accessible. But that's too easy. Let's make a script that does everything we need to.

First we inspect the dhcp lease. dhcp leases on freebsd are located in /var/db/dhclient.leases.$iface.

Since multiple leases may be present, we just parse the final lease (which should be the most recent, but YMMV).

From the lease, we extract the advertised DNS server(s): let's pretend they're 192.168.1.1 and 192.168.1.2.

For each of those servers, we whitelist connections to/from them over port 53 (but we do not change the system resolver).

Next, we perform a DNS resolution of `captive.apple.com` to each of the DNS servers. This domain is used by Apple to check for such captive portals.

For each A record, we then actually connect to the webpage. Captive portals generally don't imitate other websites, but respond with a 0-TTL DNS response, with an A record pointing to a webserver which then redirects the user to the captive portal website.
For example, if you visit `google.com`, the DNS resolver will return `192.168.1.3`. When you then browse to `google.com`, the server on `192.168.1.3` will redirect to `captive.airportwebsite.com`, which is also served by the `192.168.1.3` server.

So, connecting, we simply: `curl -I -X POST -s -A 'Mozilla' -m 10 -H 'Host: captive.apple.com' -L -k http://"$A_RECORD"/ | awk '/^Location/ {print $NF}'`.
This connects to the hijacked `captive.apple.com`, and follows any redirections that occur. The redirect-urls are collected.
Eventually, we collect a set of data such as: `captive.apple.com is hijacked by the DNS server 192.168.1.1 with A record 192.168.1.3. This redirects to http://captive.airportwebsite.com/`.

With this data, we then need to set up custom forward-zones. These specify the upstream DNS resolver used for certain domain names. An example is the following:

```
forward-zone:
	name: "wlan.schiphol.nl"
	forward-addr: 192.168.1.1
	forward-tls-upstream: no
	forward-tcp-upstream: no
```

In my other post, I mentioned that I used `tcp-upstream: yes` and `tls-upstream: yes`. These are global settings for all zones and upstream dns resolvers.
I expected that for individual forward-zones, I could disable them using `forward-tls-upstream: no` and `forward-tcp-upstream: no`. Apparently not. I'm not sure whether this is a bug or not, but I reported it in [unbound#1128](https://github.com/NLnetLabs/unbound/issues/1128). In the meantime, I've unset those global settings, and explicitly set the individual forward-zone options for the main resolver.

Following a restart of unbound, we can actually access the captive portals normally: unbound will forward dns requests (for example) for `wlan.schiphol.nl` to `192.168.1.1` -- and in this case, __only__ `wlan.schiphol.nl`.

Finally, in order to catch any dependencies, we actually `curl` the captive portal, and allow the user to add any more domains to unbound's configuration, similar to above.

unbound is restarted, and you can go on your merry way and visit the captive portal in your browser. Yay.

The script can be found here: [captive-portal-unbinder](https://github.com/MegaManSec/captive-portal-unbinder).
