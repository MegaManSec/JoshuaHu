---
layout: post
title: "Creating an eBay crawler for fun and profit"
author: "Joshua Rogers"
categories: journal
#tags: [security work life]
#image: cutting.jpg
---

My first video game was a Gameboy Advance SP (the obviously superior blue version). Other than Pokemon (Sapphire Blue!), my favorite game was Super Mario World: Super Mario Advance 2.
However, since I was young, I've always been interested in old video games.
Whether that be the Magnavox Odyssey, Atari, Intellivision, or later consoles like the Sega Master System, Nintendo NES, SNES, Dreamcast, or Gamecube, something always attracted me to games that were never really intended for consumption by somebody my age.

Around the age of 12, I got into the collecting scene of retro gaming; that is, purchasing old/retro video games simply for the sake of owning them -- a collection of antiques, if you may.
Originally, I collected everything; consoles, games, and everything in-between. For every console. Eventually, I focused solely on the Nintendo Entertainment System, with a few bits and pieces which had some sentimental value being added along the way.
Doing repairs on broken systems was also a good way to practise some skills in electrical engineering (bleh).

The reason I got into all of this is for another time to discuss, but I do find the NES and its history fascinating, and video game history outside of the USA and Japan has often been neglected.
So while collecting, I also obtained a great detail of knowledge about the history of the games I was collecting.

