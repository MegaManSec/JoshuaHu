---
layout: post
title: "Encrypted DNS over TLS on FreeBSD, and Blocking Unencrypted DNS Traffic"
author: "Joshua Rogers"
categories: security
---

Unlike systemd-based Linux distributions, FreeBSD does not [come with a switch](https://wiki.archlinux.org/title/systemd-resolved#DNS_over_TLS) to automatically turn on DNS-over-TLS (DoT) for the system resolver, and requires a bit of work to use an encrypted channel for domain resolution. In this post, we'll look at how to set up DoT for FreeBSD using `unbound(8)`, enable some hardening, and block all non-encrypted DNS traffic over port-53.

---

Note: FreeBSD comes with a built-in caching DNS resolver called `local-unbound(8)`. This is a stripped-down version of [unbound](https://www.nlnetlabs.nl/projects/unbound/about/) which provides a basic local caching and forwarding resolver, with relaxed validation (in order to be compatible with corporate and public network setups). The configuration for this resolver is located in `/var/unbound` (note: `/etc/unbound@ -> ../var/unbound`), however this configuration is overwritten periodically, so we won't be using this^[in fact, we could put our configuration in `/var/unbound/conf.d`, however this is not a proper use-case and may be subject to breakage.]. Instead, we'll be using the `dns/unbound` port.

Previously, I used [dnscrypt-proxy](https://github.com/DNSCrypt/dnscrypt-proxy) to setup a forwarding resolver which forwards to a DNS-over-HTTPS (DoH) server. I wanted to learn about unbound this time, so went with this. unbound has an [open feature request](https://github.com/NLnetLabs/unbound/issues/308) for DoH, but it looks like nobody has started development on it yet. In my opinion, DoH is more secure than DoT, as an unsophisticated firewall can simply block port 853 (DoT default port) traffic, and deny access. Oh well.

---

Firstly, we install unbound using either `pkg(8)` or from the ports tree. We enable the unbound daemon on boot:
```
$ sudo sysrc unbound_enable="YES"
unbound_enable: NO -> YES
```

unbound's configuration files are located in `/usr/local/etc/unbound`. A default configuration will act as a forwarding server, querying the root DNS servers for any domains queried, over plaintext. We need to set it up to use DoT now.

---

Secondly, we must install `ca_root_nss` either using `pkg(8)` or from the `security/ca_root_nss` port in the ports tree. This port installs Mozilla's root certificate bundle into `/usr/local/share/certs/ca-root-nss.crt` -- as well as some symlinks and other locations. This file will be used to verify the authenticity of the authenticity/certificate of the DoT server.

---

In this example, I'm using Mullvad's adblocking DoT server. Out of the available options outlined on [privacyguides.org](https://www.privacyguides.org/en/dns/#recommended-providers), I decided I trust Mullvad the most. Adblocking via DNS is one of the most simple and effective ways to ensure that my browsing experience isn't ruined by the typical oppresive ad networks (it also makes cooking/recipe websites bearable.)

Editing `/usr/local/etc/unbound.conf`, we add to the bottom:
```
forward-zone:
	name: "adblock.dns.mullvad.net"
	forward-addr: 194.242.2.3@853#adblock.dns.mullvad.net
	forward-addr: 2a07:e340::3@853#adblock.dns.mullvad.net
	forward-addr: 1.1.1.1@853#one.one.one.one
	forward-addr: 2606:4700:4700::1111@853#one.one.one.one
	forward-tls-upstream: yes

forward-zone:
        name: .
        forward-host: adblock.dns.mullvad.net#adblock.dns.mullvad.net
        forward-tls-upstream: yes
```

I think this configuration needs some explanation.

A `forward-zone` section is used to define specific configurations for certain DNS zones. In the above code-block, first a specific zone for the domain "adblock.dns.mullvad.net" is created, and then one for everything else.

Normally, you could just set the bottom `forward-zone` section and call it a day: unbound would first resolve `adblock.dns.mullvad.net` using the plaintext root DNS servers and then connect to the resolved IP address in order to perform all recursive resolutions in the future. However as I plan to completely block all outgoing port 53 connections, unbound won't be able to perform the initial resolution of `adblock.dns.mullvad.net`.

The first part of the configuration solves this issue: it specifies that when _resolving_ `adblock.dns.mullvad.net`, unbound should attempt to use one the listed four servers listed. That is to say, __when resolving__ `adblock.dns.mullvad.net` itself, unbound will use 194.242.2.3, etc. It also uses DoT in order to do this: the syntax for `forward-addr` to use DoT is `[ip-address]@[port]#[hostname]`. The port here is redundant since 853 is the default port number, however I have specified it to showcase how it works.

`forward-tls-upstream` is also redundant, as DoT does not work over UDP, but added for verbosity.

So, in order to resolve `adblock.dns.mullvad.net`, unbound will use the DoT server `194.242.2.3` (which is currently the ip address of `adblock.dns.mullvad.net`). If this fails for some reason, it will fallback to Cloudflare's DoT server -- leaking only to Cloudflare the fact that we are planning to use Mullvad's DoT server.

It is also, of course, possible to simply set the configuration to:

```
forward-zone:
        name: .
        forward-addr: 194.242.2.3@853#adblock.dns.mullvad.net
        forward-addr: 2a07:e340::3@853#adblock.dns.mullvad.net
        forward-tls-upstream: yes
```

However, I like having the fallback to resolve `adblock.dns.mullvad.net` if Mullvad ever changes IP address.

---

Finally, we need to set the `tls-cert-bundle` configuration in a `server:` block in the configuration file. This option is set to the location of the file installed by `ca_root_nss`. Therefore, `unbound.conf` is altered:
```
 	# tls-cert-bundle: ""
```
becomes
```
 	tls-cert-bundle: "/usr/local/share/certs/ca-root-nss.crt"
```

---

First checking the config, we restart unbound, and confirm the resolver is now working:

```
$ unbound-checkconf 
unbound-checkconf: no errors in /usr/local/etc/unbound/unbound.conf
$ service unbound restart
Stopping unbound.
Waiting for PIDS: 9475.
Obtaining a trust anchor...
Starting unbound.
$ drill -Q @127.0.0.1 nist.gov A
129.6.13.49
$ drill -S @127.0.0.1 nist.gov
;; Number of trusted keys: 1
;; Chasing: nist.gov. A


DNSSEC Trust tree:
nist.gov. (A)
|---nist.gov. (DNSKEY keytag: 18303 alg: 8 flags: 256)
    |---nist.gov. (DNSKEY keytag: 33751 alg: 8 flags: 257)
    |---nist.gov. (DS keytag: 33751 digest type: 2)
        |---gov. (DNSKEY keytag: 35496 alg: 13 flags: 256)
            |---gov. (DNSKEY keytag: 2536 alg: 13 flags: 257)
            |---gov. (DS keytag: 2536 digest type: 2)
                |---. (DNSKEY keytag: 20038 alg: 8 flags: 256)
                    |---. (DNSKEY keytag: 20326 alg: 8 flags: 257)
;; Chase successful
```

We can also confirm that the query is being sent to Mullvad over DoT:
```
$ sudo tcpdump -n -i wifibox0 'port 53 or port 853' 
tcpdump: verbose output suppressed, use -v or -vv for full protocol decode
listening on wifibox0, link-type EN10MB (Ethernet), capture size 262144 bytes
02:15:13.174393 IP 10.0.0.2.35553 > 194.242.2.3.853: Flags [S], seq 60052006, win 65535, options [mss 1460,nop,wscale 6,sackOK,TS val 2948857167 ecr 0], length 0
[...]
```

---

Great, so we now have a forwarding resolver using DoT. Let's harden the configuration a bit.

For brevity, I won't go into details for each of the of each configuration change, and some of them are redundant, but this is a diff of the changes I have made to `unbound.conf`:

```
158c158
< 	# msg-cache-size: 4m
---
> 	msg-cache-size: 64m
211c211
< 	# rrset-cache-size: 4m
---
> 	rrset-cache-size: 128m
286c286
< 	# tcp-upstream: no
---
> 	tcp-upstream: yes
484c484
< 	# hide-identity: no
---
> 	hide-identity: yes
487c487
< 	# hide-version: no
---
> 	hide-version: yes
490c490
< 	# hide-trustanchor: no
---
> 	hide-trustanchor: yes
516c516
< 	# target-fetch-policy: "3 2 1 0 0"
---
> 	target-fetch-policy: "-1 -1 -1 -1 -1"
522c522
< 	# harden-large-queries: no
---
> 	harden-large-queries: yes
540c540
< 	# harden-referral-path: no
---
> 	harden-referral-path: yes
545c545
< 	# harden-algo-downgrade: no
---
> 	harden-algo-downgrade: yes
560c560
< 	# qname-minimisation-strict: no
---
> 	qname-minimisation-strict: yes
568c568
< 	# use-caps-for-id: no
---
> 	use-caps-for-id: yes
609c609
< 	# prefetch: no
---
> 	prefetch: yes
612c612
< 	# prefetch-key: no
---
> 	prefetch-key: yes
933c933
< 	# tls-upstream: no
---
> 	tls-upstream: yes
```

---

Next, we block all outgoing connections on port 53 using `firewall(8)`/`ipfw(8)`. This configuration assumes that no other firewall/ipfw rules have been used.

Creating a file `/usr/local/etc/ipfw.rules`, we add:
```
#!/bin/sh
ipfw -q flush
ipfw -q add allow ip from any to any via lo0
ipfw -q add deny ip from any to any dst-port 53
ipfw -q add deny ip from any to any src-port 53
ipfw -q add allow all from any to any
```
Make sure it is executable (`chmod +x /usr/local/etc/ipfw.rules`).

This configuration:
1. allows all connections on link local addresses,
2. denies all connections to and from port 53,
3. allows all remaining connections.

We enable the firewall at boot, and then start it:
```
$ sysrc firewall_enable="YES"
firewall_enable: NO -> YES
$ sysrc firewall_script="/usr/local/etc/ipfw.rules"
firewall_script: "" -> /usr/local/etc/ipfw.rules
$ service ipfw restart
Firewall rules loaded.
```

Finally, we check whether everything works: 
```
$ drill -Q @127.0.0.1 google.com
216.58.214.14
$ drill -Q @8.8.8.8 google.com
Error: error sending query: Error creating socket
```

As expected, the unbound successfully resolves the address, while attempting to use an external plaintext resolver fails, as the packets are blocked.

---

This setup, unsurprisingly, breaks captive portals and so on. But for my use-case, it's fine.
