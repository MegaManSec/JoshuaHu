---
layout: post
title: "Making Firefox's right-click not suck with about:config"
tags: [firefox, browsers, dev_tools, macos, ai]
description: "A practical about:config checklist to declutter Firefox right-click menus on macOS, disabling AI/chatbot prompts, link previews, OCR, visual search, and other low-value context menu items."
---

On a fresh installation of Firefox on MacOS, right-clicking an image while some text on the page is highlighted (to show as many buttons as possible) looks like so:

| <img src="/files/holyshit-firefox.png" alt="Firefox fresh-install right-click" width="400"> |
|:--:|
| *Freshly installed Firefox, right-clicking* |

To be blunt: holy fucking shit, what the fuck is all of this shit? 26 rows of which 2 are greyed-out (aka: fucking useless), 7 dividers, 2 submenus; because a single row for "Ask an AI Chatbot" wasn't enough, they just had to make another _submenu_. Amazing.

The "Inspect Accessibility Properties" button was added because I opened the DevTools (Inspector) once. It's not obvious how to actually disable it ever again. Why am I shown "Copy Clean Link" if there is no clean link (or the link is already clean)? The same goes for "Copy Clean Link to Highlight". Why can't I make it so it always defaults to the "clean link" no matter what (and get rid of "Copy Link" completely, instead)? "Ask an AI Chatbot"? No, fuck you.

The rest? Completely useless. Thanks for showing me every feature you've ever shipped, with no authoritative selection of what users actually care about -- and making it completely non-obvious how to disable the useless shit here.

Enough venting, let's clean this all up. The following settings in `about:config` can be used to disable a ton of these useless right-click menu buttons. Note, some of them actually disable other functionality, so choose wisely. We can set the following to `false`:

* `browser.translations.select.enable` -- Removes the "Translate Selection" button from the right-click menu.
* `screenshots.browser.component.enabled` -- Disables the built-in Firefox screenshot functionality, which also removes the "Take Screenshot" button.
* `dom.text_fragments.enabled` -- Disables Text Fragments support, which also removes the "Copy Link to Highlight" button (and disables the auto-focus on URLs that include `#:~:text=...`).
* `privacy.query_stripping.strip_on_share.enabled` -- Removes the "Copy Clean Link" / "Copy Link Without Site Tracking" buttons.
* `devtools.accessibility.enabled` -- Disables the DevTools Accessibility Inspector and removes the "Inspect Accessibility Properties" button.
* `browser.ml.chat.menu` -- Removes the "Ask an AI Chatbot" button.
* `browser.ml.linkPreview.enabled` -- Disables Link Previews (and the AI-generated key points inside them), removing "Preview Link" button.
* `dom.text-recognition.enabled` -- Disables OCR on images, removing the "Copy Text From Image" button.
* `browser.search.visualSearch.featureGate` -- Disables Visual Search (Google Lens integration) and removes "Search Image with Google Lens" button.
* `extensions.formautofill.addresses.enabled` -- Disables address autofill and the associated menu/button that sometimes appears in forms.
* `extensions.formautofill.creditCards.enabled` -- Disables credit card/payment method autofill and removes the associated menu/button that sometimes appears in forms.
* `widget.macos.native-context-menus` -- Turns off native macOS context menus so Firefox uses its own menus. This removes the "Services" button.
* `print.enabled` -- Completely disables Firefox' printing UI and capabilities, which also removes the "Print" and "Print Selection..." buttons.

How do we look now?

| <img src="/files/firefox-fail.png" alt="Firefox right-click after disabling the above options" width="400"> |
|:--:|
| *Firefox right-clicking, after disabling everything above* |

Great, much better, we're down from 26 buttons to just 15. Here's what it looks like when you right-click on a page and when you right-click a link:

| <img src="/files/firefox-click-notext.png" alt="Right-clicking on a page" width="250"> | <img src="/files/firefox-click-link.png" alt="Right-clicking on a link" width="250"> |
| :--: | :--: |
| *Right-clicking on a page* | *Right-clicking on a link* |

We still have the following useless buttons though:

* "Bookmark Link..."
* "Save Link As..."
* "Email Image..."
* "Set Image as Desktop Background..."
* "Bookmark Page..."

Why do all of the above have `...`? ~~No clue~~ (edit: according to [this](https://news.ycombinator.com/item?id=47252016), "_it means that more information is required to complete the task (e.g. requesting the filename for saving a file)_". But the real bad news is that we can't get rid of these things by simply toggling some option in `about:config`.

We also have these when we right-click in a form:

* "Check Spelling"
* "Languages"

| <img src="/files/form-firefox-annoying.png" alt="Form right-click annoying buttons" width="300"> |
|:--:|
| *Right-clicking in a form* |

Despite the browser only being used in one language, there is no way to get rid of the "Languages" menu there. It's possible to get rid of "Check Spelling" by completely disabling spellcheck, but that's a useful feature for me, so I don't.

Those remaining useless buttons can only be removed by creating a custom [userChrome.css](https://www.userchrome.org/what-is-userchrome-css.html). I'll cover how to do that in my next post.

---

For what it's worth, it is nice that these buttons can be enabled/disabled, and `userChrome.css` is cool. But at the same time, imagine being a completely new Firefox user, who has zero use for any of this? How are they supposed to figure out how to do all of this? It took me a significant amount of time to find those settings to disable (and some of them are hacks, like disabling `print.enabled`). Maybe Firefox should implement something similar to their "Customize Toolbar", which makes it easy to plug & play each of the right-click buttons. "PRs welcome" as they say, I suppose.
