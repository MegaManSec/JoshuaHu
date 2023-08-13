---
layout: post
title: "Speeding up nmap service scanning 16x"
author: "Joshua Rogers"
categories: security
---

In my [previous post](https://lol) post, I began writing about how I was designing a port and service scanner for large-scale networks by combining port-scanning tools like masscan/zmap and service scanning tools like nmap. In this post, I'm going to dive into some of the details of nmap's service scanning, and outline how I was able to speed up nmap's service scanning by 16-times.

---

In order to determine the service running on a specific port, nmap uses a so-called "service detection probe list" which is located in a file named "nmap-service-probes".

A probe looks like the following:

`Probe TCP GetRequest q|GET / HTTP/1.0\r\n\r\n|`

The syntax for the probe is the following:

`Probe <protocol> <probename> <probestring> [no-payload]`

The format is quite simple:
* *protocol*: TCP or UDP
* *probename*: An arbitrary name of the probe such as "_GenericLines_", "_RPCCheck_", or "_X11Probe_".
* *probestring*: The data sent to the server when it is probed. Note: `q|[characters]|` is perl's "quote operator" which allows you to create strings without needing to escape special characters.
* *[no-payload]*: Used for UDP scanning so we ignore it for now.

A series of matching rules follow each probe which match on the response to each probe. An example is the following:

`match compuware-lm m|^Hello, I don't understand your request\.  Good bye\.\.\.\. $| p/Compuware Distributed License Management/`

The syntax for the probe is the following:

`match <service> <pattern> [<versioninfo>]`

The format is also quite simple:
* _service_: The service name such as "http", "ssh", "mysql", and so on.
* _pattern_: a perl-form regex pattern to match the response received from the probe.
* _[\<versioninfo\>]_: Various optional flags for extracting/displaying extrra information about the match ([read more here](https://nmap.org/book/vscan-fileformat.html))

---

It is extremely noteworthy that when nmap sends a probe, it **deliberately waits for a pre-defined amount of time**. That is to say, **there is a minimum amount of time each probe takes**. If a match is not received, the next probe is sent; up to a certain 'rarity' of probe -- "Nmap uses the rarity metric to avoid trying probes that are extremely unlikely to match". By default, probes are sent up to the _rarity_ of 7. For probe rarity 1-7, each probe waits at least 6-seconds (but most wait 7.5-seconds):
```
# Wait for at least 6 seconds for data.  It used to be 5, but some
# smtp services have lately been instituting an artificial pause (see
# FEATURE('greet_pause') in Sendmail, for example)
totalwaitms 6000
```
In reality, scanning a host for a service which is completely unidentifiable, will keep you waiting around 160-seconds:
```
# time nmap -sV localhost -p2223
Starting Nmap 7.80 ( https://nmap.org ) at 2023-08-12 14:11 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000098s latency).

[..]

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 160.66 seconds

real    2m40.676s
user    0m0.417s
sys     0m0.065s
```

2 minutes and 40 seconds is an unacceptable time for service scanning a single host. How can we improve this?

---

The most obvious solution is to simply lower the _totalwaitms_ value to something more reasonable. This will sacrifice niche results such as of the mail servers which employ these anti-spam techniques, however this is a sacrifice I believe most are willing to make. _totalwaitms_ can be changed the nmap-service-probes file.
```
# grep 'totalwaitms' /usr/share/nmap/nmap-service-probes
totalwaitms 6000
totalwaitms 7500
totalwaitms 7500
totalwaitms 7500
totalwaitms 7500
totalwaitms 11000
```
_tcpwrappedms_ also must be lowered, since it should be lower than _totalwaitms_:
```
# If the service closes the connection before 3 seconds, it's probably
# tcpwrapped. Adjust up or down depending on your false-positive rate.
tcpwrappedms 300
```

After replacing these values with _totalwaitms 300_ and _tcpwrappedms 200_, it is expected that the scan will now take just a few seconds. However...

```
# time nmap -sV localhost -p2223
[..]

real    2m17.561s
user    0m0.401s
sys     0m0.084s
```
That isn't much of an improvement at all.
