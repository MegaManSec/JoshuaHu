---
layout: post
title: "Speeding up nmap service scanning 16x"
author: "Joshua Rogers"
categories: security
---

In my [previous post](/port-scanning-networks-speeding-up-nmap-for-large-scales) post, I began writing about how I was designing a port and service scanner for large-scale networks by combining port-scanning tools like masscan/zmap and service scanning tools like nmap. In this post, I'm going to dive into some of the details of nmap's service scanning, and outline how I was able to speed up nmap's service scanning by 16-times.

---

In order to determine the service running on a specific port, nmap uses a so-called "_service detection probe list_" which is located in a file named "_nmap-service-probes_".

A probe looks like the following:

`Probe TCP GetRequest q|GET / HTTP/1.0\r\n\r\n|`

The syntax for the probe is the following:

`Probe <protocol> <probename> <probestring> [no-payload]`

The format is quite simple:
* *protocol*: TCP or UDP
* *probename*: An arbitrary name of the probe such as "_GenericLines_", "_RPCCheck_", or "_X11Probe_".
* *probestring*: The data sent to the server when it is probed. Note: `q|[characters]|` is perl's "quote operator" which allows you to create strings without needing to escape special characters.
* *[no-payload]*: Used for UDP scanning so we ignore it for now.

A series of matching rules follow each probe which match on the response to each probe. An example is the following:

`match compuware-lm m|^Hello, I don't understand your request\.  Good bye\.\.\.\. $| p/Compuware Distributed License Management/`

The syntax for the probe is the following:

`match <service> <pattern> [<versioninfo>]`

