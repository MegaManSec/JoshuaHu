---
layout: post
title: "Firefox now automatically trusting the operating system's root store for TLS certificates"
author: "Joshua Rogers"
categories: security
---

---

When Firefox 120.0 was released in late November of 2023, it included this small piece of information: [_Firefox now imports user-added TLS trust anchors (e.g., certificates) from the operating system root store. This will be enabled by default on Windows, macOS, and Android, and if needed, can be turned off in settings (Settings → Privacy & Security → Certificates)._](https://www.mozilla.org/en-US/firefox/120.0/releasenotes/).

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
