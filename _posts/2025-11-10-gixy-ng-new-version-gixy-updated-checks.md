---
layout: post
title: "Gixy-Next: an overview of a Gixy fork with updated, improved, and new checks"
description: "Overview of Gixy-Next: New Nginx security checks I added, and the quality degradation caused by low-quality AI-generated contributions."
categories: security
---

## From gixy to Gixy-Next

`gixy` is an old static analyzer for nginx configurations, which allows the operator to automatically discover vulnerabilities in statis nginc files. It works by reading the configuration into memory, and performing various static checks on the serialized, full configuration, with plugins (plug-and-play checks with the configuration tree). It is able to find the following misconfigurations:

- Server Side Request Forgery
- HTTP Splitting
- Problems with referrer/origin validation
- Redefining of response headers by "add_header" directive
- Request's Host header forgery
- none in valid_referers
- Multiline response headers
- Path traversal via misconfigured alias

While `gixy` generally works OK, the last real update was around 7 years ago, and there are a ton of bugs, inconsistencies, and missing support, which reveal themselves when using the tool with a large, enterprise-level (™) nginx configuration. [Gixy-Next](https://gixy.io/) is the saving-grace of this problem: it is an (semi-)actively maintained version of `gixy` which fixes all of those bugs, inconsistencies, and usability issues, and adds a ton of new checks for other security issues, while greatly improving the detection-rate for the issues that the original `gixy` scanned for.

## New plugins in Gixy-Next

In addition to major changes in _how_ detection of misconfigurations is handled in the older plugins, the new fork adds the following checks:

- If is evil when used in location context
- Allow specified without deny
- Setting Content-Type via add_header
- Using external DNS nameservers
- Using insecure values for server_tokens
- The try_files directive is evil without open_file_cache
- proxy_pass will decode and normalize paths when specified with a path
- worker_rlimit_nofile must be at least twice worker_connections
- error_log set to off
- Regular expression without anchors
- Regular expressions may result in easy denial-of-service (ReDoS) attacks
- Using a nonexistent regex capture group
- Missing default_server on multi-server configuration
- Hash used without a default
- nginx version disclosure
- Return directive bypasses allow/deny restrictions in the same context
- Low keepalive_requests configuration value

I created quite a few of these plugins, most of which I've documented previously on my blog [here](https://joshua.hu/nginx-return-allow-deny), [here](https://joshua.hu/nginx-dns-caching), [here](https://joshua.hu/regex-redos-recheck-nginx-gixy), [here](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium#nginx-keepalive_requests), and [here](https://joshua.hu/proxy-pass-nginx-decoding-normalizing-url-path-dangerous). I also vastly improved some of the other checks, which missed very obvious improvements on detection. ~~The only update of mine that has (still..) not landed yet is the "nginx's DNS caching problem" plugin, where nginx [caches the address of hostnames](https://joshua.hu/nginx-dns-caching) at runtime with no expiration until complete nginx restart, so any `proxy_pass` directive that concerns a hostname may send data to the wrong IP address if the IP address of the host has been rotated.~~ This plugin has now landed in [Gixy-Next](https://github.com/MegaManSec/Gixy-Next)!

## Further changes for quality improvement

Some of the changes I made to the engine itself include:

- Support escaped spaces and nested parentheses in configurations.
- Proper logging of what caused gixy to fail parsing a configuration, and real error reporting on error (no silent failure).
- Correct parsing of sub-blocks within a multi-nested configuration.
- Proper PCRE-specific regex parsing.
- nginx map support (a 1000-line patch to get [maps](https://nginx.org/en/docs/http/ngx_http_map_module.html) to be parsable and queryable).
- `alias` parsing support.
- Proper hostname checks against invalid/insecure origin/referer header regular expressions (another 1000-line patch that also uses `publicsuffixlist`).
- Improved local-ip-address checks (the old code missed some link-local ip addreesses in its checks).
- Standardized/added a full list of standard security headers to an incomplete list in one of the plugins that uses them.
- Added support for regex capture groups/variables being set inside `if(...)`.
- Ensured that output was deterministic (the same nginx configuration's scan output was ordered in the exact same way, every run).
- Standardized and fixed nginx configuration loading, where loading an nginx configuration that had been dumped using `nginx -T` (a single-file "configuration dump", which can be restored to the filesystem easily) was significantly different than a configuration which sat on the filesystem, resulting in fewer misconfigurations being found.

All of these changes took months to get working to a level of quality that I was happy with, especially with gixy's parser which was a mix of pyparsing rules and ... a bunch of regular expressions. Those regular expressions were the most difficult to work with, because formulation weren't so obvious. LLMs didn't help in explaining how they actually worked or why they were chosen the way they were (for the specific text they were parsing), so "fixing" them to work with the nginx configurations I had (which were valid, but gixy either rejected them or completely crashed) was ... difficult:).

In any case, the ~80,000-line nginx configurations (enterprise quality! (™)) which spanned various systems (kubernetes loadbalancers, an nginx fork acting as a web application firewall, "raw" nginx, etc) were finally scannable, and Gixy-Next could correctly detect all of the issues I could see by manually reviewing the configuration.

Before I started working on all of these changes, Gixy-Next would crash with those configurations -- and report success at the end! Indeed, _someone_ was using `gixy` against these configurations already, but ... nothing was ever reported as being vulnerable, because `gixy` was crashing upon scanning. Oops! As an estimate, I would guess that my total contributions totaled around 4000-lines changed in the Gixy-Next codebase.

## Quality degradation

Up until this point in writing, I haven't been completely truthful, as I've been using the name Gixy-Next. In reality, Gixy-Next is my fork of *another* fork, `gixy-ng`. Originally, I had submitted all of my changes to that fork, and most were accepted. _Note: If the rest of this blog post seems a bit wonky in terms of grammar, apologies: it was written before I created the Gixy-Next fork and only did some light editing after the fork!_

After landing around 70% of my changes in `dvershinin/gixy` on GitHub, the main developer of the fork, Danila Vershinin, went radio-silent. I put this down to them being busy elsewhere, and didn't see any reason to ask them to land the changes sooner rather than later; I had my local repository which I was using, so I was happy. I posted *that* fork on hackernews, and the GitHub project shot up from ~30 stars to ~1,000 within a day or so.

A few months later, the developer re-appeared, and had ... discovered AI coding assistants, like Copilot and Claude. New PRs were opened by Copilot and Claude in the repository, with the prompts and results of using these assistants, with patches being generated.

These patches were clearly modelled on the changes that I had submitted, and prompts were basically, "analyze this PR from MegaManSec and rewrite it" (such as [this one](https://web.archive.org/web/20251215162527/https://github.com/dvershinin/gixy/pull/74)).

Can you spot the difference below? Hint: there is none.

| ![](/files/my_patch.png) | ![](/files/copilot_patch.png) |
|:--:|
| *My Patch* | *CoPilot's Patch* |

This is _extremely_ annoying. Those PRs by the bots produced low-quality code which had bugs, didn't work, and even just failed to even apply in some cases. Some of them referenced my PRs, taking most of my code, but introducing mistakes by changing some things and not really solving any of the problems I had opened the PRs to actually solve. For example, I discovered that there was a major difference in the handling of configurations when they were read from a single file (nginx's `nginx -T` dumps the full configuration into a single file) versus when it was read from a filesystem across multiple files; with the former not allowing plugins to correctly search for vulnerable configurations. I only discovered this while investigating why the `add_header` plugin was reporting different results depending on whether an nginx-dump was used versus a real configuration that existed on the filesystem, but the bug affected every plugin. My patch fixed the issue in the engine, while Copilot's "solution" was to ... only change the `add_header` plugin [here](https://www.google.com/url?q=https://github.com/dvershinin/gixy/pull/80/commits/215e61d92fb77a176e1970706feeb9b2f6041cd7), neglecting the fact that this was an engine issue that affected every and all plugins. The Copilot "test" that was created was also **wrong**, and misreported this original issue as fixed [here](https://www.google.com/url?q=https://github.com/dvershinin/gixy/issues/64#issuecomment-3362580762). Once the developer finally listened that their Copilot-generated patch didn't fix the problem, they happily .. used Copilot again, _clearly_ against my patch, and fixed the issue (the only difference between my patch and Copilot's, is my patch included another unrelated change, and Copilot made a massive comment block that I didn't bother with):

| ![](/files/my_patch2.png) | ![](/files/copilot_patch2.png) |
|:--:|
| *My Patch* | *CoPilot's Patch* |

Some PRs were opened, closed, and re-opened again, randomly, by these bots, and even now, there are some PRs open which "fix" issues which the bots had (apparently) earlier fixed. That repository is now polluted with `.vscode` and `.cursor` files, [random files](https://www.google.com/url?q=https://github.com/dvershinin/gixy/pull/74#issuecomment-3358226367), [random junk](https://www.google.com/url?q=https://github.com/dvershinin/gixy/commit/0354464b302dba6738c1e7d9a9a50eee28569ed6#diff-6180bca1647efce95790149946cd34d303bcec4bb2e939a3b4531ffce46c3ba6R123), unclosed PRs, issues which have (maybe) been "fixed" but the bots simply replied to the issues instead of closing them, and so on. In some cases, Copilot has been used to create a new PR, and the old PRs / issue has just been left to rot, because the developer doesn't care to close it as "done" (I guess?). In another example, Copilot was used to build an `invalid_reference` [plugin](https://www.google.com/url?q=https://github.com/dvershinin/gixy/commit/fb929032a1a193b13a599c3bfd4d087e98023750), which was clearly a typo for `invalid_regex`. I say _clearly a typo_ because afterwards, another Copilot-generated [commit](https://www.google.com/url?q=https://github.com/dvershinin/gixy/commit/1e6d3470d038e182dc5ab80efb436cb412fe7c8a) changed the plugin name to `invalid_regex`, but forgot to update the [documentation](https://www.google.com/url?q=https://github.com/dvershinin/gixy/commit/0354464b302dba6738c1e7d9a9a50eee28569ed6), which [_still_](https://www.google.com/url?q=https://github.com/dvershinin/gixy/commit/1e6d3470d038e182dc5ab80efb436cb412fe7c8a) talks about "reference capture groups" instead of "regex capture groups". Sigh.

While bringing this up (while reporting, "there's something very wrong with many of the recent changes as they are introducing bugs and not solving the problems they claim to solve") with Danila Vershinin, Danila was told, "[as long as tests pass, I am happy](https://www.google.com/url?q=https://github.com/dvershinin/gixy/issues/53#issuecomment-3475772313)". That's ... also really annoying. If we could rely on tests for everything, then I wouldn't have all of these bugs to fix. That's a logical flaw that didn't give me confidence as to the quality of where `gixy-ng` was heading, and potentially where it is right now. Unfortunately, I no longer have access to those massive nginx configurations to see if all of the changes in the main fork have remained compatible with that configuration and some of the other esoteric configurations (i.e. some fucked up configurations that spanned edgecases built over a decade) I was testing my changes with. Reading the source code of the changes, the official fork will certainly not have a detection rate as high as it would if my patches were just applied without including AI.

In general, I find this situation ... really sad. I invested a significant amount of time into making this tool much better, and now the code that was created with love and passion was ... replaced by an inferior (most importantly) codebase, with a heartless (and apparently dumb) robot. In addition to my contributions being replaced with less-quality alternatives, most of the contributions I submitted to this project have been wiped from the git history. I don't know how, or why, but the majority (but not all) of the PRs I submitted were simply applied locally and then committed by the developer, which effectively wiped my name from the "Author" field in the commits. Links to my blog which explain (in technical detail) why certain configurations are unsafe have been replaced with local copies which are incomplete. This is not in the spirit of open-source, and ignores the simple principal of attribution.

## Gixy-Next

### **Update: December 15, 2025**

I couldn't bare the low quality commits anymore, and the developer, Danila Vershinin, seems all too happy to continue "creating" extremely low quality code with AI that is simply broken (and visibly requires multiple commits to fix the mistakes the AI makes for every one commit that ... the AI also makes), and is unwilling and perhaps unable to produce high quality code which isn't inherently broken. His commits show that he is not a serious programmer who cares about what he is developing with respect to quality, and his addition of advertisements for his company in his fork are disrespectful.

The upside of all of this is that his AI usage produced some comedy gold like [this response](https://web.archive.org/web/20251215162536/https://github.com/dvershinin/gixy/issues/63%23issuecomment-3620992032) where the developer's AI stated that "_this is more of an awareness/documentation issue than a security misconfiguration. Users working with cloud services (AWS ELB, etc.) where IPs change frequently should be aware of this behavior_" -- because notifying users of Gixy about misconfigurations and under-aware edgecases isn't ... exactly what Gixy is designed to do. Have a read of [this post](/gixy-gixyng-fork-long-live-ai-slop) to read more about my fork!

## Further work

A lot of the additions, changes, and bug fixes that I made in Gixy-Next came from simply coming across those issues myself and wanting to have a working product locally detecting various problems. For example, that [proxy_pass caching issue](https://joshua.hu/nginx-dns-caching) was something completely new to me, and I didn't want to have to detect that issue manually; so the new plugin deals with that (see my "[if you're doing the same thing more than once, you're doing it wrong](/ccbot-chrome-checker-bot-googlechromereleases-chromium-updates)" attitude). The `keepalive_requests` plugin came from coming across this issue [in-the-wild](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium#nginx-keepalive_requests). Why I mention this, is that I am sure there are more configurations that I simply do not know about, which could be included in Gixy-Next. But until somebody documents those issues, or I comes across them, automated checks remain missing. Further contributions with issues that people hold as institutional knowledge are highly appreciated! I am sure there are more vulnerabilities which crop up due to nginx configurations, so Gixy-Next is not a "completed" project by any metric.
