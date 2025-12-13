---
layout: post
title: "Updating FreeBSD's datetime without DNS"
description: "Fixing SSL handshake errors on FreeBSD caused by system clock resets. A quick guide to manually updating system time without DNS access."
categories: security
---

Recently opening up my FreeBSD-on-MacBook case to clean, I inadvertently reset the internal time by disconnecting the battery. When booting up the system again, my local DNS server using DNS-over-TLS refused to cooperate:

```
[1672531834] unbound[38781:0] debug: sending to target: <adblock.dns.mullvad.net.> 194.242.2.3#853
[1672531834] unbound[38781:0] debug: cache memory msg=66104 rrset=66104 infra=8449 val=66320
[1672531834] unbound[38781:0] error: ssl handshake failed crypto error:1416F086:SSL routines:tls_process_server_certificate:certificate verify failed
[1672531834] unbound[38781:0] error: ssl handshake cert error: certificate is not yet valid
[1672531834] unbound[38781:0] notice: ssl handshake failed 194.242.2.3 port 853
[1672531834] unbound[38781:0] debug: outnettcp got tcp error -1
```

That error `ssl handshake cert error: certificate is not yet valid` is because my clock was set to 1970 after being reset.

Anyways, remembering the syntax for `date(1)` is a PITA, so I wanted to save it here.

```shell
sudo date 202411150106.27
sudo service unbound restart
sudo chronyc online
sudo chronyc -a makestep
```
