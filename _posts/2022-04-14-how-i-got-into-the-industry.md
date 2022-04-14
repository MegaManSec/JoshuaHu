---
layout: post
title: "How I got into the security industry"
author: "Joshua Rogers"
categories: journal
#tags: [security work life]
#image: cutting.jpg
---

One of the most common questions I get related to my job (other than, _what does it mean to work in online security?_) is how I got into the industry. "How did I become a hacker?", and "how can I do it too?" are common questions. Unfortunately, the true answer is never what people want; there is no simple method to get into this industry, and unless you are interested in security and breaking things, you're not going to enjoy it at all. It's something that you need a passion for. If you don't like breaking things, thinking outside the box, challenging assumptions and asking questions such as "why not?", it's probably not for you. Being able to say "I don't believe you" (_you_ being either a person _or_ a system) is also essential in this line of work. Challenging the status-quo, sort of thing.

However, the question about how I got into this industry has an interesting answer, which I've never really detailed so verbosely. So I thought this post would be an interesting overview of how *I* got into this big mess. So well, here we go.

When I was around 7 or 8 years old, my school friends got me into the MMORPG RuneScape. In this game, you could build up your character, gain gold, fight monsters, fight players, etc. Something similar to WoW.
Quickly getting addicted to the game, I played it every night after school with no interruption. The game was essentially free, however you could pay a small monthly charge for extra areas/quests/etc.

