---
layout: post
title: "From gixy-ng to Gixy-Next: rescuing the nginx security scanner, Gixy, from AI slop"
tags: [gixy, nginx, security, ai_slop, programming]
description: "Introducing Gixy-Next, a maintained fork of Gixy for modern Python: improved nginx config parsing, new plugins, normalized output, and a local in-browser scanner."
---

I recently decided to fork and maintain a new version of the Gixy nginx security tooling, calling my fork *Gixy-Next*. The official website is [https://gixy.io/](https://gixy.io/), and the source code is available on GitHub at [MegaManSec/Gixy-Next](https://github.com/megamansec/gixy-next). The Python package is available on [PyPi](https://pypi.org/project/gixy-next), but there's also an [online scanner](https://gixy.io/scanner/) which can be run in your browser (locally; with WASM).

For those who don't know, Gixy is an nginx static analysis tool which was originally developed to automatically find vulnerabilities in nginx instances by parsing their configurations, and running a set of checks against them (each check being performed by a "plugin"). The original Gixy however, no longer works on modern systems, erroring out in any actively maintained version of Python:

```
NameError: name 'SRE_FLAG_TEMPLATE' is not defined. Did you mean: 'SRE_FLAG_VERBOSE'?
```

Gixy-Next works on all modern Python3 systems and adds a whole ton of new functionality, but has an unfortunate history related to its forking which I'll detail here as well.

# The Good: Gixy-Next

Gixy-Next comes with a massive amount of changes made from the original Gixy, and it's difficult to document all of them.

- 19 new plugins were added, centered around access control, resolver/DNS, proxying, regex safety, and performance footguns.
- Standardized/normalized output across all findings, allowing proper automation related to output (e.g. JSON output now normalized to be reproducible).
- `map` and `geo` support.
- Brand new security plugins:
  - `allow_without_deny`: flags `allow ...;` used without an accompanying restrictive deny (like `deny all;`) in the same scope.
  - `return_bypasses_allow_deny`: warns when `return ...;` appears in a context using `allow/deny` (because `return` is not restricted the way people often assume).
  - `proxy_pass_normalized`: flags `proxy_pass` with a URI path component (common source of path normalization/double-encoding surprises).
  - `merge_slashes_on`: flags `merge_slashes on;` due to normalization/mismatch risk.
  - `resolver_external`: flags `resolver` entries pointing to external/public resolvers.
  - `stale_dns_cache`: flags patterns where upstream hostname resolution may become stale/unsafe.
  - `version_disclosure`: flags missing/unsafe `server_tokens` behavior when full config is available.
  - `invalid_regex`: flags cases where config references regex capture groups that do not exist (often leads to incorrect routing/security logic).
  - `regex_redos`: optional plugin that checks regexes for ReDoS risk (see Tooling).
  - `add_header_content_type`: flags attempts to set `Content-Type` via `add_header`, since it can create duplicate `Content-Type` headers.
  - `add_header_multiline`: flags header values that contain a newline (often from `add_header` formatting).
  - `add_header_redefinition`: flags cases where defining any `add_header` in a nested context stops inheritance.
  - `default_server_flag`: flags `listen` blocks where no server is explicitly marked `default_server`/`default`.
  - `error_log_off`: flags `error_log off;` because `off` is not a valid target, it's a filename.
  - `hash_without_default`: flags `map`/`geo` style constructs missing a `default`.
  - `if_is_evil`: flags `if` inside `location`, since many `if` usages there have surprising semantics.
- Brand new performance plugins:
  - `try_files_is_evil_too`: flags `try_files` usage that is missing effective `open_file_cache` behavior.
  - `unanchored_regex`: flags unanchored regex `location` patterns that can be slow.
  - `low_keepalive_requests`: flags unusually low `keepalive_requests`.
  - `worker_rlimit_nofile_vs_connections`: checks that `worker_rlimit_nofile` is present and sized relative to `worker_connections`.
  - `proxy_buffering_off`: flags `proxy_buffering off;` (often a perf/throughput hazard).
- Modified security plugins with enhanced checks (higher true-positive rate and lower false-positive rate):
  - `origins`
  - `ssrf`
  - `http_splitting`
  - `alias_traversal`
  - `valid_referers`
- Parsing is now more compatible and less error-prone, especially across Python versions and edge cases.
- Input files are now consistently checked, with clearer errors if anything goes wrong.
- `include` directives are now correctly handled, meaning full nginx configurations are properly scanned.
- Regex-related checks are more compatible with real-world nginx parsing and less error-prone.

Along with all of the changes made to the codebase, I rewrote all of the documentation in a standardized-ish way, and put it on a website: [gixy.io](https://gixy.io/). It shows example bad configurations, good configurations, and most importantly, *explains the issues of why the bad configurations are bad, and the good configurations good*. In addition to documentation updates, I also created a really nice feature on this otherwise static website: [an in-browser scanner](https://gixy.io/scanner/) which uses WASM to load the Python package in the browser, allowing anybody to scan a configuration completely in their browser -- without sending their configuration to any server.

The rest of this blog post is basically ranting. Read at your own risk.

# The Bad: gixy-ng

Gixy-Next exists because another fork of Gixy, called *gixy-ng*, has turned into a dumpster fire of AI-generated slop, bug-ridden code, and emoji-filled documentation, which did not allow systems administrators to simply answer the question, "is my nginx configuration secure?" Gixy-Next came about because I wanted a scanner that did not trade correctness for velocity, did not accept unreviewable AI slop as normal, did not ship random editor artifacts, did not break core behavior and then hide behind tests, and did not treat open source as a vehicle for advertising or attribution laundering.

I've previously written about my adventures in finding new types of misconfigurations in nginx, as well as my adventures of submitting PRs to gixy-ng. In my [last post](https://joshua.hu/gixy-ng-new-version-gixy-updated-checks#quality-degradation), I outlined the poor quality code that was being "created" by the maintainer of gixy-ng, Danila Vershinin (`dvershinin`), which among other things, included:

- AI-written code which simply did not do what it advertised itself as doing.
- Obvious regressions and broken code which would not pass simple human reviews.
- Massive thousand-line changes which did not actually solve any problems that a few 10-liner changes could have solved (typical AI rewrites) and simply could not be reviewed due to the changes made.
- Outright incorrect information that recommended unsafe configurations to users.
- AI-generated junk files like `PR_ISSUE_ANALYSIS.md`, `.vscode/..randomjunk`, etc.
- PRs that flip-flopped between open and closed by Cursor, CoPilot, Claude, and VSCode bots.
- The developer stating that "if tests pass, any changes are fine".
- Tests changed to "prove" fixes worked, but incorrectly covered the issues they were supposed to prove (see that "last post" for some examples).
- Attribution stripped from some of my (dozens) of PRs and re-committed in the name of either the maintainer or one of the AI bots.
- Marketing injected into all output, all documentation, and source code.

In my previous post, I concluded with the note, "*I don't actually recommend anybody else use my local fork, so I should just get over [complaining about the ai slop]*". Since then, my thoughts have changed. This change of mind came after [my report](https://web.archive.org/web/20260000000000*/https://github.com/dvershinin/gixy/issues/63) which introduced a plugin for checking when nginx may use [stale DNS records](https://joshua.hu/nginx-dns-caching) when proxying. In that case, the maintainer used AI to respond with the following:

| ![gixy-ng's dvershinin producing an AI slop response](/files/slop/1.png) |
| :----------------------------------------------------------------------------: |
|           *gixy-ng's dvershinin producing an AI slop response*           |

So, Gixy -- whose sole purpose is to highlight misconfigurations that may result in issues -- is not the right place to detect when a configuration includes an insecure configuration, because "this is documented behavior", and "this does not apply to users who restart nginx regularly". The "references" for documentation in his response is a random nginx *blog* from 2015 **which is only accessible via archive.org**, and **my** blog. The "restart nginx" thing is so laughable, it just reminds me of that Rasmus Lerdorf quote:

> I'm not a real programmer. I throw together things until it works then I move on. The real programmers will say "yeah it works but you're leaking memory everywhere. Perhaps we should fix that." I'll just restart apache every 10 requests.

I pushed back, calling that total bullshit and that his response was as trash as his AI. His response was, "*You don't want to flag and report on millions of configurations that use a hostname in nginx configuration knowingly.*" Moments later, however, his bot reopened the issue, and commented, "*You're right, I apologize for the dismissive response. I reviewed your implementation more carefully and it's actually well-designed:*". His bot then did not commit my code, but turned my elegant code into 500-line of broken code (which also copied significant blocks of code that were exact copies of what I had written). I once again pushed back saying the code he wrote was broken. His bot created another 1000-LoC change, which was also riddled with bugs (and emojis), including blocks that as soon as you see it, you know "this isn't going to be good":

| ![more gixy-ng AI slop trash code](/files/slop/2.png) |
| :---------------------------------------------------: |
|           *more gixy-ng AI slop trash code*           |

Because nothing yells high quality codebase, like a hard-coded incomplete list of TLDs. And yes, the code was checking whether any of the hostnames ended in those TLDs, and decided whether a hostname is a domain name, if it ended in that. Shoutout to my friends working in `.ai` (for example) that just don't exist, I guess.

In another response, dvershinin (actually AI written again) responded:

> You criticize AI-generated code while your own commits show:
>
> Typos in commit messages
>
> Squashing unrelated changes together
>
> No PR, no tests provided via our test framework, no documentation

The irony here is that:

- The "typos" referenced here is a single-letter typo, like "finall" instead of "final",
- There were no squashes made.
- 8 tests were provided via the test framework, of which his AI bot stole a few verbatim.

At a certain point, there was no point fighting anymore: it was clear that the project's quality is simply in the toilet, and it would be more productive for me to simply fork the project, rip out the LLM-written (and dvershinin-approved) junk which doesn't work, and go on my merry way. So, that's what I've done.

Of course, my fork hasn't gone unnoticed. In a collection of [two](https://web.archive.org/web/20260000000000*/https://github.com/dvershinin/gixy/commit/62fbeecf74a3924a58e500ba6851141dfe390e84) different [commits](https://web.archive.org/web/20260000000000*/https://github.com/dvershinin/gixy/commit/b34db411971666fd6ba552deae22734fe4b138e4), a ~3,500-LoC change to gixy-ng copied a massive amount of the changes I made to my fork (but with extra AI-generated emojis filled throughout). Not to worry, I guess.

There was one important change that was not copied by dvershinin's fork: my [Contributing to Gixy-Next](https://gixy.io/contributing/) document, which outlined the standards that are expected for all changes submitted to the codebase, including an "AI / LLM tooling usage policy". The policy is simple: do not submit code which is unreviewable, which you do not understand, and which is broken. Any usage of AI should be accompanied by a note, "AI usage: yes" but is otherwise allowed -- as long as it's high quality changes. I think that policy is fair enough.

# The Ugly: gixy-ng

As I began working on my fork, I had to review every single commit that dvershinin had made to gixy-ng, either ripping out useless or bug-ridden changes completely, or rewriting the changes so they were at a level of quality I would accept.

I realized that my previous assessment of "the developer discovering coding agents" was not completely correct. Actually going through each commit from the beginning of gixy-ng's fork, it was obvious that AI was actually always used for this fork -- it's just that the quality dropped so quickly, so fast, that I initially noticed. I suspect what happened was that dvershinin began to use some high quality albeit costly AI agent, and then either lost access to the high quality agent or had to significantly drop the price. As I wrote in my previous post, the quality of code that Cursor/CoPilot/VSCode/Claude was committing was substantially lower than anything I had ever generated using ChatGPT; indeed, I suspect the original generally-ok-quality changes were made with ChatGPT, while the newer extremely-low quality changes were made with something else. Who knows.

While reviewing all of the changes made, I noticed a ton of amusing bugs, which are in some cases dangerous. I will detail some of them below: just the most amusing (and general "wtf?") ones (there were a lot of random bug fixes related to the fork but also the original gixy code, however I didn't document them very well.)

## Unsafe add_header_inherit

In gixy-ng's `add_header_inherit` plugin, the plugin incorrectly states that if the directive `add_header_inherit on;` is used, headers are merged between contexts.

| ![gixy-ng's incorrect solution for header inheritance issues](/files/slop/3.png) |
| :------------------------------------------------------------------------------: |
|           *gixy-ng's incorrect solution for header inheritance issues*           |

The recommendation to use `add_header_inherit on;` to solve the issue of headers being dropped between blocks in an nginx configuration is simply incorrect. NGINX's [documentation](https://nginx.org/en/docs/http/ngx_http_headers_module.html#add_header_inherit) clearly states that the correct parameter to solving this solution is the `merge` parameter

> The merge parameter enables appending values from the previous level to the values defined at the current level.

Anybody using gixy-ng and following the output of the plugin will be setting themselves up for failure.

## "example.com" does not need to contain "."

gixy-ng added some functionality to load variables via a configuration file. The loading was broken, and this was exemplified in the *broken test*, too.

| ![gixy-ng's broken test for configuration loading](/files/slop/4.png) |
| :-------------------------------------------------------------------: |
|           *gixy-ng's broken test for configuration loading*           |

Can you see the issue? The test is basically:

```py
foo_host = "example.com"
assert not foo_host.must_contain(".")
```

But how could `example.com` not MUST contain `.`? It's got `.` right there in there. Indeed, the code was broken, and the test broken. But hey, as the developer says, “[as long as tests pass, I am happy](https://web.archive.org/web/20260000000000*/https://github.com/dvershinin/gixy/issues/53#issuecomment-3475772313)", right? Sigh.

## Double `version_disclosure` reporting

In the `version_disclosure` plugin, the nginx configuration is checked for the usage (or lack there-of) of `server_tokens`. A check first runs to see whether `server_tokens` is set to `on` or `build` (which is deemed insecure). A second check is used to determine if the `server_tokens` is not set -- which is also deemed insecure due to its insecure default.

The code itself is basic for the initial "check where `server_tokens` is specifically set". But the check for when `server_tokens` is not set at all was .. totally insanely stupid.

| ![gixy-ng's insanely stupid plugin code](/files/slop/5.png) |
| :---------------------------------------------------------: |
|           *gixy-ng's insanely stupid plugin code*           |

The whole screenshotted code is from this "check when `server_tokens` is not specifically set" section. Can you spot the problem?

The problem is two-fold:

1. The highlighted code is wrong because the configuration `server_tokens on;` passes this check, meaning it never returns.
2. The rest of the code specifically looks for a `server_tokens` call .. which means `server_tokens` must specifically be set .. which has already been dealt with before this code was run.

The consequence of this was multiple reports for the same issue. The solution was to delete the non-highlighted code, and simply return if `server_tokens` was found in the `http_block`, regardless of whether it was `on`, `off`, or otherwise (because in that case, it would already have been dealt with).

## localhost is not local

Take gixy-ng's `get_external_nameservers` function, which is supposed to determine whether a hostname is local or not based on a tiny suffix list. Can you spot why?

| ![gixy-ng's broken get\_external\_nameservers function](/files/slop/6.png) |
| :------------------------------------------------------------------------: |
|            *gixy-ng's broken get_external_nameservers function*            |

What happens when a hostname is `localhost`? It's deemed external. Total failure.

## Advertising misses a newline

As mentioned, gixy-ng's maintainer decided it would be a great idea to add advertising for their business to the package. In addition to adding advertising on every page of the documentation, the advertising is also printed on every run, with code like this:

| ![Gixy-ng being used as advertising](/files/slop/8.png) |
| :-----------------------------------------------------: |
|           *Gixy-ng being used as advertising*           |

Among the obvious problem of adding advertising at all, the code misses a newline after the injected text. This pollutes the runner's terminal like so:

| ![Polluting my terminal](/files/slop/9.png) |
| :-----------------------------------------: |
|           *Polluting my terminal*           |

Great job! How could he not have noticed this? Oh right: because he didn't actually *test* his changes by running the application he's developing for.

## Non-gixy-ng stuff

I decided to take a look at what else the developer was doing on GitHub. What I found was .. sad, I would say.

### brain, please respond

| ![dvershinin approving a PR, then pinging a silent bot](/files/slop/7.png) |
| :--------------------------------------------------------------------: |
|           *dvershinin approving a PR, then pinging a silent bot*           |

In the above screenshot, dvershinin used CoPilot to "author" some AI slop code, which he happily approved and merged. Clearly, the AI slop didn't fix the issue, and then stopped responding. I don't know. A human treating a lousy AI coding agent as if it's a human, "ping", "hey, any updates?", etc. is hilarious to me.

This was in a repository related to one of dvershinin's paid offerings. I suppose his paid offerings are about the same quality as his gixy-ng slop, too.

| ![dvershinin's conversation with copilot](/files/slop/10.png) |
| :-------------------------------------------------------: |
|            *dvershinin's conversation with copilot*           |

### ai repository

I also noticed some other changes in a repository that he had created, which used AI to create commit messages.

| ![dvershinin trying to fix hallucinations](/files/slop/11.png) |
| :--------------------------------------------------------: |
|            *dvershinin trying to fix hallucinations*           |
| ![dvershinin trying to fix hallucinations](/files/slop/12.png) |
|                            :--:                            |
|            *dvershinin trying to fix hallucinations*           |

The three obvious notes from this commit message couldn't be better evidence of the problem:

* Prompt GPT to be factual, not inventive about changes
* Fix hallucinated commit messages and null errors
* Use gpt-4o-mini with low temperature (0.3) for factual output

The fact of the matter is, if you have to tell something to be factual and not to hallucinate, then something is very wrong.

# Wrapping Up

Gixy-Next exists for a pretty boring reason: I wanted a scanner I could trust again.

Along the way, it became hard to ignore that this was not just about messy commits or annoying AI output -- it was also about basic security competence. In another GitHub discussion, the gixy-ng maintainer asserted that they [could not see why the cache-control header is a security header](https://web.archive.org/web/20260000000000*/https://github.com/dvershinin/gixy/pull/44). That's like saying you can't see why encryption provides confidentiality: that's the whole point. Put simply, that is not a position you can hold while maintaining security tooling (or really, any software that claims to evaluate security posture). Put simply, clearly, they are not capable of maintaining a software which relies on security knowledge -- or at least, ability to Google (or even ask some AI!) about which headers are security related.

If you are running NGINX in production and you want a static analyzer that works on modern Python, handles real-world configs properly, and does not treat "tests pass" as a substitute for proper code review, give Gixy-Next a try. The docs live at [https://gixy.io/](https://gixy.io), and the in-browser scanner lets you test configs locally without downloading any code or uploading anything to a foreign server.

If you want to contribute, please do. Plugin ideas are more then welcome. If you plan to contribute code, please read the contribution guide first.
