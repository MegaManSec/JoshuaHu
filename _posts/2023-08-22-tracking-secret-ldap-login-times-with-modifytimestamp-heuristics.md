---
layout: post
title: "Tracking a secret LoginTime LDAP attribute with Operational Attributes"
author: "Joshua Rogers"
categories: security
---

During a recent pentest of an LDAP server, I uncovered a clever trick to disclose a hidden attribute which is used to record the exact time a user logs in. In this post, we'll delve into how this technique works, and how it can be used to expose concealed attributes like a 'VpnLoginTime'.


### The 'modifyTimestamp' Trick and Operational Attributes

_modifyTimestamp_ is a so-called _"operational attribute"_ in LDAP which is specifically designed to track the last modification time for an entry. Each user account has this attribute which looks like _20230809062809Z_. This is the YearMonthDayHourMinuteSecond that the user's account was changed _somehow_.

By regularly querying the LDAP server, we can check whether the _modifyTimestamp_ value for a specific user has changed.

If, for example, a hidden attribute for a user tracks their last login (such as to a VPN using 'VpnLoginTime'), then we don't need to see the hidden attribute: we just need to see a new _modifyTimeStamp_ and no other attribute change.

If we can see the _modifyTimestamp_ value change but we do not see any other change to the user, then we know some type of hidden attribute has been modified. If there is no hidden attribute that is being updated regularly, then we can this heuristic to strongly infer that the user has logged in at the new value of _modifyTimestamp_.

---

While tracking a hidden attribute used to keep track of when a user logs in is interesting, there's a whole other discussion about the usefulness of this. Creepy? Sure. Intentional? No. Useful? Well... Maybe an attacker can identify patterns of when a user is logging in for stalking purposes, or for a future social engineering attack with a more realistic time.

---

Of course, it is possible to hide operational attributes, which would also involve the _entryCSN_ attribute, since it also tracks time. For example: `20230818070127.624230Z#000000#002#000000`. It may also be necessary to hide the `modifiersName` operational attribute too, since it can be used to infer a change has happened (and even identify the user which made the change).