As it turned out, in this game, you could buy and sell in-game gold for real-life money. This meant that scammers and hackers were not uncommon in the game, as they could quickly gain gold, generally unpunished (RuneScape's ability to punish hackers and scammers was/are notoriously bad).
After being scammed myself, and I _think_(this is a long time ago) hacked, I became fascinated by how these scams and hacks worked. In reality, they weren't anything interesting; social engineering, phishing, etc.

While becoming interested in all of this, I also became fascinated with in-game glitching and bug abuse. This was something I had never experienced before in other games: abusing in-game bugs to achieve things that the developer of the game never intended. This could include things like becoming invincible, dying without losing items, making your in-game sprite some animal or a morphed version of what it should be, or in some cases, generating in-game gold or experience where it normally wouldn't be possible.

At the time, there were two online forums for people interested in this sort of stuff: Ezud, and Tainted-Ones. Tainted-Ones shut down less than a week after I signed up for it, so Ezud was my go-to forum.
The forum was a vBulletin-3 software forum and included a chatbox (way better than what Discord is these days!). On the forum, people could discuss bugs they have found (but not so much that they revealed enough details to show how it was done -- RuneScape would regularly browse the forum to find out how bugs are done, and fix them), theories for finding bugs, and some other things.

Making some friends on this forum, I was eventually shown a bug that could be used to generate some in-game items, which could be sold. I was banned a few days later in the game, and the bug was fixed.

After this, I became infatuated with finding bugs in games. From then on, the game _was_ to find bugs.
Teaming up with others, we found a variety of pretty uninteresting graphical glitches; but we were having great fun.

As time went by, I got into phishing -- the act of creating fake websites which would collect users' details when they entered their username and password into them.
At the time, various people were selling ready-to-use phishing programs on the Ezud forum. They were not so technical, and just simple PHP and HTML. I didn't really know how they worked, but I knew I could use them to hack people.
This was one of my first introductions to programming: HTML. Editing the phishing pages to my liking, so they were more realistic. I still remember buying my first domain, and wondering "ok, now what; where do I put the files?" -- not knowing that I would need to purchase hosting, too!

This went on for some time, before Ezud effectively died (at least the community). Most users migrated to a different forum, called G4HQ. It was the same sort of thing, but slightly more generalised.
On G4HQ, I learnt more and more about programming scripts for various purposes.

Around this time, I started visiting 4chan's /b/ board, getting more and more into so-called "online culture". Memes, trolling, etc. Ten years on, I still visit regularly (although I visit /fit/ mostly).

After quitting RuneScape for some time, I was introduced to the indie game TeeWorlds. This game is written in C++ (and back then, parts were in C), and is fully open-source. I was the only player in Australia among around 3,000 active players.
I met a certain German player in this game who introduced me to the likes of Linux, and "real" programming (i.e. _doing it myself_). After helping me get Linux(Ubuntu 8!) on my computer back then, he left me to learn everything myself.
At this time, I learnt about bash scripting, compilers, and general computing outside of a windows machine. I learnt about how to SSH into my first VPS, and run a headless Linux server. My first Github Account, named [JulianAssange](https://github.com/JulianAssange), was created on September 7th, 2010, when I was 13. It was great fun!
My friend had made a modified version of teeworlds which was my go-to for playing (so-called "blocker servers"). Wanting to further modify the game myself, I begged my friend for help; to which his response was always "learn C/C++, and read the fucking manual). [plz email me teh codez](https://thedailywtf.com/articles/plz-email-me-teh-codez) was certainly a common phrase.

I certainly didn't do that, but I did learn a lot about C/C++, as well as _enough_ to modify the server to work in ways that I wanted. For the record, I didn't go to school for about 2-years, so I had an unlimited amount of free time. Most of this was happening between the hours of 8PM-6AM, too; or basically, European time.
During this time, I learnt about DDoS attacks, and how easy it was to 'boot' other servers (or players) offline if I wanted to. A small perl script on a $5/month VPS, and your opponent was offline for as long as you'd like.

That's certainly where I learnt most of my programming; fiddling around with the game, and learning how things are done in programs.

Eventually, I stopped playing this game, and went back to RuneScape. As it turned out, some of my old friends had created a forum dedicated to abusing in-game bugs, called BugAbuse.Net. This was some time around 2011. I was 14 at the time
At this time, they had an issue: their forum had been hacked. A 0-day vulnerability had been found in the forum software they were using (vBulletin 4), and the hackers had added backdoors into the software meaning it could be hacked over-and-over again. One of the hackers would later be arrested for [unrelated activities](https://www.abc.net.au/news/2016-06-30/league-of-legends-queenslander-avoids-jail-over-sale-user-data/7557982).

My friends did not have any system administrative experience at all; they could use FTP to upload files to a server, but they didn't know anything else.
That's where I came in. I took over the system administrative role for the website, as well as becoming the lead admin. My friends remained as forum admins, too, but focused mainly on content moderation.
Since I knew how to run a Linux server, set up an HTTP server, and deal with the technical stuff, it was natural for me to take over. Anything I didn't know, I learnt extremely quickly; I was dedicated to the success of this forum.

This forum was more than just about finding in-game bugs in RuneScape. It also had an extremely dedicated section for hacking -- using RuneScape's in-game "recovery system". In this section, hacked databases could be posted, and various other lists, passwords, proxies, etc.
I was never able to get into "recovering" -- as it was called -- but I could hack websites. I learnt how to exploit vulnerabilities such as SQL injections, and quickly compiled a large cache of hacked databases.
Since most databases contained hashed(encrypted) passwords, I then learnt how to use the likes of Hashcat to decrypt them. If I couldn't hack something, I found a way to -- it was all a learning experience.

The forum was frequented by a variety of people that also hacked big-name forums related to RuneScape. Users would then use this data to try to "recover" RuneScape accounts, in hopes that their accounts contained a lot of in-game items to be sold. The forum had 25,000 members, and nearly 5,000 active users (logins within a week) at all times throughout its history. 
In some cases, the forum members hacked more than RuneScape forums. The huge [XSplit software's website was hacked in 2013](https://www.pcgamesn.com/xsplit-servers-hacked-reset-your-passwords-now) with passwords being leaked for millions of users. In many cases, we trolled some famous streamers since we had their XSplit passwords, and it was a great fun time.
Doxing, swatting, and the likes, were all common. Nothing was off limit -- except for credit cards.
Many of the hackers from the forum went on to be arrested for other things, such as [hacking Uber](https://www.zdnet.com/article/hackers-who-extorted-uber-and-linkedin-plead-guilty/).

On the RuneScape side, my efforts to troll the various employees were a huge success, and helped me learn programming even more. For example, in one case, I was given a username and password list for around 5,000 RuneScape accounts. So I created a script which would log into 10 of these at a time and post on the official RuneScape forum, spamming some random junk.
We even got a shoutout from the CEO of the company [behind the game](https://secure.runescape.com/m=forum/sl=0/forums?294,295,293,65202916) in 2013, where he wrote "This has also resulted in an increase in immature users at malicious forums like BugAbuse.Net DDoSing and stealing from many individual players". We consequently emailed him requesting the changing of text, with a fake legal threat claiming defamation; which surprisingly, he did.

For the record, I was -- and I suspect still am -- one of the best trolls I have ever met, with a natural ability to get someone to yell at their screen (or inside their head IRL) if I want to. All for the lulz.

By being exposed to so many other people interested in hacking, I gained so many skills and knowledge about everything around it. If people were discussing something I didn't know about, I went and learnt about it. It was a passion, and something I was extremely interested in.

On the server administrative side of things, I had to quickly learn about how to stop DDoS attacks from others (not a fun time), hacks, and other issues.
Learning from the ground-up how to secure against _other_ hackers certainly contributed to my ability to hack, myself. This also includes things such as social engineering attacks, and rogue moderators which we employed. Learning how to rollback in MySQL was definitely a vacation-ruining experience (a moderator had been hacked, and their account was used to delete every single post on the forum; we did not have backups, but recovered it with some peculiar mysql function).

Creating new features for the forum helped me learn how to program in PHP. I believe the forum was one of -- if not _the_ -- first website which offered a search engine for leaked details.
Similar to haveibeenpwned/leakedsource, users could purchase access to a private section on the forum where they could search leaked databases for a person's details, including passwords, email, etc.
In some cases, I purchased "private" databases to add to the search engine, resulting in even more subscriptions.
Learning more C to create a so-called "login checker" or "login brute forcer" was also a highlight.
I learnt about SEO, and at one stage, when you googled "Runescape", my forum was the 9th result on Google -- with the title "Runescape Hacking Forum". Quite amusing at the time.
I learnt about advertising, as well as managing money.

While this was all great fun, this time was also full of stress, and life lessons. Beyond the typical computing skills associated with hacking, systems administrative, and general tinkering, I learnt how to deal/manage people -- both as an administrator of a website with 5,000 active users (25,000 in total!), and as someone that had to mediate and facilitate deals between hackers.
In this environment, being an open person was the worst thing you could do -- the more information you revealed about yourself, the more likely you would be harassed, attacked, and/or fucked over somehow. But being able to quickly and naturally answer questions with fake details (i.e. lie, but naturally and quickly!) is a skill that I don't take for granted -- it has saved me in real life multiple times. The ability to close a conversation when you want to, and just say "no", too.

Fake 'friends' who were only there to use you (for your resources, skills, or what-not) were common, and I quickly learnt how to determine whether somebody was trustworthy or not. Unfortunately, this has resulted in me being a fairly closed person about my emotions and my life with *normal* people in real life -- because, somehow, I have it in my mind that the more I talk about my _personal_ life/feelings/details, they will be used against me somehow.
Fortunately, this has also meant I have developed a pretty good skill at determining who is a good person and who isn't -- very quickly. Who is valuable and who isn't, and what should be revealed to who. I have been commended on my ability to do that before. Strange, but unsurprising; I'm normally the first one to figure out someone has nefarious intentions.

The phrase "honor among thieves"("thieves will not steal from each other") was something I quickly came to realise was not true. In that landscape, everyone was out to profit (either monetarily or 'for the lulz') at anybody's expense.
Interestingly, some people, which fucked me over for nothing more than a few dollars, have gone on to do great things. Others from this time of my life, which I met online, have become some of my best friends IRL.

The forum slowly died, as did the whole hacking community around RuneScape, around 2015, when I was 17 or so. Slowly, I lost interest, and got into other hobbies. I shut down the forum when I started university since it was just breaking even. But these skills you never forget; it's not about how to do something specific, it's about how to learn to do it -- and the theory and ideas around them. The game may change, but the rules never do.

Surprisingly, I never got into serious trouble for any of this stuff. My home was raided by the police twice. In both cases, nothing happened, and my equipment was returned; I was never charged with a crime. I am still terrified whenever my doorbell rings between 05-08AM, because that's the standard "police raid" time. Not that I do anything illegal, these days.

**TL;DR**:
If you're not interested in breaking things, then the online security industry is probably not for you. If you like to be critical of things, and scrutinise every detail of certain things (e.g. a program or system), then maybe it is. You need to be able to think outside the box, and, like a jellyfish, wrap your tentacles around every single piece of a system, understanding how everything is. connected and works together. Then you need to be able to break that down, piece-by-piece, working out what is wrong -- and how it can be exploited.

In my case, I learnt nearly everything I know about hacking and computers by simply always asking the question "how was this done/made?" I also learnt about computers by creating modded versions of the Teeworlds game, and running various servers. Then I was put in a position which allowed me to put into practise everything I had learnt (being an administrator of a 25,000-member website dedicated to hacking). I learnt the necessities of programming because I needed it to grow my forum, and my modded game servers. I somehow had a network of people that helped me learn the skills needed to get into "computing", and I am indebted to them for their friendships and support over the years -- it's any wonder why they did that for me. Maybe they thought I was funny :).
