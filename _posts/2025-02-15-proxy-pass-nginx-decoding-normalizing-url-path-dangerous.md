---
layout: post
title: "proxy_pass: nginx's Dangerous URL Normalization of Paths"
author: "Joshua Rogers"
categories: security
---

I have recently been looking into dangerous path normalization by webservers (and browsers!) and ways to exploit typical configurations that are used on the internet. I've been looking at how servers handle the forward and back-slash characters (`/\`) and the dot (`.`), as well as their URL-encoded values, `%2F %5C %2E` respectively. I have detailed this problem in depth [in a proposal](https://megamansec.github.io/CSPT-CSP-Mitigation-Proposal/#problem-description) to extend the Content-Security-Policy feature, however today I want to discuss three ways this problem can be exploited, and how nginx's `proxy_pass` directive is commonly configured to allow exploitation, without operators realizing.

# The Problem

---

At its most basic, the problem I'm looking at is that paths in HTTP are no different from paths anywhere else: they can contain `/../` to traverse a path backwards. For example, `/dir1/../dir3/` really just means `/dir3/`. This has resulted in a whole vulnerability class called "path traversal vulnerability", where some applications will, for example, open a user-defined file like `/legit-file/../../../../etc/passwd` and read the server's password file.

Great, not really anything interesting there: it's a known problem. However, browsers do the same thing. When your browser visits, for example, `https://example.com/dir1/../dir3/`, it _normalizes_ the `/dir1/../dir3/` path before the request is even sent, sending only `/dir3/`. The rules for this normalization follow the [WHATWG URL Standard](https://url.spec.whatwg.org/), and include horrible historical edgecases like `\` being treated as `/`.

