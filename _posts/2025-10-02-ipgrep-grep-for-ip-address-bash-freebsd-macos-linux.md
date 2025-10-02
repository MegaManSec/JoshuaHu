---
layout: post
title: "ipgrep: grepping for ip addresses"
author: "Joshua Rogers"
categories: security
---

Regex is rarely a solution, but sometimes it can be helpful. One of the best bash aliases I started to use nearly 15 years ago is called `ipgrep`. It's a simple alias for grep, to find IPv4 addresses.

I always prefer Extended Regular Expressions ([EXE](https://en.wikibooks.org/wiki/Regular_Expressions/POSIX-Extended_Regular_Expressions) over PCRE if possible, so my expression looks like:

```
((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])
```

My bashrc contains, then:

```
alias ipgrep='grep -E "\b((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b"'
```

The `\b` values on each side ensures that `1.1.1.1a` and `1.1.1.1234` do not partially match, while `1.1.1.1.some` partially matches the `1.1.1.1`.
