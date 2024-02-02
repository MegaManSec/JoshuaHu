---
layout: post
title: "The End of Yubikeys as 2-Factor-Authentication? Google Breaks 2FA with Yubikeys in Favor of Passkeys"
author: "Joshua Rogers"
categories: security
---

---

It seems that you can no longer register a FIDO2 compliant hardware token, like a Yubikey, as a 2-factor-authentication method on Google. It can now _only_ be registered as a Passkey.

I suppose it's the natural progression of things, but it is a bit annoying if you're not ready for Passkeys yet.

---

Luckily, my co-worker worked out you _can_ actually still register it if you use the directl ink [https://myaccount.google.com/signinoptions/two-step-verification?flow=sk&opendialog=addsk](https://myaccount.google.com/signinoptions/two-step-verification?flow=sk&opendialog=addsk).

Those that have multiple accounts can add the standard `/u/1/`, `/u/2/`, etc. to the end of `google.com/`. Thanks Jakub!
