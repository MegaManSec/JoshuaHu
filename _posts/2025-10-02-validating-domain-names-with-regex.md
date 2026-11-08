---
layout: post
title: "Securely Validating Domain Names with Regular Expressions"
tags: [regex, security, programming]
description: "Validating domain names securely. A ReDoS-safe regular expression pattern for verifying hostnames and handling Punycode domains."
---

Regular expressions are rarely the solution, but sometimes they can be helpful. I recently needed to create some regex which could be used to parse _real_ domain names, and finding a definitive expression seemed to be difficult; especially one that wasn't vulnerable to ReDoS.

In reality, the best approach is to use a library specifically designed for this, and which checks the _validity_ of a domain too, which includes checking the domain against the [Public Suffix List (PSL)](https://publicsuffix.org/). `tldts` is a good library which does this. Nonetheless, sometimes a regex is needed elsewhere.

I came up with the following to test for well-formed *domain* names:

```
^(?!.{254,})((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$
```

With Punycode, that becomes:

```
^(?!.{254,})(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+(?:xn--[A-Za-z0-9-]{1,59}|[A-Za-z]{2,63})(?<!-)$
```

With no negative lookbehind, that becomes:

```
/^(?!.{254,})(?:[0-9A-Za-z](?:[0-9A-Za-z-]{0,61}[0-9A-Za-z])?\.)+(?:xn--[0-9A-Za-z-]{0,58}[0-9A-Za-z]|[A-Za-z]{2,63})$/
```

Linear-time engines like RE2, Go's `regexp`, and Rust's `regex` don't support lookarounds at all, so the length check has to move out of the regex:

```go
var domainRe = regexp.MustCompile(`^(?:[0-9A-Za-z](?:[0-9A-Za-z-]{0,61}[0-9A-Za-z])?\.)+(?:xn--[0-9A-Za-z-]{0,58}[0-9A-Za-z]|[A-Za-z]{2,63})$`)

func validDomain(s string) bool {
	return len(s) <= 253 && domainRe.MatchString(s)
}
```

Domain names are case-insensitive, and the Punycode expressions only match the `xn--` prefix in lowercase, so lowercase the input before testing it.

If you care about ReDoS, it's important to keep the anchoring here: by removing the anchors, the expressions will become vulnerable to ReDoS. If you need to parse unformatted text for hostnames, split the text by spaces and attempt to parse URLs (or something like that) before testing for the regex.

The anchors also need to mean the start and end of the whole string. In Python, PHP, and Perl, `$` also matches just before a trailing newline, so `google.com\n` passes. In Ruby, `^` and `$` match at the start and end of every line, so `evil<script>\ngoogle.com` passes too. Use `re.fullmatch()` or `\Z` in Python, `\A` and `\z` in Ruby and Perl, and the `D` modifier in PHP. JavaScript and Go are fine as they are. Even in an engine without ReDoS problems, an expression without anchors accepts any text that contains a domain, like `<script>google.com`.

If you want to include *hostnames* (or other similar identifiers) which do not have a `.` separator (such as `hostname` or `my-local-hostname`), make the dotted labels optional, and allow any label as the last one as long as it starts with a letter:

```
^(?!.{254,})(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)*[A-Za-z][A-Za-z0-9-]{0,62}(?<!-)$
```

Requiring a letter at the start of the last label keeps IP addresses like `127.0.0.1` out, since URL parsers treat a numeric (or `0x`) last label as IPv4.


What's the point of all of this? Well, when working with URLs, using built-in libraries such as Python's `urlparse` or JavaScript's `URL` constructor often pose a security challenge: these libraries can interpret and accept non-standard hostnames/domain names which may break or exploit bugs elsewhere:

```python
>>> urlparse("https://googl<script>alert(1);#script>e.com").netloc
'googl<script>alert(1);'
```

```js
> new URL("https://google.com'onerror=alert(5)").hostname
"google.com'onerror=alert(5)"
```

Note: JavaScript's `URL` constructor automatically converts unicode to punycode. Python requires manual encoding:

```
>>> urlparse("https://01-БЕЗОПАСНОСТЬ.рф").netloc
'01-БЕЗОПАСНОСТЬ.рф'
>>> urlparse("https://01-БЕЗОПАСНОСТЬ.рф").netloc.encode('idna').decode() # Decodes to punycode
'xn--01--8cdeyo3chcizco4m.xn--p1ai'
>>> urlparse("https://google.com").netloc.encode('idna').decode() # No need to decode, but it doesn't hurt
'google.com'
```

The above punycode-supported regular expressions have been tested against:

**Pass**:

```
stackoverflow.com
foodemo.net
bar.ba.test.co.uk
www.demo.com
foo.co.uk
regexr.com
g.com
xn--d1ai6ai.xn--p1ai
xn--stackoverflow.com
lol.international
xn--niato-otabd.xn--niato-otabd
stackoverflow.xn--com
stackoverflow.co.uk
google.com.au
a.net
0-0o.com
0-oz.co.uk
0-tension.com.br
0-wh-ao14-0.com-com.net
a-1234567890-1234567890-1234567890-1234567890-1234567890-1234-z.eu.us
www.google.com
abcdefghijklmnopqrstuvwxyz.ABCDEFGHIJKLMNOPQRSTUVWXYZ
google.com
mkyong123.com
mkyong-info.com
sub.mkyong.com
sub.mkyong-info.com
mkyong.com.au
g.co
mkyong.t.t.co
mkyong.com
```

**Fail**:

```
127.0.0.1
1.2.3.4
xn-fsqu00a.xn-0zwm56d
0123456789 +-.,!@#$%^&*();\\/|<>\"\'
12345 -98.7 3.141 .6180 9,000 +42
555.123.4567
+1-(800)-555-2468
g-.com
com.g
-g.com
-0-0o.com
0-0o_.com
-a.dot
a-1234567890-1234567890-1234567890-1234567890-1234567890-12345-z.eu.us
foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk.foo.co.uk
mkyong.t.t.c
mkyong,com
mkyong
mkyong.123
.com
-mkyong.com
mkyong-.com
sub.-mkyong.com
sub.mkyong-.com
stackoverflow.xn--com-
```

