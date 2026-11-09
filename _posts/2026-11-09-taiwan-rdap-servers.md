---
layout: post
title: "What's going on with Taiwan's RDAP server?"
tags: [dns, networking, security]
description: "RDAP lookups for .gov.tw domains come back 404 from TWNIC even when the domain exists. The IANA bootstrap only has a .tw entry, so every .gov.tw query lands at TWNIC, while Taiwan's government names live in a separate registry at rs.gsn.gov.tw, which WHOIS points to over rwhois."
---

RDAP is basically WHOIS, but machine-readable, with a lookup returning JSON, all served over HTTPS. `rdap.org`, the main redirector to individual RDAP servers, doesn’t hold the registration data itself, it simply.. redirects. It checks IANA's bootstrap registry for an RDAP server and sends the request there with an HTTP 302.

For example, this is the redirect for `twnic.tw`:

```
$ hcurl 'https://rdap.org/domain/twnic.tw'
HTTP/2 302
date: Mon, 09 Nov 2026 20:07:56 GMT
content-type: text/html
location: https://ccrdap.twnic.tw/tw/domain/twnic.tw
```

Following the `Location` gets a JSON object from TWNIC (Taiwan's national domain name registry). RDAP records can tell you whether a domain is active, which nameservers it uses, when it was registered or expires, and who the registrant is (whois!) For example, the output can contain some things like this for the RDAP result of `twnic.tw`:

```json
{
  "rdapConformance": ["rdap_level_0"],
  "objectClassName": "domain",
  "ldhName": "twnic.tw",
  "status": [
    "server transfer prohibited",
    "server delete prohibited",
    "server update prohibited"
  ],
  "nameservers": [
    {
      "objectClassName": "nameserver",
      "ldhName": "dns1.twnic.net.tw"
    },
    {
      "objectClassName": "nameserver",
      "ldhName": "dns2.twnic.net.tw"
    }
  ],
  "events": [
    {
      "eventAction": "registration",
      "eventDate": "2005-10-27T09:02:34Z"
    },
    {
      "eventAction": "expiration",
      "eventDate": "2099-12-31T15:59:59Z"
    }
  ],
  "entities": [
    {
      "objectClassName": "entity",
      "roles": ["registrant"],
      "vcardArray": [
        "vcard",
        [
          ["version", {}, "text", "4.0"],
          ["org", {}, "text", "Taiwan Network Information Center"]
        ]
      ]
    }
  ]
}
```

While using [NXDOMAIN'd](https://github.com/MegaManSec/NXDOMAINd) (see [this post](https://joshua.hu/nxdomaind-catch-unregistered-expired-domains-browser-supply-chain-attacks), the point is to automatically alert when your browser tries to connect to unregistered domains), the plugin alerted on `tip.railway.gov.tw`. I visited more `.gov.tw` sites and got more alerts. The sites were fine though, so I didn't really understand what was going on.

I saw:

```
$ hcurl 'https://rdap.org/domain/doesntexist.tw'
HTTP/2 302
location: https://ccrdap.twnic.tw/tw/domain/doesntexist.tw

$ hcurl https://ccrdap.twnic.tw/tw/domain/doesntexist.tw
HTTP/2 404

$ hcurl https://ccrdap.twnic.tw/tw/domain/google.tw
HTTP/2 200

$ hcurl https://ccrdap.twnic.tw/tw/domain/tip.railway.gov.tw
HTTP/2 404
```

The 302 only tells us that `.tw` has an RDAP server, but doesn't say whether a particular name is registered. For a suffix with no RDAP service listed, `rdap.org` itself returns 404. For example, `.exist` has no route:

```
$ hcurl 'https://rdap.org/domain/doesnt.exist'
HTTP/2 404
date: Mon, 09 Nov 2026 20:12:20 GMT
content-type: application/rdap+json
```

An unregistered `.com` name still gets redirected because `.com` has an RDAP server:

```
$ hcurl 'https://rdap.org/domain/dascascsa333ewafecsdc.com'
HTTP/2 302
location: https://rdap.verisign.com/com/v1/domain/dascascsa333ewafecsdc.com
```

The [IANA bootstrap](https://data.iana.org/rdap/dns.json) has an entry for `.tw`, pointing to TWNIC. There is no more-specific `gov.tw` entry. Under the [longest-match rules](https://www.rfc-editor.org/rfc/rfc9224.html), `.gov.tw` queries therefore go to TWNIC too. AFAICT, a more-specific entry is possible and `.gov.tw` not being a TLD doesn't prevent one.

The real news is that Taiwan also has a separate government domain registration system at [rs.gsn.gov.tw](https://rs.gsn.gov.tw/). A government PKI document calls it the "Government WHOIS host", and WHOIS records for `.gov.tw` names point to `rwhois://rs.gsn.gov.tw` (note that _rwhois_, not _whois_, even).

So, mystery solved. RDAP discovery sends the query to TWNIC, which doesn't return (or know about) the .gov.tw record, because it's the wrong registry.
