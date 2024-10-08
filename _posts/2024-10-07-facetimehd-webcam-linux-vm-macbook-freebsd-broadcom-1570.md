---
layout: post
title: "Webcam support on a Macbook running FreeBSD using PCI passthrough"
author: "Joshua Rogers"
categories: journal
---

## Introduction

---

In my previous post, _[A Full Guide: FreeBSD 13.3 on a MacBook Pro 11.4 (Mid 2015) (A1398)](https://joshua.hu/FreeBSD-on-MacbookPro-114-A1398)_, I outlined how to get nearly every device on a Macbook Pro 11,4 functioning while running FreeBSD. Nearly everything: except for the webcam.

In this post, I'll outline how to get the camera working on FreeBSD, by using a tiny Alpine Linux VM using FreeBSD's hypervisor bhyve, and PCI passthrough. At the end of this post, you'll have a working webcam.

In the following screenshot, you see me running `webcamd` on the FreeBSD host (top right), `ffmpeg` and `socat` in the Alpine Linux VM (top left), `ffmpeg` and `nc` on the FreeBSD host (bottom), and `pwcview` on the FreeBSD host:

![Selfie using a Macbook Pro webcam on FreeBSD](/files/freebsd-selfie.png)

## Broadcom 1570

---

The Broadcom 1570 (the webcam used by this and many other Mac products) is apparently "[_based on Ambarellas S2 series of IP cameras; likely a nerfed version of the S2Lm._](https://github.com/patjak/facetimehd/wiki/Specification---Features)". The camera can be turned on [without activating the green light](https://www.usenix.org/system/files/conference/usenixsecurity14/sec14-paper-brocker.pdf).

Broadcom does not offer any driver for this device, but luckily it has been reverse-engineered by someone and a driver exists for Linux.

## PCI Passthrough and Alpine Linux

---

In order to utilize the Linux driver, we obviously need to be running... Linux. So, the plan is to start a tiny VM running Alpine Linux, install the `facetimehd` driver, and stream the webcam back to the FreeBSD host, ultimately using `webcamd` to turn the stream into a webcam device.

![Diagram of process for using facetimehd on FreeBSD](/files/webcam-diagram.png)


## bhyve VM installation

---

First we install the `bhyve-firmware` and `vm-bhyve` packages:

```console
$ pkg install bhyve-firmware vm-bhyve
```

### vm, gateway, pf

---

We're going to use FreeBSD's Packet Filter (pf) to forward packets from the VM to the correct interface. This is necessary because if you're using `wifibox`, you can't do `vm switch add public wifibox0` to get the VM to use wifibox's network. We need to enable gateways (AKA `sysctl net.inet.ip.forwarding=1`) We also need to disable VM host checks because it causes a system crash for some reason. In `/etc/rc.conf`, we handle all of this (and enable VMs):

```
vm_enable="YES"
vm_dir="zfs:zroot/vm"
gateway_enable="yes"
pf_enable="yes"
vm_disable_host_checks="yes"
```

### vm dataset

---

We need to create a ZFS dataset in `zroot/vm`:

```console
$ zfs create zroot/vm
```

### nat gateway

---

In `/etc/pf.conf`, we set up the gateway. If your interface is not `wifibox0`, replace both instances with whatever you're using:

```
nat on wifibox0 from {192.168.8.0/24} to any -> (wifibox0)
```

### start services

---

We can either reboot, or manually start the `vm` service and deal with the other related services and settings:

```console
$ service vm start
$ sysctl net.inet.ip.forwarding=1
$ service pf start
$ zfs mount zroot/vm
```

### initalize vm

---

Now we need to initalize the VM. `vm` will download the ISO provided in the link. You may want to use a newer version.

```console
$ vm init
$ cp /usr/local/share/examples/vm-bhyve/* /zroot/vm/.templates/
$ vm switch create -a 192.168.8.1/24 public
$ vm iso https://dl-cdn.alpinelinux.org/alpine/v3.20/releases/x86_64/alpine-standard-3.20.3-x86_64.iso
$ vm create -c 1 -m 256M -s 8G -t alpine alpine
$ EDITOR=nano vm configure alpine
```

### configure vm

---

You will now have the option to configure some configurations of the VM. Here's mine:

```
loader="uefi"
cpu=1
memory=256M
network0_type="virtio-net"
network0_switch="public"
disk0_type="virtio-blk"
disk0_name="disk0.img"
uuid="6e117fda-7f28-11ef-9b47-589cfc10ffc9"
network0_mac="58:9c:fc:0f:a3:36"
passthru0="4/0/0"

# Share host's /var/tmp/folder/
#disk1_type="virtio-9p"
#disk1_name="share_name=/var/tmp/folder"
#disk1_dev="custom"
```

Some things to note:

1. `passthru0="4/0/0"` is used to perform PCI passthrough of the device located on `pci0:4:0:0`. You can make sure this is the correct value by running `pciconf -lv` and looking for the device identified as `720p FaceTime HD Camera`.
2. `loader="uefi"` is mandatory, as the standard Alpine OS uses UEFI.
3. If you want to share files between the host and VM, uncomment the final three lines, and replace `/var/tmp/folder` with where you would like the sharing the happen (from the side of the host).

### pci passthrough

---

Next, we need to set the device for the PCI device to `ppt`:

```console
$ devctl set driver pci0:4:0:0 ppt
```

### install/setup vm

---

With that done, we can now boot into the installer:

```console
$ vm install -f alpine alpine-standard-3.20.3-x86_64.iso
```

You'll be greeted with a terminal. You should run the installer:

```console
$ setup-alpine
```

#### networking

---

When asked about networking, I specified `192.168.8.2` for the address, `255.255.255.0` for the broadcast address, and `192.168.8.1` for the gateway.

#### gateway wifibox bug

---

For some reason, the forwarding of the network to `wifibox0` doesn't work inside the Alpine VM if I start `wifibox` automatically in `/etc/rc.conf`. So, I set `wifibox_enable=NO` in `/etc/rc.conf` and reboot, and manually start wifibox using `service wifibox onestart`.

#### halt

---

You can run `halt` once everything is done, and type `~.` to exit the [nmdm tty](https://man.freebsd.org/cgi/man.cgi?query=nmdm).

## Webcam VM setup

---

### boot into vm

---

Now start the VM, and use the console (or use SSH, if you set that up):

```console
$ vm start alpine
$ vm console alpine
```

Test if the network is working using `ping`. Again, if it's not working, try disable wifibox from starting on boot, and manually start it. Don't forget to set the ppt device after the reboot.

### mount shared directory

---

If you decided to share a folder between the host and VM, you can mount it now:

```console
$ mount -t 9p -o trans=virtio share_name /mnt
```

### install packages

---

First we include the community packages by editing `/etc/apk/repositories` and uncommenting the commented line. Then we install `doas`, and some packages used for building the `facetimehd` driver.

```console
$ vi /etc/apk/repositories # uncomment the community line
$ apk update
$ apk add doas build-base alpine-sdk linux-lts-dev linux-lts
$ adduser -D packager
$ addgroup packager abuild
$ passwd packager # set a password
$ echo 'permit persist :abuild' >> /etc/doas.conf
```

### build packages

---

Now we need to build some packages. This process might take awhile because we've set the VM to only have one VM and 256MB of memory; we could raise that by running `vm configure alpine` again, build the packages, then change it back, or we can just wait a bit for it all to finish.

```console
$ su packager
$ cd
$ abuild-keygen --append --install
```

The following instructions are kind of hand-wavy and are not really the best way to go about things, but oh well; this post is mostly just so I remember what I've done.

```console
$ doas apk add socat libcap2 libjpeg-turbo musl pkgconf zlib v4l-utils-libs
$ mkdir -p aports/facetimehd-firmware/
$ cd aports/facetimehd-firmware/
$ wget https://raw.githubusercontent.com/MegaManSec/webcam-aports/refs/heads/main/facetimehd-firmware/APKBUILD
$ abuild -r
$ mkdir ../facetimehd/
$ cd ../facetimehd/
$ wget https://raw.githubusercontent.com/MegaManSec/webcam-aports/refs/heads/main/facetimehd/0001-remove-device-on-shutdown.patch
$ wget https://raw.githubusercontent.com/MegaManSec/webcam-aports/refs/heads/main/facetimehd/APKBUILD
$ abuild -r
$ mkdir ../ffmpeg/
$ cd ../ffmpeg/
$ wget https://raw.githubusercontent.com/MegaManSec/webcam-aports/refs/heads/main/ffmpeg/APKBUILD
$ abuild -r
```

### install build packages

---

Now we need to install the packages we've just build.

```console
$ cd ~/packages/aports/x86_64/
$ doas apk add *.apk
```

### enable facetimehd driver

---

Now load the `facetimehd` driver and confirm it working using `dmesg`:

```console
$ modprobe facetimehd
$ dmesg
```

`dmesg` should print something along the lines of:

```
[    1.323399] videodev: Linux video capture interface: v2.00
[    1.378323] facetimehd: loading out-of-tree module taints kernel.
[    1.378330] facetimehd: module verification failed: signature and/or required key missing - tainting kernel
[    1.379735] facetimehd 0000:00:07.0: Found FaceTime HD camera with device id: 1570
[    1.380493] facetimehd 0000:00:07.0: Setting 64bit DMA mask
[    1.420654] facetimehd 0000:00:07.0: S2 PCIe link init succeeded
[    1.420886] facetimehd 0000:00:07.0: Refclk: 25MHz (0xa)
[    1.430953] facetimehd 0000:00:07.0: PLL reset finished
[    1.430954] facetimehd 0000:00:07.0: Waiting for S2 PLL to lock at 450 MHz
[    1.430974] facetimehd 0000:00:07.0: S2 PLL is locked after 10 us
[    1.441026] facetimehd 0000:00:07.0: S2 PLL is in bypass mode
[    1.461203] facetimehd 0000:00:07.0: DDR40 PHY PLL locked on safe settings
[    1.461290] facetimehd 0000:00:07.0: STRAP valid
[    1.461290] facetimehd 0000:00:07.0: Configuring DDR PLLs for 450 MHz
[    1.461344] facetimehd 0000:00:07.0: DDR40 PLL is locked after 0 us
[    1.461380] facetimehd 0000:00:07.0: First DDR40 VDL calibration completed after 3 us
[    1.461411] facetimehd 0000:00:07.0: Second DDR40 VDL calibration completed after 0 us
[    1.461411] facetimehd 0000:00:07.0: Using step size 147
[    1.461433] facetimehd 0000:00:07.0: VDL set to: coarse=0x10008, fine=0x1011a
[    1.461462] facetimehd 0000:00:07.0: Virtual VTT enabled
[    1.482090] facetimehd 0000:00:07.0: S2 DRAM memory address: 0x22159559
[    1.482201] facetimehd 0000:00:07.0: Rewrite DDR mode registers succeeded
[    1.482423] facetimehd 0000:00:07.0: Full memory verification succeeded! (0)
[    1.604916] facetimehd 0000:00:07.0: Loaded firmware, size: 1392kb
[    1.604960] facetimehd 0000:00:07.0: Failed to get S2 CMPE ACPI handle
[    1.645712] facetimehd 0000:00:07.0: ISP woke up after 0ms
[    1.645741] facetimehd 0000:00:07.0: Number of IPC channels: 7, queue size: 44865
[    1.645782] facetimehd 0000:00:07.0: Firmware requested heap size: 3072kb
[    1.655886] facetimehd 0000:00:07.0: ISP second int after 0ms
[    1.655889] facetimehd 0000:00:07.0: Channel description table at 00800000
[    1.666174] facetimehd 0000:00:07.0: magic value: 00000000 after 0 ms
[    1.666176] facetimehd 0000:00:07.0: Enabling interrupts
[    1.666663] FWMSG: 
[    1.666721] FWMSG: - APOLLO-ISP-APPLE ------------------------------------------------------------
[    1.666755] FWMSG: 
[    1.666793] FWMSG:   Restart count : 0
[    1.666845] FWMSG:   Platform : mode = TARGET, ID = 0x00000000, HW = 00020018.00000000
[    1.666968] FWMSG:   System Clock : 200000000 Hz
[    1.667010] FWMSG:   Processor mode : SUPERVISOR
[    1.667039] FWMSG:   Cache architecture type : SEPARATE
[    1.667080] FWMSG:   Cache type : WRITEBACK
[    1.667107] FWMSG:   Data Cache Line : 32 [0x20]
[    1.667148] FWMSG:   Boot arguments entries : 2
[    1.667189] FWMSG:     0000: 0x00000000 0x00000000
[    1.667224] FWMSG:   Physical memory base : 0x00000000 [TLB base 0x00160000]
[    1.667252] FWMSG:   Main memory :   base : 0x00000000
[    1.667302] FWMSG:                   size : 8388608 [0x00800000] [8.0 MB]
[    1.667353] FWMSG:   Extra heap :    base : 0x2080b000 [phy = 0x0080b000]
[    1.667403] FWMSG:                   size : 3145728 [0x00300000] [3.0 MB]
[    1.667452] FWMSG:   Shared window : base : 0x00800000 [static wiring]
[    1.667489] FWMSG:                   size : 125829120 [0x07800000] [120.0 MB]
[    1.667532] FWMSG:   Shared memory : base : 0x00800000
[    1.667568] FWMSG:                   size : 260046848 [0x0f800000] [248.0 MB]
[    1.667607] FWMSG:   TEXT : 1421992 [0x15b2a8] - text 667256, cstring  38749, const 715528
[    1.667661] FWMSG:   DATA : 8076 [0x1f8c] - data 0, bss 460, common 1452, noinit 6144
[    1.667707] FWMSG:   Heap free space : 10002626 [0x0098a0c2]
[    1.667738] FWMSG:   Heap allocated space : 94656 [0x000171c0]
[    1.667774] FWMSG:   Disclaimer : Copyright (c) APPLE Inc. All Rights Reserved.
[    1.667801] FWMSG:   Application : adc [release]
[    1.667845] FWMSG:   Linked on : Jul 25 2015 - 08:48:55
[    1.667872] FWMSG:   Release : S2ISP-01.43.00
[    1.667963] FWMSG:   H4ISPAPPLE : 11536
[    1.668080] FWMSG:   H4ISPCD : 4081
[    1.668118] FWMSG:   ffw : 4143
[    1.668186] FWMSG:   Tool-chain : iPhone OS - 7.0.3 [clang/clang++]
[    1.668220] FWMSG: 
[    1.668275] FWMSG: -------------------------------------------------------------------------------
[    1.668309] FWMSG: 
[    1.742321] FWMSG: [ISP] CMD = 0x0004 [CISP_CMD_PRINT_ENABLE]
[    1.742669] FWMSG: [ISP] CMD = 0x0003 [CISP_CMD_CONFIG_GET]
[    1.743046] FWMSG: [ISP] CH = 0 CMD = 0x010d [CISP_CMD_CH_INFO_GET]
[    1.743182] facetimehd 0000:00:07.0: Direct firmware load for facetimehd/1871_01XX.dat failed with error -2
```

### camera device information

---

We can also use `v4l2-ctl` from the `v4l-utils-libs` package we installed to list information about the camera:

```console
localhost:~# v4l2-ctl --list-formats-ext
ioctl: VIDIOC_ENUM_FMT
	Type: Video Capture

	[0]: 'YUYV' (YUYV 4:2:2)
		Size: Discrete 1280x720
			Interval: Discrete 0.033s (30.000 fps)
	[1]: 'YVYU' (YVYU 4:2:2)
		Size: Discrete 1280x720
			Interval: Discrete 0.033s (30.000 fps)
localhost:~# v4l2-ctl --device=/dev/video0 --get-parm
Streaming Parameters Video Capture:
	Capabilities     : timeperframe
	Frames per second: 25.000 (1000/40)
	Read buffers     : 4
localhost:~# v4l2-ctl --device=/dev/video0 --all
Driver Info:
	Driver name      : facetimehd
	Card type        : Apple Facetime HD
	Bus info         : PCI:0000:00:07.0
	Driver version   : 6.6.52
	Capabilities     : 0x85200001
		Video Capture
		Read/Write
		Streaming
		Extended Pix Format
		Device Capabilities
	Device Caps      : 0x05200001
		Video Capture
		Read/Write
		Streaming
		Extended Pix Format
Priority: 2
Video input : 0 (Camera: ok)
Format Video Capture:
	Width/Height      : 1280/720
	Pixel Format      : 'YUYV' (YUYV 4:2:2)
	Field             : None
	Bytes per Line    : 2560
	Size Image        : 1843200
	Colorspace        : sRGB
	Transfer Function : Default (maps to sRGB)
	YCbCr/HSV Encoding: Default (maps to ITU-R 601)
	Quantization      : Default (maps to Limited Range)
	Flags             : 
Streaming Parameters Video Capture:
	Capabilities     : timeperframe
	Frames per second: 25.000 (1000/40)
	Read buffers     : 4

User Controls

                     brightness 0x00980900 (int)    : min=0 max=255 step=1 default=128 value=128 flags=slider
                       contrast 0x00980901 (int)    : min=0 max=255 step=1 default=128 value=128 flags=slider
                     saturation 0x00980902 (int)    : min=0 max=255 step=1 default=128 value=128 flags=slider
                            hue 0x00980903 (int)    : min=0 max=255 step=1 default=128 value=128 flags=slider
        white_balance_automatic 0x0098090c (bool)   : default=1 value=1
```

### troubleshooting

---

It's possible that the device cannot be activated for some reason, especially with an error message like:

```
[   12.027408] facetimehd 0000:04:00.0: Init failed! No wake signal
[   12.027873] facetimehd: probe of 0000:04:00.0 failed with error -5
```

This error message seems to stem from the same issue [I have previously debugged in my Macbook's BCM43602 WiFi chip](https://joshua.hu/brcmfmac-bcm43602-suspension-shutdown-hanging-freeze-linux-freebsd-wifi-bug-pci-passthru). Try rebooting.

## Webcam-over-Network

---

### inside the VM

---

At this stage, we can interact with the webcam inside the VM. Now, we want to expose it on the network so our FreeBSD host can use it.

I use this command:

```bash
while true; do
	socat TCP-LISTEN:8888,reuseaddr EXEC:"ffmpeg -hide_banner -s 1280x720 -r 25 -i /dev/video0 -vcodec rawvideo -pix_fmt yuv420p -f matroska -"
	sleep 1
done
```

The idea here is that `socat` will listen on port 8888, and once a connection is made, it will execute `ffmpeg` and connect to the webcam. It will then send the feed over port 8888 in matroska format to whoever is connecting.

You can use either `yuv420p` or `yuyv422` for the `pix_fmt`. I can't see any difference between the two, but the former uses fewer cycles.

You can lower the CPU usage by playing around with the `-s` and `-r` parameters.


### freebsd host

---

#### install and enable webcamd and cuse

---

On the FreeBSD host, you must install and enable `webcamd` as well as `cuse`:

```console
$ pkg install webcamd
$ sysrc webcamd_enable=YES
$ echo 'cuse_load="YES"' >> /boot/loader.conf
```

You can also just run:

```console
$ kldload cuse
$ service webcamd onestart
```

#### v4l2loopback device with webcamd

---

Now we need to create a video4linux device:

```console
$ webcamd -c v4l2loopback
```

#### connect to vm and pipe data to device

---

Finally, we need to connect to the VM on port 8888 and simply pipe the data received into `ffmpeg`, which will write the data to `/dev/video` -- the device created by `webcamd`:

```console
$ nc -N -n --no-tcpopt 192.168.8.2 8888 | ffmpeg -hide_banner -r 25 -i pipe: -f v4l2 /dev/video0
```

#### looking in the mirror

---

We can use the `pwcview` program to view the website (or any other way, like Firefox):

```console
$ pwcview -y -f 25
```

## Sensor calibration

---

When you load the `facetimehd` driver, you will see the following warning (it is not an error):

```
[    1.743182] facetimehd 0000:00:07.0: Direct firmware load for facetimehd/1871_01XX.dat failed with error -2
```

You may also note that the camera's colors are messed up.

From [the wiki](https://github.com/patjak/facetimehd/wiki/Extracting-the-sensor-calibration-files) of the driver, we can retrieve this file. The author of that post noted that "_when using the set files (sensor calibration settings) the colors look much better._"

Instructions for manually performing those actions can be found on the wiki above. Alternatively, you can (from the VM):

```console
$ su packager
$ mkdir ~/aports/facetimehd-calibration/
$ cd ~/aports/facetimehd-calibration/
$ wget https://raw.githubusercontent.com/MegaManSec/webcam-aports/refs/heads/main/facetimehd-calibration/APKBUILD
$ abuild -r
$ doas apk add ~/packages/aports/x86_64/facetimehd-calibration-1.0.0-r0.apk
```

Reloading the `facetimehd` driver, the warning should no longer be displayed, and the colors of your website will be.. more correct:

```console
$ rmmod facetimehd
$ modprobe facetimehd
```

# The Future

---

The setup outlined in this post was heavily inspired by [wifibox](https://github.com/pgj/freebsd-wifibox). In the longterm, I would like to create something that mimicks wifibox: a mini read-only VM which automatically handles everything outlined in this post, which runs as a service on the FreeBSD host. Likewise, since wifibox already runs a mini VM for WiFi, I would like to just simply add my `facetimehd` packages into that, since there's no need to run two Alpine VMs at the same time.

But that's for the future.
