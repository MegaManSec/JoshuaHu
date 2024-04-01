---
layout: post
title: "A DoS Attack in RuneScape: In 3-Dimensions!"
author: "Joshua Rogers"
categories: security
---

I was recently discussing security, bugs, and glitches with a journalist and was reminded of an interesting bug in RuneScape, which when viewed through the lens of security, can be described as a Denial of Service (DoS) attack in three-dimensions. 

In the MMORPG RuneScape, there are doors to buildings or rooms which can be closed and opened by players: these doors, like IRL, impede the movements of everybody (or NPCs) playing the game unless they’re open.

Generally speaking in RuneScape, players are spread out around the world, and if you want to open a closed door, it’s unlikely there’s going to be anybody around you to re-close it deliberately. I should note that players can position themselves in the same space as others, so there’s no bottleneck for walking through doors, either.

There are some places that players congregate to perform tasks which gain them large amounts of in-game XP: where hundreds of players are performing the same actions in unison. That’s where “the door glitch (DoS)” came in.

Hundreds of players would enter the player-owned houses (POHs) of others (sometimes even paying for the privilege) in order to utilise a piece of equipment which could provide a multiplier of in-game XP received. The players would enter the POH, perform an action for around 20 seconds, then leave, returning in around 30 seconds to repeat. Each room in a POH had doors which could be opened or closed.

The DoS was simple: simply continuously click on the location that the door _would_ be, if it were opened — in order to close it, once was opened by another player. A POH designed with only one door to the location that the players wanted to enter would be rendered useless for players: they could continuously try to open the door and enter, but due to the way the RuneScape engine works, the closing of the door would take priority over the ability to enter the room; it would simply close again before the players could move.

A video of this being performed is [on YouTube](https://youtu.be/Mn8WxgYSqoM?si=wvY-PxcI5MhvYZlr). As he commentated at 1:50.. "what's the point of closing the door? uhh.. it's funny as fuck."

It was mundane and provided zero material benefit to the person doing it: it was simply closing a door! But at the same time, people wanted to play the game, and are being continuously denied by just one malicious player. That feeling of being denied is no different from when you’re working on something online — whether it be in a game, watching a movie, or just sending an email — and your connection suddenly becomes unstable. Your flow and rhythm is disrupted, precipitating rage from your helplessness. On the side of the attacker, it’s just trolling — for the lulz — and objectively speaking, it doesn’t really matter: it’s just a door in a game.

I think they eventually removed closable doors from POHs, so technically the bug still exists, it just isn’t as fun. 
