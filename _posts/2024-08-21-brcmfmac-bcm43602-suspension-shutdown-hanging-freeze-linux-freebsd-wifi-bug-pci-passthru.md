---
layout: post
title: "BCM43602: Debugging a Wifi chipset causing a whole-system hang with FreeBSD's bhyve VM"
author: "Joshua Rogers"
categories: journal
---

Over the past month or so, I've been investigating the BCM43602 chip, and its ability to: 1. work on freebsd using wifibox, 2. suspend with acpi's s3/suspend-to-ram.

As it stands, when starting the wifibox service, a bhyve VM is created with Alpine Linux, and PCI passthrough is used to proxy the BCM43602 chip to the VM. When the service and VM starts, the following debugging messages can be observed:

```
Starting wifibox...
bridge0: bpf attached
bridge0: Ethernet address: 58:9c:fc:10:ff:c9
bridge0: changing name to 'wifibox0'
tap0: bpf attached
tap0: Ethernet address: 58:9c:fc:10:ff:d0
tap0: promiscuous mode enabled
wifibox0: link state changed to DOWN
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0  
ppt0: using IRQ 45 for MSI ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
ppt0 mem 0xa0800000-0xa0807fff,0xa0400000-0xa07fffff at device 0.0 on pci3
ppt0: attached
tap0: link state changed to UP
wifibox0: link state changed to UP
pci0:3:0:0: Transition from D0 to D3
pci3: set ACPI power state D3 on \134_SB_.PCI0.RP03.ARPT
pci3: set ACPI power state D0 on \134_SB_.PCI0.RP03.ARPT
..done
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 2 vector 51
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 4 vector 52
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
```

`vendor=0x14e4, dev=0x43ba, revid=0x01` aka `pci0:3:0:0` aka `pci3` is the BCM chip.

The VM can successfully connect to the chip and wifi works.

When it comes to suspend/resume however, things start to go awry. I have observed the following behavior:

1. With wifibox is running and the system is suspended, it will not wakeup/resume -- even with `debug.acpi.suspend_bounce=1`.
2. Similarly, when wifibox is started and then stopped, the system will not wake up following a suspend.
3. When wifibox is started/stopped and the vmm module is unloaded, the system will not even suspend -- it completely freezes. The final message in syslog/console is: `acpi_timer0: switching timecounter, TSC-low -> ACPI-fast`.
4. I can start and stop wifibox as many times as needed: the problem is when I unload vmm / suspend.

After some debugging, I discovered that I can freeze the system on-demand by: starting/stopping wifibox, and then attempting to read from the pci device, for example by using `pciconf -lvc`. Wifibox, by default, clears the pci forcefully-set driver using `devctl clear driver -f ppt0`. After wifibox is finished shutting down, manually running `pciconf -lc pci0:3:0:0` will list the device as with no capabilities (note: I removed the `clear driver` invocation from the wifibox shutdown script and have manually run it to demonstrate the output):
```
Stopping wifibox...
tap0: link state changed to DOWN
wifibox0: link state changed to DOWN
pci0:3:0:0: Transition from D0 to D3
pci3: set ACPI power state D3 on \134_SB_.PCI0.RP03.ARPT
pci3: set ACPI power state D0 on \134_SB_.PCI0.RP03.ARPT
tap0: promiscuous mode disabled
..done
$ devctl clear driver -f ppt0
ppt0: detached
pci3: <network> at device 0.0 (no driver attached)
devctl: Failed to clear ppt0 driver: Device not configured
$ kldunload vmm if_bridge
$ pciconf -lvc pci0:3:0:0
none0@pci0:3:0:0:       class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
$
```

 Running the `pciconf -lvc` command again will cause a total system freeze. __Before__ the `clear driver` command is run, pciconf returns the following:
```
ppt0@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
    cap 01[48] = powerspec 3  supports D0 D1 D2 D3  current D0
    cap 05[58] = MSI supports 16 messages, 64 bit enabled with 1 message
    cap 09[68] = vendor (length 68)
    cap 10[ac] = PCI-Express 2 endpoint max data 128(256) RO NS
                 max read 1024
                 link x1(x1) speed 2.5(2.5) ASPM L0s/L1(L0s/L1) ClockPM enabled
    ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
    ecap 0003[13c] = Serial 1 b2cfcfffffdd6c96
    ecap 0004[150] = Power Budgeting 1
    ecap 0002[160] = VC 1 max VC0
    ecap 0018[1b0] = LTR 1
    ecap 0015[220] = Resizable BAR 1
    ecap 001e[240] = L1 PM Substates 1
```

The `pciconf` source code shows that the system crash occurs exactly when `ioctl(fd, PCIOCREAD, &pi)` is called the second time. 

Similarly, if `clear driver` is not executed and instead the `vmm` module is unloaded forcefully, `pciconf -lvc` does does display the full capabilities the first time it is executed, but on the second execution, causes a system freeze. In fact, after the vmm module is unloaded, every operation on the pci device causes the system to freeze (particularly every operation supported by `devctl`).

None of the sysctls worked, either:

```
hw.acpi.disable_on_poweroff
hw.pci.allow_unsupported_io_range
hw.pci.clear_bars
hw.pci.clear_buses
hw.pci.clear_pci
hw.pci.clear_pcib
hw.pci.do_power_resume
hw.pci.do_power_suspend
hw.pci.enable_aspm
hw.pci.enable_msi
hw.pci.enable_msix
hw.pci.pci_enable_pcie_e
hw.pci.pci_enable_pcie_hp
hw.pci.realloc_bars
hw.pci_do_power_nodriver
hw.usb.no_suspend_wait
```


So I took a different approach. As it turns out, it _is_ possible to reset `pci3`, but in a slightly different sequence. We first need to disable the `pcib4` bridge which bridges the `pci3` adapter. With the modified wifibox script which does __not__ run `clear driver`:

1. `service wifibox onestart`
2. `service wifibox onestop`
3. `kldunload vmm if_bridge`
4. `devctl disable -f pcib4` -- disable the pcib4 adapter.
5. `acpiconf -s 3 ` -- Suspend. Then resume.
6. `devctl enable pcib4`
7. `service wifibox onestart`

