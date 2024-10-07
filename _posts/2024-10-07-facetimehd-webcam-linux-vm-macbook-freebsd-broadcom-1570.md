---
layout: post
title: "Webcam support on a Macbook running FreeBSD using PCI passthrough"
author: "Joshua Rogers"
categories: journal
---

## Introduction

---

In my previous post, _[A Full Guide: FreeBSD 13.3 on a MacBook Pro 11.4 (Mid 2015) (A1398)](https://joshua.hu/FreeBSD-on-MacbookPro-114-A1398)_, I outlined how to get nearly every device on a Macbook Pro 11,4 functioning while running FreeBSD. Nearly everything: except for the webcam.

In this post, I'll outline how to get the camera working on FreeBSD, by using a tiny Alpine Linux VM using FreeBSD's hypervisor bhyve, and PCI passthrough.

At the end of this post, you'll have a working webcam. In the following screenshot, you see me running `webcamd` on the FreeBSD host, `ffmpeg` and `socat` in the Alpine Linux VM, `ffmpeg` and `nc` on the FreeBSD host, and `pwcview` on the FreeBSD host:

![Selfie using a Macbook Pro webcam on FreeBSD](/files/freebsd-selfie.png)

## Broadcom 1570

The Broadcom 1570 (the webcam used by this and many other Mac products) is apparently "_[based on Ambarellas S2 series of IP cameras; likely a nerfed version of the S2Lm.]_(https://github.com/patjak/facetimehd/wiki/Specification---Features)". The camera can be turned on [without activating the green light](https://www.usenix.org/system/files/conference/usenixsecurity14/sec14-paper-brocker.pdf).

Broadcom does not offer any driver for this device, but luckily it has been reverse-engineered by someone and a driver exists for Linux.

## PCI Passthrough and Alpine Linux

In order to utilize the Linux driver, we obviously need to be running... Linux. So, the plan is to start a tiny VM running Alpine Linux, install the `facetimehd` driver, and stream the webcam back to the FreeBSD host, ultimately using `webcamd` to turn the stream into a webcam device.

![Diagram of process for using facetimehd on FreeBSD](/files/webcam-diagram.png)




Improving the colors is outlined in [this wiki page](https://github.com/patjak/facetimehd/wiki/Extracting-the-sensor-calibration-files).