Some webservers do accept the `/../` (or even `\..\`) syntax in their paths and will automatically normalize the path before processing the request, if you are able to send a path without it being normalized by the client before the request is sent (as long as the path traversal doesn't attempt to access out-of-bounds directories -- aka above the webroot).

## %2F%2E%2E%2F

---

The problem is that some webservers will process `%2F%2E%2E%2F` -- the URL-encoded version of `/../` -- as a traversal, too. Some webservers do, some don't. Browsers do not. There are various security-related issues related to this, but let's look at three.

### Cache Poisoning

---

Consider a system with two servers: a frontend reverse proxy, and a backend server. The frontend is configured to cache all responses for the path `/static/.*`, and never cache responses for the path `/login/my-account-details`.

When requesting `/static/../login/my-account-details`, the frontend server automatically normalizes the path as `/login/my-account-details`, and ensures that the response is NOT cached.

However, take for example a request to `/static/%2E%2E%2Flogin%2Fmy-account-details`. Browsers consider this path to be accessing the `/static/` folder and a file named `%2E%2E%2Flogin%2Fmy-account-details`. If the frontend server also considers the path to be the  `/static/` folder and a file named `%2E%2E%2Flogin%2Fmy-account-details` (because it does not _decode_ the path), it WILL cache the response.

Now, if the backend server _does_ perform _decoding_ of the path, and then _normalizes_ the decoded value, the backend server will process the request as if the user were visiting `/login/my-account-details`, responding with that page. The response will be cached by the frontend server, which may contain sensitive information.

This is a case of frontend (no-decoding), backend (decoding then normalizing).

[ChatGPT](https://nokline.github.io/bugbounty/2024/02/04/ChatGPT-ATO.html) was vulnerable to this, which resulted in full account-takeover.

### Path Confusion Authentication Bypass

---

Consider a system with two servers, similar to the above one. However, instead of caching, the problem relates to access control.

If the frontend server is used to restrict access to, for example, `/secret-endpoint`, and the backend server has no authentication and decodes url-encoded paths, an attacker can access `/public%2F%2E%2E%2Fsecret-endpoint` and bypass the frontend's restriction.

This is a case of frontend (no-decoding), backend (decoding then normalizing).

This type of vulnerability led to the Tomcat webserver introducing a [ALLOW_ENCODED_SLASH](https://tomcat.apache.org/tomcat-5.5-doc/config/systemprops.html) configuration option, disabled by default. This followed the disclosure of [CVE-2007-0450](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2007-0450). Apache also has [AllowEncodedSlashes](https://httpd.apache.org/docs/2.2/mod/core.html#allowencodedslashes), which dictates whether the path can contain encoded slashes at all, to decode them and then normalize them, or to allow but not decode them.


### Client-Side Path Traversal (CSPT)

---

CSPT is a type of vulnerability which relies on the fact that browsers also normalize paths when visiting pages. For example, if a website uses javascript dynamically send requests or retrieve pages. Take for example a (poor) example:

```js
const articleName = new URLSearchParams(window.location.search).get('articleName');

const articleUrl = `https://example.com/static/article/{$articleName}`;
const response = await fetch(articleUrl);
```

In this example, the `articleName` parameter is retrieved from the URL that user is viewing, and a request is made to the website, based on that parameter. However, if the parameter is `../../user-uploads/malicious-file.txt`, the page `https://example.com/user-uploads/malicious-file.txt` will be retrieved by the file -- the _browser_ performs the normalization here (but no decoding).

A (poor) solution to this issue is to use the [encodeURIComponent](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/encodeURIComponent) function on the variable. This function encodes various characters, including `? & / \`. If performed, the retrieved URL would be `https://example.com/static/article/..%2F..%2Fuser-uploads%2Fmalicious-file.txt`.

This also affects other operations which result in loading resources, like `<img src />`, for example: the browser will always normalize, if it can -- but it will _not_ decode.

These types of vulnerabilities are still under-researched, but some interesting research can be found [here](https://medium.com/@renwa/client-side-path-traversal-cspt-bug-bounty-reports-and-techniques-8ee6cd2e7ca1). Likewise, you can read the [proposal](https://megamansec.github.io/CSPT-CSP-Mitigation-Proposal/) I have written for more details of this issue.

## nginx proxy_pass

---

Considering the first two vulnerabilities above pertained to a frontend (no-decoding, only normalizing) and backend (decoding and normalizing), it is possible to think of the third vulnerability in a similar manner: the frontend is simply the browser (no-decoding, only normalizing), and the backend is the webserver (decoding and normalizing).

This is where it gets interesting. nginx's `proxy_pass` directive _will_ perform decoding and normalization in most circumstances. While the first two vulnerabilities are less likely to be affected, since `location` matching _[is performed against a normalized URI, after decoding the text encoded in the “%XX” form, resolving references to relative path components “.” and “..”](https://nginx.org/en/docs/http/ngx_http_core_module.html)_ (i.e. it is both decoded and normalized), the third vulnerability is still valid.


### Vulnerable proxy_pass Configuration

---

Consider the following configuration:

```
location /1/ {
  proxy_pass http://127.0.0.1:8080/;
}
```

When a request is made to the server with the path `/1/filename`, the request is proxied to the backend, consuming the `/1/`. The backend therefore sees the path as `/filename`.

However, when the request is made with the path `/1/filename%2F%2E%2E%2F`, nginx first decodes the path to `/1/filename/../`, and then normalizes it to `/1/`. Since the `location` still matches the decoded-normalized value, it then passes **the decoded-normalized value** to the backend. The backend server sees the path `/`.

This is because the rewrite-rule variable `$1` is set to `$uri` (which is the **decoded** path) when a path (such as `/`) in the `proxy_pass` directive is set.

This means that protection afforded by the aforementioned `encodeURIComponent()` function are useless: the browser encodes the path, and the frontend server just decodes it before sending it to the backend.

From the example before, when the frontend server handles `https://example.com/static/article/..%2F..%2Fuser-uploads%2Fmalicious-file.txt`, the backend server will simply see `https://example.com/user-uploads/malicious-file.txt`.

### Safe proxy_pass Configuration

---

The above vulnerable configuration about _is_ documented in [proxy_pass](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass):

>If the `proxy_pass` directive is specified with a URI, then when a request is passed to the server, the part of a [normalized](https://nginx.org/en/docs/http/ngx_http_core_module.html#location) request URI matching the location is replaced by a URI specified in the directive:
>proxy_pass http://127.0.0.1/;
>
>If `proxy_pass` is specified without a URI, the request URI is passed to the server in the same form as sent by a client when the original request is processed, or the full normalized request URI is passed when processing the changed URI:
>proxy_pass http://127.0.0.1;

So, if a path is attached to the value of `proxy_pass`, this decoding-and-normalizing occurs. Therefore, for a safe configuration, we need to use:

```
location /1/ {
  proxy_pass http://127.0.0.1:8080;
}
```

In the above case, if we send a request with the path `/1/%2E%2E%2F`, the backend will see the exact same thing -- i.e. no decoding, because `$1` (also known as `$uri`) is the raw path.

### Vulnerable Advanced proxy_pass Configuration

---

But, what about the consumption of `/1/`? We don't want the backend to see the `/1/` path either, so what can we do?

An **incorrect** solution would be the following:

```
location /1/ {
  rewrite ^/1(/.*) $1 break;
  proxy_pass http://127.0.0.1:8080;
}
```

This is incorrect when rewrite rules are used, because when rewrite rules are used, the default uri (`$uri`/`$1`) is the **decoded** path. It's counter-intuitive, but `$1` is the raw path for `proxy_pass` only when:

1. No rewrite rule is in place,
2. There is no path specified in the `proxy_pass` directive.

### Safe Advanced proxy_pass Configuration

---

The solution then, is this:

```
location /1/ {
  rewrite ^ $request_uri;
  rewrite ^/1(/.*) $1 break;
  return 400; # extremely important!
  proxy_pass http://127.0.0.1:8080/$1;
}
```

`$request_uri` is the full, non-decoded, un-normalized path. Effectively, the first rewrite rule sets `$1`/`$uri` to the raw path.

Any value after `/1/` is extracted, and set to the path that is sent to the backend server.

Finally we use `$1` in `proxy_pass`.

The tl;dr is that if we pass any path to `proxy_pass` after the host, we **must** use `rewrite ^ $request_uri;` and use either `$1` or `$uri` in the path.

Note: In the above example, the backend will actually be passed a path with two `//` at the beginning, since we capture `/` on the second rewrite rule, and we add another `/` on the `proxy_pass` line. You can remove `/` on the `proxy_pass` line, but I left it for brevity.

Also note that the following rule results in double-encoding and should not be used either:

```
location /1/ {
  rewrite ^ $request_uri;
  rewrite ^/1(/.*) $1 break;
  return 400;
  proxy_pass http://127.0.0.1:8080/
}
```

`/1/%2F` will be passed to the backend server as `/%252F` -- the `$1` or `$uri` is really important!

#### return 400

---

Why is the `return 400;` required? Basically, rewriting (and the return statement) and `proxy_pass` occur in different passes of the configuration. The `return 400` is part of the rewriting processing. Consider the configuration without it:

1. `rewrite ^ $request_uri;` -- sets the location to `$request_uri`.
2. `rewrite ^/1(/.*) $1 break;` -- matches and rewrites `$1` from `/1/[..]` to `/[..]` and breaks from rewriting. location is still `/1/[..]`, but `$1`, which `proxy_pass` uses, is `/[..]`.
3. If there was a match in the above rewriting, rewriting processing stops due to the `break` directive, the location block is tried again. Since location still begins with `/1/`, `proxy_pass` is used.
4. If no match was made, i.e. the `$request_uri` doesn't begin with `/1/` but the normalized path does, the rewriting processing continues, with the location still being the unnormalized `$request_uri`. The rewriting processing finishes, and the location is checked again -- since it doesn't begin with `/1/` anymore (remember: it started as being the normalized location, then was switched to `$request_uri`), the location block is no longer valid -- so no `proxy_pass` is used.

If the requested path was `//1/`, the location would initially be `/1/` (since location is normalized), then would get changed to `//1/` (since it's the `$request_uri`), and the second pass of the location check would therefore no longer match. `return 400` stops the rewriting processing from occuring when no match in step 2 occurs in the above steps.

Without the `return 400` to catch the fall-through, it may be possible to (for example, and not limited to) retrieve files from the directory (if it exists). For example, requesting `//1/file.html` may result in the nginx attempting to respond with the **file** `/1/file.html` in the webroot of the nginx server, such as `/var/www/html/1/file.html`, if the location `//1/file.html` (which is now the _location_ of the request) does not get picked up by some other rule.

Exhausting, no?


### Safe Advanced proxy_pass Configuration 2

---

A more advanced configuration may look like this, too:

```
location /1/ {
  rewrite ^ $request_uri;
  rewrite ^/1(/.*) /special/location$1/folder/ break;
  return 400; # extremely important!
  proxy_pass http://127.0.0.1:8080/$1;
}
```

A request made to `/1/2` will be the the back-end server as `/special/location/1/2/folder`.

No decoding will occur, so you're safe!


## Automatically Identifying the Problem

---

I was surprised to find that there were no online tools to automatically detect this issue on webservers, either externally or internally (i.e. by probing the webserver versus analysis of configuration). Therefore, I plan to make a tool which can detect these issues automatically.

In the meantime, I've sent a PR to [gixy-ng](https://github.com/dvershinin/gixy) with a new plugin to detect this issue. gixy-ng is an actively maintained fork of Yandex's nginx configuration static analyzer. This issue will be detected automatically, with this post as reference!
