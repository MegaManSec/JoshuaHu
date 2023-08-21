---
layout: post
title: "Slack's anti-noscript dark pattern (or: an open redirect for noscript users)"
author: "Joshua Rogers"
categories: journal
#tags: [security work life]
#image: cutting.jpg
---

Hurrah! Another website that is completely broken when disabling Javascript: this time when a false redirect!

I have JavaScript disabled in my browser, and that always comes with interesting side effects. Most recently, I've discovered that except for the homepage, Slack's website is completely inoperable; not that it won't load, but that it forcibly redirects you to another website. Let's take a look.

When visiting the homepage of slack.com, the HTML source code contains the following:
```
<noscript><meta http-equiv="refresh" content="0; URL=&quot;\/?nojsmode=1&quot;"></noscript>
```

It's as simple as day to me: if JavaScript isn't enabled, the user should be redirected to slack.com/?nojsmode=1. Sure! Great!

However, something has gone wrong on Slack's end where they've tried to escape `"/?nojsmode=1"`, which has resulted in the HTML being malformed (and I offer no clues as to why they would even be using quotation marks since that would have closed the `content` tag anyway).

Visiting the homepage isn't really important to me. Visiting the login page at https://slack.com/ssb/signin_redirect is, however. Due to this glitch, as soon I as visit https://slack.com/ssb/signin_redirect_, I get redirected to https://ssb//signin_redirect?nojsmode=1 with no warning or explanation.

After contacting their support, I got nowhere. I was told it was deliberate, and that everything was working as intended -- i.e. redirecting the user to an invalid website: _"The behavior you are seeing now is the expected behavior, and not something we would take to our engineers to fix."_. 

Even after taking a a screenshot of an HTML validation website which clearly showed that the only error on the website was that one redirect/refresh tag, I was told that "we detect you are blocking JavaScript, and yes, https://ssb/ is the correct redirect link for you to be redirected to." Useless.

Finally, while writing up this blog post, I realized I could redirect the person browsing the website to _any_ URL, which is effectively an open redirect vulnerability. So I reported it to their bug bounty.

Visiting https://slack.com/joshua%2Ehu redirects you to https://joshua.hu/.

---

In response to the bug bounty report, they simply responded:

```
We have had this behavior reported to us before, and we do not feel as though this behavior poses a significant enough risk to warrant a priority fix. While the behavior does result in a redirect, open redirect is considered a low-severity vulnerability, and when combined with the fact that javascript needs to be disabled, and that it is enabled by default in almost all browsers, we do not believe the behavior poses a significant security risk.

For these reasons, we will be closing this report as Informative. Regardless, we appreciate you bringing this to our attention, and we hope you continue to submit to our program.
```

We've gone from "this behavior is deliberate" to _"this is considered a low-severity vulnerability"_ (which I completely agree with, and have no interest in collecting some $50 bounty for).

Then it hit me: this is probably a deliberate dark pattern for users to disable noscript on the Slack website, so it's easier to track users.
