---
layout: post
title: "Network Security: Absurdity of Shared NICs with BMCs and Management Networks"
author: "Joshua Rogers"
categories: security
---

BMCs are [back in the news again](https://genius.com/31040477), with a vulnerability in Supermicros BMC being discovered that allows someone to install [unsigned (read: malicious) firmware that persists across normal update paths](https://thehackernews.com/2025/09/two-new-supermicro-bmc-bugs-allow.html). Since BMCs are—quite literally—backdoors on a server's motherboard that allow remote control, this is a real problem. BMCs are the technical component of what's commonly called a "remote management controller," and implementations span vendors: Dell iDRAC, HPE iLO, Supermicro BMC, Lenovo XClarity, and so on. They let administrators control systems when the OS isn't reachable (for example, networking is misconfigured or the OS is being reinstalled). These BMCs are fun for hacking, and a few years ago I learnt about the absurdity of how some of these are designed to use a shared NIC for both the host OS and the BMC.

BMCs are generally accessible through two means: via the IPMI protocol (normally port 623), or via some clunky web panel. Both of these means of access have historically been extremely simple to hack. [So it goes](https://www.goodreads.com/questions/251943-what-does-so-it-goes-mean-the-narrator). The IPMI protocol includes a null-cipher (Suite 0, or Cipher 0) which, if enabled, allows unauthenticated administrative access; in 2013 researchers found that most major vendors supported it, and shipped with it enabled by default, allowing anybody to get access to these systems (no authentication required for backdoor access to the server; awesome). So it goes... Each of the main server providers' web panels have also been found to be vulnerable to unauthenticated remote code execution, and simple exploits to go from unauthenticated to administrative access are available. So it goes..... Who would have guessed it was so easy to take over a server?:-). The other bad news is that it seems nobody ever updates these BMCs, and any server older than 4 or 5 years probably doesn't receive any updates either, so some type of exploit to gain access is kind of inevitable. Did you know the NSA uses servers which do not have BMCs installed at all?

In professional networks (™), BMCs are segregated from the internet (unless you're [NordVPN](https://www.techradar.com/news/whats-the-truth-about-the-nordvpn-breach-heres-what-we-now-know) and .. expose it to the internet), inside their own VLAN which does not allow outsiders to connect to them at all. Even if some type of "internal network" exists (super secure ™), a so-called "management network" is just another "internal network" made up of these BMCs, which are only accessible by connecting through some type of specific jumpbox, or with a highly-elevated privileged VPN or proxy or something -- basically, a management network is generally cut off from the rest of the world completely, and is only made up of BMCs and some other management-related systems (monitoring systems for power, for example). Although BMCs are generally authenticated, due to their highly privileged states (literally; a virtualized "in-person" experience allowing complete takeover of the host OS), they are not easily accessed.

The point is, a company might have an "internal network", and then above that, it'll also have a completely separate network called a "management network" which only sysadmins can access, containing these BMCs, probably some Fan & Power Controllers, and/or Remote Power Management Interfaces for Power Distribution Units.

Great, so we have this highly-sensitive piece of rubbish embedded into our server motherboard, which gives anybody with access root on the server. Since it's insecure by design and full of exploitable vulnerabilities (surprisingly, not by design), BMCs live in a management network that requires some hoops to get into, generally intended to only be accessible by a system administrator. So.. ~browser logic security~ server security assured? We can all get back to pouring soup? Not so fast.

Some (read: a lot) of these BMCs suffer from a fundamental architectural flaw: they share a physical NIC/port with the host, so frames for both endpoints are carried by a single device. As with any shared port, link negotiation and traffic handling can be influenced by either stack. Practically, the host OS can create an interface with an address on the management subnet and send traffic _through_ the shared port—it doesn't need to impersonate the BMC. This gives anyone on the normal server direct access to the highly restricted management network, and lets you hop between BMCs (or other devices on the management network) like it's a Super Mario game.

Here's a poorly ChatGPT-generated diagram of the situation:

| ![Shared NIC Motherboard Diagram](/files/BMC-Shared.png) |
|:--:|
| *Shared NIC Motherboard Diagram* |

In the above diagram, the server is using a shared NIC: the BMC and host egress the **same physical port** that's cabled to the management switch (the host may also have other NICs for production). Because the shared port is software-defined, the host OS can "hijack" the path by assigning any address on the BMC's management subnet (or a VLAN sub-interface if tagging is used), becoming part of the management network!

Why a VLAN sub-interface at all? In many deployments the management network is delivered as an IEEE 802.1Q–tagged VLAN on that shared port. The BMC attaches the VLAN tag itself, but the host will **not** tag frames unless you create a sub-interface (e.g., `eth0.100`). Without that tag, the packets go to the native/untagged VLAN (or get dropped) instead of the management VLAN.

So, how do we work out which address to use? Luckily IPMI helps: on the host OS we can query the BMC to learn its subnet and settings. (note: the LAN channel isn't always 1; but you can probe channels starting from 0 up to, like, 10, and then query the LAN settings.) For example:

```
$ ipmitool channel info 1
Channel 0x1 info:
 Channel Medium Type     : 802.3 LAN
 Channel Protocol Type   : IPMB-1.0
 Session Support         : multi-session
 Active Session Count    : 0
 Protocol Vendor ID      : 7154
 Volatile(active) Settings
  Alerting               : enabled
  Per-message Auth       : disabled
  User Level Auth        : enabled
  Access Mode            : always available
 Non-Volatile Settings
  Alerting               : enabled
  Per-message Auth       : disabled
  User Level Auth        : enabled
  Access Mode            : always available

$ ipmitool lan print 1

Set in Progress         : Set Complete
Auth Type Support       : NONE MD2 MD5 PASSWORD
Auth Type Enable        : Callback : MD5 PASSWORD
                          User     : MD5 PASSWORD
                          Operator : MD5 PASSWORD
                          Admin    : MD5 PASSWORD
                          OEM      :
IP Address Source       : Static Address
IP Address              : 192.168.10.42
Subnet Mask             : 255.255.255.0
MAC Address             : 00:25:90:ab:cd:ef
SNMP Community String   : public
BMC ARP Control         : ARP Responses Enabled, Gratuitous ARP Disabled
Gratuitous ARP Interval : 0.0 seconds
Default Gateway IP      : 192.168.10.1
Default Gateway MAC     : 00:11:22:33:44:55
Backup Gateway IP       : 0.0.0.0
Backup Gateway MAC      : 00:00:00:00:00:00
802.1q VLAN ID          : 100
802.1q VLAN Priority    : 0
RMCP+ Cipher Suites     : 0,1,2,3,6,7,8,12
Cipher Suite Priv Max   : aaaaaaaaaaaaaaa
```

And then we simply ... create an interface on our Linux system (the host OS) on that subnet. We can do this either for untagged, or tagged management VLANs:

```
# Untagged mgmt network on the shared port
$ ip addr add 192.168.10.42/24 dev eth69
$ ip link set eth69 up
```

or

```
# If the mgmt network is VLAN 100 on the shared port
$ ip link add link eth69 name eth69.100 type vlan id 100
$ ip addr add 192.168.10.42/24 dev eth69.100
$ ip link set eth69.100 up
```

We get the values to be used from the `802.1q VLAN ID`, `IP Address`, and `Subnet Mask` output of `ipmitool`.
If `802.1q VLAN ID : Disabled`, then the management network is untagged, so we just use the base interface. If it shows a number (e.g. `100`), the management network is tagged, so we create an interface tagged with that value so the host adds that tag on egress. Using `type vlan id 100` tells Linux to create a logical interface that inserts the 802.1Q tag (100) on every frame. Switches will only place those tagged frames into the management VLAN; untagged frames go to the native VLAN (or get dropped), so we won't actually reach the management network without it.

... and voila! the Linux server -- not "in the internal network" can now .. access the management network. All because of the shared NIC, which can effectively be hijacked (by design). Your Linux host's network interface is going to take preference over the BMC, most likely, in the shared NIC paradigm.

... and voilà! The Linux server -- although on the "internal" network -- can now reach the management network, simply because the shared NIC can be leveraged by the host stack.

So, from a linux host, we've now gained access to the management network by simply creating a network interface with the same address and mask as the BMC when it's connected to the management network via a shared NIC. What can we do with this new-found access to the management network? Well, it depends what's "on the network", of course. However, let's assume the management network is made up of other BMCs which have never been updated (because "it's on the management network; why would it need updating", rofl), we can:

- Take over the BMCs of other servers using the latest exploit, granting us shell access on the host OS of each of the servers,
- Take over the BMCs and monitor the traffic to the BMCs, collecting the usernames and passwords used to authenticate over IPMI or the web panel (LDAP, anybody?),
- Install (in the case of the SuperMicro exploit) a backdoored BMC firmware which cannot be removed,
- Restrict access to the BMCs' upgrade mechanism, ensuring that the old exploit works forever.


The real issue with the SuperMicro exploit outlined in the first paragraph of this post is that if somebody installs a malicious BMC firmware that cannot be removed, ownership can never be revoked. Imagine, for example:

1. Rent a server from a hosting company,
2. Install a malicious BMC firmware that cannot be removed,
3. Stop renting the server from the company,
4. Wait for the hosting company to rent the same server to another customer,
5. ????
6. Profit! (your malicious BMC firmware, which has some type of backdoor, now gives you access to another random customer's server.)

Since hosting companies cannot truly assure that a firmware is legitimate (it can simply respond with whatever it wants, including a fake checksum), the only real option is to .. solder off the BMC chip, re-flash it, and solder it back onto the motherboard. Not going to happen:-).

So, management networks? Well they're just another form of an internal network; but with critical systems running inside them that can be easily abused to take over servers. My negative opinions of "internal networks" are well-known and quite simple: an internal network gives the illusion of security, and afford users the subconscious psychological authorization to simply cram any insecure junk in the network without proper security controls or consideration due to the feeling of "only _we_ can access it". There are more than enough ways to gain access to an internal network; not all of them technological. It's not that I don't believe in the rule of least privilege; I do, even for networking, however a simple "segmented" network in which everything simply lives together is not a secure solution; it's simply lazy.

Generally speaking, it seems that the only way to win this management network game is not to play at all. The second best way, however, is to restrict both incoming _and_ outgoing traffic from the management network, and segment each BMC from one-another. It's obvious that if the internet can access your management network, it's really bad -- but it's also really bad if your management network can access the internet. Blocking access _to_ the internet from the management network doesn't fully solve the problem (a BMC can simply connect to the internet through a compromised host OS), but it certainly makes it significantly more difficult for an attacker to exfiltrate or gain access remotely. Segmenting management device traffic from one-another also assures that when one of your BMCs gets hacked (such as through the shared NIC method outlined in this post), your whole management network isn't sitting wide open. Obviously, you should be using a physically separate BMC NIC, with the BMC NIC cabled only to the management network switch; a shared NIC is simply unacceptable, from a security point of view.