I've talked at various conferences (such as Penny Arcade Exhibition/PAX), have [written papers](https://www.linkedin.com/in/joshua-alexander-rogers/recent-activity/posts), have [contributed to newspapers](https://www.smh.com.au/technology/nintendos-nes-launched-30-years-ago-in-australia-this-month-or-did-it-20170707-gx6ex0.html), and have even contributed to [museum exhibitions](https://playitagainproject.com/nintendo-arrives-in-australia/) about the history of video games.
I even finished my Bachelor of Arts with a final project [related to the preservation of old video games](https://joshua.hu/files/GameLost.pdf).
I've also met many great people by collecting and researching these games and their histories, including professional scholars, archivists, and people from similar professions.
One day (yeah, I'll keep saying it!) my book will be finished about the history of the NES in Australia/Europe.

Anyways, on top of simply purchasing these old systems for fun, I also bought and sold games for a profit, where I could, to fund my future purchases (I was "seriously" collecting between the ages of 15-20, so I did not have a real job).
Unlike in America, where there is a culture of giving away old video games for nearly nothing -- via garage sales, meet&swaps, second-hand/charity stores, and websites like craigslist -- in Australia, it is extremely rare to find older video games for such great prices, as most owners know that they can be sold second-hand for a nice amount of money. There's always money to be made in Australia...
This meant that the only major way to find second-hand retro video games -- being sold by the average seller, not from other collectors -- was through eBay.

With much greater demand from collectors than a supply of retro video games in Australia, searching eBay once a day or so would rarely result in finding a good deal on a game, because other people would quickly spot the listing and purchase it.
While in reality, I was checking eBay more like every hour since it was a simple f5-click on my computer, and at the time I was spending probably 14-hours a day on my computer, I still wasn't satisfied with how inefficient this was, and after missing out on some amazing deals by just 5-or-10-minutes, I wanted a solution which would automate nearly everything for me.
Likewise, I wanted a way to filter out all the listings which had been relisted (i.e. they were previously listed, and did not get sold, thus being listed again) -- since that made up most of the new listings on eBay, and I wouldn't be buying those items anyways.

My solution was to create a simple bot that, every few minutes, would do the following:
1. Retrieve the latest eBay listings in Australia with the keyword "NES" (in XML format).
2. Loop through each of the auctions, adding all of the information into a database if it had not already been entered.
3. Determine whether any of the new listings were in fact _new_ -- not relistings, and create a small notification if a _true_ new item had been listed.
4. Check old auctions and log their ending prices and details, if they sold (or not).
 
In addition to alerting me to unique new listings, I also wanted to retrieve and store historical data from listings from eBay, because it was interesting for both myself and other collectors to be able to look back further than eBay's public "past listings" history, about how much certain games sold for (some rare games would appear on eBay only once a year, and eBay's website only displayed 90-days worth of history).
Therefore, once a listing had ended, the script would also update the database with some information about whether it sold or not, how much it sold for, the number of bidders (if it was an auction), and so on.
If I remember correctly, I wanted to store the names of all the people who bid on auctions -- and how much they bid -- but there was no simple way of doing this using eBay's API, and it likely would not have been overly helpful for us anyways. In the end, I simply stored the winning bidder's name and details.

I decided to write this bot in PHP since it had in-built XML parsing, and MySQL handling and this project was not complicated at all. The source will probably never be publicized either, so I could write it as horribly as I wanted!

**Step 1: Retrieve Latest Listings**

eBay provides various APIs for retrieving data from its website. In order to retrieve the "latest listings", I used the "findItemsAdvanced" API, which spews out some basic information about the most recently listed items ([example in JSON](https://developer.ebay.com/devzone/finding/callref/Samples/findItemsAdvanced_basic_out_json.txt)).
Most of that information was useless to me, so I solely used this API to grab the unique listing item (_itemId_).
Enumerating each of the _itemid_ values, the local database was queried to check whether there were any new listings.

**Step 2: Retrieve Information About Latest Listings**

If there are any new listings that had not been added to the database, the next step was to retrieve all the information about that listing, and decide what to do with the data.
eBay provides another API to retrieve detailed information about listings, called [GetSingleItem](https://developer.ebay.com/devzone/shopping/docs/CallRef/GetSingleItem.html#detailControls).  They also provide an API to retrieve information about the shipping details of an item (some listers would inflate shipping costs, making their listing appear cheaper in the "original price") named [GetShippingCosts](https://developer.ebay.com/devzone/shopping/docs/CallRef/GetShippingCosts.html).
By using these two APIs, the following information was collected:

|Field| Type   | Note                                  |
|--------------|--------|---------------------------------------|
| UserID       | String |                                       |
| Title        | String |                                       |
| Location     | String |                                       |
| StartTime    | Int    |                                       |
| EndTime      | Int    | May Change For BIN/Cancelled Auctions |
| ShippingCost | Int    |                                       |
| BINPrice     | Int    | Buy-It-Now Price                      |
| StartPrice   | Int    | Lowest Bidding Price                  |
| IsBin        | Bool   | Buy-It-Now Listing?                   |
| IsBO         | Bool   | Best-Offer Enabled?                   |
| IsAuction    | Bool   | Standard Auction Type?                |
| GalleryURI   | String | URI For Main Image Of Listing         |

Various different decisions had to be made based on the information retrieved, which I won't go into great detail about. However, it was possible for a listing to be all three types of listings: Buy-It-Now, Auction, and include a Best-Offer option, so they had to be recorded appropriately. If the current price of the item was not the same as the "minimum amount you could bid", then it implied that somebody had already bid on the auction before we retrieved this data (i.e. our bot was a bit slower than we hoped for).
The bot also retrieved the first image from the gallery of the listing, and then MD5-hashed it, and stored it.
The final query into the database looked like the following:
```php
$query = "INSERT INTO `sales` (" .
	"`active`, `userid`, `title`, `listingid`, `location`, `starttime`, `endtime`, `imgchk`, " .
	"`binprice`, `startprice`, `shippingcost`, " .
	"`bin`, `bestoffer`, `auction`, `endprice`, `realendtime`, `description`, `bidders`) VALUES (" .
		  
	"'T', '" . $seller . "', '" . $title . "', '" . $itemid . "', '" . $location .
	"', '" . $starttime . "', '" . $endtime . "', '" . $img . "', '";

$query .= ($isBin ? $bin : "0.0");
	$query .= "', '";
	$query .= ($Auction ? $startprice : "0.0");

	$query .= "', '" . $shippingcost . "', '" . ($isBin?"T":"F") . "', '" . ($bestOffer?"T":"F") . "', '" . ($Auction?"T":"F") . "', " . "0,0,0,0);";
```
Looking back, it certainly wasn't the most elegant, but it worked well.

**Step 3: Check Whether It's An Original Listing**

I figured that a listing could be considered a 'relist' if the following conditions were met: the title of the listing, the seller's userid, and the gallery image of the item, had previously been seen (I do not remember seeing any cases where this assumption failed). Therefore, in order to determine whether the listing was completely new or not, the following query was used in our local database:
```php
$result = mysqli_query($conn, "select userid from sales where title='" . $title . "' AND userid='" . $seller . "' AND listingid != '" . $itemid . "' AND imgchk='" . $img . "';");
```
The number of results from this query would indicate how many times this exact same listing's contents had been seen before, but in a different listing (i.e. different _itemid_). If the result was greater than 0, it was a relist; if it was 0, it was completely new. 
If the result was 0, a bell was sent to the terminal, which would alert me to take a look at the listing. I experimented with sending alerts to my phone using pushover.net, however, I quickly disabled this since I didn't like my phone being spammed.

**Step 4: Check Old Listings**

In order to check old listings, an SQL query was run which did something like the following:
```SQL
SELECT endtime,listingid FROM sales WHERE UNIX_TIMESTAMP(NOW()) > endtime+60 AND active='T'
```
This query would take all the listings which _should_ have already ended at least one minute ago, and which were still stored as 'active' in the database (i.e. they had not been seen as 'ended' already).

With each of the "supposed to be finished listings", their detailed information is once again obtained using the `GetSingleItem` API.

If the already-stored time that the auction was supposed to end differs from the time it actually ended (or not!), the stored `EndTime` is updated with the newer value. This could happen if an auction had _already_ ended, or if the auction was changed to end _later_.

If the auction was still active when it shouldn't be (i.e. the stored `EndTime` is in the past), this would indicate some sort of bug in my logic of the script.

The description of the auction was stored at this stage. The reason for not storing the description when first seeing a new auction is that many eBay users update the description after listing their item, so it's better to check it when the auction finishes, to see what information was added. 

The number of views of the auction was recorded, as well as the number of bidders. The number of views of the auction was recorded, as well as the number of bidders. If the item sold, the ending price was recorded, as well as the winner's userid and their feedback number. Information about the listing was then logged, and finally, the item was set to inactive.

Recording the winning bidder's name and feedback was useful because we liked to be able to check what other games a bidder had won in the past -- something not possible on eBay's website. Since eBay obfuscates the winner's userid (such as a****b) in the same way each auction, it was as simple as querying the local database for the winner's obfuscated userid, with a feedback score _approximately_ the same as an earlier auction

[![Terminal Screen Showing Output](/assets/img/terminal.png)](/assets/img/terminal.png)

In this screenshot of the terminal output (press the image to open a larger version), we can see what I saw when I opened the terminal. Blue lines were informational (such as whether a game had sold or not) as well as listings that were detected to be relisted. Yellow lines were warnings (which were expected and accounted for in the code). Green lines were new listings that had never been seen before (i.e. not a relisting) -- each of these lines caused a bell to sound in my terminal when they were printed.

This script ran for around 3-years and was extremely helpful in letting me obtain some great deals on rare games, and some of my friends (before telling them what I had made) commented that I must be on eBay refreshing every minute or so. The statistics of sold listings were also extremely helpful for myself and my friends in determining how many specific games had been sold over time, their prices, and sometimes to whom they were sold.

The script only ran on Australian eBay and discarded any results which were located out of the country. However, I did have requests from people to let them use the script in their respective countries or for other search queries (for example, for Playstation products). I never did set that up for anybody, mostly because it only worked on Linux and none of my friends knew how to use that. But hey, maybe one day I'll rewrite it and let them use it :).
