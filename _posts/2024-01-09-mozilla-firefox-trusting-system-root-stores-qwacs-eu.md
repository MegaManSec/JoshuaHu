---
layout: post
title: "Firefox now automatically trusting the operating system's root store for TLS certificates - update: it does so only for user-added ones"
description: "Firefox now defaults to trusting user-added certificates in the OS root store. Learn about this policy shift, its security implications, and how it affects you."
categories: security
---

---

When Firefox 120.0 was released in late November of 2023, it included this small piece of information: [_Firefox now imports TLS trust anchors (e.g., certificates) from the operating system root store. This will be enabled by default on Windows, macOS, and Android, and if needed, can be turned off in settings (Preferences → Privacy & Security → Certificates)._](https://www.mozilla.org/en-US/firefox/120.0/releasenotes/).

That's a big move, especially considering it is antithetical to the goals of Mozilla, and what  Mozilla apparently stands for and believes in relation to certificates. By relinquishing the power they hold by maintaining their own root certificate store, they effectively revoke their own gate-keeping abilities -- which is a power they hold.

---

In 2019, Mozilla [posted about the goals and rationale](https://blog.mozilla.org/security/2019/02/14/why-does-mozilla-maintain-our-own-root-certificate-store/
) for maintaining a root certificate:

_The primary alternative to running our own root store is to rely on the one that is built in to most operating systems (OSs). However, relying on our own root store allows us to provide a consistent experience across OS platforms because we can guarantee that the exact same set of trust anchors is available to Firefox. In addition, OS vendors often serve customers in government and industry in addition to their end users, putting them in a position to sometimes make root store decisions that Mozilla would not consider to be in the best interest of individuals._.

For all of its browsers on all operating systems (except Linux), is this no longer true? Is this no longer the stance of Mozilla?

---

I, of course, have no explanation for any this change. Possibly it's some type of relinquishing of power in response to the EU's initiative to [weaken the security of the web with QWACs](https://securityriskahead.eu/) (and provide financial incentive for CAs to sell more unnecessary products). If Mozilla no longer enforces its root store in its browser, perhaps their argument can in the future be "we can't forcing you to use our root store, you can force EU users to install the EU trust lists into their operating systems".

Surprisingly, there seems to be little discussion on this change. Did it slip through the cracks?

Definitely something to monitor in the coming months.


---

Update: It seems at some stage Mozilla updated that blog post: _Firefox now imports user-added TLS trust anchors (e.g., certificates) from the operating system root store_. Specifically, __now imports user-added TLS trust anchors__.

So the change is actually that Firefox will automatically import **user-added** certificates from the system trust store -- and the original release notes were merely incorrect. That makes a lot more sense.

This begs the question: how does Firefox determine what a user-added certificate is? This is handled in [security/manager/ssl/EnterpriseRoots.cpp](https://github.com/mozilla-firefox/firefox/blob/main/security/manager/ssl/EnterpriseRoots.cpp), and ChatGPT summarizes quite nicely:

-   Windows: it opens the ROOT and CA stores only under LM, CU, Group Policy, and Enterprise locations that are intended for user/admin installed certs. The comment spells it out: these stores should not include Microsofts root program. It then filters for TLS server auth and imports roots from those locations only. No access to AuthRoot or other Microsoft built-in stores.

-   macOS: it enumerates third-party keychain certs, then immediately discards any cert that has trust settings in the System domain, which is how Apple ships built-ins. Only User/Admin domain trust that indicates Trust Root or Trust As Root is treated as a trust anchor.

-   Android: it calls the Java wrapper to fetch entries from the Android CA store and treats whatever comes back as roots. In Firefoxs implementation that wrapper returns user-installed CAs, not the system set. There is no code here that queries the system CA list directly.