The output of running this can be seen below. Note that I have added some debugging messages into FreeBSD's pci kernel module.
```
$ service wifibox onestop
Stopping wifibox....pcib4: Josh: pcib_release_resource
...OK
$ devctl disable -f pcib4
pcib4: Josh: calling bus_generic_detach()
pci3: Josh: calling bus_generic_detach()
ppt0: detached
pcib4: Josh: pcib_release_resource
pcib4: Josh: pcib_release_resource
pcib4: Josh: pcib_release_resource
pci3: detached
pcib4: detached
$ kldunload vmm if_bridge
$ acpiconf -s 3
$ devctl enable pcib4
pcib4: Josh: pcib_probe
pcib4: <ACPI PCI-PCI bridge> at device 28.2 on pci0
pcib4: Josh: pcib_attach_common
pcib4: Josh: pcib_setup_secbus
pcib4: Josh: pcib_probe_windows
pcib4: failed to allocate initial I/O port window: 0-0xfff
pcib4: failed to allocate initial memory window: 0-0xfffff
pcib4: failed to allocate initial prefetch window: 0-0xfffff
pcib4:   domain            0
pcib4:   secondary bus     3
pcib4:   subordinate bus   3
pci3: <ACPI PCI bus> on pcib4
pcib4: Josh: pcib_read_ivar
pcib4: Josh: pcib_read_ivar
pcib4: Josh: pcib_alloc_resource
pci3: Josh: pcib_alloc_subbus
pcib4: allocated bus range (3-3) for rid 0 of pci3
pci3: domain=0, physical bus=3  
pcib4: Josh: pcib_read_ivar
pcib4: Josh: pcib_read_ivar
found-> vendor=0x14e4, dev=0x43ba, revid=0x01
        domain=0, bus=3, slot=0, func=0
        class=02-80-00, hdrtype=0x00, mfdev=0
        cmdreg=0x0000, statreg=0x0010, cachelnsz=0 (dwords)
        lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
        intpin=a, irq=255
        MSI supports 16 messages, 64 bit
        map[10]: type Memory, range 64, base 0, size 15, memory disabled
        map[18]: type Memory, range 64, base 0, size 22, memory disabled
pcib6: Josh: pcib_probe
pci3: <network> at device 0.0 (no driver attached)
$ service wifibox onestart
bridge0: bpf attached
bridge0: Ethernet address: 58:9c:fc:10:ff:c9
bridge0: changing name to 'wifibox0'
tap0: bpf attached
tap0: Ethernet address: 58:9c:fc:10:ff:d0
tap0: promiscuous mode enabled
wifibox0: link state changed to DOWN
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0000, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0000, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0A
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
ppt0 at device 0.0 on pci3
ppt0: attached
tap0: link state changed to UP
wifibox0: link state changed to UP
pci0:3:0:0: Transition from D0 to D3
pci3: set ACPI power state D3 on \134_SB_.PCI0.RP03.ARPT
pci3: set ACPI power state D0 on \134_SB_.PCI0.RP03.ARPT
..done
$ pciconf -lvc pci0:3:0:0
none2@pci0:3:0:0:        class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0133
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
    cap 01[48] = powerspec 3  supports D0 D1 D2 D3  current D0
    cap 05[58] = MSI supports 16 messages, 64 bit
    cap 09[68] = vendor (length 68)
    cap 10[ac] = PCI-Express 2 endpoint max data 128(256) RO NS
                 max read 512
                 link x1(x1) speed 2.5(2.5) ASPM L0s/L1(L0s/L1) ClockPM enabled
    ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
    ecap 0003[13c] = Serial 1 b2cfcfffffdd6c96
    ecap 0004[150] = Power Budgeting 1
    ecap 0002[160] = VC 1 max VC0
    ecap 0018[1b0] = LTR 1
    ecap 0015[220] = Resizable BAR 1
    ecap 001e[240] = L1 PM Substates 1
```

Of note is some differences in the "found->" line. The original:
```
cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
map[10]: type Memory, range 64, base 0xa0800000, size 15, enabled
map[18]: type Memory, range 64, base 0xa0400000, size 22, enable
```

and the new output after suspend/resume:
```
cmdreg=0x0000, statreg=0x0010, cachelnsz=0 (dwords)
map[10]: type Memory, range 64, base 0, size 15, memory disabled
map[18]: type Memory, range 64, base 0, size 22, memory disabled
```

Obviously also, the following new information is interesting:

```
pcib4: failed to allocate initial I/O port window: 0-0xfff
pcib4: failed to allocate initial memory window: 0-0xfffff
pcib4: failed to allocate initial prefetch window: 0-0xfffff
```

Likewise, the `pciconf` output is different:
```
1c1
< ppt0@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
---
> ppt0@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0133
6c6
<     cap 05[58] = MSI supports 16 messages, 64 bit enabled with 1 message
---
>     cap 05[58] = MSI supports 16 messages, 64 bit 
9c9
<                  max read 1024
---
>                  max read 512
11c11
<     ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
---
>     ecap 0001[100] = AER 1 0 fatal 0 non-fatal 0 corrected
```
A different subdevice id and maxread? That's strange.

