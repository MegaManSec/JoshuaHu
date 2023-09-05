---
layout: post
title: "5 Tips For Port Service Scanning 16x Faster: Part 1"
author: "Joshua Rogers"
categories: security
---

In recent years, nmap's prevalence for large-scale (TCP) port scanning has diminiuished due to newer and faster tools such as zmap and masscan becoming available. However, nmap's service scanning still remains the best tool for identification of what is actually running on open ports, with its service scanning probes (and its scripting engine).

Recently, I've been working on a tool which continuously scans large-scale networks (multiple /8 and /12 blocks, for ports 1-65535) and identifies the services running behind them (with the goal of periodically comparing reachable services between certain time-frames). Creating such a tool, I faced a few difficulties in terms of speed and accuracy, and I wanted to detail the challenges, considerations, and solutions, that I discovered (and with the massive help of my former boss). So, here's five tips for port service scanning at scale.

---

### (1). Split scanning into multiple phases: use the right tool for the right job.
It's as simple as this: at any serious type of scale, nmap is too slow for the task of determining whether a port is open or closed. Therefore, it's best to completely remove nmap from the formula when it comes to discovering open ports. Instead, we opt for purpose-built scanners like [masscan](https://github.com/robertdavidgraham/masscan) and [zmap](https://github.com/zmap/zmap). These tools are (literally) one thousand times faster than nmap when it comes to port discovery. By using these tools, we can then feed their results into nmap for service scanning. I ended up going with masscan.

---

### (2). If you scan a single network too fast, you're probably going to DoS your going to piss off a lot of people (even if they're your friends).
During my testing, I quickly discovered that it is quite easy to cripple an internal network by port-scanning with too many packets per second. Top-of-the-rack switches and some "on-prem solutions" simply don't have the power to handle the throughput that scanning will generate. With the appropriate equipment, zmap and masscan can scan at 14.88-million packets-per-second. Although your server may be able to handle that throughput, there is no absolutely no guarantee that the equipment connected to it can (whether that be the switch of your own server, or the switch of the network you're scanning). Rate-limiting for certain network blocks is going to be necessary (or, if possible, randomize scanning (although this does not guarantee that a network will not be overloaded, as there is a random chance that you can scan the same network at the same time)).

---

### (3). Mass-scanning (or zmapping) at scale isn't 100% reliable.
Intense scans can cause various problems somewhere or another: overloaded networks, CPUs, or other behavior that cannot necessarily be detected by the scanner. That means that ports which truly are open may be missed. While zmap and masscan both offer the option for "retries", this option does not take into account ports discovered open (i.e. they are retried whether they are detected as open or not). Even if the were able to only retry closed ports, only a few ports of 65535 are going to be open anyways; therefore, each retry is effectively going to add another full unit of scanning-time. A balance between reliability and speed is going to need to be considered, dependent on the network. This should be a configuration which can be set on a network-to-network basis.

---

### (4). Port discovery scanning does not have to be coupled with port service scanning.
The results from a scan for open ports does not need to be fed into the service scanning phase immediately. The tool I was creating was intended to do port *service* scanning once every 7 days. Instead of scanning for open ports every 7 days, I scan for open ports continuously: at a much slower rate, albeit more accurately. This scanning runs in the background for a week and scans the hosts multiple times throughout the week. At the weekly interval, the summation of the open ports found in the previous week are finally passed to nmap for service scanning.

---

### (5). nmap should be patched to not deliberately be slow when scanning hosts.
As it turns out, nmap's service scanning speed is deliberately extremely slow for accuracy purposes. By making some changes to the nmap code, we can get 16x speedup in service scanning. Read about it [on this blog post here](/nmap-speedup-service-scanning-16x).


