---
layout: post
title: "You can no longer star archived GitHub repositories"
tags: [programming, security]
description: "GitHub no longer lets you star, or un-star, an archived repository. I archive my finished repositories, so here's what I've set up instead: a ruleset that blocks pushes, with issues, PRs, and Actions disabled."
---

I like to archive my popular, but "finished" GitHub repositories, for two main reasons:

1. If my SSH key ever gets stolen, it limits the damage that an attacker can do to my popular GitHub repositories,
2. Those repositories are, as far as I consider, "finished", and will no longer get updates.

You can't star archived GitHub repositories anymore, however. You can fork the repository and then star the fork, but it's no longer possible to star the original.

| <img src="/files/github-star.png" alt="The greyed-out Star button on my archived Squid-Security-Audit repository, with the tooltip: You can't star MegaManSec/Squid-Security-Audit" width="500"> |
|:--:|
| *"You can't star MegaManSec/Squid-Security-Audit"* |

This also means you can no longer _un-star_ an archived repository. This was reported back [in August](https://github.com/orgs/community/discussions/203738), but it seems that this "feature" has been rolled out to more users since then.

In order to achieve something similar (an archived but still public repository which will be useful for others), I've instead set up these repositories to:

1. Disallow pushing to any branch (with a ruleset),
2. Disallow creating issues, PRs, discussions, etc.,
3. Disable Actions.

How annoying.
