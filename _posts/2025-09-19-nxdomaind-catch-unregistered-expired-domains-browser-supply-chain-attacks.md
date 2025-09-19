---
layout: post
title: "NXDOMAIN'd: Catching unregistered domains for fun and profit"
author: "Joshua Rogers"
categories: security
---

## NXDOMAIN'd

Sometimes, companies simply change domains, leaving old scripts pointing towards non-existent domains. Sometimes this includes more than just scripts: image, css, and font files are just some possible resources which could be loaded from a dangling domain. How can we discover these domains, and register them (for effectively, a supply-chain attack)?

That's what NXDOMAIN'd is for: a browser extension which monitors all domains that are loaded in the browser, and checks whether they are actually registered or not.

This extension works in both Firefox and Chrome, and is open source. The source code can be found at [https://github.com/MegaManSec/NXDOMAINd](https://github.com/MegaManSec/NXDOMAINd). The extension can be downloaded on the release page, [https://github.com/MegaManSec/NXDOMAIND/releases](https://github.com/MegaManSec/NXDOMAIND/releases).

With the modern internet a hellhole of javascript files connecting to external resources across a chain of hundreds of domains (for tracking and advertising, of course), the risk of a website loading some type of resource from a domain which simply no longer exists becomes a reality. If a website loads a javascript file from one-website.com, which loads another from two-website.com, which then loads another from three-website.com, the blast-radius of some type of malicious script on three-website.com now includes your website. Subresource integrity helps with validating scripts with some type of bill of material, ensuring the direct script loaded hasn't been modified, but 1) who uses that, and 2) what about scripts that are loaded from _that_ script?

Note: It would be way more effective to do this on the DNS level -- just monitor your local DNS resolver for any NXDOMAIN responses, for example. But, I wanted to make a browser extension.

## Use Cases

Do you want to do any of the following?

- Show your own ads,
- Rewrite links for your affiliate programs,
- DDoS,
- Access user data,
- Show FAKE NEWS,
- Mine crypto in the browser
- ... and more?

Then this script is for you!

## How It Works

The script works as such:

1. When a website is connected-to, the extension extracts the domain name of the host.
2. The extension then attempts to check the domain's registration status using Registration Data Access Protocol (RDAP). RDAP is a WHOIS replacement, which implements standardized data access, and access is available over https. Because it's over https, we can access the results directly from an extension.
3. If RDAP fails (not all registry operators support RDAP yet), the extension falls back to DNS (using DNS-over-HTTPS), and checks if the response is NXDOMAIN.
4. If the domain is determined to be unregistered, an alert appears in the extension button with this fact. In all cases, the results are cached.

## Extra Notes

Other than that it works surprisingly well, there are a few concerns about this extension from my side.

### DNS Leak to RDAP and and DoH Servers

By definition, this extension will leak the domains that you connect to, to the RDAP and DoH servers. In both cases, these are encrypted, so anybody on-the-wire cannot monitor it, but the _domains_ (not full hostnames) are leaked to https://rdap.org/ and https://dns.google/ and possibly https://cloudflare-dns.com/.

RDAP works by redirecting a request (with a 302 redirect) to the appropriate foreign server for the correct domain registry. For example, `https://rdap.org/domain/google.nl` redirects to `https://rdap.sidn.nl/domain/google.nl`. This means that you also leak domains to the registry (which all use https).

### Cached Domains

By definition, this extension will cache all domain names of all of the websites you visit, including all resources. This goes beyond what the normal browser history includes (because it doens't include resources). Be conscious of this.

### What is NXDOMAIN anyways?

A DNS response of NXDOMAIN does not _always_ mean a domain is unregistered! Who knew!

The registry for `.co.za` does not offer RDAP, and as such, `rdap.org` will return a 404, resulting in a fallback to DoH in the extension. Let's take this domain for example:

```
$ dig softmar.co.za
[..]
;; ->>HEADER<<- opcode: QUERY, status: NXDOMAIN, id: 53353
```

We get `NXDOMAIN` as the status. So that means it's unregistered, right? Well, not so fast!

```
$ whois -h whois.registry.net.za softmar.co.za
Domain Name: softmar.co.za
Registry Domain ID: 3w2dd_DOMAIN-CO.ZA
Registrar WHOIS Server: Whois.markmonitor.com
Registrar URL: https://www.markmonitor.com/
Updated Date: 2024-03-21T10:41:50Z
Creation Date: 2022-04-22T12:18:49Z
Registry Expiry Date: 2026-04-22T12:18:49Z
Registrar Registration Expiration Date: 2026-04-22T12:18:49Z
Registrar: MarkMonitor
Registrar IANA ID: 292
Registrar Abuse Contact Email: ccops@markmonitor.com
Registrar Abuse Contact Phone: +1.2083895740
Reseller:
Domain Status: serverHold https://icann.org/epp#serverHold
[..]
Name Server: ns1.markmonitor.com
Name Server: ns3.markmonitor.com
Name Server: ns4.markmonitor.com
Name Server: ns2.markmonitor.com
```

It's certainly registered! So what's going on here? The key is in the fact the domain status is in `serverHold`. Let's try asking the authorative server for an SOA record:

```
$ dig +norec @ns1.markmonitor.com SOA softmar.co.za

; <<>> DiG 9.10.6 <<>> +norec @ns1.markmonitor.com SOA softmar.co.za
; (2 servers found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: REFUSED, id: 8275
;; flags: qr; QUERY: 1, ANSWER: 0, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1232
; OPT=15: 00 14 ("..")
;; QUESTION SECTION:
;softmar.co.za.			IN	SOA
```

So, the status from the authoritative server is `REFUSED`. It should return AA + an SOA record. Since it doesn't it means one of:
- Zone not loaded on those servers yet (most common).
- The server is not acting authoritative for that zone at all.

The zone is not loaded because the domain is in serverHold status -- _practically_ deleted, but not actually deleted (because there is no such thing as deleting a domain). As such, ZACR (the .co.za domain registry) pre-delegation checks fail, and such the co.za zone omits the NS softmar.co.za delegation. This results in the `NXDOMAIN`.

Basically, the REFUSED from MarkMonitor nameservers tells the registry that the domain is "not ready", so the registry won't even forward the DNS request upstream to MarkMonitor, which the registry assumes to mean the domain is not registered.

There is no good way to solve this in an extension (i.e. using only https), so I won't even try.
