---
layout: post
title: "Chromium leaking the Referer header despite no-referrer"
tags: [security, browsers, privacy, bug_bounty]
description: "Chrome ignored Referrer-Policy: no-referrer for fonts and images loaded from inline CSS, sending the full page URL to same-origin servers and the origin to everyone else. I reported it in January 2025. After four unanswered requests for updates, it was fixed in Chrome 158 in November 2026 as CVE-2026-130935, with a $2,000 bounty."
---

This is the short story of CVE-2026-130935, a bug/vulnerability I reported to Google on 2025-01-25, which was [fixed](https://chromereleases.googleblog.com/2026/11/stable-channel-update-for-desktop_01699533288.html) on 2026-11-17.

A [referrer policy](https://www.w3.org/TR/referrer-policy/) is a website's declaration to a browser, asking it to modify the algorithm used to populate the Referer header when fetching subresources, prefetching, or performing navigations. For example, a website can use the `no-referrer` policy to prevent the browser from sending the Referer header completely, or the `same-origin` policy to send it only when the request is made to a URL with the same origin. The `origin` policy sends only the origin, without any of the other specific details (URL path, and so on). This allows websites to control how much information about the referring page is disclosed to connected-to websites. These days, browsers default to `strict-origin-when-cross-origin`, which sends the full URL (excluding #fragments) to same-origin requests, only the origin to cross-origin requests, and no header at all for https -> http requests.

While working at Semrush, I discovered that Chrome / Chromium was not respecting the "Referrer-Policy: no-referrer" policy when making requests for fonts, in the typical `<style>@font-face ...` manner. When a request was made to the same origin, the full referrer was sent to the src URL. When the request was cross-origin, the origin populated the Referer header. Since `no-referrer` was used, neither of these things should have happened. According to the [bug report](https://issues.chromium.org/issues/392139161), the bug also affected images loaded via CSS, but I never looked into that.

I discovered this bug by accident. For "business requirement" reasons (lol), Semrush was passing around authz tokens in GET parameters on its website. Other than the obvious reasons for this being a stupid thing to do, it also meant that these tokens were being leaked into logs, from logging on the pages of every same-origin request which was being fired when a user visited a page with the tokens in the URL.

In addition to the leaking of confidential data from the URLs, there are quite a few good reasons to use a referrer policy to completely scrub the Referer header, including privacy.

The bug was first worked on at the beginning of April 2025, in [this](https://chromium-review.googlesource.com/c/chromium/src/+/6427352) still-open change request. It went silent, and my requests for updates in July, September, November, and January were ignored. In October 2026, the fix was merged. As I noted in my "bug bounty 2025" [post](https://joshua.hu/2025-bug-bounty-stories-fail#chromium-security-feature), "It was marked as P2 / S2. 90-day full disclosure policy, anybody?" (note: it was actually P2 / S3, I was wrong in that post).

Anyways, nearly two years later, the bug was fixed. A $2,000 USD bounty was awarded.

# Timeline

| Date | Event |
|---|---|
| 2021-05-27 | [CL 2896901](https://chromium-review.googlesource.com/c/chromium/src/+/2896901) was merged. A Chromium engineer later said this change probably introduced the bug. |
| 2025-01-25 | I reported the bug, tested on Chrome 131. |
| 2025-01-28 | Google reproduced it (also on Chrome 132) and set it to S3 severity, P2 priority. |
| 2025-04-03 | The assignee linked the bug to CL 2896901, noted that images loaded via CSS were affected too, and started a fix in [CL 6427352](https://chromium-review.googlesource.com/c/chromium/src/+/6427352). That change is still open. |
| 2025-07-02 | I asked for an update. No reply. |
| 2025-09-02 | I asked again. No reply. |
| 2025-11-27 | I asked again. No reply. |
| 2026-01-07 | I asked again. No reply. |
| 2026-10-19 | The bug was reassigned to another engineer, who picked it up. |
| 2026-10-20 | The fix, [CL 8602043](https://chromium-review.googlesource.com/c/chromium/src/+/8602043), was merged, and the bug was marked fixed. |
| 2026-10-21 | A follow-up fix for when the policy comes from `<meta name="referrer">`, [CL 8603655](https://chromium-review.googlesource.com/c/chromium/src/+/8603655), was merged. |
| 2026-11-17 | Chrome 158 was released to stable with the fix, listed as CVE-2026-130935 in the [release notes](https://chromereleases.googleblog.com/2026/11/stable-channel-update-for-desktop_01699533288.html). |
| 2026-11-18 | A $2,000 bounty was awarded. |
| 2026-11-20 | This post. |
