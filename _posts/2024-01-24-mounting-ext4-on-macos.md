---
layout: post
title: "Mounting and reading an ext4 drive on MacOS"
author: "Joshua Rogers"
categories: security
---

---

Today I will.. mount an ext4 drive on MacOS.

```bash
$ brew install --cask macfuse
==> Downloading https://formulae.brew.sh/api/cask.jws.json
#=#=-  #       #                                                                                                                                                                                                                                               #=O#-     #        #                                                                                                                                                                                                                                           -#O=- #      #          #                                                                                                                                                                                                                                      -=O#-   #        #           #                                                                                                                                                                                                                                 -=O=-#      #        #            #                                                                                                         ######################################################################################################################################################################################################################################################### 100.0%
Warning: Not upgrading macfuse, the latest version is already installed
$ brew install ext4fuse
==> Downloading https://formulae.brew.sh/api/formula.jws.json
######################################################################################################################################################################################################################################################### 100.0%
ext4fuse: Linux is required for this software.
libfuse@2: Linux is required for this software.
Error: ext4fuse: Unsatisfied requirements failed this build.
```

Hmm.. Yes brew, you're right. I'm not using Linux. So why can I even try to install this brew? Weird. Anyways, this works:

```bash
$ brew install pkg-config
$ git clone https://github.com/gerard/ext4fuse.git && cd "$(basename "$_" .git)"
$ make
$ diskutil list # Fiund the disk and partition you want to mount
/dev/disk4 (external, physical):
   #:                       TYPE NAME                    SIZE       IDENTIFIER
   0:     FDisk_partition_scheme                        *2.0 TB     disk4
   1:                      Linux                         2.0 TB     disk4s1
$ mkdir ~/ext4_mount
$ sudo ./ext4fuse /dev/disk4 ~/ext4_mount -o allow_other
mount_macfuse: the file system is not available (1)
```

Oops! ext4fuse requires a kernel module to operate, and you need to shutdown your computer to allow the loading of kernel modules (it's a security feature so malicious software can't load kernel modules).

1. Shutdown the computer fully,
2. Press and hold the power button until the computer starts and you are booted into the "Boot Options" menu,
3. Press options and log into your admin account,
4. On the top left of the screen under "utilities", select "startup security utility",
5. Unlock your drive if it's encrypted, and then selected "reduced security" and "allow user management of kernel extensions from identified developers.",
6. Press restart on the top left.

Booting again, we try again:

```bash
$ diskutil list # Might have changed disk number
$ sudo ./ext4fuse /dev/disk4 ~/ext4_mount -o allow_other
```

Success!

ext4fuse can only read from ext4 disks, but luckily for me, that's.. good enough.
