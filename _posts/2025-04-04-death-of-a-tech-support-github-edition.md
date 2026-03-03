---
layout: post
title: "Hello, Kafka Support Here, How Can I Help You? GitHub Edition"
tags: [essays, dev_tools]
description: "A Kafkaesque experience with GitHub support regarding case-sensitivity bugs in commit emails, and dealing with unhelpful 'AI' style responses."
---

In a [previous post](/slack-is-broken-with-noscript), I outlined how I found an extremely annoying bug in Slack's website, causing it to automatically redirect me to an invalid page every single time I visited the Slack website with NoScript enabled. Looking to get this issue fixed, my post outlined how support could not be more unhelpful, informing me the broken website was, in fact, working completely fine and as intended, and it wouldn't be "fixed" because there's nothing to be fixed! Eventually, my only way to get the issue fixed was to report it via Slack's bug bounty, where technologically-inclined people were available to look at my issue. In this post, I'll outline a similar story about experiencing a bug in GitHub, reporting the bug with full technical details, and receiving useless feedback and the typical "it's your fault it's not working, we won't fix anything". Of course, the bug has been fixed, and it was not "my fault".

---

I've recently been experimenting with setting arbitrary user email addresses for each of my git repositories on GitHub (more on why in another post), and came across some interesting functionality involving uppercase characters in email addresses in the GitHub UI. It is generally well-known that when you commit a change in git, two email addresses are associated with the commit: one for the "committer" (the person committing the change) and one for the "author" (the person who wrote the change). We can view the separate author and commiters' email addresses by using, for example, `git log --pretty=format:"<%ae> | <%ce>"`:

```
<author email> | <committer email>
<MegaManSec@users.noreply.github.com> | <MegaManSec@users.noreply.github.com>
<19999111122@Joshua.Hu> | <joshua-github-JoshuaHu@joshua.hu>
```

For the first commit, we see both the author and commiters email address are the same. In the second commit, the author email is different from the commiter email. GitHub has a handy design in which its UI displays the fact that the author and committer have different emails (or, are different people). When the author and committer are the same, the standard `<name> committed` is shown on the commit. However, when the author and committer are different, a message `<name 1> authored and <name 2> committed` is shown instead. This can be useful, for example, when a PR has to be refactored, but the project owner wants to include the original author's name when committing; or some commit policy, who knows.

But, GitHub had a bug. If the _commiter's_ email had a single uppercase letter, the UI would always display the author and committer as two different people. To figure out why this bug was occurring, I considered each case:

| Committer     | Author        | Names Listed |
|---------------|---------------|--------------|
| test@test.com | test@test.com | 1            |
| Test@test.com | test@test.com | 1            |
| test@test.com | Test@test.com | 2            |
| Test@test.com | Test@test.com | 2            |

Email addresses are case insensitive, so all of these should list one name in the GitHub UI. However, as we see, if the author's email address includes an uppercase character, two names are listed -- even if the author and committer both contain the same uppercase character.

It seemed obvious enough to me: somewhere in GitHub's code, they were converting the committer's email address to lowercase before comparing it to the author's email address -- but they had forgotten to convert the author's email address to lowercase before comparing the addresses. This explained why an uppercase character in the committer's email address would not result in two names being listed on the GitHub UI, if the author's email address was all-lowercase, while any uppercase character in the author's email address would result in two names. This bug has existed since at least 2021, because I found a [StackOverflow post](https://stackoverflow.com/questions/61599585/github-says-authored-and-committed-different-people-but-its-the-same-person-and/69691073#69691073) partially describing the problem as well.

Alright, bug found, bug explained, time to report it to GitHub's support so they can fix it. That's where it all went wrong.

Providing a link to an example commit where the UI shows a different committer and author despite a single address used, I provided the simple reproduction steps of:

```
git config user.email Test@joshua.hu
echo 'a' >> README.md
git add README.md
git commit -a -m 'test'
git push origin main
```

The response?

