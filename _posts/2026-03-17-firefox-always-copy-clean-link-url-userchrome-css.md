---
layout: post
title: "Always 'Copy Clean Link' when possible on Firefox, with userChrome.css"
tags: [firefox, browsers, dev_tools]
description: "A userChrome.css guide for ensuring that Firefox always copies a 'Clean Link' if available, while only showing the default 'Copy Link' button on right-click."
---

In my [last](https://joshua.hu/firefox-making-right-click-not-suck) two [posts](https://joshua.hu/firefox-making-right-click-not-suck-even-more-with-userchrome), I outlined how to clean up the right-click menu in Firefox to remove useless buttons, using either `about:config` or `userChrome.css`, respectively. One of my major complaints was that when right-clicking a link, I was presented with two buttons: one for 'Copy Link', and one for 'Copy Clean Link' -- with the latter 99.99% of the time being greyed out due to the link already being 'clean'. I found the greyed out link annoying since it simply cluttered up the menu as an unclickable button; and even if it were clickable, I wouldn't deliberately use it -- I'm so used to clicking 'Copy Link' that I just always want to click that; I don't want to make the split-second decision of copying a link based on two different buttons. In my ideal world, the 'Copy Link' button would *always* clean the link, if possible; but this is not an option in Firefox.

Since my previous posts, [realansgar](https://realansgar.dev/) reached out and offered an idea for how to achieve what I wanted, by using CSS to hide the 'Copy Clean Link' button if it was greyed out (disabled), and hide the 'Copy Link' button if 'Copy Clean Link' was not greyed out. This post goes into how to do that.

Following the same instructions as in my post about setting up Firefox to use [userChrome.css](https://joshua.hu/firefox-making-right-click-not-suck-even-more-with-userchrome), ensure that `#context-stripOnShareLink` is not set to `display: none !important;` (as the instructions in _that_ post recommend) and that `privacy.query_stripping.strip_on_share.enabled` is enabled in `about:config`. We then add the following to our `userChrome.css`:

```css
#context-stripOnShareLink[disabled=true] {
  display: none !important;
}
#contentAreaContextMenu:has(#context-stripOnShareLink:not([disabled=true])) #context-copylink {
  display: none !important;
}
```

Restarting Firefox should make it start working. The CSS basically dictates that at any time, right-clicking a link will only ever show one button: either 'Copy Link' or 'Copy Clean Link' (defaulting to 'Copy Link', but showing 'Copy Clean Link' if it is available). [This link to a blog post from Sentry](https://blog.sentry.io/seer-debug-with-ai-at-every-stage-of-development/?utm_source=tldr&utm_medium=paid-community&utm_campaign=seer-fy27q1-seerlaunch&utm_content=newsletter-secondary-ai-learnmore) is a good link to test. Since most of the link contains tracking, right-clicking should only show 'Copy Clean Link'.

Generally speaking, I would much rather it just always showed 'Copy Link' and the cleaning is opaque (to make the menu predictable). I came up with the following CSS instead:

```css
#context-stripOnShareLink[disabled],
#context-stripOnShareLink[hidden],
#context-copylink[hidden] {
  display: none !important;
}

#contentAreaContextMenu:has(#context-stripOnShareLink:not([disabled]):not([hidden])) #context-copylink {
  display: none !important;
}

#context-copylink .menu-text,
#context-stripOnShareLink .menu-text {
  visibility: collapse !important;
}

#context-copylink::after,
#context-stripOnShareLink::after {
  content: "Copy Link" !important;
  display: -moz-box !important;
}
```

This ensures that links are always cleaned if possible, and the right-click menu button always says 'Copy Link'.

Maybe Firefox will one day offer a "Copy Clean Link by Default" option, but until then, this is a good solution.
