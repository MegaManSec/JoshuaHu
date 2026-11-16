---
layout: post
title: "Python's ipaddress is_global and is_private"
tags: [python, networking, security]
description: "Python's ipaddress module has changed which addresses it calls global or private three times in patch releases, so the same address can get a different answer depending on which Python 3.11, 3.12 or 3.13 release you run."
---

I found this interesting.

Python's `ipaddress` has `is_global` and `is_private`, which can be used to determine whether a network address is internet-routable or internal/private-only respectively.

These change over time. What surprised me is that they were changed in patch releases:

1. [CVE-2024-4032](https://nvd.nist.gov/vuln/detail/CVE-2024-4032) ([gh-113171](https://github.com/python/cpython/issues/113171)): the module's lists were out of date with IANA's special-purpose address registries. It was fixed in 3.11.10 and 3.12.4.
2. [gh-122792](https://github.com/python/cpython/issues/122792): IPv4-mapped IPv6 addresses (`::ffff:a.b.c.d`) now take their properties from the embedded IPv4 address.
3. [gh-124217](https://github.com/python/cpython/issues/124217): `3fff::/20`, the new IPv6 documentation prefix from [RFC 9637](https://www.rfc-editor.org/rfc/rfc9637.html), is no longer global.

`ipaddress.ip_address(addr).is_global` across a couple releases:

| Address | 3.11.9, 3.12.3 | 3.11.10, 3.12.4–3.12.6, 3.13.0 | 3.11.11, 3.12.7, 3.13.1+ |
|---|---|---|---|
| `192.0.0.8` | True | False | False |
| `64:ff9b:1::1` | True | False | False |
| `2002::1` | True | False | False |
| `2001:1::1` | False | True | True |
| `3fff::1` | True | True | False |

`::ffff:100.100.100.100` (a Tailscale-style address, mapped) is global on 3.13.0, and not on 3.13.1.

Distributions backported the CVE fix into their own builds, but not always, so two OS' that both say "Python 3.11" disagree.

In reality, probably none of this matters. But perhaps you could just parse IANA's [IPv4](https://www.iana.org/assignments/iana-ipv4-special-registry/iana-ipv4-special-registry-1.csv) and [IPv6](https://www.iana.org/assignments/iana-ipv6-special-registry/iana-ipv6-special-registry-1.csv) registries yourself.
