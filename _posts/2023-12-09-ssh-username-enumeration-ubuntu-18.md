---
layout: post
title: "SSH Adventures Continued: Invalid CVE-2018-15473 Patches"
author: "Joshua Rogers"
categories: security
---

Let's say you're like me, and you're indirectly conducting research into how different versions of the ssh client on Ubuntu produce warning/error messages when connecting to different versions of the ssh server.

Like me, you come across a strange situation. When you attempt to ssh into a server, you get different responses depending on the username. For a username which does in fact correlate to a user on the remote server, you get prompted for a password:
```
$ ssh root@10.0.0.1
root@10.0.0.1's password:
```
But for a user that doesn't exist:
```
$ ssh invalid@10.0.0.1
Connection closed by 10.0.0.1 port 22
```

That's definitely not supposed to happen. You're not supposed to be able to so easily determine whether a remote server has a user corresponding to a username without first having access to the server.

After some time trying to figure out why the remote server was effectively disclosing whether a username existed or not to anybody that tried to connect, I finally came across Ubuntu bug report 1934501: ["CVE-2018-15473 patch introduce user enumeration vulnerability"](https://bugs.launchpad.net/ubuntu/+source/openssh/+bug/1934501). 

---

In 2018, it was discovered that by sending a specifically crafted packet to an openssh server, it was possible to determine whether a username corresponded to a user on a remote server or not (i.e. an oracle.) This bug was assigned CVE-2018-15473.

It seems that somehow, for over two years, the patch for _that_ vulnerability introduced a similar vulnerability into Ubuntu 18.04's openssh. Sending a specifically crafted packet to the server wasn't necessary: if you tried to connect with an invalid username, the client would simply report "Connection closed by [host] port [port]".

As always, it's not so simple. Different versions of ssh (the client) report different error messages. I've discovered three variations so far that indicate whether a user exists or not.

### OpenSSH_6.6.1p1 Ubuntu-2ubuntu2.13, OpenSSL 1.0.1f 6 Jan 2014

```
$ ssh -q invalid@10.0.0.1
$ ssh invalid@10.0.0.1
Connection closed by 10.0.0.1
```

ssh's `-q` flag suppresses the error which indicates the username does not exist on the remote host.


### OpenSSH_7.2p2 Ubuntu-4ubuntu2.10, OpenSSL 1.0.2g 1 Mar 2018
```
$ ssh invalid@10.0.0.1
Connection to 10.0.0.1 closed by remote host.
Connection to 10.0.0.1 closed.
$ ssh -q invalid@10.0.0.1
Connection to 10.0.0.1 closed by remote host.
```
In this example, the error message is shown despite ssh's `-q` flag being used. The error message is different.

sdev@n22-04-04:~$ ssh lol@172.17.64.169
Connection to 172.17.64.169 closed by remote host.
Connection to 172.17.64.169 closed.

### OpenSSH_7.6p1 Ubuntu-4ubuntu0.3, OpenSSL 1.0.2n  7 Dec 2017
```
$ ssh -q invalid@10.0.0.1
$ ssh invalid@10.0.0.1
Connection closed by 10.0.0.1 port 22
```

### OpenSSH_8.2p1 Ubuntu-4ubuntu0.9, OpenSSL 1.1.1f 31 Mar 2020
```
$ ssh -q invalid@10.0.0.1
$ ssh invalid@10.0.0.1
Connection closed by 10.0.0.1 port 22
```
The same as above.

### OpenSSH_8.4p1 Debian-5+deb11u2, OpenSSL 1.1.1w  11 Sep 2023
```
$ ssh invalid@10.0.0.1
invalid@10.0.0.1: Permission denied (publickey).
````

No different from an invalid key, so it doesn't idicate whether the user exists or not (note: this is a Debian client, not Ubuntu).