(While writing this report, I discovered that others noted these strange changes, too. For example, In this [QubesOS report](https://github.com/QubesOS/qubes-issues/issues/3734#issuecomment-583552765), it's noted that _"the BCM43602 adapter's subsystem changes the device number from 0x0173 to 0x0157"_.)

Also of particular note is that when we restart wifibox the second time, the following debugging messages do __not__ appear:

```
ppt0: attempting to allocate 1 MSI vectors (16 supported)  
msi: routing MSI IRQ 45 to local APIC 6 vector 50  
ppt0: using IRQ 45 for MSI  
ppt0: attempting to allocate 1 MSI vectors (16 supported)  
msi: routing MSI IRQ 45 to local APIC 0 vector 53  
ppt0: using IRQ 45 for MSI  
ppt0: attempting to allocate 1 MSI vectors (16 supported)  
msi: routing MSI IRQ 45 to local APIC 2 vector 51  
ppt0: using IRQ 45 for MSI  
ppt0: attempting to allocate 1 MSI vectors (16 supported)  
msi: routing MSI IRQ 45 to local APIC 4 vector 52  
ppt0: using IRQ 45 for MSI  
ppt0: attempting to allocate 1 MSI vectors (16 supported)  
msi: routing MSI IRQ 45 to local APIC 6 vector 50  
ppt0: using IRQ 45 for MSI
```

Although wifibox started and there seems to be _some_ activity in the pci buses, the VM cannot succesfully probe and attach to the chip. The dmesg output reveals:
```
[    0.888052] brcmfmac: brcmf_chip_recognition: SB chip is not supported
[    0.888055] brcmfmac: brcmf_pcie_probe: failed 14e4:43ba
```

So upon suspension/resume, the Linux kernel module no longer recognizes the chip -- That's probably because of the subdevice id changing: in the VM, `/sys/devices/pci0000:00/0000:00:06.0/subsystem_device` still contains the old `0x0152`.  Anyways, [this Linux bug report](https://bugzilla.kernel.org/show_bug.cgi?id=196019#c5) notes that "This suggests the read32 (which maps to ioread32) returned all ones (0xffffffff), which may suggest power is gated to part of the device."

No matter the amount of resets, suspends, deletes, and so on, of `pcib3` and `pcib4`, the chip remains unrecognized and maintains that changed subdevice id. I eventually moved on to a new thought: can I release or powerdown the chip directly from the VM?

As it turns out, yes: by removing the pci device from the VM, "everything works as expected"__™__. I figured this out while writing this text: [rubber duck debugging](https://en.wikipedia.org/wiki/Rubber_duck_debugging) ftw.

---

First we start wifibox. No surprises or changes from the other invocations:

```
$ service wifibox onestart
bridge0: bpf attached
bridge0: Ethernet address: 58:9c:fc:10:ff:c9
bridge0: changing name to 'wifibox0'
tap0: bpf attached
tap0: Ethernet address: 58:9c:fc:10:ff:d0
tap0: promiscuous mode enabled
wifibox0: link state changed to DOWN
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
pci0: driver added
found->	vendor=0x8086, dev=0x8c3a, revid=0x04
	domain=0, bus=0, slot=22, func=0
	class=07-80-00, hdrtype=0x00, mfdev=1
	cmdreg=0x0006, statreg=0x0010, cachelnsz=0 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D3  current D0
	MSI supports 1 message, 64 bit
pci0:0:22:0: reprobing on driver added
pci1: driver added
pci2: driver added
pci3: driver added
found->	vendor=0x14e4, dev=0x43ba, revid=0x01
	domain=0, bus=3, slot=0, func=0
	class=02-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D2 D3  current D0
	MSI supports 16 messages, 64 bit
pci0:3:0:0: reprobing on driver added
pci4: driver added
found->	vendor=0x14e4, dev=0x1570, revid=0x00
	domain=0, bus=4, slot=0, func=0
	class=04-80-00, hdrtype=0x00, mfdev=0
	cmdreg=0x0006, statreg=0x0010, cachelnsz=64 (dwords)
	lattimer=0x00 (0 ns), mingnt=0x00 (0 ns), maxlat=0x00 (0 ns)
	intpin=a, irq=255
	powerspec 3  supports D0 D1 D3  current D0
	MSI supports 1 message, 64 bit
pci0:4:0:0: reprobing on driver added
ppt0 mem 0xa0800000-0xa0807fff,0xa0400000-0xa07fffff at device 0.0 on pci3
ppt0: attached
tap0: link state changed to UP
wifibox0: link state changed to UP
pci0:3:0:0: Transition from D0 to D3
pci3: set ACPI power state D3 on \134_SB_.PCI0.RP03.ARPT
pci3: set ACPI power state D0 on \134_SB_.PCI0.RP03.ARPT
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 2 vector 51
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 4 vector 52
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
```

Then we connect to the VM and "remove" the device:
```
$ wifibox console
Connecting, type "~." to leave the session...
Connected
root
wifibox:~# echo 1 > /sys/devices/pci0000:00/0000:00:06.0/remove
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 2 vector 51
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 4 vector 52
ppt0: using IRQ 45 for MSI
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
wifibox:~# ~.
[EOT]
```

As we see here, as soon as we "remove" the device, those msi lines which were missing before have appeared.

Then we stop wifibox and unload vmm (and if_bridge):

```
$ sudo service wifibox onestop
Stopping wifibox....pci0:3:0:0: Transition from D0 to D3
pci3: set ACPI power state D3 on \_SB_.PCI0.RP03.ARPT
pci3: set ACPI power state D0 on \_SB_.PCI0.RP03.ARPT
...OK
$ sudo kldunload vmm if_bridge
ppt0: detached
pci3: <network> at device 0.0 (no driver attached)
```

Despite the `vmm` module being unloaded, the `ppt0` driver on the `pci3` device is still being used (which doesn't matter):
```
ppt0@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
    cap 01[48] = powerspec 3  supports D0 D1 D2 D3  current D0
    cap 05[58] = MSI supports 16 messages, 64 bit 
    cap 09[68] = vendor (length 68)
    cap 10[ac] = PCI-Express 2 endpoint max data 128(256) RO NS
                 max read 1024
                 link x1(x1) speed 2.5(2.5) ASPM L0s/L1(L0s/L1) ClockPM enabled
    ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
    ecap 0003[13c] = Serial 1 b2cfcfffffdd6c96
    ecap 0004[150] = Power Budgeting 1
    ecap 0002[160] = VC 1 max VC0
    ecap 0018[1b0] = LTR 1
    ecap 0015[220] = Resizable BAR 1
    ecap 001e[240] = L1 PM Substates 1
```

(Note: we can optionally clear the driver using `devctl clear driver -f pci0:3:0:0` after wifibox stops, but it doesn't seem to matter at all.)

Suspending the machine from here works, as does resuming. This is the output when starting after a suspension/resume, as well as another echo (this time with some extra debugging):

```
$ service wifibox onestart
user@evilco:~$ ppt0 mem 0xa0800000-0xa0807fff,0xa0400000-0xa07fffff at device 0.0 on pci3
ppt0: attached
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
pcib0: Josh: pcib_get_id
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 2 vector 51
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 4 vector 52
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource

wifibox:~# echo 1 > /sys/devices/pci0000:00/0000:00:06.0/remove
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 0 vector 53
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 2 vector 51
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 4 vector 52
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
ppt0: attempting to allocate 1 MSI vectors (16 supported)
msi: routing MSI IRQ 45 to local APIC 6 vector 50
ppt0: using IRQ 45 for MSI
pcib4: Josh: pcib_alloc_resource
pcib4: Josh: pcib_release_resource
```

When resuming, the `pci3` device is still attached to `ppt0` (if you don't clear it). Starting wifibox again, it successfully connects to the chip. Happy days.

Using the following sequence of operations, suspend/resume completely works with wifibox:

1. Start wifibox
2. `echo 1 > /sys/devices/pci0000:00/0000:00:06.0/remove` in the VM
3. Stop wifibox
4. `kldunload vmm if_bridge`
5. suspend
6. Start wifibox
7. ...etc...

---

Now comes the difficult part: where is the actual issue here located?

According to the Linux documentation, [pci remove "does not involve any kind of hot-plug functionality"](https://www.kernel.org/doc/Documentation/filesystems/sysfs-pci.txt), "e.g. powering off the device". So "removing" the device doesn't power off the device. But what _does_ it does, especially to invoke those "ppt0: attempting to allocate 1 MSI vectors (16 supported)" messages that are present?

In [drivers/pci/remove.c](https://github.com/torvalds/linux/blob/6e4436539ae182dc86d57d13849862bcafaa4709/drivers/pci/remove.c#L117), `pci_stop_and_remove_bus_device` calls `pci_stop_bus_device` and `pci_remove_bus_device`.

`pci_stop_bus_device` is as follows:
```C
	pci_pme_active(dev, false);

	if (pci_dev_is_added(dev)) {
		of_platform_depopulate(&dev->dev);
		device_release_driver(&dev->dev);
		pci_proc_detach_device(dev);
		pci_remove_sysfs_dev_files(dev);
		of_pci_remove_node(dev);

		pci_dev_assign_added(dev, false);
	}
```

`pci_pme_active` looks promising, but [PME (see this link for an explanation of PME in a nutshell as well as ACPI sleep ](https://www.eetimes.com/pme-signal-is-a-pitfall-for-pci-designers-implementing-acpi/) is already disabled by default for all the devices on this system, according to `PCIM_PSTAT_PME`. So that's a no-op.

Anyways, [brcmf_pcie_remove()](https://github.com/torvalds/linux/blob/master/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c#L2527) is eventually called when the PCI device is being removed, and the following important actions are taken (with some pseudocode added):

```C
	brcmf_pcie_write_reg32(devinfo, devinfo->reginfo->mailboxmask, 0);

	free_irq(pdev->irq, devinfo);
	pci_disable_msi(pdev);

	brcmf_pcie_reset_device(devinfo); // Disables ASPM, resets the watchdog, enables ASPM, and then does some weird thing where it reads the config for various configuration registers, then re-sets them.
	pci_disable_bus_mastering(devinfo->pdev);
```

Which of these is necessary for the device to work after the system is shut down? I'm not sure. I don't currently have any way of debugging Linux, as I'm traveling. Otherwise, I would just build a custom kernel and test which are necessary. Within the current context, to make matters "worse", the VM doesn't call "remove" for devices when the system is halted, either. 

My solution here is to not debug further: it's to simply ensure that the device is removed before a shutdown. The patch for this extremely annoying bug is therefore:

```
diff --git a/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c b/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c
index ce482a3877e90a..865a2f25c8feb7 100644
--- a/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c
+++ b/drivers/net/wireless/broadcom/brcm80211/brcmfmac/pcie.c
@@ -2711,6 +2711,7 @@ static struct pci_driver brcmf_pciedrvr = {
 	.id_table = brcmf_pcie_devid_table,
 	.probe = brcmf_pcie_probe,
 	.remove = brcmf_pcie_remove,
+	.shutdown = brcmf_pcie_remove,
 #ifdef CONFIG_PM
 	.driver.pm = &brcmf_pciedrvr_pm,
 #endif
```

This fixes [QubesOS#3734](https://github.com/QubesOS/qubes-issues/issues/3734), [this Proxmox report](https://forum.proxmox.com/threads/bcm43602-passthrough-to-macos-vm-kernel-panic.115682/), [this other Hackintosh report](https://www.reddit.com/r/hackintosh/comments/c38u1l/problem_with_pci_passthrough_broadcom_wifi_card/), [this Redhat report](https://bugzilla.redhat.com/show_bug.cgi?format=multiple&id=1294415), and [possibly this Linux report](https://bugzilla.kernel.org/show_bug.cgi?id=100201), too.

The issue here may have been obvious for someone with more experience with drivers and these Broadcom chips, but at least I've learnt a lot about how drivers in FreeBSD work, and Linux.


---

For the sake of anybody searchin this device via their favorite search engine in the future, I include some dumps from `pciconf -lvc` and `devinfo -rv`:

```
hostb0@pci0:0:0:0:	class=0x060000 rev=0x08 hdr=0x00 vendor=0x8086 device=0x0d04 subvendor=0x106b subdevice=0x0147
    vendor     = 'Intel Corporation'
    device     = 'Crystal Well DRAM Controller'
    class      = bridge
    subclass   = HOST-PCI
    cap 09[e0] = vendor (length 12) Intel cap 0 version 1
pcib1@pci0:0:1:0:	class=0x060400 rev=0x08 hdr=0x01 vendor=0x8086 device=0x0d01 subvendor=0x106b subdevice=0x0147
    vendor     = 'Intel Corporation'
    device     = 'Crystal Well PCI Express x16 Controller'
    class      = bridge
    subclass   = PCI-PCI
    cap 0d[88] = PCI Bridge subvendor=0x106b subdevice=0x0147
    cap 01[80] = powerspec 3  supports D0 D3  current D0
    cap 05[90] = MSI supports 1 message 
    cap 10[a0] = PCI-Express 2 root port max data 128(256)
                 max read 128
                 link x4(x8) speed 8.0(8.0) ASPM L1(L0s/L1)
                 slot 1 power limit 75000 mW
    ecap 0002[100] = VC 1 max VC0
    ecap 0005[140] = Root Complex Link Declaration 1
    ecap 0019[d94] = PCIe Sec 1 lane errors 0
pcib2@pci0:0:1:1:	class=0x060400 rev=0x08 hdr=0x01 vendor=0x8086 device=0x0d05 subvendor=0x106b subdevice=0x0147
    vendor     = 'Intel Corporation'
    device     = 'Crystal Well PCI Express x8 Controller'
    class      = bridge
    subclass   = PCI-PCI
    cap 0d[88] = PCI Bridge subvendor=0x106b subdevice=0x0147
    cap 01[80] = powerspec 3  supports D0 D3  current D0
    cap 05[90] = MSI supports 1 message 
    cap 10[a0] = PCI-Express 2 root port max data 128(128)
                 max read 128
                 link x4(x8) speed 2.5(5.0) ASPM disabled(L0s/L1)
                 slot 2 power limit 75000 mW
    ecap 0002[100] = VC 1 max VC0
    ecap 0005[140] = Root Complex Link Declaration 1
    ecap 0019[d94] = PCIe Sec 1 lane errors 0
vgapci0@pci0:0:2:0:	class=0x030000 rev=0x08 hdr=0x00 vendor=0x8086 device=0x0d26 subvendor=0x106b subdevice=0x0147
    vendor     = 'Intel Corporation'
    device     = 'Crystal Well Integrated Graphics Controller'
    class      = display
    subclass   = VGA
    cap 05[90] = MSI supports 1 message enabled with 1 message
    cap 01[d0] = powerspec 2  supports D0 D3  current D0
    cap 13[a4] = PCI Advanced Features: FLR TP
hdac0@pci0:0:3:0:	class=0x040300 rev=0x08 hdr=0x00 vendor=0x8086 device=0x0d0c subvendor=0x106b subdevice=0x0147
    vendor     = 'Intel Corporation'
    device     = 'Crystal Well HD Audio Controller'
    class      = multimedia
    subclass   = HDA
    cap 01[50] = powerspec 2  supports D0 D3  current D0
    cap 05[60] = MSI supports 1 message enabled with 1 message
    cap 10[70] = PCI-Express 1 root endpoint max data 128(128) FLR NS
                 max read 128
xhci0@pci0:0:20:0:	class=0x0c0330 rev=0x05 hdr=0x00 vendor=0x8086 device=0x8c31 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family USB xHCI'
    class      = serial bus
    subclass   = USB
    cap 01[70] = powerspec 2  supports D0 D3  current D0
    cap 05[80] = MSI supports 8 messages, 64 bit enabled with 1 message
none0@pci0:0:22:0:	class=0x078000 rev=0x04 hdr=0x00 vendor=0x8086 device=0x8c3a subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family MEI Controller'
    class      = simple comms
    cap 01[50] = powerspec 3  supports D0 D3  current D0
    cap 05[8c] = MSI supports 1 message, 64 bit 
hdac1@pci0:0:27:0:	class=0x040300 rev=0x05 hdr=0x00 vendor=0x8086 device=0x8c20 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset High Definition Audio Controller'
    class      = multimedia
    subclass   = HDA
    cap 01[50] = powerspec 2  supports D0 D3  current D0
    cap 05[60] = MSI supports 1 message, 64 bit enabled with 1 message
    cap 10[70] = PCI-Express 1 root endpoint max data 128(128) FLR
                 max read 128
    ecap 0002[100] = VC 1 max VC1
pcib3@pci0:0:28:0:	class=0x060400 rev=0xd5 hdr=0x01 vendor=0x8086 device=0x8c10 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family PCI Express Root Port'
    class      = bridge
    subclass   = PCI-PCI
    cap 10[40] = PCI-Express 2 root port max data 128(128)
                 max read 128
                 link x0(x1) speed 0.0(5.0) ASPM disabled(L0s/L1)
                 slot 0 power limit 0 mW HotPlug(empty) surprise
    cap 05[80] = MSI supports 1 message enabled with 1 message
    cap 0d[90] = PCI Bridge subvendor=0x8086 subdevice=0x7270
    cap 01[a0] = powerspec 3  supports D0 D3  current D0
pcib4@pci0:0:28:2:	class=0x060400 rev=0xd5 hdr=0x01 vendor=0x8086 device=0x8c14 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family PCI Express Root Port'
    class      = bridge
    subclass   = PCI-PCI
    cap 10[40] = PCI-Express 2 root port max data 128(128)
                 max read 128
                 link x1(x1) speed 2.5(5.0) ASPM L0s/L1(L0s/L1)
                 slot 2 power limit 100 mW
    cap 05[80] = MSI supports 1 message 
    cap 0d[90] = PCI Bridge subvendor=0x8086 subdevice=0x7270
    cap 01[a0] = powerspec 3  supports D0 D3  current D0
pcib5@pci0:0:28:3:	class=0x060400 rev=0xd5 hdr=0x01 vendor=0x8086 device=0x8c16 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family PCI Express Root Port'
    class      = bridge
    subclass   = PCI-PCI
    cap 10[40] = PCI-Express 2 root port max data 128(128)
                 max read 128
                 link x1(x1) speed 5.0(5.0) ASPM L1(L0s/L1)
                 slot 3 power limit 100 mW
    cap 05[80] = MSI supports 1 message 
    cap 0d[90] = PCI Bridge subvendor=0x8086 subdevice=0x7270
    cap 01[a0] = powerspec 3  supports D0 D3  current D0
isab0@pci0:0:31:0:	class=0x060100 rev=0x05 hdr=0x00 vendor=0x8086 device=0x8c4b subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = 'HM87 Express LPC Controller'
    class      = bridge
    subclass   = PCI-ISA
    cap 09[e0] = vendor (length 12) Intel cap 1 version 0
		 features: AMT, 4 PCI-e x1 slots
ichsmb0@pci0:0:31:3:	class=0x0c0500 rev=0x05 hdr=0x00 vendor=0x8086 device=0x8c22 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series/C220 Series Chipset Family SMBus Controller'
    class      = serial bus
    subclass   = SMBus
pchtherm0@pci0:0:31:6:	class=0x118000 rev=0x05 hdr=0x00 vendor=0x8086 device=0x8c24 subvendor=0x8086 subdevice=0x7270
    vendor     = 'Intel Corporation'
    device     = '8 Series Chipset Family Thermal Management Controller'
    class      = dasp
    cap 01[50] = powerspec 3  supports D0 D3  current D0
    cap 05[80] = MSI supports 1 message 
ahci0@pci0:1:0:0:	class=0x010601 rev=0x01 hdr=0x00 vendor=0x144d device=0xa801 subvendor=0x144d subdevice=0xa801
    vendor     = 'Samsung Electronics Co Ltd'
    device     = 'S4LN058A01[SSUBX] AHCI SSD Controller (Apple slot)'
    class      = mass storage
    subclass   = SATA
    cap 01[40] = powerspec 3  supports D0 D3  current D0
    cap 05[50] = MSI supports 8 messages, 64 bit enabled with 8 messages
    cap 10[70] = PCI-Express 2 endpoint max data 128(128) FLR RO NS
                 max read 512
                 link x4(x4) speed 8.0(8.0) ASPM L1(L1) ClockPM enabled
    ecap 0001[100] = AER 2 0 fatal 0 non-fatal 1 corrected
    ecap 0003[148] = Serial 1 0000000000000000
    ecap 0004[158] = Power Budgeting 1
    ecap 0019[168] = PCIe Sec 1 lane errors 0
    ecap 0018[188] = LTR 1
    ecap 001e[190] = L1 PM Substates 1
none1@pci0:3:0:0:	class=0x028000 rev=0x01 hdr=0x00 vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = 'BCM43602 802.11ac Wireless LAN SoC'
    class      = network
    cap 01[48] = powerspec 3  supports D0 D1 D2 D3  current D0
    cap 05[58] = MSI supports 16 messages, 64 bit 
    cap 09[68] = vendor (length 68)
    cap 10[ac] = PCI-Express 2 endpoint max data 128(256) RO NS
                 max read 1024
                 link x1(x1) speed 2.5(2.5) ASPM L0s/L1(L0s/L1) ClockPM enabled
    ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
    ecap 0003[13c] = Serial 1 b2cfcfffffdd6c96
    ecap 0004[150] = Power Budgeting 1
    ecap 0002[160] = VC 1 max VC0
    ecap 0018[1b0] = LTR 1
    ecap 0015[220] = Resizable BAR 1
    ecap 001e[240] = L1 PM Substates 1
none2@pci0:4:0:0:	class=0x048000 rev=0x00 hdr=0x00 vendor=0x14e4 device=0x1570 subvendor=0x14e4 subdevice=0x1570
    vendor     = 'Broadcom Inc. and subsidiaries'
    device     = '720p FaceTime HD Camera'
    class      = multimedia
    cap 01[48] = powerspec 3  supports D0 D1 D3  current D0
    cap 05[58] = MSI supports 1 message, 64 bit 
    cap 09[68] = vendor (length 68)
    cap 10[ac] = PCI-Express 2 endpoint max data 128(512) RO NS
                 max read 512
                 link x1(x1) speed 5.0(5.0) ASPM L1(L0s/L1) ClockPM disabled
    ecap 0001[100] = AER 1 0 fatal 0 non-fatal 1 corrected
    ecap 0003[13c] = Serial 1 000000ffff000000
    ecap 0004[150] = Power Budgeting 1
    ecap 0002[160] = VC 1 max VC0
    ecap 0018[1b0] = LTR 1
    ecap 0015[220] = Resizable BAR 1
```
```
nexus0
  efirtc0
  cryptosoft0
  aesni0
  ram0
      I/O memory addresses:
          0x0-0x57fff
          0x59000-0x9ffff
          0x100000-0x78d00fff
          0x78d49000-0x78d5cfff
          0x78d8f000-0x78e39fff
          0x78e8f000-0x78ed2fff
          0x78eff000-0x78f84fff
          0x78fdf000-0x78ffffff
          0x100000000-0x47f5fffff
  apic0
      I/O memory addresses:
          0xfec00000-0xfec0001f
  smbios0
      I/O memory addresses:
          0x78f8b000-0x78f8b01e
  acpi0
      Interrupt request lines:
          0x9
      I/O ports:
          0x2e-0x2f
          0x4e-0x4f
          0x61
          0x63
          0x65
          0x67
          0x80
          0x92
          0xb2-0xb3
          0x800-0x87f
          0x1800-0x187f
          0xffff
      I/O memory addresses:
          0xe0000000-0xefffffff
          0xfed10000-0xfed17fff
          0xfed18000-0xfed18fff
          0xfed19000-0xfed19fff
          0xfed1c000-0xfed1ffff
          0xfed20000-0xfed3ffff
          0xfed45000-0xfed8ffff
          0xfed90000-0xfed93fff
          0xfee00000-0xfeefffff
          0xff000000-0xffffffff
    acpi_ec0 pnpinfo _HID=PNP0C09 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.EC__
        I/O ports:
            0x62
            0x66
    cpu0 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU0
      acpi_perf0
      est0
      p4tcc0
      acpi_throttle0
      coretemp0
      cpufreq0
    cpu2 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU1
      acpi_perf2
      est2
      p4tcc2
      acpi_throttle2
      coretemp2
      cpufreq2
    cpu4 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU2
      acpi_perf4
      est4
      p4tcc4
      acpi_throttle4
      coretemp4
      cpufreq4
    cpu6 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU3
      acpi_perf6
      est6
      p4tcc6
      acpi_throttle6
      coretemp6
      cpufreq6
    cpu1 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU4
      acpi_perf1
      est1
      p4tcc1
      acpi_throttle1
      coretemp1
      cpufreq1
    cpu3 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU5
      acpi_perf3
      est3
      p4tcc3
      acpi_throttle3
      coretemp3
      cpufreq3
    cpu5 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU6
      acpi_perf5
      est5
      p4tcc5
      acpi_throttle5
      coretemp5
      cpufreq5
    cpu7 pnpinfo _HID=none _UID=0 _CID=none at handle=\_PR_.CPU7
      acpi_perf7
      est7
      p4tcc7
      acpi_throttle7
      coretemp7
      cpufreq7
    pcib0 pnpinfo _HID=PNP0A08 _UID=0 _CID=PNP0A03 at handle=\_SB_.PCI0
        I/O ports:
            0xcf8-0xcff
      pci0
          PCI domain 0 bus numbers:
              0
        hostb0 pnpinfo vendor=0x8086 device=0x0d04 subvendor=0x106b subdevice=0x0147 class=0x060000 at slot=0 function=0 dbsf=pci0:0:0:0 handle=\_SB_.PCI0.MCHC
        pcib1 pnpinfo vendor=0x8086 device=0x0d01 subvendor=0x106b subdevice=0x0147 class=0x060400 at slot=1 function=0 dbsf=pci0:0:1:0 handle=\_SB_.PCI0.PEG0
            I/O memory addresses:
                0xa0b00000-0xa0bfffff
            PCI domain 0 bus numbers:
                1
          pci1
              pcib1 bus numbers:
                  1
            ahci0 pnpinfo vendor=0x144d device=0xa801 subvendor=0x144d subdevice=0xa801 class=0x010601 at slot=0 function=0 dbsf=pci0:1:0:0 handle=\_SB_.PCI0.PEG0.SSD0
                Interrupt request lines:
                    0x20
                    0x21
                    0x22
                    0x23
                    0x24
                    0x25
                    0x26
                    0x27
                pcib1 memory window:
                    0xa0b00000-0xa0b01fff
              ahcich0 at channel=0
                  I/O memory addresses:
                      0xa0b00100-0xa0b0017f
        pcib2 pnpinfo vendor=0x8086 device=0x0d05 subvendor=0x106b subdevice=0x0147 class=0x060400 at slot=1 function=1 dbsf=pci0:0:1:1 handle=\_SB_.PCI0.PEG1
            I/O ports:
                0x4000-0x6fff
            I/O memory addresses:
                0xa0d00000-0xacdfffff
                0xace00000-0xb8dfffff
            PCI domain 0 bus numbers:
                5-155
          pci2
              pcib2 bus numbers:
                  5
        vgapci0 pnpinfo vendor=0x8086 device=0x0d26 subvendor=0x106b subdevice=0x0147 class=0x030000 at slot=2 function=0 dbsf=pci0:0:2:0 handle=\_SB_.PCI0.IGPU
            Interrupt request lines:
                0x2c
            I/O ports:
                0x3000-0x303f
            I/O memory addresses:
                0x90000000-0x9fffffff
                0xa0000000-0xa03fffff
          drm0
            drm1
              lkpi_iic6
                iicbus6
                  iic6 at addr=0
            drm2
              lkpi_iic7
                iicbus7
                  iic7 at addr=0
            drm3
            drm4
              lkpi_iic8
                iicbus8
                  iic8 at addr=0
            drm5
            drm6
          drmn0
            drm128
            lkpi_iic0
              iicbus0
                iic0 at addr=0
            lkpi_iic1
              iicbus1
                iic1 at addr=0
            lkpi_iic2
              iicbus2
                iic2 at addr=0
            lkpi_iic3
              iicbus3
                iic3 at addr=0
            lkpi_iic4
              iicbus4
                iic4 at addr=0
            lkpi_iic5
              iicbus5
                iic5 at addr=0
            fbd0
        hdac0 pnpinfo vendor=0x8086 device=0x0d0c subvendor=0x106b subdevice=0x0147 class=0x040300 at slot=3 function=0 dbsf=pci0:0:3:0 handle=\_SB_.PCI0.HDAU
            Interrupt request lines:
                0x28
            I/O memory addresses:
                0xa0c10000-0xa0c13fff
          hdacc0 pnpinfo vendor=0x8086 device=0x2807 revision=0x00 stepping=0x00 at cad=0
            hdaa0 pnpinfo type=0x01 subsystem=0x80860101 at nid=1
              pcm0 at nid=3
        xhci0 pnpinfo vendor=0x8086 device=0x8c31 subvendor=0x8086 subdevice=0x7270 class=0x0c0330 at slot=20 function=0 dbsf=pci0:0:20:0 handle=\_SB_.PCI0.XHC1
            Interrupt request lines:
                0x29
            I/O memory addresses:
                0xa0c00000-0xa0c0ffff
          usbus0
            uhub0
              wsp0 pnpinfo vendor=0x05ac product=0x0274 devclass=0x00 devsubclass=0x00 devproto=0x00 sernum="D3H74250UC1FTV4A76PF" release=0x0624 mode=host intclass=0x03 intsubclass=0x01 intprotocol=0x02 at bus=0 hubaddr=1 port=12 devaddr=3 interface=2 ugen=ugen0.3
              usbhid0 pnpinfo vendor=0x05ac product=0x0274 devclass=0x00 devsubclass=0x00 devproto=0x00 sernum="D3H74250UC1FTV4A76PF" release=0x0624 mode=host intclass=0x03 intsubclass=0x00 intprotocol=0x00 at bus=0 hubaddr=1 port=12 devaddr=3 interface=0 ugen=ugen0.3
                hidbus0
                  unknown pnpinfo page=0xff00 usage=0x000b bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=0
              usbhid1 pnpinfo vendor=0x05ac product=0x0274 devclass=0x00 devsubclass=0x00 devproto=0x00 sernum="D3H74250UC1FTV4A76PF" release=0x0624 mode=host intclass=0x03 intsubclass=0x01 intprotocol=0x01 at bus=0 hubaddr=1 port=12 devaddr=3 interface=1 ugen=ugen0.3
                hidbus1
                  hkbd1 pnpinfo page=0x0001 usage=0x0006 bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=0
                  unknown pnpinfo page=0x000c usage=0x0001 bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=1
                  unknown pnpinfo page=0xff00 usage=0x0006 bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=2
              usbhid2 pnpinfo vendor=0x05ac product=0x0274 devclass=0x00 devsubclass=0x00 devproto=0x00 sernum="D3H74250UC1FTV4A76PF" release=0x0624 mode=host intclass=0x03 intsubclass=0x00 intprotocol=0x00 at bus=0 hubaddr=1 port=12 devaddr=3 interface=3 ugen=ugen0.3
                hidbus2
                  unknown pnpinfo page=0xff00 usage=0x000d bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=0
              usbhid3 pnpinfo vendor=0x05ac product=0x0274 devclass=0x00 devsubclass=0x00 devproto=0x00 sernum="D3H74250UC1FTV4A76PF" release=0x0624 mode=host intclass=0x03 intsubclass=0x00 intprotocol=0x00 at bus=0 hubaddr=1 port=12 devaddr=3 interface=4 ugen=ugen0.3
                hidbus3
                  unknown pnpinfo page=0xff00 usage=0x0003 bus=0x03 vendor=0x05ac product=0x0274 version=0x0624 at index=0
        unknown pnpinfo vendor=0x8086 device=0x8c3a subvendor=0x8086 subdevice=0x7270 class=0x078000 at slot=22 function=0 dbsf=pci0:0:22:0
            I/O memory addresses:
                0xa0c19100-0xa0c1910f
        hdac1 pnpinfo vendor=0x8086 device=0x8c20 subvendor=0x8086 subdevice=0x7270 class=0x040300 at slot=27 function=0 dbsf=pci0:0:27:0 handle=\_SB_.PCI0.HDEF
            Interrupt request lines:
                0x2a
            I/O memory addresses:
                0xa0c14000-0xa0c17fff
          hdacc1 pnpinfo vendor=0x1013 device=0x4208 revision=0x03 stepping=0x00 at cad=0
            hdaa1 pnpinfo type=0x01 subsystem=0x106b8000 at nid=1
              pcm1 at nid=19,18,16,28
              pcm2 at nid=24
        pcib3 pnpinfo vendor=0x8086 device=0x8c10 subvendor=0x8086 subdevice=0x7270 class=0x060400 at slot=28 function=0 dbsf=pci0:0:28:0
            Interrupt request lines:
                0x2b
            PCI domain 0 bus numbers:
                2
        pcib4 pnpinfo vendor=0x8086 device=0x8c14 subvendor=0x8086 subdevice=0x7270 class=0x060400 at slot=28 function=2 dbsf=pci0:0:28:2 handle=\_SB_.PCI0.RP03
            I/O memory addresses:
                0xa0400000-0xa08fffff
            PCI domain 0 bus numbers:
                3
          pci3
              pcib4 bus numbers:
                  3
            unknown pnpinfo vendor=0x14e4 device=0x43ba subvendor=0x106b subdevice=0x0152 class=0x028000 at slot=0 function=0 dbsf=pci0:3:0:0 handle=\_SB_.PCI0.RP03.ARPT
                pcib4 memory window:
                    0xa0400000-0xa07fffff
                    0xa0800000-0xa0807fff
        pcib5 pnpinfo vendor=0x8086 device=0x8c16 subvendor=0x8086 subdevice=0x7270 class=0x060400 at slot=28 function=3 dbsf=pci0:0:28:3 handle=\_SB_.PCI0.RP04
            I/O memory addresses:
                0x80000000-0x8fffffff
                0xa0900000-0xa0afffff
            PCI domain 0 bus numbers:
                4
          pci4
              pcib5 bus numbers:
                  4
            unknown pnpinfo vendor=0x14e4 device=0x1570 subvendor=0x14e4 subdevice=0x1570 class=0x048000 at slot=0 function=0 dbsf=pci0:4:0:0 handle=\_SB_.PCI0.RP04.CMRA
                pcib5 memory window:
                    0xa0900000-0xa09fffff
                    0xa0a00000-0xa0a0ffff
                pcib5 prefetch window:
                    0x80000000-0x8fffffff
        isab0 pnpinfo vendor=0x8086 device=0x8c4b subvendor=0x8086 subdevice=0x7270 class=0x060100 at slot=31 function=0 dbsf=pci0:0:31:0 handle=\_SB_.PCI0.LPCB
          isa0
            sc0
            vga0
            atkbdc0
            fdc0
            ppc0
            uart0
                Interrupt request lines:
                    0x4
                I/O ports:
                    0x3f8
            uart1
        ichsmb0 pnpinfo vendor=0x8086 device=0x8c22 subvendor=0x8086 subdevice=0x7270 class=0x0c0500 at slot=31 function=3 dbsf=pci0:0:31:3 handle=\_SB_.PCI0.SBUS
            Interrupt request lines:
                0x12
            I/O ports:
                0xefa0-0xefbf
            I/O memory addresses:
                0xa0c19000-0xa0c190ff
          smbus0
        pchtherm0 pnpinfo vendor=0x8086 device=0x8c24 subvendor=0x8086 subdevice=0x7270 class=0x118000 at slot=31 function=6 dbsf=pci0:0:31:6
            I/O memory addresses:
                0xa0c18000-0xa0c18fff
    unknown pnpinfo _HID=none _UID=0 _CID=SMBUS at handle=\_SB_.PCI0.SBUS.BUS0
    unknown pnpinfo _HID=none _UID=0 _CID=SMBUS at handle=\_SB_.PCI0.SBUS.BUS1
    atdma0 pnpinfo _HID=PNP0200 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.DMAC
        DMA request lines:
            4
        I/O ports:
            0x0-0x1f
            0x81-0x91
            0x93-0x9f
            0xc0-0xdf
    unknown pnpinfo _HID=INT0800 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.FWHD
    hpet0 pnpinfo _HID=PNP0103 _UID=0 _CID=PNP0C01 at handle=\_SB_.PCI0.LPCB.HPET
        Interrupt request lines:
            0x18
            0x19
            0x1a
            0x1b
            0x1c
            0x1d
            0x1e
            0x1f
        I/O memory addresses:
            0xfed00000-0xfed03fff
    unknown pnpinfo _HID=PNP0000 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.IPIC
        I/O ports:
            0x20-0x21
            0x24-0x25
            0x28-0x29
            0x2c-0x2d
            0x30-0x31
            0x34-0x35
            0x38-0x39
            0x3c-0x3d
            0xa0-0xa1
            0xa4-0xa5
            0xa8-0xa9
            0xac-0xad
            0xb0-0xb1
            0xb4-0xb5
            0xb8-0xb9
            0xbc-0xbd
            0x4d0-0x4d1
    fpupnp0 pnpinfo _HID=PNP0C04 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.MATH
        I/O ports:
            0xf0
    acpi_sysresource0 pnpinfo _HID=PNP0C02 _UID=2 _CID=none at handle=\_SB_.PCI0.LPCB.LDRC
    atrtc0 pnpinfo _HID=PNP0B00 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.RTC_
        Interrupt request lines:
            0x8
        I/O ports:
            0x70-0x71
    attimer0 pnpinfo _HID=PNP0100 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.TIMR
        Interrupt request lines:
            0x0
        I/O ports:
            0x40-0x43
            0x50-0x53
    asmc0 pnpinfo _HID=APP0001 _UID=0 _CID=SMC-HURONRIVER at handle=\_SB_.PCI0.LPCB.SMC_
        I/O ports:
            0x300-0x31f
        I/O memory addresses:
            0xfef00000-0xfef0ffff
    unknown pnpinfo _HID=ACPI0008 _UID=0 _CID=SMC-ALS at handle=\_SB_.PCI0.LPCB.ALS0
    unknown pnpinfo _HID=PNP0C09 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.EC__ (disabled)
    unknown pnpinfo _HID=ACPI0001 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.EC__.SMB0 (disabled)
    unknown pnpinfo _HID=ACPI0002 _UID=0 _CID=none at handle=\_SB_.PCI0.LPCB.EC__.SMB0.SBS0
    unknown pnpinfo _HID=APP000B _UID=0 _CID=GMUX at handle=\_SB_.PCI0.LPCB.GMUX
        I/O ports:
            0x700-0x7fe
    acpi_sysresource1 pnpinfo _HID=PNP0C02 _UID=1 _CID=none at handle=\_SB_.PCI0.PDRC
    acpi_sysresource2 pnpinfo _HID=PNP0C01 _UID=2 _CID=none at handle=\_SB_.MEM2
    pci_link0 pnpinfo _HID=PNP0C0F _UID=1 _CID=none at handle=\_SB_.LNKA
    pci_link1 pnpinfo _HID=PNP0C0F _UID=2 _CID=none at handle=\_SB_.LNKB
    pci_link2 pnpinfo _HID=PNP0C0F _UID=3 _CID=none at handle=\_SB_.LNKC
    pci_link3 pnpinfo _HID=PNP0C0F _UID=4 _CID=none at handle=\_SB_.LNKD
    pci_link4 pnpinfo _HID=PNP0C0F _UID=5 _CID=none at handle=\_SB_.LNKE
    pci_link5 pnpinfo _HID=PNP0C0F _UID=6 _CID=none at handle=\_SB_.LNKF
    pci_link6 pnpinfo _HID=PNP0C0F _UID=7 _CID=none at handle=\_SB_.LNKG
    pci_link7 pnpinfo _HID=PNP0C0F _UID=8 _CID=none at handle=\_SB_.LNKH
    battery0 pnpinfo _HID=PNP0C0A _UID=0 _CID=none at handle=\_SB_.BAT0
    acpi_acad0 pnpinfo _HID=ACPI0003 _UID=0 _CID=none at handle=\_SB_.ADP1
    acpi_lid0 pnpinfo _HID=PNP0C0D _UID=0 _CID=none at handle=\_SB_.LID0
    acpi_button0 pnpinfo _HID=PNP0C0C _UID=0 _CID=none at handle=\_SB_.PWRB
    unknown pnpinfo _HID=APP0002 _UID=14 _CID=BACKLIGHT at handle=\_SB_.PNLF
    acpi_button1 pnpinfo _HID=PNP0C0E _UID=0 _CID=none at handle=\_SB_.SLPB
    acpi_timer0 pnpinfo unknown
        ACPI I/O ports:
            0x1808-0x180b
```

