---
layout: post
title: "Credential Stuffing Done Right: Some Tips"
author: "Joshua Rogers"
categories: security
---

---

Say you’re someone with a massive list of usernames and passwords that have been hacked over the years, and you want to take perform what the cool kids of today call “credential stuffing”: attempting to use those usernames and passwords on a specific website in order to gain access to accounts on that service. How would you do it in the most sensible and productive manner?

Whether it be DropBox, Skype, Uber, GitHub, RuneScape, Bank websites, Crypto exchanges, or just email accounts, using previously compromised credentials in new locations remains one of the most successful methods to compromise accounts for a specific website en-masse.

If I were to do this, I would approach it systematically. Specifically, I would ask the following questions.

---

Does the website have a published password policy? If not, can we determine some restrictions on the password, like length or character set? Does the JavaScript on the password creation/change page provide any hints?

If so, filter out any user:pass combinations whose passwords are invalid for the website.

---

Does the website have any restriction on username or email (whatever is used to log in)? Can those restrictions be discerned via the registration page? Is there a maximum or minimum length? Are all characters accepted?

If so, filter out the user:pass combinations whose usernames/emails are invalid for the website.

---

Perhaps most importantly: does the website leak the existence of accounts based on usernames or emails? Is there some oracle to determine whether an account exists such as a lookup feature (banks, for example, may tell you that an account doesn’t exist when you try to transfer money to an email address), registration page, login page, profile page, high score page, change username/email page, or something else?

if so, use it to determine which accounts from your username:password list actually correspond to real accounts. The biggest waste of your time is checking whether credentials work for accounts that don’t even exist.

---

Does the login process implement any form of rate-limiting or use of captchas after a certain amount of invalid logins?

If so, is there an alternative method of authenticating which doesn’t? Is there a support panel that doesn’t? A secondary or peripheral website which is connected to the same accounts database? How about all of the different (iOS, android, Microsoft store, macOS store) app versions? Is there an alternative API?

---

Is it possible to simply bypass the captcha or rate limiting? Are there any bugs in the implementation? Can an AI guess the captcha? Can you just remove the captcha data from the request (or send other values such that it gets accepted due to weak typing)?

---

Does the website reset the invalid login count after a successful login? I.e on a website that forces a captcha after 3 invalid logins can you:

1. Login with an unknown login (invalid login)
2. Login with an unknown login (invalid login)
3. Login with a known valid login (valid login)

Such that you can now check 2 more invalid logins, using a valid login to avoid the captcha every time?

---

Does the website support IPv6? A /32 block (4 billion addresses) are extremely cheap, and protections don’t normally start blocking /48 blocks at a time like they should.

---

Is the block even IP-based or can we get around it by wiping cookies, local storage, or some other state?

---

Can we send some header like X-Forwarded-For to spoof the address?

---

If none of these can help, then it looks like you’re buying ip addresses from some botnet. You can get about 100,000 addresses for 100USD for 24 hours.

---

Can you determine how long an IP address is blocked/captched for? If it’s not too long, write your checker to re-try proxies after that time.

---

Can you determine how many failed login attempts cause a captcha/block? If so, invalidate the proxy locally after that amount of invalid logins. For example, if the website blocks you after 3 failed logins, don’t bother even trying the proxy if it’s been used for 3 failed logins - you don’t need confirmation that a proxy is dead.

---

Proxies (especially public ones) are slow and may even be dead. Retry requests using them if there’s a connection failure: count how many connection failures in a row have occurred: 3? Mark the proxy as dead. If a connection is successful, set the connection failures to 0: it’s alive (for now)! I implemented something like this [in an account checker I wrote in C (note to self: don't write an account checker in C)](https://github.com/MegaManSec/RS-Account-Checker).

---

Does the website have some type of bot detection? Bypass it using [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) and/or [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver).

---

Work out the minimum state required to login, and the best endpoint: does the website have an idempotent API which requires no state? If so, use it.

---

You’ll want to do all of this using some type of VPN or proxy. Once the website operators find out about this, they’ll look back and find the first probing. Just because you’re checking accounts using proxies, Tor, a vpn, or some hacked server, doesn’t matter your reconnaissance can be done using your real ip.

---

Although some problems can be solved with literal brute force, that doesn’t mean that’s how they’re best solved. Fine-tuning attacks for the environment provides higher quality results and speeds up the attack: time saved can be spent on performing whatever action you actually want to use these accounts for.

All of the listed questions, solutions, and examples here come from real-world cases. This stuff isn’t rocket-science but it requires some patience to do properly. Most of the work involved is not in the checker itself but rather how you “massage” the data you feed the checker.
