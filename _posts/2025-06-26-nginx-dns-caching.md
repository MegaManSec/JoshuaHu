---
layout: post
title: "nginx's proxy_pass DNS caching problem"
author: "Joshua Rogers"
categories: security
---

# a problem

Today I learnt: nginx's `proxy_pass` directive does not obey DNS TTLs; in fact, by default, it _never_ re-resolves the IP address of a host, and only uses the IP address of the specified host which was resolved when nginx was started. This presents interesting engineering and security implications.

The problem is quite simple: if `proxy_pass` points towards an upstream server described with a hostname (or domain) -- whether it be on the internet or an intranet -- there is no guarantee that the IP address for the upstream server won't change. If you're using some cloud service, then the IP address of your service is definitely going to change quite reguarely. The DNS records of your hostname change too, but if nginx has been misconfigured, it will start sending connections to whoever/whatever picks up the now-stale IP address; you could be sending data to random people, and receiving data from random people.

The followng nginx configuration is vulnerable to this problem:

```
server {
    location / {
        proxy_pass https://myapp-prod-a1b2c3d4e5f.us-east-1.elb.amazonaws.com;

        proxy_set_header Host               myapp-prod-a1b2c3d4e5f.us-east-1.elb.amazonaws.com;
        proxy_set_header X-Real-IP          $remote_addr;
        proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  $scheme;
    }
}
```

When nginx starts, it resolves `myapp-prod-a1b2c3d4e5f.us-east-1.elb.amazonaws.com`, and then uses those results forever. In the above example, which is based on AWS loadbalancer, the IP addresses may change at any time, and the TTL for the DNS records is just 60-seconds: meaning AWS only guarantees the IP address(es) which have been resolved are correct for the next 60-seconds; much longer than forever.

# dns service discovery in nginx

An older [blog post](https://web.archive.org/web/20250617053714/https://www.f5.com/company/blog/nginx/dns-service-discovery-nginx-plus) from the nginx team outlines the different ways DNS resolution happens in nginx. The following two configurations do not perform any re-resolution:

```
server {
    location / {
        proxy_pass http://backends.example.com:8080;
    }
}
```
```
upstream backends {
    least_conn;
    server backends.example.com:8080 max_fails=3;
}

server {
    location / {
        proxy_pass http://backends;
    }
}
```

DNS resolution in the above two examples only occur at nginx's startup (and uses the default DNS resolver, e.g. `/etc/resolv.conf` or `getaddrinfo()`). The blog post goes on to give the following configuration example:

```
resolver 10.0.0.2 valid=10s;
server {
    location / {
        set $backend_servers backends.example.com;
        proxy_pass http://$backend_servers:8080;
    }
}
```

The post states:

> When you use a variable to specify the domain name in the proxy_pass directive, NGINX re‑resolves the domain name when its TTL expires. You must include the resolver directive to explicitly specify the name server (NGINX does not refer to /etc/resolv.conf as in the first two methods). By including the valid parameter to the resolver directive, you can tell NGINX to ignore the TTL and re‑resolve names at a specified frequency instead. Here we tell NGINX to re‑resolve names every 10 seconds.

So, to ensure that the hostname is re-resolved, some type of variable must be used in the `proxy_pass` directive -- we can set the hostname using the `set` directive for example, and then use `proxy_pass` with the variable. From here, we must set a proper [resolver directive](https://nginx.org/en/docs/http/ngx_http_core_module.html#resolver); in the example above, `valid=10s` can be dropped, instead using the default action of respecting DNS records' TTL values.

In my testing, it isn't mandatory for the "domain name" specifically to be set using a variable, it can be anything inside the `proxy_pass` directive (including the path). For example, `proxy_pass https://example.com/$uri` results in the `resolver` being used. If you set that `proxy_pass` directive without a `resolver` directive, you'll probably see error messages like `no resolver defined to resolve example.com`.

The downside to all of this is that we cannot use the `upstream` module while being able to re-resolve hosts unless we use nginx's paid version, NGINX Plus. So for those using the free version of nginx, there's a decision to make: is it likely that an IP address of a host will change, or do you need to use the `upstream` module more and accept the privacy, security, and unknown issues that may arise from `proxy_pass` pointing to stale IP addresses?

# a solution

The original config example in this post can be changed to the following, ensuring that TTL values are respected:

```
resolver 8.8.8.8;
server {
    location / {
        set $upstream_host myapp-prod-a1b2c3d4e5f.us-east-1.elb.amazonaws.com;
        proxy_pass https://$upstream_host;

        proxy_set_header Host               $upstream_host;
        proxy_set_header X-Real-IP          $remote_addr;
        proxy_set_header X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto  $scheme;
    }
}
```

Note: using a public resolver [may not be the best idea](https://web.archive.org/web/20250604032459/https://blog.zorinaq.com/nginx-resolver-vulns/), but YMMV. Most systems have some type of local resolver.