>GitHub matches your commit email against the verified addresses on your account.
>From what I see, the commit uses Test@joshua.hu, which is not one of the emails you have on file (i.e [snip] or MegaManSec@users.noreply.github.com).
>
>To fix this, you can either:
>Add the exact email from your commit to your GitHub account under Settings > Emails, OR
>Update your local Git config to use one of your verified addresses:
>git config user.email "[snip]"
>
>After that, any new commits should show the same author and committer details in GitHub’s UI.

What? I don't care about "verified addresses". I replied with a screenshot of the issue: a commit with both the author and committer emails set to "Test@test.com", and one with both emails set to "test@test.com".

![Bugged GitHub UI](/files/GitHubUI.png)

The support person went on:

>It appears this limitation arises from how Git handles email addresses.
>Although email addresses are typically case-insensitive by industry standards, Git doesn’t normalize them and instead treats each email string literally.
>As a result, commits made with test@test.com and Test@test.com are viewed as separate identities in Git.
>You may notice the same behavior in certain GitHub views, as GitHub is built on Git.
>That said, both Git and GitHub provide ways to address this.
>
>Locally on Git, you can use gitmailmap to unify these case variations by mapping them to a single author in logs and stats.
>
>Here’s an example .mailmap file that merges test@test.com and Test@test.com into one identity under your verified address ([snip]).
>Place this file at the root of your repository, commit it, then run git shortlog -sne to see all commits grouped under the same author:
>
>
>Joshua Rogers <[snip]>  Joshua Rogers <test@test.com>
>Joshua Rogers <[snip]>  Joshua Rogers <Test@test.com>
>
>Here’s an example of the difference in output without and with a .mailmap file:
>
> Without mailmap
>$ git shortlog -sne
>     3  Joshua Rogers <test@test.com>
>     2  Joshua Rogers <Test@test.com>
>     1  Joshua Rogers <[snip]>
>
> With mailmap
>$ git shortlog -sne
>     6  Joshua Rogers <[snip]>
>
>For more details, consult the git check-mailmap documentation and the mailmap section of the Git documentation.
>
>Currently, GitHub doesn’t support mailmap files.
>For GitHub, if commits use the same address but differ only by capitalization (e.g., Test@test.com vs. test@test.com), adding any one of those variations to your account will link all related commits to the same user.

Once again.. what? Nice wall of text; but that doesn't help at all. This has nothing to do with my problem at all? Are they trolling me? My response:

>Thank you, but that still doesn't resolve the issue.
>
>"Git doesn’t normalize them and instead treats each email string literally. As a result, commits made with test@test.com and Test@test.com are viewed as separate identities in Git"
>
>If that's the case, why is the commit https://github.com/MegaManSec/github-support-example/commit/c5d50f6e3cbf21617a903516f7b349f1b3e34d7a showing as two people? It is a single email address: Test@test.com.

They responded:

>The “two people” you’re seeing are the commit’s author and committer. You can confirm this by running:
>
>git log -1 c5d50f6 --pretty=format:"%H%nAuthor: %an <%ae>%nCommitter: %cn <%ce>%nDate: %ad%n%n%s%n%b"
>
>Which shows:
>
>c5d50f6e3cbf21617a903516f7b349f1b3e34d7a
>Author: Joshua Rogers <Test@test.com>
>Committer: Joshua Rogers <Test@test.com>
>Date: Tue Mar 18 20:27:13 2025 +1100
>
>Commit with unverified email with uppercase
>
>In Git, the author and committer can be different entities, so they’re listed separately.
>
>On GitHub, each email address in a commit is matched to an account if it’s already registered.
>If there’s no GitHub account associated with that email address, the commit remains unverified or appears under a separate identity.
>By adding Test@test.com to your GitHub account, those commits will be linked to you.

At this point, I couldn't believe this wasn't some prank; the support person is telling me that the committer and author can be two different people, and that's why they're listed separately -- despite literally copying and pasting the full git log, showing that the author and committer are the exact same. I decided the most productive thing to do would be to dumb down everything to the level of responses I'm getting:

