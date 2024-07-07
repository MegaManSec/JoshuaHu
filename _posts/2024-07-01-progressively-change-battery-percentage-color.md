---
layout: post
title: "Cute color progression for my battery status indicator"
author: "Joshua Rogers"
categories: journal
---


Around a decade ago I was building a custom version of i3blocks (read: a version that _just works for me_) and wanted to display my battery percentage status, color-coded to the percentage: progression from green for 100%, and red for 0%. As the battery status shifts up and down, I wanted the color to also change towards yellow (for 50%), and then towards red/green depending on the value. This isn't technologically interesting and it's just a 5-minute C program that I wanted to save the documentation somewhere for the future. Anyways, yay for additive RGB and bitshifts! 

Consider red, green, and yellow in RGB
```
FF0000 -- Red - 0%
00FF00 -- Green - 100%
FFFF00 -- Yellow - 50%
```
From kindergarten we know that to get yellow, we mix green and red. Therefore from 0% to 50%:
```
FF0000
FF0100
FF0200
...
FFFE00
FFFF00
```

Effectively, for percentages 1-50, we need to add more green until fully saturated. Per percentage (1-50), we need to scale the progression of the green-ness by 1/50: `0xFF/50=5.1` so for every percentage of battery from 1 to 50, we add 5.1 of "green-ness".

```C
if(battery <= 50){
	double green_ratio = battery/50.0; // Ratio of battery out of 50
	int green = 0x0000FF; // A full color in the RGB model, shift 8 to move it to G.
	int red = 0xFF0000; // Red

	green *= green_ratio; // Multiply by the "green-ness" ratio
	green = green << 8; // Push into the G of RGB
	sprintf(rgb, "#%06x\n", red + green);
}
```
There's some truncation that happens related to the green-ness (can't add the .1 of green) but whatever.

For 51-100%, the formula is pretty much the same, but given yellow (FFFF00), we slowly _decrease_ red. i.e:

```C
if(battery > 50) {
	double red_ratio = (battery-50.0)/50;
	int red = 0x0000FF; // A full color in the RGB model, shift 16 to move it to R.
	int yellow = 0xFFFF00; // Yellow

	red *= red_ratio; // Multiple by the 'red-ness' ratio
	red = red << 16; // Push into the R of RGB
	sprintf(rgb, "#%06x\n", yellow - red);
}
```

---

I used the same algorithm for monitoring some kernel state in freebsd related to memory, namely `vm.stats.vm` and page_size, free_count, cache_count, inactive_count, and page_count.
