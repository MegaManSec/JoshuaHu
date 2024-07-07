---
layout: post
title: "On using private browsing mode for half a year"
author: "Joshua Rogers"
categories: journal
---

Since the beginning of the year, I've been experimenting with a nearly-permanent use of "private browsing" in the browser on my computers, and phone.

### The Setup

On the computers, I used Firefox with "Always use private browsing mode" enabled (_Privacy & Security -> History -> Always use private browsing mode._) I shut down my computers when I'm not using them.

On my phone, I used Safari with every tab in the "private mode" section; each tab is completely separated . Something important to note is that Safari already wipes browsing history after one month; I'm not sure about cookies and other site data, but probably not. 

I use AdGuard's DNS-based adblocking on both my computer and my phone, to make life more bearable.

The purpose of experimenting with this was to determine whether it's viable to live without the hundreds of thousands of lines of history amassing in your browser, and whether any improvements could be suggested for browsers. If it's bearable, using private mode all the time can enhance your privacy, as if your history isn't stored, it can't be reconstructed simply by retrieving your device.

### My Notes:

---

99% of my browsing history is useless. Knowing that I went to the page https://website.com/page?id=2, then https://website.com/page?id=3, then https://website.com/page?id=4 and so on, does not help me in the slightest, except when I already have the tab open (to go backwards/forwards).

---

Not a single website on the internet provides a pleasurable cookie consent popup, and having to click through (sometimes multiple!) them on very website is the biggest time-waste of my browsing experience. Yes, you care about my privacy so much, that you're going to share my data with 938 of your partners. Google's consent is particularly annoying in Safari because it's so long that you need to click their button "read further" three times; but how convenient that the button to click "more options", which sends you off to another page, is in the same location as the "read further" button -- i.e. if you click the "read further" button's location four times, you need to go back and do it all over again.

---

Captchas when accessing a website. This includes Google itself (which , every website using Cloudflare, and more. Google seems to have a bug which causes, for example, _https://www.google.com/sorry/index?continue=https://google.com/search%3Fq%3Djapanese%2Bpachimon%2Bpostcards_ to redirect to simply _https://www.google.com/sorry/index_ sometimes. Then when you try to go backwards, you get immediately redirected to _https://www.google.com/sorry/index_ again, effectively losing the information of what you were searching. Sometimes the captcha also doesn't load. 

---

"Login with Google" popups on websites like StackOverflow and reddit, are similarly annoying like the cookie popups. Nobody wants to login with Google while trying to read how to perform mouth-to-mouth resuscitation. Nobody wants to login with Google except for on the login page, in general.

---

Being asked whether you want to _confirm_ whether you want to open a page using an app (i.e. some intent) instead of the browser is great (Safari only). This should be the default behavior IMO: so many times in the past I've wanted to view the website-version of something and it automatically opened the app (which may not have the information or functionality that the real website does).

---

In general, I noticed that I used websites which required logins fewer times a day than before, due to the greater resistance/higher hurdle to get to where I wanted to go. Probably, this is a good thing since that's mostly social media. For websites that don't _require_ a login, I never logged in unless I _needed_ to.

---

I found that I kept about as many tabs open at any time as I normally would; i.e. I didn't just keep every website I use open in a new tab in order for them to be more searchable. This further supports the theory that it is not a detriment to the browsing experience to not "just save everything" like the collection of history normally does.

---

Bookmarks, bookmarks, bookmarks. For everything I wanted to look at later (which I would normally be able to find by searching my history), I bookmarked the page under a folder called "read later". For websites which I visited regularly enough (regardless of the full URLs), I bookmarked as normal. I never use bookmarks normally, and these were simply so they would appear when I searched for something; basically a "forced history collection".

---

### Summary

Overall, the experience was fine: I lost a few websites and pages that I wanted to keep, but life goes on.

I also learnt that Safari/WebKit is quite horrible on iOS, with pages seemingly disappearing when you press back/forward too quickly or when pages don't load fast enough. This is incredibly annoying and there's no way recover the "missing" page since it isn't in the history.

In my opinion, the ideal experience for my browser would be:
1. No history being saved, except for some excepted domains (with a button which can "add this website to domains with saved history" somewhere),
2. No site data being saved, except for some excepted domains (as above),
3. Somehow the ability to save cookie consent cookies (or any cookies) for arbitrary websites; I don't want to save all cookie consent cookies, because then there would be a big list of every website I've viewed which has a cookie consent cookie.
4. Each tab acting as a separate/sandboxed private mode -- just like Safari. That is to say, sessions and data are allocated for each tab, and the data they hold (cookies, site data, temporary history) are not shared between them.
