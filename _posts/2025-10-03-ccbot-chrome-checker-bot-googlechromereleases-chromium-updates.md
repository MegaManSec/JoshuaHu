---
layout: post
title: "CCBot: Chrome Checker Bot for Chrome Security Releases"
tags: [dev_tools, programming, security]
description: "Automating chrome security tracking. CCBot is a Python tool that parses the chaotic Google Chrome Releases blog to alert on critical updates."
---

In IT (and perhaps in life in general), if you're ever doing the same thing more than once, you're doing it wrong. Indeed; if you're the head of application security at a browser company that uses Chromium and your role includes checking the official Google Chrome Release page every day or two in order to find out whether Google has patched some vulnerability in Chromium -- so you can send a Slack message directing your browser's developers to upgrade Chromium, to protect all of your users -- then you're ... doing it wrong.

A not-so-cool fact about Google, Chrome, and Chromium, is that when Chromium receives critical security updates, they do not coordinate those updates so well with all of the other browser vendors which use Chromium under-the-hood. That means that it's typical for users of Chrome to start receiving security updates at the same time that Chromium-based browser vendors first even hear about a fix. This leads to an inevitable lag between when vulnerabilities are patched in Chrome, and when they're patched in other browwsers. A patch for an exploited in-the-wild Chromium vuln? Tough luck; you'll get your (Opera\|Vivaldi\|Brave\|Edge\|whatever) security update in a week or so.

What makes this situation even funnier, is that Google does not have a feed for when they release security updates for Chrome (or Chromium). They do have a general Google Chrome Release blog, but this is completely unstructured, and there are dozens of posts every week for all versions of Chrome, including non-security updates, beta releases, and more. Typical CVE feeds are also hopeless when it comes to Chrome/Chromium, because they are also delayed, as Google simply drops security updates whenever they want.

This is generally speaking, quite ridiculous. Therefore, I created a small bot which crawls the Chrome Release blog, parses every blog post, and looks for any security releases. Instead of a human acting like a bot -- visiting the blog every day and posting a link to the blog post to inform developers that they need to upgrade Chromium in the browser they develop -- the bot can do it much more consistently.

The bot itself, which I call CCBot (Chrome Checker Bot; also named after the former head of AppSec at Opera, whose initials are CC (pronounced: _sissy_)) is quite elegant in how it works. Its source code can be found here: [https://github.com/megamansec/ccbot](https://github.com/megamansec/ccbot). It uses Google's Chrome Release blog's RSS feed, and filters for a post with the attribute (`Extended Stable updates` or `Stable updates`) AND `Desktop Update`. This filter was created by.. trial and error, basically looking at a large set of historical security update posts, and working out that Google inconsistently set the post attributes for stable desktop releases (which are the ones we care about for looking for security releases). It also needs to make sure that the title of the blog post is "stable channel update for desktop" -- because some non-stable updates are categorized with the attribute `Stable updates` for some reason (sigh). Of course, the formatting of the page differs from time-to-time because it's a human writing these blog posts in Blogger (i.e. with a WYSIWYG editor), so multiple searches are conducted to look for a security-related release:

```python
# Match the CVEs posted in the description based on HTML.
# We use two expressions based on previous occurences.
def extract_security_content(description):
    span_pattern = r'<span.*?> {0,1}(Critical|High|Medium|Low) {0,1}.*?<\/span><span.*?>.{0,5}(CVE.*?) {0,1}<\/span>'
    span_match = re.findall(span_pattern, description, re.IGNORECASE)
    if span_match:
        return span_match

    span_pattern = r'\>\] {0,1}(Critical|High|Medium|Low) {0,1}.*?.{0,5}(CVE.*?) {0,1}\.'
    span_match = re.findall(span_pattern, description, re.IGNORECASE)
    if span_match:
        return span_match

    return None

# Match CVEs posted in the post based on the rendered text of the post.
# We first render the HTML's text itself, then match the CVEs, as this is likely more consistent than HTML.
def extract_security_content_from_url(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')
    cve_section = soup.find('div', {'class': 'post-body'})
    cve_text = cve_section.get_text()
    cve_pattern = r' {0,1}(Critical|High|Medium|Low) {0,1}(CVE-\d+-\d+): ([^.]*)\.'
    cve_matches = re.findall(cve_pattern, cve_text)
    return cve_matches
```

Basically, we first check the HTML that is included in the post in the RSS feed; historically, two different HTML tags have been used, so we attempt to extract a semi-standard (with an an uneven amount of spaces...) text which these blog posts _generally_ follow. If that fails, we then render the HTML, and attempt to extract the _text_ with that semi-standard structure -- albeit still with possible one or two spaces added in (just to make it more difficult, of course).

I've previously outlined some of the issues I discovered while dealing with Google's RSS feeds, [here](/google-feedburner-broken-caching-if-modified-since) and [here](/wtf-google-feedburner-cache-problem-atom-rss), and the whole RSS feed thing is such a hassle too: one of the RSS feeds for the Chrome Release blog stopped working one day, delaying its results by a week; then a year later, they completely got rid of that RSS feed, unannounced. Still to this day, as outlined in the former post, caching of the rss feed is completely broken, and Google _really_ doesn't want you to use the `if-modified-since` http header to avoid retrieving feed data that you don't need to.

Anyways, all of this generally works still and as far as I'm aware, it hasn't missed a security announcement from Google. It did, however, once crash when the Google Chrome Release blog had a single post which included a character which wasn't ASCII, crashing Python due to an encoding error with `UnicodeEncodeError: 'ascii' codec can't encode character '\u25bc' in position 38113: ordinal not in range(128)` (the solution was simply to force utf-8 encoding). At least one browser company _still_ uses this bot (and it ain't Vivaldi) in order to alert on new security-related Chrome/Chromium releases. I think that's a failure on everybody's side: Google should really be coordinating this with large browser vendors, and browser vendors should .. have a better system to note and patch Chromium vulnerabilities -- but hey, at least Google can say Chrome is the most secure browser, and the quickest to patch vulnerabilities!

