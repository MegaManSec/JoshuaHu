---
layout: post
title: "Identifying ReDoS Vulnerabilities in Nginx Configurations Using gixy-ng"
description: "Automating ReDoS detection in Nginx. How I integrated 'recheck' into 'gixy-ng' to identify vulnerable regex configurations via a custom plugin."
categories: security
---

## ReDoS in Nginx

In my [previous post](https://joshua.hu/nginx-directives-regex-redos-denial-of-service-vulnerable), I started to look into ReDoS vulnerabilities in nginx configurations. I found that it was possible to attack an nginx server with a comparatively-small amount of requests per second, leading to the nginx server eating up its system's CPU. In this post, I'll be describing my attempt to detect ReDoS vulnerabilities in nginx configurations, with a custom plugin for [gixy-ng](https://github.com/dvershinin/gixy), and the unfortunate reality of having to create a web API for checking regular expressions for ReDoS vulnerabilities.

A brief reminder of the issue. ReDoS is a class of vulnerability where a regular expression can consume a massive amount of processing resources when attempting to match a string, especially due to [catastrophic backtracking](https://www.regular-expressions.info/catastrophic.html). This means that, for example, if you have a Location-block in your nginx configuration like `location ~ ^/(.*)\.(.*)$`, it is possible to exhaust a massive amount of processing power by accessing the URL `/.........................`. With just a few requests per second, it is possible to overload a server, rendering it inoperable.

## ReDoS Checkers

I compared a ton of different ReDoS checking tools. [regexploit](https://github.com/doyensec/regexploit), [vuln-regex-detector](https://github.com/davisjam/vuln-regex-detector), [seccamp-redos](https://github.com/n4o847/seccamp-redos), [saferegex](https://github.com/jkutner/saferegex), [redos-detector](https://github.com/olivo/redos-detector), [redos-detector](https://github.com/tjenkinson/redos-detector) (a different one), [RegexStaticAnalysis](https://github.com/NicolaasWeideman/RegexStaticAnalysis), [regexploit](https://github.com/doyensec/regexploit), [safe-regex](https://github.com/davisjam/safe-regex), and [recheck](https://github.com/makenowjust-labs/recheck). I did not test [RegexEval](https://github.com/s2e-lab/RegexEval) because it relies on AI and having an OpenAI key. I did not test [rat](https://github.com/phreppo/rat) because it does not support backreferences and lookarounds (although, it seems like a very good solution otherwise).

From my testing, _recheck_ provided the best results, and in general, I'm happier with its source code and approach to identifying ReDoS vulnerabilities. The only problem? recheck is only available in JavaScript/TypeScript or Scala, while gixy-ng is written in Python.

## _recheck_ HTTP API

My solution to this problem is.. not a good one. It involves exposing recheck via an HTTP API, which can be queried by gixy-ng. My implementation of the server can be found here: [MegaManSec/recheck-http-api](https://github.com/MegaManSec/recheck-http-api).

The server can handle multiple expressions in a single request, but gixy-ng considers each expression separately, so it has to request the endpoint as many times as there are expressions.

An example request to the API can be seen below:

```
{
  "1": {"pattern": "^(a+)+$", "modifier": ""},
  "2": {"pattern": "^[a-z]+$^[a-z]+$^[a-z]+$^[a-z]+$^[a-z]+$ ( ..... over one 1000 characters ...... )", "modifier": "i"},
  "3": {"pattern": "(......very long and slow regular expression, causing a timeout of recheck......)", "modifier": ""},
  "4": {"pattern": "^not-vulnerable[0-9]*$", "modifier": "m"}
}
```

which should result in the response:

```
{
  "1": {
    "source": "^(a|a+)+$",
    "flags": "",
    "complexity": {"type": "exponential", "summary": "exponential", "isFuzz": false},
    "status": "vulnerable",
    "attack": {"pattern": "'a' + 'a'.repeat(31) + '\\x00'", "string": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\u0000", "base": 31, "suffix": "\u0000", "pumps": [{"prefix": "a", "pump": "a", "bias": 0}]},
    "checker": "automaton",
    "hotspot": [{"start": 4, "end": 5, "temperature": "heat"}]
  },
  "2": null,
  "3": {
    "source": "some-very-long-regex",
    "flags": "",
    "checker": "automaton",
    "error": {"kind": "timeout"},
    "status": "unknown"
  },
  "4": {
    "source": "^not-vulnerable[0-9]*$",
    "flags": "m",
    "checker": "automaton",
    "complexity": {"type": "linear", "summary": "linear", "isFuzz": false},
    "status": "safe"
  }
}
```

The security of recheck has not been tested. I do not know if it is possible to cause remote code execution by sending a crafted string to it. In any case, any server hosting the API should not be exposed to the internet, and should preferably be self-hosted.

## gixy-ng integration

I have submitted a PR to gixy-ng with the functionality to specify a URL to a server hosting my recheck-http-api solution. I am unsure if it will land, but at least it exists. The PR can be found [here](https://github.com/dvershinin/gixy/pull/30). The new plugin option, `--regex-redos-url`, specifies the URL to a server hosting recheck-http-api.

An example of using the integration is seen below:

```shell
# gixy --regex-redos-url http://localhost:3001/recheck

==================== Results ===================

>> Problem: [regex_redos] Detect directives with regexes that are vulnerable to Regular Expression Denial of Service (ReDoS).
Description: Regular expressions with the potential for catastrophic backtracking allow an nginx server to be denial-of-service attacked with very low resources (also known as ReDoS).
Additional info: https://joshua.hu/regex-redos-recheck-nginx-gixy
Reason: Regex is vulnerable to 2nd degree polynomial ReDoS: /statis/(.*)\.js\.map.
Pseudo config:

server {
	server_name servername.com;

	location ~ /static/(.*)\.js\.map {
	}
}
```

The recheck-http-api server supports caching too, meaning in you can leave it long-running and continuously query it (e.g. from a CI/CD system) with minimal performance overhead (as the API will only actually do work when _new_ regular expressions are checked).
