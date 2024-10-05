---
layout: post
title: "A Full Guide: FreeBSD 13.3 on a MacBook Pro 11.4 (Mid 2015) (A1398)"
author: "Joshua Rogers"
categories: journal
---

---

Recently having been gifted an older Apple MacBook Pro 11.4 Retina (Mid 2015) (A1398), this post seeks to document my experience of installing, configuring, and fixing bugs in FreeBSD 13.3.

**Note**: Not all of the patches and changes I detail in this post have landed in upstream yet (especially the `freebsd-src` and `asmctl` patches), and some may never even land in FreeBSD 13.3 (AKA `releng/13.3`). Therefore, you may have to build some things yourself, or use a newer version.

# Why FreeBSD?

---

Why not?

I'm a big fan of FreeBSD in general and made the jump from Ubuntu around 10 years ago. I've found that FreeBSD has a more-sane [filesystem hierarchy](https://man.freebsd.org/cgi/man.cgi?query=hier) than most Linux-based operating systems, especially in terms of local programs and user-installed utilities, is easier to manage over time, is more lightweight and simple, and in general, is easier to tinker as necessary. Most importantly, however, it also makes things harder to skip steps when you need to make changes to the system -- there are fewer training wheels like Linux-based operating systems have, and RTFM is normally the best option; so when you do things, you really need to understand what you're doing. Note: I don't think FreeBSD is inherently any more or less safe than Linux: I think more hackers' eyes are on the Linux kernel than FreeBSD, so fewer exploits are found in FreeBSD. FreeBSD jails are cool. I also think FreeBSD is just fun to play with, and I believe in _technodiversity_, and a Linux monoculture benefits few.

A git repository of all the configurations outlined in this post can be found [here on Github](https://github.com/MegaManSec/dotfiles/).

# Macbook Pro 11.4 A1398 Hardware

---

This version of the Macbook Pro comes with the following hardware:

| Component   | Specification                                  |
|-------------|------------------------------------------------|
| CPU         | Core i7-4870HQ CPU @ 2.50GHz                   |
| GPU         | Integrated Iris Pro Graphics 5200 / 1.5GB      |
| Disk        | SSD SM0256G 256GB                              |
| Memory      | 8GB SODIMM DDR3 1600MT/s                       |
| WiFi / BT   | BCM43602 802.11ac Wireless LAN SoC, Bluetooth 4.0 |
| Webcam      | 720p FaceTime HD Camera                        |
| Sound       | Cirrus Logic CS4208                            |

There are some other components, such as an SD card reader, as well as 2 USB3.0, 1 HDMI, and 2 Thunderbolt 2 ports. More on those later.

The only component that I do not have working yet is the webcam. More on this later.

# Installation

---

## FreeBSD Base OS Installation

---

I used the [FreeBSD 13.3 memstick installer](https://www.freebsd.org/where/). Use the amd64 version. When turning on the Macbook, hold and press the Alt (left) button. Choose the FreeBSD Boot Installer, and begin the installation.

This post doesn't go much into the initial installation process of FreeBSD. It's up to you what you want to do there.

On my system, I continued with the `us.macbook.kbd` keymap. I installed src, ports, and kernel-dbg. I used Auto (ZFS) and GPT (BIOS+UEFI), with GELI full-disk encryption and so-on.

**Note**: The inbuilt WiFi chip is not natively supported by FreeBSD, so you will need to (temporarily) use a USB WiFi or Ethernet dongle, or (as I will explain) copy some files from a different system to the Macbook. You could also just transplant a different chip into the system.

**Note**: If for some reason you're going to be installing FreeBSD on an external drive, ZFS does not seem to work as no EFI partition is created. UFS. This probably isn't important for anybody else, but while re-testing these installation notes on an external drive, I couldn't use ZFS.

Continue setting up the system as normal: install a text editor, set up [doas(1)](https://www.freshports.org/security/doas) or [sudo(1)](https://www.freshports.org/security/sudo) if you want, and install `bash` or `zsh` if that's your thing. You can add a non-root user to the `wheel` group by running, as root: `pw groupmod wheel -m user`. `/usr/local/etc/doas.conf` should contain something like: `permit :wheel`.

I personally installed `sudo` instead, added the user to the wheel group, and allowed passwordless usage:

```bash
$ pkg install sudo
$ pw groupmod wheel -m user
```

and then added `%wheel ALL=(ALL:ALL) NOPASSWD: ALL` to `/usr/local/etc/sudoers`.

Note that nearly all of the commands outlined in this guide should be run as root or with `doas`/`sudo`. Copying and pasting without knowing what you're doing may result in system failure.

Finally, for whatever reason, my `/tmp` directory was messed up on install, and I had to run:

```bash
$ chmod 1777 /tmp
```

## Wi-Fi

---

This Macbook uses a Broadcom [BCM43602](https://www.broadcom.com/products/wireless/wireless-lan-infrastructure/bcm4360) chip for WiFi. Although the chip is supported on Linux, it will never be officially supported by FreeBSD due to licensing and technical reasons (a proprietary, closed-source driver is necessary). But, it is still possible to use it on a FreeBSD system.

[Wifibox(8)](https://www.freshports.org/net/wifibox/) is an extremely helpful project that spins up a very-low-resource Alpine Linux VM using FreeBSD's [bhyve (BSD hypervisor)](https://wiki.freebsd.org/bhyve), and passes through the system's wireless card from the FreeBSD machine into the guest, essentially using the Linux VM as a wifi driver. That's how we'll be using wifi on this system.

After fixing [some bugs](https://github.com/pgj/freebsd-wifibox-port/pull/36) and a quick [debugging session](https://github.com/pgj/freebsd-wifibox/issues/65#issuecomment-2175678374) with the `wifibox` developer, and then fixing some more bugs (more on this later), we got `wifibox` working with this Macbook.

If you don't have a USB WiFi or Ethernet dongle, then we can install `wifibox` a different way. To do so, we first need _some_ type of internet connection on a different system. We can either:

1. Download the `wifibox` pre-compiled package from the FreeBSD pkg repository and copy them to the laptop, or
2. Download the `wifibox` source code and some pre-compiled packages from the FreeBSD pkg repository, copy them to the laptop, install the pre-compiled packages, then compile and install `wifibox` manually.

**Alternatively**: If you install FreeBSD with the DVD installer, the `wifibox` package should already be available on the system without the necessity of downloading anything (but this is untested by me).

**Note**: If you do have an alternative method of using internet on the Macbook temporarily (like with a dongle), just do that and install `wifibox` from the ports tree and save yourself a lot of messing around.

### Using packages from the FreeBSD pkg repository

---

On a _different_ FreeBSD system that _is_ connected to the internet, you can run the following command which will retrieve the pre-compiled pkg files for `wifibox`:

```bash
$ pkg fetch -o /tmp/ --dependencies wifibox 
Updating FreeBSD repository catalogue...
FreeBSD repository is up to date.
All repositories are up to date.
The following packages will be fetched:

New packages to be FETCHED:
	grub2-bhyve: 0.40_11 (472 KiB: 0.38% of the 122 MiB to download)
	socat: 1.8.0.1 (202 KiB: 0.16% of the 122 MiB to download)
	wifibox: 1.4.2 (1 KiB: 0.00% of the 122 MiB to download)
	wifibox-alpine: 20240506 (122 MiB: 99.45% of the 122 MiB to download)
	wifibox-core: 0.13.0 (14 KiB: 0.01% of the 122 MiB to download)

Number of packages to be fetched: 5

The process will require 122 MiB more space.
122 MiB to be downloaded.

Proceed with fetching packages? [y/N]: y
```

The `pkg` files will then be sitting in `/tmp/All/`. From here, you need to copy them to Macbook somehow -- like, with a USB.

On the Macbook, you can then install the packages using:

```bash
$ pkg add grub2-bhyve-0.40_11.pkg
$ pkg add socat-1.8.0.1.pkg
$ pkg add wifibox-1.4.2.pkg
$ pkg add wifibox-alpine-20240506.pkg
$ pkg add wifibox-core-0.13.0.pkg
```

If you do not have access to another FreeBSD machine, you can download these files manually from here -- **Note**: they may be outdated by the time you're reading this.

- [grub2-bhyve-0.40_11.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/grub2-bhyve-0.40_11.pkg)
- [socat-1.8.0.1.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/socat-1.8.0.1.pkg)
- [wifibox-1.4.2.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/wifibox-1.4.2.pkg)
- [wifibox-alpine-20240506.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/wifibox-alpine-20240506.pkg)
- [wifibox-core-0.13.0.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/wifibox-core-0.13.0.pkg)

The only problem with this method is that the default _RECOVERY_ option for `wifibox` is `RECOVER_RESTART_VMM`. This means that on suspend, no action is taken; and on resume, the guest is stopped, `vmm(4)` is unloaded and loaded, and then the guest is started again. On this Macbook, this is not possible, as `vmm` causes a full system hang upon resume if it is still loaded upon suspend. I have a patch for this (details below), but it has not yet landed in the FreeBSD source as of writing this.

#### Building from ports

---

When you finally get internet working here, my recommendation is to install `wifibox-core` and `wifibox-alpine` from the ports tree, and replace the pre-compiled package:

```bash
$ cd /usr/ports/net/wifibox-core/
$ make config
```

We need to enable the option `RECOVER_SUSPEND_VMM`. Next we install it, and remove the pre-compiled package:

```bash
$ make
$ pkg remove wifibox-core
$ make reinstall
```

Then configure `wifibox-alpine`:

```bash
$ cd /usr/ports/net/wifibox-alpine/
$ make config
```

I left the following options enabled:

```bash
FW_BRCM
COMP_XZ
APP_WPA_SUPPLICANT
KERN_LTS
```

Now build and install:

```bash
$ make
$ pkg remove wifibox-alpine
$ make reinstall
```

### Building with source code

---

This method is quite convoluted.

First, we need to install the FreeBSD packages `grub2-bhyve`, `socat`, `gtar`, `patchelf`, and `squashfs-tools-ng` on the Macbook.
Since we have no internet, we need to copy those files from somewhere else using a USB. The packages can either be downloaded using the `pkg` tool on another system already running FreeBSD (with internet):

```bash
$ pkg fetch -o /tmp/ gtar patchelf squashfs-tools-ng grub2-bhyve socat
Updating FreeBSD repository catalogue...
FreeBSD repository is up to date.
All repositories are up to date.
The following packages will be fetched:

New packages to be FETCHED:
	grub2-bhyve: 0.40_11 (472 KiB: 27.19% of the 2 MiB to download)
	gtar: 1.35_1 (714 KiB: 41.19% of the 2 MiB to download)
	patchelf: 0.14.3_1 (76 KiB: 4.36% of the 2 MiB to download)
	socat: 1.8.0.1 (202 KiB: 11.64% of the 2 MiB to download)
	squashfs-tools-ng: 1.3.1 (271 KiB: 15.62% of the 2 MiB to download)

Number of packages to be fetched: 5

The process will require 2 MiB more space.
2 MiB to be downloaded.

Proceed with fetching packages? [y/N]: y
```

The files will be sitting in `/tmp/All/`.

Or manually:

- [gtar-1.35_1.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/gtar-1.35_1.pkg)
- [patchelf-0.14.3_1.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/patchelf-0.14.3_1.pkg)
- [squashfs-tools-ng-1.3.1.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/squashfs-tools-ng-1.3.1.pkg)
- [socat-1.8.0.1.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/socat-1.8.0.1.pkg)
- [grub2-bhyve-0.40_11.pkg](http://pkg.freebsd.org/FreeBSD:13:amd64/latest/All/grub2-bhyve-0.40_11.pkg)

Next, we need to download the packages that build the Alpine Linux VM. If you're using a different FreeBSD machine to do this, you can just clone [https://github.com/pgj/freebsd-wifibox-port.git](https://github.com/pgj/freebsd-wifibox-port.git), run `make -C freebsd-wifibox-port/net/wifibox-alpine`, and then find the packages in `/usr/ports/distfiles/wifibox-alpine/`. If you're not using FreeBSD yet, you need to download the files manually. This is super annoying, so I'm just going to link each of the packages for the time being:

- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/alpine-minirootfs-3.20.3-x86_64.tar.gz](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/alpine-minirootfs-3.20.3-x86_64.tar.gz)
- [https://git.kernel.org/pub/scm/linux/kernel/git/firmware//linux-firmware.git/snapshot/linux-firmware-20240909.tar.gz](https://git.kernel.org/pub/scm/linux/kernel/git/firmware//linux-firmware.git/snapshot/linux-firmware-20240909.tar.gz)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/baselayout-3.6.5-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/baselayout-3.6.5-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/busybox-1.36.1-r4.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/busybox-1.36.1-r4.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/ifupdown-ng-0.12.1-r3.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/ifupdown-ng-0.12.1-r3.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/iptables-1.8.10-r1.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/iptables-1.8.10-r1.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/iw-6.9-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/iw-6.9-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libcap2-2.70-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libcap2-2.70-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libcrypto3-3.3.2-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libcrypto3-3.3.2-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libmnl-1.0.5-r2.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libmnl-1.0.5-r2.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libnftnl-1.2.6-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libnftnl-1.2.6-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libnl3-3.9.0-r1.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libnl3-3.9.0-r1.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libssl3-3.3.2-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/libssl3-3.3.2-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/musl-1.2.5-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/musl-1.2.5-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/openrc-0.54-r1.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/openrc-0.54-r1.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/pcsc-lite-libs-2.2.3-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/upstream/pcsc-lite-libs-2.2.3-r0.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/wpa_supplicant-2.10-r9.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/wpa_supplicant-2.10-r9.apk)
- [https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/linux-lts-6.6.50-r0.apk](https://github.com/pgj/freebsd-wifibox-alpine/releases/download/packages/linux-lts-6.6.50-r0.apk)
- [https://codeload.github.com/pgj/freebsd-wifibox-alpine/tar.gz/2b0702c10d5f81064525ca7cc679ccdb66a3cc6a?dummy=/pgj-freebsd-wifibox-alpine-2b0702c10d5f81064525ca7cc679ccdb66a3cc6a_GH0.tar.gz](https://codeload.github.com/pgj/freebsd-wifibox-alpine/tar.gz/2b0702c10d5f81064525ca7cc679ccdb66a3cc6a?dummy=/pgj-freebsd-wifibox-alpine-2b0702c10d5f81064525ca7cc679ccdb66a3cc6a_GH0.tar.gz)


We then need to download the appropriate `freebsd-wifibox` script and code. We find the file to download easily:

```bash
$ grep GH_TAGNAME freebsd-wifibox-port/net/wifibox-core/Makefile | awk '{print "https://codeload.github.com/pgj/freebsd-wifibox/tar.gz/"$NF}'
https://codeload.github.com/pgj/freebsd-wifibox/tar.gz/4abcf0936fdd5a04fcd7fd53811ebb5aab7b70a9
```

Or linked (at the moment):

[https://codeload.github.com/pgj/freebsd-wifibox/tar.gz/4abcf0936fdd5a04fcd7fd53811ebb5aab7b70a9](https://codeload.github.com/pgj/freebsd-wifibox/tar.gz/4abcf0936fdd5a04fcd7fd53811ebb5aab7b70a9).

Now that we have everything downloaded, we copy the `freebsd-wifibox-port` repository, the `grub2-bhyve`, `socat`, `gtar`, `patchelf`, and `squashfs-tools-ng` packages, and all of the other files downloaded onto a USB (or otherwise).

Now, on the Macbook running FreeBSD we:

```bash
$ mkdir /usr/ports/distfiles/wifibox-alpine/
```

We move all of the downloaded packages to that directory, with the exception of the final one: `pgj-freebsd-wifibox-0.14.0-4abcf0936fdd5a04fcd7fd53811ebb5aab7b70a9_GH0.tar.gz` in my case. That final file should be placed in `/usr/ports/distfiles/`. Make sure the files are `chown root:wheel` and `chmod 644`.

We also copy the `freebsd-wifibox-port` repository to the Macbook.

We then install the `grub2-bhyve`, `socat`, `gtar`, `patchelf`, and `squashfs-tools-ng` packages:

```bash
$ pkg add gtar-1.35_1.pkg
$ pkg add patchelf-0.14.3_1.pkg
$ pkg add squashfs-tools-ng-1.3.1.pkg
$ pkg add grub2-bhyve-0.40_11.pkg
$ pkg add socat-1.8.0.1.pkg
```

Now it's time to prepare the building of wifibox:

```bash
$ cd freebsd-wifibox-port
$ make -C net/wifibox-core config
```

We need to enable the option `RECOVER_SUSPEND_VMM`, as suspending while `wifibox` is running (and thus the `vmm(4)` module) will result in a system freeze. This ensures that the suspend/resume function works on this Macbook, by stopping `wifibox` and unloading `vmm` upon a suspension, and then starting `wifibox` again on resume.

Next, we set the options for the Alpine Linux VM which will be running.

```bash
$ make -C net/wifibox-alpine config
```

I left the following options enabled:

```bash
FW_BRCM
COMP_XZ
APP_WPA_SUPPLICANT
KERN_LTS
```

Now we can build:

```bash
$ kldload linux64
$ mkdir -p /compat/linux
$ make -C net/wifibox-alpine install
$ make -C net/wifibox-core install
$ make -C net/wifibox install
```

`wifibox` should now be installed.

Once you finally have internet installed on the Macbook, you should use the official port for build these two packages in the future (i.e. perform the previous steps but use `/usr/ports/net/wifibox-core/` and `/usr/ports/net/wifibox-alpine/`). Instructions [previously made clear here](#building-from-ports).

---

Now we need to configure the `wifibox` service.

We need to find the PCI socket that the wifi chip is located in. On my system, it's `pci:0:3:0:0`:

```bash
$ pciconf -lv |grep -B3 network
none@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
```

The configuration for the passthrough (along with some other options) is found in `/usr/local/etc/wifibox/bhyve.conf.sample`, and can be copied to `/usr/local/etc/wifibox/bhyve.conf`. We need to (at least) set the `passthru` value. In this case, I set mine to

```bash
passthru=3/0/0
```

to correspond to the PCI socket identified before (note `pci0:3:0:0` becomes `3/0/0` in the configuration).

---

The `wpa_supplicant.conf` file containing the wifi details for the guest (Linux) VM is accesible from the (FreeBSD) host in `/usr/local/etc/wifibox/wpa_supplicant/wpa_supplicant.conf`. We can create a hardlink (a symlink will not work) from `/etc/wpa_supplicant.conf` on the host to that file, making it accessible from the VM:

```bash
$ ln /etc/wpa_supplicant.conf /usr/local/etc/wifibox/wpa_supplicant/wpa_supplicant.conf
```

From the host, we can then edit `/etc/wpa_supplicant.conf` manually, or append to the file with something like this:

```bash
$ wpa_passphrase ssid passphrase
network={
	ssid="ssid"
	#psk="passphrase"
	psk=2b1d17284c5410ee5eaae7151290e9744af2182b0eb8af20dd4ebb415928f726
}
```

---

Now we test whether it all works. Starting the `wifibox` service, we then request a session from the guest VM's DHCP server using `dhclient`:

```bash
$ service wifibox onestart
Starting wifibox.......OK
$ dhclient wifibox0
DHCPREQUEST on wifibox0 to 255.255.255.255 port 67
DHCPREQUEST on wifibox0 to 255.255.255.255 port 67
DHCPACK from 10.0.0.1
bound to 10.0.0.2 -- renewal in 432000 seconds.
$ ping 1.1.1.1
PING 1.1.1.1 (1.1.1.1): 56 data bytes
64 bytes from 1.1.1.1: icmp_seq=0 ttl=51 time=11.510 ms
```

Once you're connected, you can view all of the DHCP information in `/var/db/dhclient.leases.wifibox0`. For example:

```bash
$ cat /var/db/dhclient.leases.wifibox0
lease {
  interface "wifibox0";
  fixed-address 10.0.0.2;
  option subnet-mask 255.255.255.0;
  option routers 10.0.0.1;
  option domain-name-servers 192.168.30.1,8.8.8.8,8.8.4.4;
  option dhcp-lease-time 864000;
  option dhcp-message-type 5;
  option dhcp-server-identifier 10.0.0.1;
  renew 5 2024/9/20 06:06:29;
  rebind 2 2024/9/24 00:06:29;
  expire 3 2024/9/25 06:06:29;
}                                     
```

The guest VM acquires a lease from the connected-to wifi network, and then leases the FreeBSD host 10.0.0.1. If you want the lease to use a different address, or port-foward _to_ the FreeBSD host, have a read [of this blog](https://xyinn.org/md/freebsd/wifibox) for some more information about that. Although the network topology is really basic, the tl;dr is that..

```
**NOTE**: If you have something running on those addresses (like I have wireguard on **10.0.0.1**), you'll 
want to adjust the relevant files in the wifibox directory.

In my case, I just shifted wifibox to use **10.1.0.0/24** addresses and everything worked. I was still able 
to communicate with all LAN services on both **192.168.1.0/24** and **10.0.0.0/24** with no issues.

I edited the following files to achieve this in the **wifibox/appliance** directory: **interfaces.conf**, 
**udhcpd.conf**, and **uds_passthru.conf**.

Also note that devices on your LAN attempting to communicate to a particular port on this machine won't be 
able to communicate due to the double NAT and firewalling going on. You'll need to adjust the VM firewall 
appropriately.
```

---

We can enable `wifibox` on startup by adding the following to `/etc/rc.conf`:

```bash
wifibox_enable="YES"
ifconfig_wifibox0="SYNCDHCP powersave"
background_dhclient_wifibox0="YES"
defaultroute_delay="0"
```

`background_dhclient_wifibox0` and `defaultroute_delay="0"` ensure that the `dhclient` doesn't delay the bootup process.

---

`/usr/local/etc/wifibox/core.conf` includes an option related to logging. The logfile for the `wifibox` service is found in `/var/log/wifibox.log`, and some log files from the guest VM are exposed in `/var/run/wifibox/appliance/log/`.

---

As the host, we can also access a shell on the guest system if we want. If we had set `console=yes` in the aforementioned `bhyve.conf`, we could call `service wifibox console` and be greeted with a console. The root username is `root`, and there is no password. Exit by typing `~.` (it may require pressing enter and typing it again).

While using the guest console, I discovered some bugs in FreeBSD and in `wifibox`. Communication is performed via [nmdm(4)](https://man.freebsd.org/cgi/man.cgi?query=nmdm), which "_provides two tty(4) devices connected by a virtual null modem cable._" These devices can be created by any `stat()` to `/dev/nmdm..[AB]`. The problems were:

1. When `wifibox` shuts down, it checks the existence of the `nmdm` modems `/dev/nmdm-wifibox.1A/B` and deletes the files if found. However, the devices will likely already be shutdown when this happens, and checking for their existence simply re-creates them again (since checking for their existence calls `stat()`). Likewise, deleting the files does not shutdown the device, so without a file corresponding to the device, it becomes impossible to shutdown the device. Reported in [wifibox#104](https://github.com/pgj/freebsd-wifibox/issues/104).
2. The `nmdm(4)` module itself has no way to unload the module if a device has been created (but is not in use). Patch submitted in [freebsd-src#1367](https://github.com/freebsd/freebsd-src/pull/1367) to allow the force shutting down of the module.

---

While testing `wifibox` on my system, I also tested it with suspend/resume. Suspend worked fine, but resume would not work: the system would simply hang and not be brought back up.
After a few tiresome days of debugging, I eventually worked out that the issue related to the chip having an invalid internal state, which froze the system. Information about that issue [is detailed in my post here](https://joshua.hu/brcmfmac-bcm43602-suspension-shutdown-hanging-freeze-linux-freebsd-wifi-bug-pci-passthru), but the gist of it is that: if the chip is initialized once and then not correctly uninitialized, a re-initalization upon resuming will cause the system to lock up.
Likewise, the VM, even when being shut down before the host suspends, would not uninitalize the chip. I submitted a couple patches and reports for this:

1. A Linux kernel patch to uninitalize the chip when shutting down [here](https://lore.kernel.org/linux-wireless/CA+17n5vH_Y6Qr72DH=QgFUSO5CGn-grvcgY-i3+LPqkRzCjEzw@mail.gmail.com/).
2. A `wifibox` issue to forcefully and automatically "remove" (thus uninitalize) the chip from inside the VM when shutting down [here](https://github.com/pgj/freebsd-wifibox-alpine/pull/29).
3. A `wifibox` patch to correctly shut down the VM when the `wifibox` service is stopped [here](https://github.com/pgj/freebsd-wifibox/pull/110).

On that last one: as it turned out, `wifibox` had a bug from its inception, where when the service was stopped, a `kill -TERM` would kill the daemon script, but not actually forward the TERM signal to `bhyve` (the VM). By killing the PGID (process group) instead of PID, we can kill everything at the same time.

---

I also proposed a patch to FreeBSD, specifically in relation to the `vmm` module, and the whole Intel VMX system. The VMX code has/had functionality for resuming the module:

```c
 static void
 vmx_modresume(void)
 {
       if (vmxon_enabled[curcpu])
               vmxon(&vmxon_region[curcpu * PAGE_SIZE]);
 }
```

This code runs on every resume. The problem is, there is no code for _suspension_. This means that the `VMXON` instruction will be called on memory that was already VMXON. When the VMXON instruction is run on the same area of memory for which it is already _ON_, the result is undefined: a crash, hang, or nothing at all. In my case, a full system hang on resume. Likewise, MSR lock is lost upon suspension, so a proper re-initalization of the memory is necessary. So, my solution was twofold: One, I had to add hooks for suspension in the VMX code. Then, in the `vmm` code, suspension will execute:

```c
vmx_modsuspend(void)
{
        if(vmxon_enabled[curcpu])
                vmx_disable(NULL);
}
```

And two, I made the resume code call `vmx_enable(NULL);` to ensure the lock is re-aquired -- that function then calls `vmxon()`, too.

With this change, all seems to be well with the world. The system no longer hangs on suspend/resume when the `vmm` module is still loaded. At least for my wifi chip, however, it does require unloading and then reloading the `vmm` module upon resume (which means the `wifibox` VM needs to be destroyed). But at least it doesn't lock up the laptop! Patch in [freebsd-src#1419](https://github.com/freebsd/freebsd-src/pull/1419).

---

Finally: in order to make sure suspend/resume actually works, we need to do a little bit more work, depending on the OS version.

On resume, the `rc.d` script installed by `wifibox` is automatically called, and the VM will be started (and `vmm` will be loaded). This is handled in `/usr/local/etc/rc.d/wifibox`. However, FreeBSD-13 does not handle _suspension_ in the same manner.

Therefore, we need to configure a `devd` rule to pick up the ACPI _suspend_ event, and suspend the `wifibox` VM before the whole system suspends. We can do that by creating `/usr/local/etc/devd/wifibox.conf` with the following:

```bash
notify 11 {
	match "system"		"ACPI";
        match "subsystem"	"Suspend";
        action "service wifibox suspend";
	action "/etc/rc.suspend acpi $notify";
}
```

I submitted a patch to `wifibox` for this. Previously, the suspension action of `wifibox` would not be completed before the system actually suspended, meaning upon resume, `wifibox` would be both suspending and resuming at the same time, and `vmm` would not be unloaded before suspension. Patches in [freebsd-wifibox#119](https://github.com/pgj/freebsd-wifibox/pull/119]).

From FreeBSD-14.0, the `devd` rule shouldn't be necessary. In commit [2cf8ef5910fd3754f8021f9c67fde6b9d9030f33](https://github.com/freebsd/freebsd-src/commit/2cf8ef5910fd3754f8021f9c67fde6b9d9030f33), functionality was added to automatically call all `suspend` functions provided in `rc.d` scripts.


## Graphics

---

### Xorg

---

We'll be using Xorg. We need to install Xorg, xf86-video-intel, and the meta-package [drm-kmod](https://www.freshports.org/graphics/drm-kmod/):

```bash
$ pkg install xorg drm-kmod xf86-video-intel
```

---

**Note**: The older `xf86-video-intel` package is used because the GPU on this Macbook is fairly outdated, and significant screen tearing occurs with kernel modesetting ([DRM](https://wiki.ubuntu.com/X/Glossary#What_is_.22DRI.22.3F__What_is_.22DRM.22.3F_.22DDX.22.3F)). **If and only if** you want to try your luck _without_ the `xf86-video-intel` package and instead use [DDX](https://wiki.ubuntu.com/X/Glossary#What_is_.22DRI.22.3F__What_is_.22DRM.22.3F_.22DDX.22.3F), you need to manually load the kernel module and/or set it to be loaded automatically:

```bash
$ kldload /boot/modules/i915kms.ko
$ sysrc kld_list+="/boot/modules/i915kms.ko"
```

YMMV: I've only added this in case you would like to see what screen tearing looks like:).

---

We need to add any user that will be using Xorg to the `video` group:

```bash
$ pw groupmod video -m user
```

And finally, we need to set `sysctl kern.evdev.rcpt_mask=3`. This will be important for when we set up the trackpad later. We also make this persistent:

```bash
$ echo 'kern.evdev.rcpt_mask=3' >> /etc/sysctl.conf
```

The installation message of `xorg` explains what's going on here:

```
$ pkg info -xD xorg-server
[..]
If your kernel is compiled with the EVDEV_SUPPORT option enabled (default starting from FreeBSD 12.1) it is 
recommended to enable evdev mode in pointer device drivers like ums(4) and psm(4).

This will give improvements like better tilt wheel support for mice and centralized gesture support via 
xf86-input-synaptics or libinput drivers for touchpads. [..] In case you're using a serial mouse or any 
other mouse that *only* works over sysmouse(4) and moused(8) on an evdev enabled kernel, please run this:

sysctl kern.evdev.rcpt_mask=3

To make it persistent across reboots, add to this /etc/sysctl.conf:

kern.evdev.rcpt_mask=3
```


### i3

---

I use the `i3` window manager. One day I'll use `sway`, but for the time being: `pkg install i3 i3lock i3status dmenu i3bar xautolock`.

#### .xinitrc

---

We then need to create a `.xinitrc` file in the user's home directory, which will be called when we start X. It's a basic shell script which loads some X resources, a modmap, starts a `urxvt` daemon (more on this later), sets xrandr to output at 2880x1800px, and then start `i3`:

```bash
#!/bin/sh
rm $HOME/.serverauth.*

userresources=$HOME/.Xresources
usermodmap=$HOME/.Xmodmap

if [ -f "$userresources" ]; then
    xrdb -merge "$userresources"
fi

if [ -f "$usermodmap" ]; then
    xmodmap "$usermodmap"
fi

urxvtd -q -f -o
xrandr --output eDP-1 --mode 2880x1800

xautolock -detectsleep -time 10 -secure -locker "sh -c 'i3lock -f ; sudo acpiconf -s 3'" &

exec i3
```

the `xautolock` line locks the screen and makes the system suspend, following 10 minutes of inactivity -- **note** the `sudo` in there and change it as necessary (`acpiconf` requires root permission).

It also deletes any serverauth files which haven't been cleaned up on a system shutdown.

#### .Xresources

---

Then, we create `.Xresources`:

```bash
Xft.dpi: 221
Xcursor.size: 21
```

These two settings ensure that the screen and cursor are sized appropriately for the screen size.

#### .Xmodmap

---

Then we need to create `.Xmodmap`. This file is used to map key button presses to symbols. These values can be retrieved using `xev(1)`.

The formatting for each `keycode` is as follows:

> The first keysym is used when no modifier key is pressed in conjunction with this key, the second with Shift, the third when the Mode_switch key is used with this key and the fourth when both the Mode_switch and Shift keys are used.

I made the following changes:

```
< keycode  67 = F1 F1 F1 F1 F1 F1 XF86Switch_VT_1
< keycode  68 = F2 F2 F2 F2 F2 F2 XF86Switch_VT_2
< keycode  69 = F3 F3 F3 F3 F3 F3 XF86Switch_VT_3
< keycode  70 = F4 F4 F4 F4 F4 F4 XF86Switch_VT_4
< keycode  71 = F5 F5 F5 F5 F5 F5 XF86Switch_VT_5
< keycode  72 = F6 F6 F6 F6 F6 F6 XF86Switch_VT_6
< keycode  73 = F7 F7 F7 F7 F7 F7 XF86Switch_VT_7
< keycode  74 = F8 F8 F8 F8 F8 F8 XF86Switch_VT_8
< keycode  75 = F9 F9 F9 F9 F9 F9 XF86Switch_VT_9
< keycode  76 = F10 F10 F10 F10 F10 F10 XF86Switch_VT_10
---
> keycode  67 = XF86MonBrightnessDown NoSymbol XF86Switch_VT_1
> keycode  68 = XF86MonBrightnessUp NoSymbol XF86Switch_VT_2
> keycode  69 = NoSymbol NoSymbol XF86Switch_VT_3
> keycode  70 = NoSymbol NoSymbol XF86Switch_VT_4
> keycode  71 = XF86KbdBrightnessDown NoSymbol XF86Switch_VT_5
> keycode  72 = XF86KbdBrightnessUp NoSymbol XF86Switch_VT_6
> keycode  73 = XF86AudioPrev NoSymbol XF86Switch_VT_7
> keycode  74 = XF86AudioPlay NoSymbol XF86Switch_VT_8
> keycode  75 = XF86AudioNext NoSymbol XF86Switch_VT_9
> keycode  76 = XF86AudioMute NoSymbol XF86Switch_VT_10


< keycode  94 = less greater less greater bar brokenbar bar
< keycode  95 = F11 F11 F11 F11 F11 F11 XF86Switch_VT_11
< keycode  96 = F12 F12 F12 F12 F12 F12 XF86Switch_VT_12
---
> keycode  94 = grave asciitilde grave asciitilde
> keycode  95 = XF86AudioLowerVolume NoSymbol XF86Switch_VT_11
> keycode  96 = XF86AudioRaiseVolume NoSymbol XF86Switch_VT_12


< keycode 133 = Super_L NoSymbol Super_L
< keycode 134 = Super_R NoSymbol Super_R
---
> keycode 133 = Mode_switch
> keycode 134 = Mode_switch
```

The first part ensures that each of the F1-F10 buttons works correctly.
A normal F1 click will correspond to `XF86MonBrightnessDown`, while `Mode_switch+F1` will move us to VT1.

The second part corresponds to the ``` or `~` button on the bottom-left of the keyboard, as well as the F11 and F12 buttons.

The third part corresponds to the `cmd` buttons on the left and right of the keyboard. I like to set the cmd buttons to act as `Mode_switch` buttons -- this means you can press left or right `cmd` and F1 to move to VT1 (for example).

If you don't want to set the `cmd` buttons to be `Mode_switch`, you can change each of the F-buttons' second column ("_Shift modifier + the key_", AKA _NoSymbol_ in my version), which you can then use `Shift+F[1-12]` to switch VTs. So for example, `keycode  67 = F1 F1 F1 F1 F1 F1 XF86Switch_VT_1` would instead become `keycode  67 = XF86MonBrightnessDown XF86Switch_VT_1`, and you would use `Shift+F1` to switch to VT1.

#### i3 config

---

Now that we have everything set up for X, we need to create a configuration for `i3`.

I made the start of this configuration over a decade ago, so who knows what's changed in that time. But, it works for me still.

```bash
font fixed

set $mod Mod1

set $exec exec --no-startup-id

set $refresh_i3status killall -SIGUSR1 i3status

floating_modifier $mod

tiling_drag modifier titlebar

bindsym $mod+Return exec urxvtc

bindsym $mod+Shift+q kill
bindsym $mod+F4 kill
bindsym $mod+q kill

bindsym $mod+d dmenu_run
bindsym $mod+space dmenu_run

bindsym $mod+j focus left
bindsym $mod+k focus down
bindsym $mod+l focus up
bindsym $mod+semicolon focus right

bindsym $mod+Shift+j move left
bindsym $mod+Shift+k move down
bindsym $mod+Shift+l move up
bindsym $mod+Shift+semicolon move right

bindsym $mod+Shift+Left move left
bindsym $mod+Shift+Down move down
bindsym $mod+Shift+Up move up
bindsym $mod+Shift+Right move right

bindsym $mod+Left workspace prev
bindsym $mod+Right workspace next

# Split horizontal or vertical
bindsym $mod+h split h
bindsym $mod+v split v

# Fullscreen
bindsym $mod+f fullscreen

# Layout: stacked, tabbed, or split, toggling of split mode (nearly always toggle split).
bindsym $mod+s layout stacking
bindsym $mod+w layout tabbed
bindsym $mod+e layout toggle split

# Float or tile window
bindsym $mod+Shift+space floating toggle

# change focus between tiling / floating windows
bindsym $mod+a focus mode_toggle

bindsym $mod+1 workspace "1:www"
bindsym $mod+2 workspace "2:network"
bindsym $mod+3 workspace "3:email"
bindsym $mod+4 workspace "4:devel"
bindsym $mod+5 workspace "5:music"
bindsym $mod+6 workspace "6:general"
bindsym $mod+7 workspace 7
bindsym $mod+8 workspace 8
bindsym $mod+9 workspace 9
bindsym $mod+0 workspace 10

# move focused container to workspace
bindsym $mod+Shift+1 move container to workspace "1:www"
bindsym $mod+Shift+2 move container to workspace "2:network"
bindsym $mod+Shift+3 move container to workspace "3:email"
bindsym $mod+Shift+4 move container to workspace "4:devel"
bindsym $mod+Shift+5 move container to workspace "5:music"
bindsym $mod+Shift+6 move container to workspace "6:general"
bindsym $mod+Shift+7 move container to workspace number 7
bindsym $mod+Shift+8 move container to workspace number 8
bindsym $mod+Shift+9 move container to workspace number 9
bindsym $mod+Shift+0 move container to workspace number 10

mode "resize" {
        bindsym j           resize shrink width 10 px or 10 ppt
        bindsym k           resize grow height 10 px or 10 ppt
        bindsym l           resize shrink height 10 px or 10 ppt
        bindsym semicolon   resize grow width 10 px or 10 ppt


        bindsym Left        resize shrink width 1 px or 1 ppt
        bindsym Down        resize grow height 1 px or 1 ppt
        bindsym Up          resize shrink height 1 px or 1 ppt
        bindsym Right       resize grow width 1 px or 1 ppt

        bindsym $mod+Left       resize shrink width 10 px or 10 ppt
        bindsym $mod+Down       resize grow height 10 px or 10 ppt
        bindsym $mod+Up         resize shrink height 10 px or 10 ppt
        bindsym $mod+Right       resize grow width 10 px or 10 ppt

        bindsym Return mode "default"
        bindsym Escape mode "default"
        bindsym $mod+r mode "default"
}

bindsym $mod+r mode "resize"

bar {
        status_command i3bar
        position top
}

default_border pixel 0
default_floating_border pixel 0
for_window [class="^.*"] border pixel 1

focus_follows_mouse no

bindsym Control+$mod+Shift+l exec i3lock -f

bindsym $mod+Tab workspace next

bindsym $mod+Shift+c reload

bindsym $mod+Shift+r restart

bindsym $mod+Shift+e exec "i3-nagbar -t warning -m 'You pressed the exit shortcut. Do you really want to exit i3? This will end your X session.' -b 'Yes, exit i3' 'i3-msg exit'"

bindsym Mode_Switch+Shift+4 --release exec scrot -s /home/user/Pictures/Screenshots/Screenshot-%Y-%m-%d:%H:%M:%S.png -e 'ln -fs "$f" /tmp/latest-screenshot.png'

bindsym XF86MonBrightnessDown exec asmctl video down
bindsym XF86MonBrightnessUp exec asmctl video up

bindsym XF86KbdBrightnessDown exec asmctl key down
bindsym XF86KbdBrightnessUp exec asmctl key up

bindsym XF86AudioLowerVolume exec mixer vol -2
bindsym XF86AudioRaiseVolume exec mixer vol +2
bindsym XF86AudioMute exec ~/scripts/mixer.sh

bindsym XF86AudioPrev exec playerctl previous
bindsym XF86AudioPlay exec playerctl play-pause
bindsym XF86AudioNext exec playerctl next
```

This configuration uses `Mod1` (the left `Alt` button) for key combinations. You can use the command buttons by setting `set $mod Mode_switch`, for example, if you set them before.
I use a custom-built program for the `status_command` bar which is specific to my needs, but you will probably use `i3bar` or `i3status`.

`~/scripts/mixer.sh` contains the following:

```bash
#!/bin/sh
set -euo pipefail

VOL_TMP="/home/user/.config/i3/.volume"

curvol="$(mixer -S vol | awk -F":" '{print $NF}')"

touch "$VOL_TMP"
chmod 600 "$VOL_TMP"

[ -O "$VOL_TMP" ] || exit 1 # Ensure we're the owner
[ -f "$VOL_TMP" ] || exit 1 # Ensure it's a file
[ -L "$VOL_TMP" ] && exit 1 # Ensure it's not a symlink

if [ "$curvol" -gt 0 ]; then
	echo "$curvol" > "$VOL_TMP"
	mixer vol set 0
else
	mixer vol set "$(cat "$VOL_TMP")"
fi
```

Basically, it's used to save the volume level and then set the volume to zero when F10 is pressed. Then you can unmute and set the previous volume automatically by clicking F10 again.

[playerctl(1)](https://www.freshports.org/multimedia/playerctl) is a program that uses DBUS to control common media players across windows and programs, using a single API. [More info here (it's called MPRIS)](https://wiki.archlinux.org/title/MPRIS). We use it to get the F7,F8,F9 buttons to work as expected: any program that supports the protocol will be paused when you press F8, no matter which window you're in (for example).

[asmctl(1)](https://www.freshports.org/sysutils/asmctl) is used to control the keyboard and screen backlight (more on this later).

[scrot(1)](https://www.freshports.org/graphics/scrot/) is used to take screenshots. Make sure you have those installed:

```bash
$ pkg install playerctl asmctl scrot
```

The left or right cmd buttons (AKA `Mode_switch`), in combination with `shift` and `4`, can be used to take screenshots with `scrot`.

#### urxvt

---

I use the unicode rxvt terminal. It's basic and gets the job I want done:

```bash
$ pkg install rxvt-unicode
```

Back in the `.Xresources` file, we can specify various options. These are my settings:

```bash
URxvt*allow_bold:       true
URxvt.perl-ext-common: default,matcher,resize-font
URxvt.url-launcher: /usr/local/bin/firefox
URxvt.matcher.button: 1
URxvt*background: Black
URxvt*foreground: White

URxvt.color12: rgb:5c/5c/ff

XTerm*bellIsUrgent: true
URxvt.urgentOnBell: true
URxvt.visualBell: true

URxvt.scrollTtyOutput: false
URxvt*scrollTtyKeypress:    true
URxvt.scrollWithBuffer: true

URxvt.saveLines: 500000

URxvt.internalBorder: 4

URxvt.font:      xft:monospace:size=8

URxvt.keysym.Control-Left:   \033[1;5D
URxvt.keysym.Control-Right:  \033[1;5C
URxvt.keysym.Control-space:  \033[1;5C
```

Most of this is obvious, and I won't go into much detail.

The last three lines mean you can use `control+left` to move the cursor in the terminal backwards a word or two, and either `control+right` or `control+space` to move forwards. Note that `Control-space` is case-sensitive.

If you want the terminal to audibly beep on an alert, you can add `bell-command` to the `URxvt.perl-ext-common`, and set `URxvt.bell-command: /usr/bin/beep`.

---

The `resize-font` extension is a custom extension which allows you to either:

1. resize the terminal window to be bigger or smaller,
2. resize the _contents_ (text) of the terminal window to be bigger or smaller (keeping the terminal window the same size).

This behavior matches the default terminal on MacOS. I developed half of the functionality and have uploaded the extension onto Github.

By default, the `control+shift+plus` and `control+shift+minus` key-combinations keep the terminal window size the same, but make the text larger/smaller respectively.
`control+plus` and `control+minus` change the terminal window size, keeping the text proportionate to the window size -- thus larger/smaller, too. `control+0` resets both the terminal size and the text size. `control+shift+/` (AKA `control+?`) shows the current text size.

Note that obviously, if the terminal window is not floating, it just makes the text smaller/larger.

The source code can be found [on my Github](https://github.com/MegaManSec/urxvt-resize-font), where I added the various bug fixes and new functionality. `urxvt` searches for the extension in `$HOME/.urxvt/ext/resize-font`. The file should be executable (`chmod 744` will do).

### wsp

---

The [wellspring touchpad driver](https://man.freebsd.org/cgi/man.cgi?query=wsp) (`wsp`) module is the most up-to-date and most-compatible module for the Macbook's touchpad. However, it had various bugs and problems. You could not single-click and then continue using the trackpad without raising your finger first. Likewise, I added the functionality to allow a single-click to be held down, and a second finger to move freely (for example to single-select and move the selection-point). Some other issues were also fixed. I submitted [freebsd-src#1365](https://github.com/freebsd/freebsd-src/pull/1365) and as of today it has landed, but it may not be in `releng/13.3`. Cherry-pick it and build the kernel yourself if you need to (you can check whether you are using the patched version by checking whether `sysctl hw.usb.wsp.max_double_tap_distance` returns an error or not).

In order to use the `wsp` module, ensure it is loaded in `/boot/loader.conf`:

```bash
wsp_load="YES"
```

I then set the following in `/etc/sysctl.conf` to make my (apparently large?) thumb be recognized (it would sometimes be recognized as a palm due to taking up such a large area, thus being ignored):

```bash
hw.usb.wsp.max_double_tap_distance=2000
```

You can also set the following to ensure that the other drivers aren't loaded (this is not really necessary, but I did this while debugging the following issue). This should be added to `/etc/rc.conf`:

```bash
devmatch_blocklist="ng_ubt ubtbcmfw bcm5974 wmt hms ums psm hcons"
```

#### wsp suspension issues

---

**Note**: At the moment, when the system suspends and resumes resumes, the wsp driver loses the trackpad and the `usbhid` driver is used instead. I do not currently have a fix for this other than compiling the kernel myself. My patch for that issue is simply:

```
diff --git a/sys/dev/usb/input/wsp.c b/sys/dev/usb/input/wsp.c
index d5a801d10081..d668e91e853f 100644
--- a/sys/dev/usb/input/wsp.c
+++ b/sys/dev/usb/input/wsp.c
@@ -754,7 +754,7 @@ wsp_probe(device_t self)
        if (usbd_lookup_id_by_uaa(wsp_devs, sizeof(wsp_devs), uaa) != 0)
                return (ENXIO);
 
-       return (BUS_PROBE_DEFAULT);
+       return (BUS_PROBE_DEFAULT + 2);
 }
 
 static int
```

### Screen Backlight

---

The commonly used `acpi_video` driver does not seem to work on this system, so the associated `sysctl` values cannot be used. However, the screen backlight can be controlled using the [backlight(8)](https://man.freebsd.org/cgi/man.cgi?query=backlight) program (and its associated kernel module).

A bug seems to exist in the screen. When you set the backlight to a value, it seems to make the backlight one value lower than expected. For example:

```bash
$ backlight 50
$ backlight
brightness: 49
```

This is not a bug in the `backlight(8)` program. Using the `backlight(9)` interface, the backlight is set to the incorrect value too. This incidentally means that it is impossible to raise the backlight by a single level incrementally: since, for example, we set `backlight 50` but it actually sets the backlight to `49`, if we increment again, we will simply set it again to `50` -- and this will repeat forever.

Due to this bug, it is also impossible to decrease the backlight by a single digit (in a single action). For example, if the backlight is currently `50` and we set `backlight 49`, the backlight will actually be set to `48`. One might think we could just do `backlight 50` (while the backlight is already `50`) to get it to decrease to `49` due to this bug, but due to a (probably valid) line of code in the `backlight(9)` interface, the backlight won't be set to a value that it already is.

Anyways, instead of using `backlight(8)`, you can also use [asmctl(1)](https://www.freshports.org/sysutils/asmctl) -- more on this later.

### Hardware Acceleration

---

The CPU used in this Macbook supports hardware acceleration for AVC/H264 and VP9 decoding. The `libva-intel-driver` package provides acceleration support, and the FreeBSD handbook [recommends two other packages](https://docs.freebsd.org/en/books/handbook/x11/):

```bash
$ pkg install libva-intel-driver mesa-libs mesa-dri
```

We could also install the `libva-utils` package which provides `vainfo`, which we could confirm use to check that acceleration is working:

```bash
$ vainfo
Trying display: wayland
error: XDG_RUNTIME_DIR is invalid or not set in the environment.
Trying display: x11
libva info: VA-API version 1.22.0
libva info: Trying to open /usr/local/lib/dri/i965_drv_video.so
libva info: Found init function __vaDriverInit_1_22
libva info: va_openDriver() returns 0
vainfo: VA-API version: 1.22 (libva 2.22.0)
vainfo: Driver version: Intel i965 driver for Intel(R) Haswell Mobile - 2.4.1
vainfo: Supported profile and entrypoints
      VAProfileMPEG2Simple            :	VAEntrypointVLD
      VAProfileMPEG2Simple            :	VAEntrypointEncSlice
      VAProfileMPEG2Main              :	VAEntrypointVLD
      VAProfileMPEG2Main              :	VAEntrypointEncSlice
      VAProfileH264ConstrainedBaseline:	VAEntrypointVLD
      VAProfileH264ConstrainedBaseline:	VAEntrypointEncSlice
      VAProfileH264Main               :	VAEntrypointVLD
      VAProfileH264Main               :	VAEntrypointEncSlice
      VAProfileH264High               :	VAEntrypointVLD
      VAProfileH264High               :	VAEntrypointEncSlice
      VAProfileH264MultiviewHigh      :	VAEntrypointVLD
      VAProfileH264MultiviewHigh      :	VAEntrypointEncSlice
      VAProfileH264StereoHigh         :	VAEntrypointVLD
      VAProfileH264StereoHigh         :	VAEntrypointEncSlice
      VAProfileVC1Simple              :	VAEntrypointVLD
      VAProfileVC1Main                :	VAEntrypointVLD
      VAProfileVC1Advanced            :	VAEntrypointVLD
      VAProfileNone                   :	VAEntrypointVideoProc
      VAProfileJPEGBaseline           :	VAEntrypointVLD
      VAProfileVP9Profile0            :	VAEntrypointVLD
```

---

For Firefox, we need to specifically enable hardware acceleration. This is as simple as visiting [about:config](about:config) and setting the `gfx.webrender.all` configuration to `true`. I have read elsewhere how various other flags need to be changed, [like some 'media...' flags](https://forums.freebsd.org/threads/dedicated-gpu-runs-hot-for-absolutely-no-reason.90315/post-623703) as well as [browser.tabs.remote.autostart and the setting of the environmental value MOZ_X11_EGL=1](https://www.reddit.com/r/freebsd/comments/igq5xd/comment/g2vbzpc/). Even the official Github repository mentions some of these [flags and variables](https://github.com/elFarto/nvidia-vaapi-driver). But, as far as I can tell, and with all benchmarks tested, this is not the case. Unless I'm missing something quite serious, it is not necessary to set any flag other than `gfx.webrender.all`, and no environmental values are necessary.


There is a [long-standing bug](https://forums.freebsd.org/threads/sleep-resume-caveats-and-gotchas.90831/post-638290) in X on FreeBSD, where hardware acceleration will cease to work if the virtual terminal is switched more than once. Since we boot into v0 and the X session occupies v8, any changes from the X session will make acceleration stop working until a reboot.

To force H264 in Firefox, you can use the [enhanced-h264ify](https://github.com/alextrv/enhanced-h264ify) extension.

When suspension happens, the vt is automatically switched. To ensure this doesn't happen, set the following in `/etc/sysctl.conf`:

```bash
hw.syscons.sc_no_suspend_vtswitch=1
kern.vt.suspendswitch=0
```


## Suspend/Resume

---

Suspend/resume works fine. You can only suspend/resume after the graphic drivers are loaded. So, either start X, or add the following to `/etc/rc.conf`: `kld_list="i915kms"`. This ensures that the driver is loaded on boot.

Also, make sure the necessary changes outlined above with respect to `wifibox` are made (AKA: check whether the patches have been committed and that you've built `wifibox-core` with `RECOVER_SUSPEND_VMM`).

Finally, ensure that the following sysctls are set in `/etc/sysctl.conf`:

```bash
hw.acpi.power_button_state=S3
hw.acpi.lid_switch_state=S3
```

The first one makes the power button suspend instead of shutdown. The second makes the system suspend when the lid is closed.

## Sound

---

Some sound devices are automatically picked up by pcm:

```bash
$ cat /dev/sndstat 
Installed devices:
pcm0: <Intel Haswell (HDMI/DP 8ch)> (play)
pcm1: <Cirrus Logic (0x4208) (Analog 4.0/2.0)> (play/rec) default
pcm2: <Cirrus Logic (0x4208) (Analog Headphones)> (play)
pcm3: <Cirrus Logic (0x4208) (Digital)> (play)
No devices installed from userspace.
```

However, no sound is heard. We need to set some device hints to get it working. [snd_hda(4)](https://man.freebsd.org/cgi/man.cgi?snd_hda) describes the process for setting the correct pins for audio devices in `/boot/device.hints`. It was a little bit hard to follow, and there were no good online resources, so I will provide a small guide of how I understand this all to work.

First, we run `sysctl dev.hdac.1.pindump=1`, where the current configuration for the sound devices is printed to the system log. The values can be seen by running `dmesg`. I have removed the unimportant entries:

```bash
hdaa1: Dumping AFG pins:
hdaa1: nid   0x    as seq device       conn  jack    loc        color   misc
hdaa1: 16 002b4020 2  0  Headphones    Jack  Combo   0x00       Green   0
hdaa1:     Caps:    OUT HP           Sense: 0x00000000 (disconnected)
hdaa1: 18 90100110 1  0  Speaker       Fixed Unknown Internal   Unknown 1
hdaa1:     Caps:    OUT             
hdaa1: 19 90100112 1  2  Speaker       Fixed Unknown Internal   Unknown 1
hdaa1:     Caps:    OUT             
hdaa1: 24 00ab9040 4  0  Mic           Jack  Combo   0x00       Pink    0
hdaa1:     Caps: IN             VREF Sense: 0x00000000 (disconnected)
hdaa1: 28 90a60100 0  0  Mic           Fixed Digital Internal   Unknown 1 DISA
hdaa1:     Caps: IN                 
hdaa1: 33 004be030 3  0  SPDIF-out     Jack  Combo   0x00       White   0
hdaa1:     Caps:    OUT              Sense: 0x00000000 (disconnected)
hdaa1: NumGPIO=6 NumGPO=2 NumGPI=0 GPIWake=1 GPIUnsol=1
hdaa1:  GPIO0: output state=0
hdaa1:  GPIO1: disabled
hdaa1:  GPIO2: disabled
hdaa1:  GPIO3: disabled
hdaa1:  GPIO4: disabled
hdaa1:  GPIO5: disabled
hdaa1:  GPO0: state=0hdaa1:  GPO1: state=0
```

Each association (`as`) corresponds to a single device, made up of 'pins' (the specifics of how this works and what it means can be read about [here](https://forums.freebsd.org/threads/no-audio-on-my-system.57473/#post-327863) as well as the manual). We need to group together pins to specific `as` values, and set a:

```
as Association number.  Associations are used to group individual pins to form a complex multi-pin device.

seq Sequence number.  A unique, per-association number used to order pins inside the particular 
association. For multichannel input/output associations sequence numbers encode channel pairs positions: 0 
- Front, 1 - Center/LFE, 2 - Back, 3 - Front Wide Center, 4 - Side. Standard combinations are: (0) - 
Stereo; (0, 2), (0, 4) - Quadro; (0, 1, 2), (0, 1, 4) - 5.1; (0, 1, 2, 4) - 7.1.

The sequence number 15 has a special meaning for output associations.  Output pins with this number and 
device type “Headphones” will duplicate (with automatic mute if jack detection is supported) the first pin 
in that association.
```

This Macbook has stereo speakers, so we need to pin two pins to a single as, with the seq (0,2). Based on the pindump, the fixed speakers use pins 18 and 19. Therefore, we set in `/boot/device.hints`:

```bash
hint.hdac.1.cad0.nid18.config="as=2 seq=2" # Speaker 2, as=2
hint.hdac.1.cad0.nid19.config="as=2 seq=0" # Speaker 1, as=2
```

We also have a headphone jack on this system. As explained:

```
The sequence number 15 has a special meaning for output associations. Output pins with this number and device type “Headphones” will duplicate (with automatic mute if jack detection is supported) the first pin in that association.
```

So, for the Headphones-out, we use the `as=2` again:

```bash
hint.hdac.1.cad0.nid16.config="as=2 seq=15 type=Headphones" # Headphone jack-out
```

When we plug headphones (or otherwise) into the 3.5mm jack, the system will also automatically route audio through them and. 

We also have an inbuilt microphone: pin 28. So, we create a new device for that:

```bash
hint.hdac.1.cad0.nid28.config="as=3" # Inbuilt Microphone, as=3
```

There is also a Headphones-in pin for the 3.5mm jack. I don't have headphones which have a microphone to test this, so I have left it unchanged. The config `hint.pcm.%d.rec.autosrc` in the manual looks particularly interesting in relation to this, though (it seems that it can be used to automatically use the headphone jack for recording when it is plugged in).

What's remaining is the SPDIF port on pin 33. I have never used SPDIF, and have no intention of using it, so I have completely disabled it. Without disabling it, a red light is constantly turned on inside the jack, which is also annoying:

```bash
hint.hdac.1.cad0.nid33.config="conn=None" # kill the SPDIF light
```

---

Finally, we need to set the so-called "gpio_config". The manual isn't so helpful with explaining how to find the right value, but it does state:

```
Overrides audio function GPIO pins configuration set by BIOS. 
May be specified as a set of space-separated “num=value” pairs, where num is GPIO line number, and value is one of: “keep”, “set”, “clear”, “disable” and “input”.
“GPIOs” are a codec's General Purpose I/O pins which system integrators sometimes use to control external muters, amplifiers and so on. If you have no sound, or sound volume is not adequate, you may have to experiment a bit with the GPIO setup to find the optimal setup for your system.
```

By default, the value is:

```bash
$ sysctl dev.hdaa.1.gpio_state
dev.hdaa.1.gpio_state: 0=output(0) 1=disabled 2=disabled 3=disabled 4=disabled 5=disabled
```

`0=output(0)` isn't in the set of "_value is one of_", so there must be something wrong there. In the end, I worked out that setting the following hint makes the audio work:

```bash
hint.hdaa.1.gpio_config="0=set" # This makes sound work.
```

---

All-in-all, I have the following in `/boot/device.hints`:

```bash
hint.hdaa.1.gpio_config="0=set" # This makes sound work.

hint.hdac.1.cad0.nid18.config="as=2 seq=2" # Speaker 2, as=2
hint.hdac.1.cad0.nid19.config="as=2 seq=0" # Speaker 1, as=2
hint.hdac.1.cad0.nid16.config="as=2 seq=15 type=Headphones" # Headphone jack
hint.hdac.1.cad0.nid28.config="as=3" # Inbuilt Microphone, as=3

hint.hdac.1.cad0.nid33.config="conn=None" # kill the SPDIF light
```

In `/etc/sysctl.conf`, I also have the following, but I'm not sure if it really does anything for my usage:

```bash
dev.pcm.1.play.vchanmode=adaptive
dev.pcm.1.play.vchanrate=96000
dev.pcm.1.play.vchans=16
hw.snd.maxautovchans=16
```

---

If the sound is too quiet, you can experiment with the sysctl `hw.snd.vpc_0db`. A lower value will raise the volume, but result in sound clipping.

## Keyboard

---

The keyboard mostly works fine out of the box. The only problem is that the LED on the capslock button does not work. For whatever reason, the default [ukbd(4)](https://man.freebsd.org/cgi/man.cgi?query=ukbd&sektion=4&format=html) driver cannot send the proper signal to the inbuilt keyboard to set LEDs. However, the [hkbd(4)](https://man.freebsd.org/cgi/man.cgi?query=hkbd&sektion=4&manpath=freebsd-release-ports) driver _does_ work. It's not really obvious why ukbd doesn't work, but we need to force the system first to _not_ use ukbd, and second to _use_ hkbd. As the manual states:

```
If you want to use a HID keyboard as your default and not use an AT keyboard at all, you will have to 
remove the device atkbd line from the kernel configuration file. Because of the device initialization 
order, the HID keyboard will be detected after the console driver initializes itself and you have to 
explicitly tell the console driver to use the existence of the HID keyboard. This can be done in one of the 
following two ways.
```

Luckily, we don't actually have to recompile the kernel to get rid of atkbd (which will use ukbd). Instead, we can use device hints. First we add the following to `/boot/device.hints` to disable ukbd and enable hkbd:

```bash
hint.ukbd.0.disabled="1" # kill ukbd
hint.hkbd.0.at="usb" # use hkbd
```


Next, in `/boot/loader.conf` we set:

```bash
hkbd_load="YES" # load hkbd
hw.usb.usbhid.enable="1" # enable
```

**Note**: Since we are disabling `ukbd`, there will be no working keyboard when booting into single-user-mode. Therefore, to enter single-user-mode with a keyboard, boot into the "loader prompt" from the FreeBSD bootloader (press 3), then type:

```bash
set hint.ukbd.0.disabled=0
boot -s
```

## Webcam

---

The webcam does not work. However, I am hopeful that in the future with FreeBSD's [webcamd](https://github.com/hselasky/webcamd) and [facetimehd](https://github.com/patjak/facetimehd), I can get it working. Once that's done, I will update this post as well as outline in a new post how I achieved that.

## ASMC

---

Apple System Management Controller (SMC) (ASMC) is the subsystem used by this Macbook for controlling (among other things) the keyboard backlight and fans. It is also used for temperature monitoring. At the time of writing this, FreeBSD does not recognize this Macbook as using ASMC, but I have submitted a patch in [freebsd#1366](https://github.com/freebsd/freebsd-src/pull/1366) that fixes that. The patch may not be in `releng/13.3` yet -- if not, cherry-pick the patch and build the kernel. Once that is introduced, you can add the following to `/boot/loader.conf` to load the asmc module:

```bash
asmc_load="YES"
```

Of note are the following sysctl values:

```bash
dev.asmc.0.fan.0.targetspeed
dev.asmc.0.fan.0.minspeed
dev.asmc.0.fan.1.minspeed
dev.asmc.0.light.control
```

The first three values are the fanspeed (the first one being read-only), and the final one is the keyboard backlight. On this Macbook, there is a maximum value of 9000 (probably rpm) for the fanspeeds. The light.control value is from 0 to 100.

### asmctl

---

[asmctl(1)](https://www.freshports.org/sysutils/asmctl) can be used to control the screen brightness and keyboard backlight without requiring root (it uses setuid as root).

Previously, the tool would fail to work if the sysctl values associated with the `acpi_video(4)` driver could not be set (for the screen brightness). Since that driver doesn't work on this Macbook, the tool would completely fail. I fixed that in [asmctl#15](https://github.com/yuichiro-naito/asmctl/pull/15).

I also added support for the `backlight(9)` API into the tool, added the ability to restore the keyboard backlight on reboot, fixed various bugs, and fixed the extremely inconsistent formatting of the source code in [asmctl#17](https://github.com/yuichiro-naito/asmctl/pull/17). With this patch, we can now:

1. Control the screen's brightness using `asmctl` (using `backlight(9)`),
2. Save and restore the screen's brightness on a system shutdown/boot,
3. Save and restore the screen's brightness when the power adaptor is plugged in or disconnected.
4. Save and restore the keyboard brightness on a system shutdown/boot.

The saved values are stored in `/var/lib/asmctl.conf`. For example:

```
backlight_economy_level=81
backlight_full_level=94
backlight_current_level=81
dev.asmc.0.light.control=0
```

In this example, the laptop is currently disconnected from the power adaptor, and has a brightness of 81. If I plug in the power adaptor, the brightness will automatically be set to 94.

On a reboot, the brightness will automatically be set to the value it had previously been set to, depending on whether the power adaptor is plugged in or not. The keyboard backlight will automatically be restored, too.

The above functionality is handled by a `devd` rule in `/usr/local/etc/devd/asmctl.conf`:

```bash
notify 20 {
        match "system"          "ACPI";
        match "subsystem"       "ACAD";
        action "/etc/rc.d/power_profile $notify";
        action "/usr/local/bin/asmctl video acpi";
        action "/usr/local/bin/asmctl key acpi";
};
```

#### Fan Control

---

To automatically control the fan, I created a script (inspired by [this](https://wiki.freebsd.org/Laptops/Apple_MacBookPro9%2C2?action=AttachFile&do=view&target=asmcfan) in `/usr/local/bin/asmcfan`:

```bash
#!/bin/sh
if ! kldstat | grep -q asmc.ko
then
  kldload asmc
fi

TEMP=$(sysctl -n dev.cpu.0.temperature | cut -c 1-2)
CUR_SPEED=$(sysctl -n dev.asmc.0.fan.0.targetspeed)
SET_SPEED=0

if [ "$TEMP" -le 48 ]; then
  SET_SPEED=2000
elif [ "$TEMP" -le 56 ]; then
  SET_SPEED=2800
elif [ "$TEMP" -le 62 ]; then
  SET_SPEED=3000
elif [ "$TEMP" -le 68 ]; then
  SET_SPEED=3200
elif [ "$TEMP" -le 84 ]; then
  SET_SPEED=4000
elif [ "$TEMP" -le 88 ]; then
  SET_SPEED=4400
elif [ "$TEMP" -le 92 ]; then
  SET_SPEED=5000
elif [ "$TEMP" -le 96 ]; then
  SET_SPEED=6000
else
  SET_SPEED=6800
fi

if [ "$SET_SPEED" -ne "$CUR_SPEED" ]; then
  sysctl dev.asmc.0.fan.0.minspeed="$SET_SPEED" dev.asmc.0.fan.1.minspeed="$SET_SPEED"
fi

exit 0
```

I then made sure it was executable and owned by root:wheel, and added it as a cronjob to be run as root.

```bash
chown root:wheel /usr/local/bin/asmcfan
chmod +x /usr/local/bin/asmcfan
echo '*      *       *       *       *       root    /usr/local/bin/asmcfan >/dev/null' >> /etc/crontab
```

## Bluetooth

---

Bluetooth works out-of-the-box:

```bash
$ usbconfig -d ugen0.2 show_ifdrv
ugen0.2: <Broadcom Corp. Bluetooth USB Host Controller> at usbus0, cfg=0 md=HOST spd=FULL (12Mbps) pwr=ON (0mA)
```

```bash
$ hccontrol -n ubt0hci inquiry
Inquiry result, num_responses=1
Inquiry result #0
	BD_ADDR: [snip]
	Page Scan Rep. Mode: 0x1
	Page Scan Period Mode: 00
	Page Scan Mode: 00
	Class: 08:04:3c
	Clock offset: 0x2649
Inquiry complete. Status: No error [00]
```

I have no real need for Bluetooth, but I did test Bluetooth headphones by [following this guide](https://forums.freebsd.org/threads/bluetooth-audio-how-to-connect-and-use-bluetooth-headphones-on-freebsd.82671/) and it worked fine.

---

Since I have no need for Bluetooth on this system, I want to completely disable the chip to save a little bit of power. The chips really use USB buses, so are configurable via the USB subsystem. Executing `usbconfig -d ugen0.2 power_off` will completely power off the device. We want to do this both on startup as well as resume (since the device is brought back up on suspend/resume). We make this modular, as an rc.d command script. Creating a script `/usr/local/etc/rc.d/kill_usb_devices`:

```bash
#!/bin/sh

# PROVIDE: kill_usb_devices
# KEYWORD: resume
#
# Enable with kill_usb_devices=YES in /etc/rc.conf
#
# Set kill_usb_devices_list to a comma-separated list of usb devices to be shutdown.
#
# Example:
# Given `usbconfig`:
#   ugen0.1: <Intel XHCI root HUB> at usbus0, cfg=0 md=HOST spd=SUPER (5.0Gbps) pwr=SAVE (0mA)
#   ugen0.2: <Broadcom Corp. Bluetooth USB Host Controller> at usbus0, cfg=0 md=HOST spd=FULL (12Mbps) pwr=ON (0mA)
#   ugen0.3: <Apple Inc. Apple Internal Keyboard / Trackpad> at usbus0, cfg=0 md=HOST spd=FULL (12Mbps) pwr=ON (500mA)
#   ugen0.4: <Apple Card Reader> at usbus0, cfg=0 md=HOST spd=SUPER (5.0Gbps) pwr=ON (224mA)
#
# A valid value of kill_usb_devices_list would be:
# kill_usb_devices_list="Intel XHCI root HUB,Broadcom Corp. Bluetooth USB Host Controller"
#

. /etc/rc.subr

: ${kill_usb_devices_enable=NO}
: ${kill_usb_devices_list=""}

name="kill_usb_devices"
rcvar="kill_usb_devices_enable"

USBCONFIG="/usr/sbin/usbconfig"
GREP="/usr/bin/grep"

load_rc_config "$name"

extra_commands="resume"
start_cmd="kill_power"
resume_cmd="kill_power"

kill_power() {
  [ -z "$kill_usb_devices_list" ] && exit 0
  IFS=","

  for usb_item in $kill_usb_devices_list; do
    usbdev="$($USBCONFIG | $GREP -m1 -- "$usb_item")"

    [ -z "$usbdev" ] && continue

    ugen="${usbdev%% *}"
    ugen="${ugen%:}"

    [ -z "$ugen" ] && continue

    $USBCONFIG -d "$ugen" power_off
  done

  unset IFS
  exit 0
}

run_rc_command "$1"
```

Make sure the file is executable and owned by root/wheel (it should be already):
```bash
$ chmod +x /usr/local/etc/rc.d/kill_usb_devices
$ chown root:wheel /usr/local/etc/rc.d/kill_usb_devices
```

The gist of the script is that when the system starts or resumes, if `kill_usb_devices` is enabled, each device (identified, separated by commas, by the `kill_usb_devices_list` variable in `/etc/rc.conf`) is powered off.

It is possible to change `power_off` in the script to `power_safe` to use power saving mode for the devices: it seems to work for the Bluetooth chip (and the SD card reader: more on that later).

In `/etc/rc.conf`, we set:

```bash
kill_usb_devices_enable="YES"
kill_usb_devices_list="Broadcom Corp. Bluetooth USB Host Controller"
```

We can confirm it works:

```bash
$ usbconfig -d ugen0.2
ugen0.2: <Broadcom Corp. Bluetooth USB Host Controller> at usbus0, cfg=0 md=HOST spd=FULL (12Mbps) pwr=ON (0mA)
$ /usr/local/etc/rc.d/powersave resume
$ usbconfig -d ugen0.2
ugen0.2: <Broadcom Corp. Bluetooth USB Host Controller> at usbus0, cfg=255 md=HOST spd=FULL (12Mbps) pwr=OFF (0mA)
```

## Thunderbolt

---

I've never used the Thunderbolt ports on any Mac. However, I noticed that on this system the only way for them to even appear (in `pciconf -lv`) is to set the following in `/boot/loader.conf`:

```bash
hw.pci.clear_buses=1
```

I do not know whether there are any adverse effects or how to use the ports, sorry. They appear in `pciconf -lv` like this:

```bash
pcib6@pci0:2:0:0:       class=0x060400 rev=0x00 hdr=0x01 vendor=0x8086 device=0x156d subvendor=0x0000 subdevice=0x0000
    vendor     = 'Intel Corporation'
    device     = 'DSL5520 Thunderbolt 2 Bridge [Falcon Ridge 4C 2013]'
    class      = bridge
    subclass   = PCI-PCI
none3@pci0:4:0:0:       class=0x088000 rev=0x00 hdr=0x00 vendor=0x8086 device=0x156c subvendor=0x0000 subdevice=0x0000
    vendor     = 'Intel Corporation'
    device     = 'DSL5520 Thunderbolt 2 NHI [Falcon Ridge 4C 2013]'
    class      = base peripheral  
```

## SD-Card Reader

---

The SD-card reader works out-of-the-box, located at `/dev/da0`:

```bash
da0 at umass-sim0 bus 0 scbus1 target 0 lun 0
da0: <APPLE SD Card Reader 3.00> Removable Direct Access SPC-4 SCSI device
da0: Serial Number 000000000820
da0: 400.000MB/s transfers
da0: Attempt to query device size failed: NOT READY, Medium not present
da0: quirks=0x2<NO_6_BYTE>
```

```bash
$ usbconfig -d ugen0.4
ugen0.4: <Apple Card Reader> at usbus0, cfg=0 md=HOST spd=SUPER (5.0Gbps) pwr=ON (224mA)
```


I don't use the SD card reader, so I will add `Apple Card Reader` to `kill_usb_devices_list` in `/etc/rc.conf`. That means, the value is now:

```bash
kill_usb_devices_list="Broadcom Corp. Bluetooth USB Host Controller,Apple Card Reader"
```

## Other Changes

---

### Coredump saving

---

For some reason when a kernel coredump occurred, the coredump would not be saved, and the system would boot with the error:

```bash
savecore: /dev/ada0p3: Operation not permitted
```

`dumpdev=AUTO` was previously set in `/etc/rc.conf`, which I changed to:

```bash
dumpdev="/dev/ada0p3"
dumpdir="/var/crash"
savecore_enable="YES"
```

In `/etc/fstab`, I changed 

```bash
/dev/ada0p3.eli         none    swap    sw         0       0
```
to

```bash
/dev/ada0p3.eli         none    swap    sw,late         0       0
```

Coredumps now save correctly. 

### Power Saving

---

As with all of these types of systems, I set up `powerd` to conserve power. In `/etc/rc.conf`, I have:

```bash
powerd_enable="YES" # Save power
powerd_flags="-n min -a hiadaptive -b adaptive -i 25 -r 85"
performance_cx_lowest="Cmax"
economy_cx_lowest="Cmax"
```

I also have this in `/etc/sysctl.conf`:

```bash
kern.hz=100
kern.sched.preempt_thresh=224
```

In `/boot/loader.conf`, I have:

```bash
hw.pci.do_power_nodriver=3

compat.linuxkpi.fastboot=1
compat.linuxkpi.enable_dc=4
compat.linuxkpi.enable_fbc=1
compat.linuxkpi.enable_rc6=7
compat.linuxkpi.semaphores=1
compat.linuxkpi.disable_power_well=1

compat.linuxkpi.i915_fastboot=1
compat.linuxkpi.i915_enable_dc=4
compat.linuxkpi.i915_enable_fbc=1
compat.linuxkpi.i915_enable_rc6=7
compat.linuxkpi.i915_semaphores=1
compat.linuxkpi.i915_disable_power_well=1
```

Why the doubled-up `linuxkpi` lines? Because I can't work out which are actually doing something. But one of each does something!

Likewise, this in `/boot/device.hints`: `hint.ahcich.0.pm_level=5` -- which ensures that for each ahci device, the "_driver initiates SLUMBER PM state transition 125ms after port becomes idle._"

### Enhanced mouse movements

---

[moused(8)](https://man.freebsd.org/cgi/man.cgi?moused(8)) is used to enhance some movements of the mouse. I set the following:

```bash
moused_enable="YES"
moused_flags="-A 1.3,2.6 -a 1.4 -r high"
```

### Auto-boot with power adapter

---

When Macbooks are turned off but plugged into a power socket, they will automatically boot. I don't like this behavior, especially because it just automatically boots into my zfs loader encryption key prompt and runs my CPU hot. This behavior can be disabled by changing the value in the NVRAM. This requires booting into the recovery mode of the Macbook. Reboot, and hold the left Cmd button and the 'r' button: [this blog post](https://osxdaily.com/2017/05/18/access-terminal-recovery-mode-mac/) outlines the steps.

In the terminal, then type `nvram AutoBoot=%00`. It can be turned back on with `nvram AutoBoot=%03`.

### Expose

---

Since we set up all of the F-buttons except F3 and F4, I looked into whether it's possible to get a similar experience to the one on a Macbook: [expose](https://en.wikipedia.org/wiki/Mission_Control_(macOS)).

Apparently [i3expo-ng](https://github.com/morrolinux/i3expo-ng) provides the functionality to view all open windows in i3. I haven't tested it, though.

### Encrypted DNS over TLS with unbound

---

I use encrypted DNS over TLS by running a recursive caching DNS server (`unbound`) on my system, using Mullvad's DoT server. I have outlined instructions of doing that [on this blog](https://joshua.hu/encrypted-dns-over-tls-unbound-mullvad-freebsd-block-unencrypted-dns-traffic) already.

### Encrypted NTP with NTS with chronyd

---

I use encrypted NTP, facilitated by `chronyd`. I have outlined the instructions to getting that working already [on this blog](https://joshua.hu/encrypted-ntp-nts-chronyd-freebsd).

### Bash

---

I use `bash` and set it as the default shell for my user:

```bash
$ pkg install bash
$ chsh -s /usr/local/bin/bash user
```

I use bash-completion:

```bash
$ pkg install bash-completion
```

I symlink `.bashrc` to `.bash_profile`:

```bash
$ ln -s .bash_profile .bashrc
```

My `.bash_profile` is quite simple and clearly archaic based on the `$debian_chroot` part which isn't applicable on FreeBSD at all.

```bash
HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=100000
HISTFILESIZE=200000
EDITOR=nano

export EDITOR
export LC_ALL=C

shopt -s checkwinsize
force_color_prompt=yes
color_prompt=yes

PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

alias ipgrep='grep -E '\''[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'\'''

alias ls='ls -GF'

[[ $PS1 && -f /usr/local/share/bash-completion/bash_completion.sh ]] && \
        source /usr/local/share/bash-completion/bash_completion.sh

alias cp='cp -p'
alias psf='ps -d'

export SSH_AUTH_SOCK=~/.ssh/ssh-agent.$HOSTNAME.sock
ssh-add -l &>/dev/null
if [ $? -ge 2 ]; then
  rm "$SSH_AUTH_SOCK" &>/dev/null
  ssh-agent -a "$SSH_AUTH_SOCK" &>/dev/null
fi
```

### Nano

---

I use nano. My config is pretty basic:

```bash
set nowrap
set fill 78
include /usr/local/share/nano/*.nanorc
```

---

# Afterword

All in all, setting up FreeBSD on this system comfortably has taken up way too much time. But, somebody had to do it, and with all of the additions and changes outlined in this post, I'm now happily using the system as my daily driver.

I have set up a git repository with all of the changes outlined in this post (and some more). I'll get around to adding a list of installed packages and creating a script which automates the installation of everything one day. You can find the git repository on [https://github.com/MegaManSec/dotfiles/](https://github.com/MegaManSec/dotfiles/).