The format is also quite simple:
* _service_: The service name such as "_http_", "_ssh_", "_mysql_", and so on.
* _pattern_: a perl-form regex pattern to match the response received from the probe.
* _[\<versioninfo\>]_: Various optional flags for extracting/displaying extrra information about the match ([read more here](https://nmap.org/book/vscan-fileformat.html))

---

It is extremely noteworthy that when nmap sends a probe, it **deliberately waits for a pre-defined amount of time**. That is to say, **there is a minimum amount of time each probe takes**. If a match is not received, the next probe is sent; up to a certain 'rarity' of probe -- "_Nmap uses the rarity metric to avoid trying probes that are extremely unlikely to match_". By default, probes are sent up to the _rarity_ of 7. For probe rarity 1-7, each probe waits at least 6-seconds (but most wait 7.5-seconds):
```
# Wait for at least 6 seconds for data.  It used to be 5, but some
# smtp services have lately been instituting an artificial pause (see
# FEATURE('greet_pause') in Sendmail, for example)
totalwaitms 6000
```
In reality, scanning a host for a service which is completely unidentifiable, will keep you waiting around 160-seconds:
```
# time nmap -sV localhost -p2223
Starting Nmap 7.80 ( https://nmap.org ) at 2023-08-12 14:11 UTC
Nmap scan report for localhost (127.0.0.1)
Host is up (0.000098s latency).

[..]

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 160.66 seconds

real    2m40.676s
user    0m0.417s
sys     0m0.065s
```

2 minutes and 40 seconds is an unacceptable time for service scanning a single host. How can we improve this?

---

The most obvious solution is to simply lower the _totalwaitms_ value to something more reasonable. This will sacrifice niche results such as of the mail servers which employ these anti-spam techniques, however this is a sacrifice I believe most are willing to make. _totalwaitms_ can be changed the nmap-service-probes file.
```
# grep 'totalwaitms' /usr/share/nmap/nmap-service-probes
totalwaitms 6000
totalwaitms 7500
totalwaitms 7500
totalwaitms 7500
totalwaitms 7500
totalwaitms 11000
```
_tcpwrappedms_ also must be lowered, since it should be lower than _totalwaitms_:
```
# If the service closes the connection before 3 seconds, it's probably
# tcpwrapped. Adjust up or down depending on your false-positive rate.
tcpwrappedms 300
```

After replacing these values with _totalwaitms 300_ and _tcpwrappedms 200_, it is expected that the scan will now take just a few seconds. However...

```
# time nmap -sV localhost -p2223
[..]

real    2m17.561s
user    0m0.401s
sys     0m0.084s
```
That isn't much of an improvement at all.

As it turns out, probes which do not have a specifically defined _servicewaitms_ use a default value of 5000. Therefore, we can either add values to each of the probes, or we can compile nmap ourselves and change the default value in [service_scan.h](https://github.com/nmap/nmap/blob/master/service_scan.h#L79). I went for the second option, and changed the default value in nmap's source code and then compiled my own version of nmap.

I didn't want to change the values of _totalwaitms_ and _tcpwrappedms_ at all in the /usr/share/nmap/nmap-service-probes file, so I also edited the [parsing code](https://github.com/nmap/nmap/blob/master/service_scan.cc#L1358) such that these values in the nmap-service-probes file are completely ignored:

I once again tried scanning, and..
```
# time nmap localhost -p9999 -sV
[..]

real    0m10.481s
user    0m0.400s
sys     0m0.037s
```

Success! We've just turned our 160-second scan into just 10-seconds. Can we do anything to make it even faster? 

---
Using nmap's debugging flag, we can check to see the timeout and delays for various of its actions:
```text
# nmap localhost -p9999 -sV -d2
[...]
NSOCK INFO [9.1460s] nsock_write(): Write request for 48 bytes to IOD #29 EID 699 [127.0.0.1:9999]
NSOCK INFO [9.1460s] nsock_read(): Read request from IOD #29 [127.0.0.1:9999] (timeout: 300ms) EID 706
NSOCK INFO [9.1460s] nsock_trace_handler_callback(): Callback: WRITE SUCCESS for EID 699 [127.0.0.1:9999]
NSOCK INFO [9.4460s] nsock_trace_handler_callback(): Callback: READ TIMEOUT for EID 706 [127.0.0.1:9999]
NSOCK INFO [9.4460s] nsock_iod_delete(): nsock_iod_delete (IOD #29)
Completed Service scan at 15:02, 9.01s elapsed (1 service on 1 host)
NSE: Script scanning 127.0.0.1.
NSE: Starting runlevel 1 (of 2) scan.
Initiating NSE at 15:02
Completed NSE at 15:02, 0.00s elapsed
NSE: Starting runlevel 2 (of 2) scan.
Initiating NSE at 15:02
[..]
NSOCK INFO [9.4620s] nsock_read(): Read request from IOD #1 [127.0.0.1:9999] (timeout: 7000ms) EID 26
```

We can see that the timeout is correctly being set to 300ms for the service scanning. However, NSE scripts, which nmap uses for version detection (among other things), use a different system for setting the timeout -- in this case, there is a maximum timeout of 7000ms. Diving into `nselib/comm.lua` reveals how this timeout is set by the scripts:
```lua
-- This timeout value (in ms) is added to the connect timeout and represents
-- the amount of processing time allowed for the host before it sends a packet.
-- For justification of this value, see totalwaitms in nmap-service-probes
local REQUEST_TIMEOUT = 6000

-- Function used to get a connect and request timeout based on specified options
local function get_timeouts(host, opts)
  local connect_timeout, request_timeout
  -- connect_timeout based on options or stdnse.get_timeout()
  if opts and opts.connect_timeout then
    connect_timeout = opts.connect_timeout
  elseif opts and opts.timeout then
    connect_timeout = opts.timeout
  else
    connect_timeout = stdnse.get_timeout(host)
  end

  -- request_timeout based on options or REQUEST_TIMEOUT + connect_timeout
  if opts and opts.request_timeout then
    request_timeout = opts.request_timeout
  elseif opts and opts.timeout then
    request_timeout = opts.timeout
  else
    request_timeout = REQUEST_TIMEOUT
  end
  request_timeout = request_timeout + connect_timeout

  return connect_timeout, request_timeout
end
```

Basically, a connection timeout and a request timeout is set based on the options defined in the NSE files. Not all default NSE scripts implicitly set a timeout, so a minimum 6-second _request_timeout_ is often used. Even from the scripts that do set a timeout, the timeout is usually 5-seconds or more.

Instead of editing every NSE file to implicitly set a low timeout or `nselib/comm.lua`, we can edit the _l_set_timeout_ function in [nse_nsock.cc](https://github.com/nmap/nmap/blob/master/nse_nsock.cc#L772) to set a maximum of a 500ms timeout.

The exact speed-up from doing this depends on the scripts which run during service and version scanning.

---

In this post, we've explored how nmap has a very high forced-delay for its service scanning, as well as high timeouts for its NSE scripts. By making a few simple changes, we can speed up service scanning by up to 16x. Note that the values of 500, 300, and 200ms are all arbitrary, however they are what I decided on based on my use-case and the network configuration of my environment.

A patch is provided for nmap.
```diff
diff --git a/nse_nsock.cc b/nse_nsock.cc
index 18a75a7bb..2e88c0fed 100644
--- a/nse_nsock.cc
+++ b/nse_nsock.cc
@@ -769,6 +769,8 @@ static int l_set_timeout (lua_State *L)
   int timeout = nseU_checkinteger(L, 2);
   if (timeout < -1) /* -1 is no timeout */
     return luaL_error(L, "Negative timeout: %f", timeout);
+  if (timeout > 500)
+    timeout = 500;
   nu->timeout = timeout;
   return nseU_success(L);
 }
diff --git a/service_scan.cc b/service_scan.cc
index f7de2ea8c..9b6d3af1f 100644
--- a/service_scan.cc
+++ b/service_scan.cc
@@ -1342,10 +1342,11 @@ void parse_nmap_service_probe_file(AllProbes *AP, const char *filename) {
       } else if (strncmp(line, "fallback ", 9) == 0) {
         newProbe->fallbackStr = strdup(line + 9);
       } else if (strncmp(line, "totalwaitms ", 12) == 0) {
-        long waitms = strtol(line + 12, NULL, 10);
+/*        long waitms = strtol(line + 12, NULL, 10);
         if (waitms < 100 || waitms > 300000)
           fatal("Error on line %d of nmap-service-probes file (%s): bad totalwaitms value.  Must be between 100 and 300000 milliseconds", lineno, filename);
         newProbe->totalwaitms = waitms;
+*/
       } else if (strncmp(line, "tcpwrappedms ", 13) == 0) {
         long waitms = strtol(line + 13, NULL, 10);
         if (waitms < 100 || waitms > 300000)
diff --git a/service_scan.h b/service_scan.h
index b17e3d242..807faa77a 100644
--- a/service_scan.h
+++ b/service_scan.h
@@ -84,8 +84,8 @@
 #include <assert.h>
 
 /**********************  DEFINES/ENUMS ***********************************/
-#define DEFAULT_SERVICEWAITMS 5000
-#define DEFAULT_TCPWRAPPEDMS 2000   // connections closed after this timeout are not considered "tcpwrapped"
+#define DEFAULT_SERVICEWAITMS 300
+#define DEFAULT_TCPWRAPPEDMS 200   // connections closed after this timeout are not considered "tcpwrapped"
 #define DEFAULT_CONNECT_TIMEOUT 5000
 #define DEFAULT_CONNECT_SSL_TIMEOUT 8000  // includes connect() + ssl negotiation
 #define MAXFALLBACKS 20 /* How many comma separated fallbacks are allowed in the service-probes file? */
```
