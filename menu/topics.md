---
layout: page
title: Topics
description: "Browse the various posts written by Joshua Rogers, ordered and grouped by category."
permalink: /topics
---

Every post on this site, grouped by subject. If you're new here, this is the
fastest way to work out what this blog is about: pick whichever cluster looks
interesting and go from there.

## AI, LLMs, and AI slop (culture + security + tooling)

Critiques of LLM-generated code and culture, alongside hands-on evaluations of
AI-powered security tooling: what these tools actually find, and the messes
they leave behind.

* [Design taste in the age of LLMs: visualizing CVE data](https://joshua.hu/design-taste-visualizing-cve-data-llms)
* [LLMs are destroying art: the art of code, literature, and culture](https://joshua.hu/code-is-art-llm-people-losers)
* [wtf is NS_ERROR_INVALID_CONTENT_ENCODING? investigating shared dictionaries and ChatGPT breakage in Firefox](https://joshua.hu/chatgpt-fail-loading-firefox)
* [From gixy-ng to Gixy-Next: rescuing Gixy from AI slop](https://joshua.hu/gixy-ng-ai-slop-gixy-next-maintained)
* [Another AI slop story: ChatGPT vs. Human](https://joshua.hu/ai-slop-story-nginx-leaking-dns-chatgpt)
* [AI slop security engineering: Okta's nextjs-auth0 troubles](https://joshua.hu/ai-slop-okta-nextjs-0auth-security-vulnerability)
* [Retrospective: AI-powered security engineers and source code scanners](https://joshua.hu/retrospective-zeropath-ai-sast-source-code-security-scanners-vulnerability)
* [Hacking with AI SASTs: An overview of "AI Security Engineers" / "LLM Security Scanners" for Penetration Testers and Security Teams](https://joshua.hu/llm-engineer-review-sast-security-ai-tools-pentesters)

## Nginx, Gixy-Next, ReDoS, and regex security

Research into nginx configuration pitfalls — proxy_pass URL normalization,
DNS caching, allow/deny surprises — plus Gixy-Next (the maintained fork of the
Gixy configuration scanner) and work on detecting ReDoS-vulnerable regular
expressions.

* [Gixy-Next: an overview of a Gixy fork with updated, improved, and new checks](https://joshua.hu/gixy-ng-new-version-gixy-updated-checks)
* [Identifying ReDoS Vulnerabilities in Nginx Configurations Using Gixy-Next](https://joshua.hu/regex-redos-recheck-nginx-gixy)
* [Can Nginx Configurations Be Vulnerable to ReDoS Expressions?](https://joshua.hu/nginx-directives-regex-redos-denial-of-service-vulnerable)
* [A Comparison of Tools to Detect ReDoS-vulnerable Expressions](https://joshua.hu/comparing-redos-detection-tools)
* [Securely Validating Domain Names with Regular Expressions](https://joshua.hu/validating-domain-names-with-regex)
* [proxy_pass: nginx's Dangerous URL Normalization of Paths](https://joshua.hu/proxy-pass-nginx-decoding-normalizing-url-path-dangerous)
* [nginx "allow" and "deny" directives with "return"](https://joshua.hu/nginx-return-allow-deny)
* [nginx's proxy_pass DNS caching problem](https://joshua.hu/nginx-dns-caching)

## Web platform, browsers, feeds, and HTTP/TLS debugging

Debugging writeups from the web's plumbing: HTTP/2 breakage in intercepting
proxies, TLS session key extraction, sandboxed iframes, broken feed caching,
and making Firefox behave.

* [Debugging failures of HTTP/2 in Burp, mitmproxy, and browsers](https://joshua.hu/http2-burp-proxy-mitmproxy-nginx-failing-load-resources-chromium)
* [Extracting TLS Session Keys in Burp Proxy a la SSLKEYLOGFILE](https://joshua.hu/extracting-tls-session-keys-burp-proxy-debugging)
* [One-Way Sandboxed Iframes: Creating a Read-Only Iframe Sandbox That Can't Read Back](https://joshua.hu/rendering-sandboxing-arbitrary-html-content-iframe-interacting)
* [Feedburner's Caching Problem](https://joshua.hu/google-feedburner-broken-caching-if-modified-since)
* [wtf Google: cacheable rss feeds are dead, and Atom feeds are delayed](https://joshua.hu/wtf-google-feedburner-cache-problem-atom-rss)
* [Firefox now automatically trusting the operating system's root store for TLS certificates - update: it does so only for user-added ones](https://joshua.hu/mozilla-firefox-trusting-system-root-stores-qwacs-eu)
* [Slack login is broken with noscript](https://joshua.hu/slack-is-broken-with-noscript)
* [Making Firefox's right-click not suck with about:config](https://joshua.hu/firefox-making-right-click-not-suck)
* [Making Firefox's right-click not suck, even more, with userChrome.css](https://joshua.hu/firefox-making-right-click-not-suck-even-more-with-userchrome)
* [Always 'Copy Clean Link' when possible on Firefox, with userChrome.css](https://joshua.hu/2026-03-17-firefox-always-copy-clean-link-url-userchrome-css)

## FreeBSD, Macs, and hardened networking

Running FreeBSD on Apple hardware, locking down the network layer with
encrypted DNS and NTP, and assorted macOS and desktop quality-of-life fixes.

* [A Full Guide: FreeBSD 13.3 on a MacBook Pro 11.4 (Mid 2015) (A1398)](https://joshua.hu/FreeBSD-on-MacbookPro-114-A1398)
* [Webcam support on a Macbook running FreeBSD using PCI passthrough](https://joshua.hu/facetimehd-webcam-linux-vm-macbook-freebsd-broadcom-1570)
* [BCM43602: Debugging a Wifi chipset causing a whole-system hang with FreeBSD's bhyve VM](https://joshua.hu/brcmfmac-bcm43602-suspension-shutdown-hanging-freeze-linux-freebsd-wifi-bug-pci-passthru)
* [Encrypted DNS over TLS on FreeBSD with Unbound, and Blocking Unencrypted DNS Traffic](https://joshua.hu/encrypted-dns-over-tls-unbound-mullvad-freebsd-block-unencrypted-dns-traffic)
* [An automatic captive-portal resolver and DNS white-lister for DNS over TLS with Unbound](https://joshua.hu/captive-portal-automatic-unbound-resolve-forward-zone-blocked-dns-traffic)
* [Encrypted NTP using NTS and chrony on FreeBSD](https://joshua.hu/encrypted-ntp-nts-chronyd-freebsd)
* [Updating FreeBSD's datetime without DNS](https://joshua.hu/updating-freebsd-time-with-no-dns)
* [Magic Switch: share a Magic Keyboard & Trackpad between two Macs (free)](https://joshua.hu/magic-switch-easily-switch-magic-keyboard-trackpad-mouse-between-mac-macbook-macos)
* [Mounting and reading an ext4 drive on MacOS](https://joshua.hu/mounting-ext4-on-macos)
* [Swapping/Remapping the silcrow (S) key for a tilde on international Macbooks](https://joshua.hu/remapping-keys-macbook-incorrect-tilde-section-double-s-silcrow-characters-keyboard)
* [Exclusive i3 keysyms for specific programs. or: Binding Escape on imagemagick's import](https://joshua.hu/program-specific-i3-keysym-keybinds-screenshot-imagemagick-import-escape)
* [Cute color progression for my battery status indicator](https://joshua.hu/progressively-change-battery-percentage-color)

## Fuzzing and vulnerability research (AFL++, harnessing, corpora)

Practical fuzzing engineering with AFL++: harnessing interpreters and
libraries, tuning campaigns, and the tricks that make large-scale fuzzing
actually work.

* [Fuzzing scripting languages' interpreters' native functions using AFL++ to find memory corruption and more](https://joshua.hu/aflplusplus-fuzzing-scripting-languages-natively)
* [Automatically Generating a Well-Tuned Fuzzing Campaign With AFL++](https://joshua.hu/aflplusplus-generate-fuzzing-campaign-commands-options-secondary-fuzzers)
* [Fuzzing with memfd_create(2) and fmemopen(3)](https://joshua.hu/fuzzing-with-memfd-createfd-fmemopen-syscall-function)
* [Fuzzing glibc's libresolv's res_init()](https://joshua.hu/fuzzing-glibc-libresolv)
* [Fuzzing with multiple servers in parallel: AFL++ with Network File Systems](https://joshua.hu/fuzzing-multiple-servers-parallel-aflplusplus-nfs)
* [Attacking a scripting language's cryptographic functions with Wycheproof](https://joshua.hu/pikeproof-wycheproof-pike-checks)

## SSH, LDAP, and internal-network offensive engineering

Offensive tooling and techniques for internal networks: SSH-Snake, SSH
backdoors and quirks, LDAP monitoring, and post-exploitation adventures in
Kubernetes and Vault.

* [SSH-Snake: Automatic traversal of networks using SSH private keys](https://joshua.hu/ssh-snake-ssh-network-traversal-discover-ssh-private-keys-network-graph)
* [SSH-Snake Update: Multi-IP Domain Resolution](https://joshua.hu/ssh-snake-multi-ip-domain-resolution-bash-cannot-assign-list-to-array-member)
* [Achieving persistence with a hidden SSH backdoor](https://joshua.hu/sshd-backdoor-and-configuration-parsing)
* [SSH Adventures Continued: Invalid CVE-2018-15473 Patches](https://joshua.hu/ssh-username-enumeration-ubuntu-18)
* [Playing with SSH: carriage returns on stderr output](https://joshua.hu/ssh-stderr-printing-carriage-return)
* [Bash and SSH fun: SSH is eating my stdin! Or: why does my Bash script not continue after returning from a function?](https://joshua.hu/bash-script-not-continuing-from-function-ssh-eating-stdin)
* [More fun with bash: bash, ssh, and ssh-keygen version quirks](https://joshua.hu/more-fun-with-bash-ssh-and-ssh-keygen-version-differences)
* [Dumping bash variable values from memory using gdb](https://joshua.hu/dumping-retrieving-bash-variables-in-memory-coredump)
* [LDAP Watchdog: Real-time LDAP Monitoring for Linux and OpenLDAP](https://joshua.hu/ldap-watchdog-openldap-python-monitoring-tool-realtime-directory-slack-notifications)
* [Tracking a secret LoginTime LDAP attribute with Operational Attributes](https://joshua.hu/tracking-secret-ldap-login-times-with-modifytimestamp-heuristics)
* [Nagios Plugins: Hacking Monitored Servers with check_by_ssh and Argument Injection: CVE-2023-37154](https://joshua.hu/nagios-hacking-cve-2023-37154)
* [Describing All Kubernetes Pods of All Namespaces for Fun and Profit](https://joshua.hu/kubernetes-describe-all-pods)
* [Stealing All of Hashicorp Vault's Secrets Using Login Enumeration](https://joshua.hu/hashicorp-vault-secret-dumping)

## Big writeups: incidents, vulns, audits, and DoS

The long ones: a 55-vulnerability Squid audit, supply-chain backdoors, libwebp
fallout, and other incidents, audits, and denial-of-service research.

* [33 Vulnerabilities in cJSON](https://joshua.hu/cjson-json-parser-cve-vulnerabilities)
* [Hacking fun with zip-slips, tar-slips, symlinks, hardlinks, collisions, and more](https://joshua.hu/tarslip-zipslip-symlink-hardlink-generator)
* [55 Vulnerabilities in Squid Caching Proxy and 35 0days](https://joshua.hu/squid-security-audit-35-0days-45-exploits)
* [CVE-2023-4863: Fallout hits Facebook; probably much much more](https://joshua.hu/libwebp-fallout-facebook-image-compression-proxies)
* [Two infinite loop / DoS vulnerabilities in image-size](https://joshua.hu/image-size-infinite-loop-dos-vulnerabilities)
* [How to DoS MySQL/MariaDB and PostgresSQL Servers With Fewer Than 55kb of Data](https://joshua.hu/postgresql-mysql-mariadb-denial-of-service-dos-attack)
* [root with a single command: sudo logrotate](https://joshua.hu/gaining-root-with-logrotate-sudo-ubuntu)
* [Supply chain attacks and the many (other) different ways I've backdoored your dependencies](https://joshua.hu/how-I-backdoored-your-supply-chain)
* [NXDOMAIN'd: Catching unregistered domains for fun and profit](https://joshua.hu/nxdomaind-catch-unregistered-expired-domains-browser-supply-chain-attacks)
* [Network Security: Absurdity of Shared NICs with BMCs and Management Networks](https://joshua.hu/bmc-ipmi-idrac-backdoors-servers-shared-nic-management-network-takeover)
* [Bypassing Zscaler, Kandji MDM, and Apple Business Manager for Fun and Lulz](https://joshua.hu/bypassing-kandji-mdm-apple-business-abmmacos-2025)
* [No new iPhone? No secure iOS: Looking at an unfixed iOS vulnerability](https://joshua.hu/apple-ios-patched-unpatched-vulnerabilities)
* [A DoS Attack in RuneScape: In 3-Dimensions!](https://joshua.hu/runescape-denial-of-service)
* [Proxy Services, Hijacked Companies, and the Rabbit-Hole of Fake Hosting Companies and Big Sky Services](https://joshua.hu/rokso-proxy-service-hijacked-shell-companies-spam-big-sky-services)
* [Attacking a temperamental ten-year-old Jenkins server](https://joshua.hu/attacking-a-ten-year-old-jenkins-server)
* [My 2025 Bug Bounty Stories](https://joshua.hu/2025-bug-bounty-stories-fail)
* [Some Thoughts on "Fixing Security Issues"](https://joshua.hu/Thoughts-on-Fixing-security-issues)

## Auth, accounts, and credential abuse

How authentication breaks in practice: hardware keys and 2FA, session
persistence, credential stuffing, and one very broken bank PIN.

* [The End of Yubikeys as 2-Factor-Authentication? Google Breaks 2FA with Yubikeys in Favor of Passkeys](https://joshua.hu/enrolling-hardware-keys-2fa-google-workspace)
* [On the Google Account Persistence Exploit](https://joshua.hu/on-google-account-persistence-exploit-malware-session-api-token-theft)
* [Credential Stuffing Done Right: Some Tips](https://joshua.hu/credential-stuffing-done-right)
* [A RuneScape Hacker's Dream: An Authenticator and PIN Bypass](https://joshua.hu/runescape-bank-pin-exploit-bypass-username-enumeration-captchaless-login)

## Programming, tooling, and practical notes

Smaller tools and practical notes: bash oddities, decompiler abuse, crawlers,
and development-environment setups that actually work.

* [CCBot: Chrome Checker Bot for Chrome Security Releases](https://joshua.hu/ccbot-chrome-checker-bot-googlechromereleases-chromium-updates)
* [body: A bash script to get the middle of a file, instead of head \| tail](https://joshua.hu/body-head-tail-bash-script-middle-of-file)
* [ipgrep: grepping for ip addresses](https://joshua.hu/ipgrep-grep-for-ip-address-bash-freebsd-macos-linux)
* [Breaking decompilers with single-function, and no-main() C codebases](https://joshua.hu/packing-codebase-into-single-function-disrupt-reverse-engineering)
* [Flattening Arrays, Tail Call Recursion, and Stack Overflows in JavaScript](https://joshua.hu/javascript-infinite-tail-call-recursion-stack-overflow)
* [A small solution to DNS rebinding in Python](https://joshua.hu/solving-fixing-interesting-problems-python-dns-rebindind-requests)
* [NodeJS, nvm, yarn, and npm on MacOS in 2025](https://joshua.hu/nvm-yarn-npm-node-setup-macos-2025)
* [CodeQL on MacOS](https://joshua.hu/codeql-on-macos)
* [Comparing different versions of AWK with WebAssembly](https://joshua.hu/compare-different-versions-of-awk-online-with-webassembly)
* [Crawling every Debian .deb package in history from snapshot.debian.org, learning the .deb format, and finding rate-limiting bypasses](https://joshua.hu/crawling-snapshot-debian-org-every-debian-package-rate-limit-bypass)
* [Creating an eBay crawler for fun and profit](https://joshua.hu/automating-ebay-browsing-for-fun-and-profit)

## Recon and scanning

Making nmap dramatically faster at service scanning, with measurements.

* [5 Tips For Port Service Scanning 16x Faster: Part 1](https://joshua.hu/port-scanning-networks-speeding-up-nmap-for-large-scales)
* [Speeding up nmap service scanning 16x](https://joshua.hu/nmap-speedup-service-scanning-16x)
* [Improve nmap's service scanning with this 1 weird trick!](https://joshua.hu/nmap-improving-service-scanning-results)

## Video game history and culture series

Research into retro video game history around the world: regional markets,
promotional bus tours, and cross-cultural essays.

* [Video Games Around The World: South Africa](https://joshua.hu/video-games-around-the-world-south-africa)
* [Video Game History Around The World: An Essay](https://joshua.hu/video-game-history-around-the-world-essay)
* [Exploring "Bus Tours" of Nintendo and Sega: The Nintendo Challenger, Campus Challenge, and More](https://joshua.hu/exploring-bus-tours-of-nintendo-and-sega)
* [Some Thoughts on Cross-Cultural Video Game and Music](https://joshua.hu/some-thoughts-on-cross-cultural-video-game-and-music)

## Personal essays, travel, and culture series

Travel, immigration adventures, workplace culture, and the other things that
don't fit anywhere else.

* [On self-imposed constraints and shame](https://joshua.hu/self-imposed-constraints)
* [A helicopter story](https://joshua.hu/helicopter-story)
* [POV: You land at Melbourne Airport](https://joshua.hu/pov-entering-melbourne-airport-total-failure-society)
* [On being an illegal immigrant, hacking an unlimited Schengen visa, and becoming Polish](https://joshua.hu/i-was-an-illegal-immigrant-schengen-visa-overstay-poland)
* [On Iranian Censorship, Bypasses, Browser Extensions, and Proxies](https://joshua.hu/iranian-browser-extension-addon-censorship-bypasses)
* [Losing Sight and Vision of Your Mission and Culture](https://joshua.hu/losing-sight-vision-mission-of-your-role)
* [Losing Sight and Vision of Your Mission and Culture: Part 2](https://joshua.hu/losing-sight-vision-mission-of-your-role-part-2)
* [Losing Sight and Vision of Your Mission and Culture: Part 3](https://joshua.hu/losing-sight-vision-mission-of-your-role-part-3)
* [Losing Sight and Vision of Your Mission and Culture: Part 3.5](https://joshua.hu/losing-sight-vision-mission-of-your-role-part-3-5)
* [Revisiting My Old Blog](https://joshua.hu/revisiting-my-old-blog)
* [Revisiting the past: Security recommendations of a 17-year-old Joshua](https://joshua.hu/revisiting-the-past)
* [My Wroclaw tourism tips and recommendations](https://joshua.hu/wroclaw-tourism-tips)
* [How I got into the security industry](https://joshua.hu/how-i-got-into-the-industry)
* [Hello, Kafka Support Here, How Can I Help You? GitHub Edition](https://joshua.hu/death-of-a-tech-support-github-edition)
* [On using private browsing mode for half a year](https://joshua.hu/using-private-browsing-mode-only)
