---
layout: post
title: "A small solution to DNS rebinding in Python"
author: "Joshua Rogers"
categories: security
---

# Reporting to an AI Bug Bounty

In the first time in probably a decade, I reported a vulnerability on a bug bounty platform. I learnt about the platform _[huntr](https://huntr.com/)_, and checked out the recently disclosed vulnerabilities. A fixed vulnerability in [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) piqued my interest: an SSRF. For fun, I checked whether the affected code was vulnerable to DNS rebinding. [It was](https://github.com/Significant-Gravitas/AutoGPT/security/advisories/GHSA-wvjg-9879-3m7w) (and to [another issue](https://github.com/Significant-Gravitas/AutoGPT/security/advisories/GHSA-ggcm-93qg-gfhp)), and so I decided to report it to see what'll happen. Just a few hours later, the platform marked my report as a duplicate and _publicized my report_. The report was not a duplicate though, and they had just revealed to the world the information about the vulnerability. In reponse to this, AutoGPT dropped that the platform, I had some laughs, and AutoGPT fixed the vulnerabilities (with my support). This post details my solution to fixing DNS rebinding in Python.

# DNS Rebinding

A quick recap: DNS rebinding is a technique by which you can bypass host-based restrictions on requests being made by an application, stemming from a time-of-check-time-of-use (TOCTOU) disparity between when a hostname is resolved as a pre-flight check, versus when a hostname is resolved during a request. That's a lot of words, but the point is, if an application does the following to stop requests from being sent to internal (or otherwise) destinations as such:

```python
ip_addresses_of_host = resolve_addresses(hostname) # Returns a list of ip addresses `hostname` resolves to

for address in ip_addresses_of_host:
    if is_local_address(address): # checks if an address is a local address
        return False

requests.get(hostname)
```

then the application is not fully protected, because the first resolution of the ip addresses of the hostname may not result in the same ip address as when `requests` sends the actual request. The first resolution can say "these results are valid only for 0-seconds", so when `requests` attempts to connect to the host, it re-resolves the ip address, which may change. This is easily seen with the useful `1u.ms` service, which makes rebinding attacks easy:

```shell
$ dig +short @1.1.1.1 make-1.2.3.4-rebind-169.254-169.254-rr.1u.ms
1.2.3.4
$ dig +short @1.1.1.1 make-1.2.3.4-rebind-169.254-169.254-rr.1u.ms
169.254.169.254
```

# Python Solution to DNS Rebinding

So with that all said and done, how do we protect against this in Python?

My solution is:

```python
import requests
import ssl
import sys
from urllib.parse import urlparse, urlunparse
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

class HostHeaderSSLAdapter(HTTPAdapter):
    """Adapter that connects to an IP address but validates TLS for a different host."""
    def __init__(self, ssl_hostname, *args, **kwargs):
        self.ssl_hostname = ssl_hostname
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        kwargs['ssl_context'] = context
        kwargs['server_hostname'] = self.ssl_hostname  # This works for urllib3>=2
        self.poolmanager = PoolManager(*args, **kwargs)

url = "https://example.com/"

parsed_url = urlparse(url)
original_hostname = parsed_url.netloc
# Resolve the first IP address for the hostname
resolved_ip = resolve_first_ip(original_hostname)

# Check if the resolved address is local (or blocklisted)
if is_local_address(resolved_ip):
    sys.exit(1)

# Create a session and mount the custom adapter
session = requests.Session()
# Ensure https certificate is checked against cn=original_hostname
adapter = HostHeaderSSLAdapter(original_hostname)
session.mount("https://", adapter)

# Send request with proper Host header (original_hostname)
headers = {
    "Host": original_hostname
}

# Reconstruct netloc, replacing the hostname with its associated IP address
netloc = ""
if parsed_url.username and parsed_url.password:
    netloc = '{}:{}@'.format(parsed_url.username, parsed_url.password)
elif parsed_url.username:
    netloc = '{}@'.format(parsed_url.username)

netloc += resolved_ip

if parsed_url.port:
    netloc += ':{}'.format(parsed_url.port)

# Replace the netloc with the reconstructed netloc
url = parsed_url._replace(netloc=netloc)

# Do not follow redirects, as they may redirect to blocked addresses.
response = session.get(url, headers=headers, allow_redirects=False)

print("Status Code:", response.status_code)
print("Response Headers:", response.headers)
```

The idea behind this code is:

1. Resolve an IP address for the hostname of the to-be-retrieved website,
2. Check whether the IP address is blocked (such as it being a local address),
3. Create a session for the request and ensure that the request checks any https certificate against the original hostname,
4. Replace the hostname in the request with the IP address of the hostname,
5. Set the `Host` header in the HTTP request to the original request,
6. Send the request.

This is equivalent to:

```shell
$ dig +short example.com
23.215.0.138
$ curl --resolve example.com:443:23.215.0.138 https://example.com
```

Note:

```
--resolve <[+]host:port:addr[,addr]...>
    Provide a custom address for a specific host and port pair. Using this, you can make the curl requests(s) use a specified address
    and prevent the otherwise normally resolved address to be used. Consider it a sort of /etc/hosts alternative provided on the command line.
    The port number should be the number used for the specific protocol the host is used for. It means you need several entries if you want
    to provide addresses for the same host but different ports.
```

So in Python, as far as I'm concerned, the example script is secure, as long as the `resolve_first_ip` and `is_local_address` functions are. Redirects cannot be followed as they may forward the request to a blocked address, but this can be overcome with [manual intervention](https://requests.readthedocs.io/en/latest/api/#requests.Response.is_redirect) and handling redirects manually.

Specifically in the case of redirects, one must ensure that the handling of redirects does not leak cross-origin cookies. This can be solved using [RequestsCookieJar](https://3.python-requests.org/_modules/requests/cookies/#RequestsCookieJar), for example:

```python
s = requests.session()
s.cookies.set("COOKIE_NAME", "the cookie works", domain="example.com") # Ensures that the cookie is not sent to any domain other than example.com (note: may need to set the domain to the resolved ip address, instead)
```

A more comprehensive solution to all of this would and could monkey patch `requests.Session.request` to perform the host-replacing-and-checking before sending any request at all.