>Hi Rocky,
>
>Me click link: https://github.com/MegaManSec/github-support-example/commit/c5d50f6e3cbf21617a903516f7b349f1b3e34d7a and two people are shown for author/committer
>yes very good
>Me run your git command `git log -1 c5d50f6 --pretty=format:"%H%nAuthor: %an <%ae>%nCommitter: %cn <%ce>%nDate: %ad%n%n%s%n%b"` and see author and committer
>
>but me no see different between "Author: Joshua Rogers <Test@test.com>" and "Committer: Joshua Rogers <Test@test.com>"
>Why same person as author and committer show two people in github link? Me no understand

That seemed to work:

>Thanks for your patience.
>
>I understand how this could be confusing.
>I’ve reached out to our engineering team for further clarification on why uppercase and lowercase emails might be treated differently.
>As soon as I hear back, I’ll let you know.

Great! Mission accomplished after 7 days since the original report! However, I couldn't put past the fact that the support person implied that _I_ was fundamentally the one that doesn't understand something, by stating that "_[it] can be confusing_". "I've asked them for clarification why the the emails may be treated differently" -- Blah blah blah, just say "Oh, it looks like this is a bug indeed."

---

So, I decided to troll a bit:

>Yes, it is very confusing, and I am very confused by this.
>So how can I fix it?

I was recently inspired by the post ["My Scammer Girlfriend: Baiting A Romance Fraudster"](https://www.bentasker.co.uk/posts/blog/security/seducing-a-romance-scammer.html), where the author followed a "romance scammer" by pretending to be a man named "Carl". "_Carl struggled with spelling (which got worse as conversations progressed)"; "Carl's spelling degraded over time"; "The initial drop-off in Carl's spelling hadn't been entirely deliberate, but once it started I decided to let it happen to see how much of a headache they were willing to put up with._" So, I decided to be like Carl.

My replies got more and more distorted:

> Thnk you! It's been rly confusng not knoing what's goin on. Is there a way 2 get my email adress verifid as Jooooooooshua@joshua.hu (Look @ teh J)? And will my commts w/ that email show up as 1 persn or 2?

...

> Ooh thx u sir. Added email Test@test.com so commit w/ that shows mine. But says email used? How fix? Confuse cuz made commits w/ it b4.

At this stage, the GitHub support page started acting up, and my replies were being sent (with confirmation via email), but they weren't appearing on the page. More trolling ensued:

> i reply b4 but it not in the page??? page broken maybe?? idk but i did say the thing plz read the msg:

> i fink dis page broken?? i klik coment und it load https://support.github.com/ticket/personal/0/3292787?sequence=5 but message not write??

> ok website is fized. so how 2 ad Test@test.com? it say mail in use already?

After a day, the website seemed fixed, and I got reply. The ticket was then closed as completed (it had not been fixed).

> Y tiket clos?

The reply was:

> Oops! Sorry about that. It looks like the status I set caused the ticket to automatically close after 4 days. We'll keep it on hold until we hear back from the engineering team.

In response to this, I sent one last reply:

> P̸̜̥͇̈̎̃͝ĺ̶͎e̴̛͉͂̓a̴͔̯̫͔̐̇͝s̸̮̻̔̏e̴̪̱͉̖̐ ̷̯̹̮̽̚͝͝h̸̗̼̃̐̉e̴̝̜͋ͅl̵̠̳̇́p̷̛͚͎̄͆͗͜ ̵̻̫̳͙̽̂̀ī̴̯̱̖͇̈́͂̅t̶̜͉͗̚ ̷̞͍̬͋̏̂̕͜i̵̜̹̺͒͜s̷̟͖̑ ̴̞͇̊͌̋͑s̸̱͓͘ỏ̷̱̪̮̬͆̾ ̷̨̠̹̦͋̅ç̸̉̅̐o̶͙͕͖̲͝n̵̞͂f̶̺̿̐u̷̘̻̘̎s̸̙͈̭̈́̃i̶͉̝͘n̷͔̎͌͆̕g̸̹̈̄̑
