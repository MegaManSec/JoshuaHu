---
layout: post
title: "SSH-Snake Update: Multi-IP Domain Resolution"
author: "Joshua Rogers"
categories: security
---

---

After releasing [SSH-Snake](https://github.com/MegaManSec/SSH-Snake) one week ago and it receiving a quick 700-stars (thank you!) on Github, multiple postings on HackerNews, a mention in [Hackaday](https://hackaday.com/2024/01/05/this-week-in-security-bitwarden-reverse-rdp-and-snake/), and a few reposts on LinkedIn, I thought I'd quickly add an important feature that was missing: Resolution of domains which have multiple IPv4 addresses. This post details how that works.

---

When SSH-Snake has finished compiling a list of possible destinations (a destination is a username and host combination) that it should attempt to SSH into, it performs a form of de-duplication. In order to de-duplicate destinations, the script attempts to resolve all of the hostnames for the hosts of the destinations, ensuring that they are valid. For example, given the following destinations:

```bash
user1@hostname.com
user2@hostname.com
user3@10.2.3.4
user1@hostname2.com
```

the script will resolve `hostname.com` and parse its IPv4 address (such as `10.1.1.1`), changing the first two destinations to `user1@10.1.1.1`, and `user2@10.1.1.1`. The third destination is left alone because it is also in the username@ipaddress format. However, for the fourth destination, if `hostname2.com` resolves to `10.1.1.1`, then it is a duplicate of the first line: so it is ignored -- makes sense, right? Why bother connecting to `user1@10.1.1.1` twice?

In order to not resolve the same host over and over, the script also uses an internal cache of resolved hosts. Once it's resolved `hostname2.com` once, it doesn't try again -- it uses its internally cached response. Let's look at the source code:

```bash
  for ssh_dest in "${ssh_dests[@]}"; do
    is_ssh_dest "$ssh_dest" || continue # Checks if the host has been ignored in this loop

    ssh_user="${ssh_dest%%@*}"
    ssh_host="${ssh_dest#*@}"

    # Check if the host has already been resolved. If it has, use the internally cached answer.
    if [[ -v 'resolved_hosts["$ssh_host"]' || ${#resolved_hosts["$ssh_host"]} -gt 0 ]]; then
      resolved_ssh_host="${resolved_hosts["$ssh_host"]}"
    else
      resolved_ssh_host="$(getent ahostsv4 -- "$ssh_host" 2>/dev/null)"
      resolved_ssh_host="${resolved_ssh_host%% *}" # format is 'ip\t[junk]

      # Answer must begin with 1 or 2 ($res 0.1.2.3 will respond with 0.1.2.3).
      if [[ "${resolved_ssh_host:0:1}" =~ [12] ]]; then
        [[ "$resolved_ssh_host" =~ ^127\. ]] && resolved_ssh_host="127.0.0.1" # If it's loopback, always use 127.0.0.1
        # Cache the host
        resolved_hosts["$ssh_host"]="$resolved_ssh_host"
      else
        # Ignore this host
        _ignored_hosts["$ssh_host"]=1
        # Also ignore the resolved host (which may not necessarily be the same as the host).
        [[ -n "$resolved_ssh_host" ]] && _ignored_hosts["$resolved_ssh_host"]=1
        continue
      fi
    fi

    # Check whether the resolved host is ignored. If so, also add the unresolved host to _ignored_hosts.
    [[ -v '_ignored_hosts["$resolved_ssh_host"]' || ${#_ignored_hosts["$resolved_ssh_host"]} -gt 0 ]] && _ignored_hosts["$ssh_host"]=1
    # add_ssh_dest will check whether the $ssh_user@$resolved_ssh_host is ignored.

    valid_ssh_dests["$ssh_user@$resolved_ssh_host"]=1
  done

  ssh_dests=()

  for ssh_dest in "${!valid_ssh_dests[@]}"; do
    add_ssh_dest "$ssh_dest"
  done
```
We can see that when a host is resolved, the resolution undergoes some checks to make sure the response is valid. If it is, the first IPv4 address is placed into `resolved_hosts["$ssh_host"]` -- i.e. cached. Future destinations using this host will use the already-resolved answer. The now-resolved destination is placed into the `valid_ssh_dests` associative array, which will be used to overwrite the original list of destinations.

---

The above code is flawed because it doesn't account for hostnames that have multiple IPv4 addresses. If a hostname resolves to multiple addresses, we want to try all of the addresses. So what can we do? The easy thing to do would be to turn `resolved_hosts["$ssh_host"]` into an multi-dimentional array: `resolved_hosts["$ssh_host"][0]`, `resolved_hosts["$ssh_host"][1]`, and so on. But that's not possible:

```bash
$ declare -A test
$ test["user"]=("1" "2")
-bash: test["user"]: cannot assign list to array member
$ test["user"][0]=1
-bash: test[user][0]=1: command not found
```

So what can we do to save multiple hostnames in this variable? Well, I decided that since the values of each host are well-defined, we can take advantage of the default Internal Field Separator (IFS) in Bash (a space) and build a string for each host with the collection of resolved IPv4 address, and loop over them with the space as the separator. The basic example of this is:

```bash
$ declare -A test
test["user"]="1 2 3 4"
for val in ${test["user"]}; do
  echo "$val"
done
1
2
3
4
```

Editing the SSH-Snake script, we get:

```bash
    # Check if the host has already been resolved. If it has, use the internally cached answer.
    if [[ -v 'resolved_hosts["$ssh_host"]' || ${#resolved_hosts["$ssh_host"]} -gt 0 ]]; then
      : # do nothing
    else
      resolved_ssh_hosts="$(getent ahostsv4 -- "$ssh_host" 2>/dev/null | awk '/RAW/{print $1}')"
      for resolved_ssh_host in "${resolved_ssh_hosts[@]}"; do
        # Answer must begin with 1 or 2 ($res 0.1.2.3 will respond with 0.1.2.3).
        if [[ "${resolved_ssh_host:0:1}" =~ [12] ]]; then
          [[ "$resolved_ssh_host" =~ ^127\. ]] && resolved_ssh_host="127.0.0.1" # If it's loopback, always use 127.0.0.1
          [[ -v '_ignored_hosts["$resolved_ssh_host"]' || ${#_ignored_hosts["$resolved_ssh_host"]} -gt 0 ]] && continue
          # Cache the host
          resolved_hosts["$ssh_host"]+="$resolved_ssh_host "
        else
          # Ignore this RESOLVED host (might save us a few cycles).
          # Don't add the ssh_host to _ignored_hosts become it may have non-ignored hosts, too.
          [[ -n "$resolved_ssh_host" ]] && _ignored_hosts["$resolved_ssh_host"]=1
        fi
       done
    # No IPs resolved for the host, add the host to _ignored_host.
    if [[ "${#resolved_hosts["$ssh_host"]}" -lt 7 ]]; then
      _ignored_hosts["$ssh_host"]=1
      continue
    fi

    # Loop through each host (which are space-separated now), so no quotation marks.
    for resolved_ssh_host in ${resolved_hosts["$ssh_host"]}; do
      valid_ssh_dests["$ssh_user@$resolved_ssh_host"]=1
    done

```

We first resolve the host and extract each of its unique IPv4 addresses. Then we loop over each ip address checking the validity, and append the address to the _string_ `resolved_hosts["$ssh_host"]`. After that, we ensure that the string contains at least one valid host. If it does, then we loop through each space-separated value (note `in ${resolved_hosts["$ssh_host"]}` NOT `in "${resolved_hosts["$ssh_host"]}"`, adding the appropriate values to the `valid_ssh_dests` array.

---

The only reason this really works is because we know in advance that each IPv4 address is going to be a fixed string: it doesn't contain spaces, so Bash can parse each address _as if_ it were an array -- but it's not!


