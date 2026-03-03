---
layout: post
title: "nginx 'allow' and 'deny' directives with 'return'"
tags: [nginx, web_platform, dev_tools]
description: "The 'return' directive in Nginx bypasses 'allow' and 'deny' rules due to rewrite phases. Learn why this happens and how to fix it with try_files."
---

Another popular configuration I've found in nginx configurations is as follows:

```
location /a_folder/ {
  allow 127.0.0.1;
  deny all;
  return 200 "This is my secret folder!";
}
```

The problem is, this doesn't work as one would expect. During nginx's runtime, the first "stage" of a request is its rewrite phase ([source](https://web.archive.org/web/20250517011347/https://nginx.org/en/docs/dev/development_guide.html#http_phases)). This rewrite phase is responsible for the directives [break, if, return, rewrite, rewrite_log, set, and uninitalized_variable_warn](https://web.archive.org/web/20250517012614/http://nginx.org/en/docs/http/ngx_http_rewrite_module.html). The famous saying in nginx is "[if is evil](https://web.archive.org/web/20231227223503/https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/)". But what about `return`? Indeed, `return` can be evil, too.

In the above example, first the `return` is evaluated in the rewrite stage, and then _in theory_, the `allow` and `deny` directives are evaluated (in the `ngx_http_access_module` module). However, since `return`.. returns, the access directives are never evaluated, and the endpoint will always return what is set, no matter the intention of the configuration.

In order to do what is intended, the correct configuration is:

```
location /a_folder/ {
  allow 127.0.0.1;
  deny all;

  try_files "" @secret_msg;
}

location @secret_msg {
  internal;
  default_type text/plain;
  return 200 "This is my secret folder!";
}
```
