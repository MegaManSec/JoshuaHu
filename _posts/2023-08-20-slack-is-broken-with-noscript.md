---
layout: post
title: "Slack login is broken with noscript"
author: "Joshua Rogers"
categories: journal
#tags: [security work life]
#image: cutting.jpg
---

Hurrah! Another website that is completely broken when disabling Javascript: this time with a false redirect!

I have JavaScript disabled in my browser, and that always comes with interesting side effects. Most recently, I've discovered that except for the homepage, Slack's website is completely inoperable; not that it won't load, but that it forcibly redirects you to another website. Let's take a look.

When visiting the homepage of slack.com, the HTML source code contains the following:
```
<noscript><meta http-equiv="refresh" content="0; URL=&quot;\/?nojsmode=1&quot;"></noscript>
```

It's as simple as day to me: if JavaScript isn't enabled, the user should be redirected to slack.com/?nojsmode=1. Sure! Great!

However, something has gone wrong on Slack's end where they've tried to escape `"/?nojsmode=1"`, which has resulted in the HTML being malformed (and I offer no clues as to why they would even be using quotation marks since that would have closed the `content` tag anyway).

Visiting the homepage isn't really important to me. Visiting the login page at _https://slack.com/ssb/signin_redirect_ is, however. Due to this glitch, as soon as I visit _https://slack.com/ssb/signin_redirect_, I get redirected to _https://ssb//signin_redirect?nojsmode=1_ with no warning or explanation.

After contacting their support, I got nowhere. I was told it was deliberate, and that everything was working as intended -- i.e. redirecting the user to an invalid website: _"The behavior you are seeing now is the expected behavior, and not something we would take to our engineers to fix."_. 

Even after taking a a screenshot of an HTML validation website which clearly showed that the only error on the website was that one redirect/refresh tag, I was told that "we detect you are blocking JavaScript, and yes, _https://ssb/_ is the correct redirect link for you to be redirected to." Useless.

Finally, while writing up this blog post, I realized I could redirect the person browsing the website to _any_ URL, which is effectively an open redirect vulnerability. So I reported it to their bug bounty.

Visiting _https://slack.com/joshua%2Ehu_ redirects you to _https://joshua.hu/_.

---

In response to the bug bounty report, they simply responded:

```
We have had this behavior reported to us before, and we do not feel as though this behavior poses a significant enough risk to warrant a priority fix.
While the behavior does result in a redirect, open redirect is considered a low-severity vulnerability, and when combined with the fact that javascript needs to be disabled, and that it is enabled by default in almost all browsers, we do not believe the behavior poses a significant security risk.

For these reasons, we will be closing this report as Informative.
Regardless, we appreciate you bringing this to our attention, and we hope you continue to submit to our program.
```

We've gone from "this behavior is deliberate" to _"this is considered a low-severity vulnerability"_ (which I completely agree with, and have no interest in collecting some $50 bounty for).

Then it hit me: this is probably a deliberate dark pattern for users to disable noscript on the Slack website, so it's easier to track users.

---


Credit where credit is due. I responded to the bug bounty report again stating that I do not want a bounty, I just want this fixed:
```
To be honest, it's difficult to see how a security flaw which which affects the people that try their hardest to be secure (i.e. those that disable javascript from running on random websites) is seemingly the deliberate behavior of the website.
Also, "Open Redirects" are specifically listed under the programme's "Qualifying Vulnerability Descriptions".

Regardless of all of that, I don't care about any bounty here (I made this hackerone account just to reply this): can you just fix it? Unless it's a dark pattern to try to get people to disable noscript on the slack website so it's easier to track them, I can't see any reason this is deliberate (as I was told in the support email).
It's obvious what the issue is; just put us noscript users out of our misery, please.
```

and I received a response saying they will actively look into fixing it now, since it **obviously** isn't how it should be:

```
We appreciate your concern.
After discussing your comments internally, we agree that this behavior is not ideal, and we have determined we will address the behavior as a result of this report.

That said, we still feel this behavior does not pose a significant security risk, and as such, we will unfortunately not be offering a bounty for this report.
Please let us know if you have any further questions or concerns, and we’ll be sure to get back to you as soon as possible.
```

Yay! Let's hope it gets patched soon enough.
