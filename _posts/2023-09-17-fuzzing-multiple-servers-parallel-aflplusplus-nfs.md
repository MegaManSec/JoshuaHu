---
layout: post
title: "Fuzzing with multiple servers in parallel: AFL++ with Network File Systems"
author: "Joshua Rogers"
categories: security
---


## Introduction
When fuzzing large-scale applications, using a single server (even with 4 64-core AMD Ryzen CPUs) may not be powerful enough by itself. That's where parallelized/distributed fuzzing comes in (i.e. automatic sharing of results between fuzzing systems). In this guide, we'll take a look at how to set up multiple servers fuzzing the same program using [AFL++](https://github.com/AFLplusplus/AFLplusplus), linked all together with an NFS (Network File System).

### Step 1: Set up the NFS servers
To start, we need to set up an NFS on on each of the systems we're going to be fuzzing on. In this post, we're going to use four servers named _fuzz_, _buzz_, _ping_, and _pong_. Each server has the IP addresses _10.0.0.10_, _10.0.0.11_, _10.0.0.12_, and _10.0.0.13_, respectively.

We'll start with _fuzz_.

1\. Install NFS server, create a directory (which we will be _exporting_), and set the permissions:
```bash
sudo apt install nfs-kernel-server
sudo mkdir -p /mnt/fuzz/
sudo chown -R nobody:nogroup /mnt/buzz
sudo chmod -R 666 /mnt/fuzz
```

2\. Edit the NFS export configuration. In this configuration, we limit the access to _/mnt/fuzz_ to the addresses of the four systems:
```bash
sudo su
cat << EOF >> /etc/exports
/mnt/fuzz  10.0.0.10/32(rw,insecure,async,no_root_squash,no_subtree_check)
/mnt/fuzz  10.0.0.11/32(rw,insecure,async,no_root_squash,no_subtree_check)
/mnt/fuzz  10.0.0.12/32(rw,insecure,async,no_root_squash,no_subtree_check)
/mnt/fuzz  10.0.0.13/32(rw,insecure,async,no_root_squash,no_subtree_check)
EOF
exit
```

3\. Export the configuration and restart the server:
```bash
sudo exportfs -a
sudo systemctl restart nfs-kernel-server
```
We then need to repeat this on each of the other servers. To set up the _buzz_ server, we follow the instructions exactly the same, but replacing any reference to _fuzz_ with _buzz_.

### Step 2: Mount the remote NFS servers

Now that we've set up the NFS _servers_, we now need to mount each of the _remote_ filesystems on each server.

```bash
sudo apt install nfs-common

[ -d "/mnt/fuzz" ] || (sudo mkdir /mnt/fuzz && sudo mount -o r,noacl,nocto,nodiratime,noatime,bg,rsize=32768,wsize=32768 10.0.0.10:/mnt/fuzz /mnt/fuzz)

[ -d "/mnt/buzz" ] || (sudo mkdir /mnt/buzz && sudo mount -o r,noacl,nocto,nodiratime,noatime,bg,rsize=32768,wsize=32768 10.0.0.11:/mnt/buzz /mnt/buzz)

[ -d "/mnt/ping" ] || (sudo mkdir /mnt/ping && sudo mount -o r,noacl,nocto,nodiratime,noatime,bg,rsize=32768,wsize=32768 10.0.0.12:/mnt/ping /mnt/ping)

[ -d "/mnt/pong" ] || (sudo mkdir /mnt/pong && sudo mount -o r,noacl,nocto,nodiratime,noatime,bg,rsize=32768,wsize=32768 10.0.0.13:/mnt/pong /mnt/pong)
```

Basically, we mount all of the remote NFS' on each server: if the directory already exists, then there's no need to mount it since it's the local version. If a directory is ever unmounted (so, during a reboot), then none of the mounts will run; you should delete the empty directories.

### Step 3: Start fuzzing on the servers

Now we set up the fuzzing on each server. In this case, we start on _fuzz_. 

When fuzzing, we are outputting the _local_ crashes to _/mnt/fuzz/_ and treat all of the remote NFS' as "foreign fuzzers": read-only. Locally, all fuzzers (using the _-M_ and _-S_ flags) share results, so we only need to specify the main queue for each foreign fuzzer: 
The flags are as followed:
```bash
afl-fuzz -i corpus/ -M fuzz_1 -o /mnt/fuzz/ -F /mnt/buzz/buzz_1/queue/ -F /mnt/ping/ping_1/queue/ -F /mnt/pong/pong_1/queue/ ./fuzzed-program
```
Still on the _fuzz_ server, we then fuzz with all of the cores available:
```bash
afl-fuzz -i corpus/ -S fuzz_2 -o /mnt/fuzz/ ./fuzzed-program
afl-fuzz -i corpus/ -S fuzz_3 -o /mnt/fuzz/ ./fuzzed-program
...
```
All of the flags used are as followed:
```
  -i dir        - input directory with test cases
  -o dir        - output directory for fuzzer findings
  -M/-S id      - distributed mode (-M sets -Z and disables trimming)
  -F path       - sync to a foreign fuzzer queue directory (requires -M)
```

Basically, _afl-fuzz_ on this machine is continuously reading and writing to the local _/mnt/fuzz_, and _periodically_ checking the remote _/mnt/buzz/buzz_1/queue/_, _/mnt/ping/ping_1/queue/_, and _/mnt/pong/pong_1/queue/_ for any new findings from the other servers. Checking those _remote_ directories can be slow due to the network overhead, however since they are not continuously reading the remote locations, the overhead is limited.

Finally, we repeat this process on all of the other servers.

On the _buzz_ server, we would run:
```bash
afl-fuzz -i corpus/ -M buzz_1 -o /mnt/buzz/ -F /mnt/fuzz/fuzz_1/queue/ -F /mnt/ping/ping_1/queue/ -F /mnt/pong/pong_1/queue/ ./fuzzed-program
```
and
```bash
afl-fuzz -i corpus/ -S buzz_2 -o /mnt/buzz/ ./fuzzed-program
afl-fuzz -i corpus/ -S buzz_3 -o /mnt/buzz/ ./fuzzed-program
...
```
And similarly on the other servers.


## Conclusion
Syncing data between multiple systems in order to fuzz a target in parallel is a problem that can be solved in multiple ways. By using NFS' to make the queue directories of other systems available, we create a fairly easy-to-scale solution which fits the job as needed. What's more, a simple bash script can enumerate all of the instructions in this blog post quite easily, assuming conformity in the hostnames of each of the systems used for fuzzing: but that's for another time...
