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

