---
layout: post
title: "Automatically Generating a Well-Tuned Fuzzing Campaign With AFL++"
author: "Joshua Rogers"
categories: security
---

---

Tuning a fuzzer is in many ways a full-time job, and even working out what you really want to achieve by tuning is difficult to define. Getting the more out of your cores is important, and code coverage, code path discovery, and exploitation attempts are all important. To help with tuning an AFL++ fuzzer, AFL++ recommends various secondary fuzzers with different options based on how many cores your fuzzing machine has. In the documentation, they [list various percentages of each option](https://aflplus.plus/docs/fuzzing_in_depth/#c-using-multiple-cores) to use.  The instructions provided are simple. For example, 40% should run with `-P explore`, 10% with `-L 0`, and so on. But calculating all of those options every time is quite burdensome, and takes up too much time.

Instead of doing this manually, I made a script to generate the commands necessary based on an arbitrary number of cores. It's quite simple, and assumes three fuzzers: the normal binary (probably built with `AFL_HARDEN=1`), a fuzzer with sanitizers, and a fuzzer with CMPLOG. The percentages are as follows:

1. Use AFL_DISABLE_TRIM=1 to 65% of fuzzers,
2. Use AFL_KEEP_TIMEOUTS=1 to 50% of fuzzers,
3. Use AFL_EXPAND_HAVOC_NOW=1 for 40% of fuzzers,
4. Use -L 0 for 10% of fuzzers,
5. Use -Z for 20% of fuzzers,
6. Use -P explore for 40% of fuzzers,
7. Use -P exploit for 20% of fuzzers,
8. Use -a binary for 30% of fuzzers,
9. Use -a ascii for 30% of fuzzers,
10. Use a different -p "fast", "explore", "coe", "lin", "quad", "exploit", "rare" for each fuzzer,
11. Use a fuzzer built with sanitizers for one fuzzer,
12. Use CMLOG fuzzers for 30% of all fuzzers,
13. Of the CMPLOG fuzzers, 70% use -l 2, 10% -l 3, and 20% -l 2AT.

Imagine calculating all of that for each of your fuzzing campaigns...

The source code [is available here on GitHub](https://github.com/MegaManSec/AFLplusplus-Parallel-Gen).

The script is slightly dumb in that it is possible for a fuzzing campaign to have: `-P explore -P exploit -a binary -a ascii` -- but it will still run fine.

Usage is simple: call the python script like `./generate.py -n N --fuzz-out <dir> --corpus <dir> --fuzz-loc <loc> --san-fuzz-loc <loc> --cmp-fuzz-loc <loc>`. An example is as follows:

```bash
$ python3 generate.py -n 32 --fuzz-out "/dev/shm/fuzz" --corpus "/dev/shm/corpus" --fuzz-loc ~/fuzz.bin --san-fuzz-loc ~/fuzz.san.bin --cmp-fuzz-loc ~/fuzz/cmplog.bin

AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -Z -a binary -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main1 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -P explore -a binary -a ascii -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main2 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -Z -a binary -a binary -p coe -i /dev/shm/corpus -o /dev/shm/fuzz -S main3 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -S main4 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -P explore -a binary -p quad -i /dev/shm/corpus -o /dev/shm/fuzz -S main5 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -a binary -p exploit -i /dev/shm/corpus -o /dev/shm/fuzz -S main6 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -L 0 -a binary -p rare -i /dev/shm/corpus -o /dev/shm/fuzz -S main7 -l 3 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -P explore -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main8 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 afl-fuzz -P explore -P exploit -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main9 -l 2 /home/user/fuzz.cmplog.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -a binary -p coe -i /dev/shm/corpus -o /dev/shm/fuzz -S main10 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -a binary -a ascii -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -S main11 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -L 0 -P explore -a binary -p quad -i /dev/shm/corpus -o /dev/shm/fuzz -S main12 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -Z -a binary -p exploit -i /dev/shm/corpus -o /dev/shm/fuzz -S main13 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -P explore -a binary -p rare -i /dev/shm/corpus -o /dev/shm/fuzz -S main14 /home/user/fuzz.bin
AFL_AUTORESUME=1 afl-fuzz -P exploit -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main15 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -L 0 -P explore -P exploit -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main16 /home/user/fuzz.bin
AFL_AUTORESUME=1 afl-fuzz -a binary -p coe -i /dev/shm/corpus -o /dev/shm/fuzz -S main17 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -a binary -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -S main18 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -P exploit -a binary -p quad -i /dev/shm/corpus -o /dev/shm/fuzz -S main19 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -a binary -p exploit -i /dev/shm/corpus -o /dev/shm/fuzz -S main20 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -a binary -p rare -i /dev/shm/corpus -o /dev/shm/fuzz -S main21 /home/user/fuzz.bin
AFL_AUTORESUME=1 afl-fuzz -P explore -a binary -a ascii -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main22 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -P explore -a ascii -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main23 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -P exploit -a binary -a binary -p coe -i /dev/shm/corpus -o /dev/shm/fuzz -S main24 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -P explore -a binary -a ascii -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -S main25 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -Z -P exploit -a ascii -a binary -p quad -i /dev/shm/corpus -o /dev/shm/fuzz -S main26 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -a binary -p exploit -i /dev/shm/corpus -o /dev/shm/fuzz -S main27 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -Z -a ascii -a binary -p rare -i /dev/shm/corpus -o /dev/shm/fuzz -S main28 /home/user/fuzz.bin
AFL_AUTORESUME=1 afl-fuzz -a binary -a ascii -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main29 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -P explore -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main30 /home/user/fuzz.bin
AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 AFL_EXPAND_HAVOC_NOW=1 afl-fuzz -Z -a ascii -a binary -p coe -i /dev/shm/corpus -o /dev/shm/fuzz -S main31 /home/user/fuzz.san.bin
AFL_FINAL_SYNC=1 AFL_AUTORESUME=1 afl-fuzz -P explore -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -M main /home/user/fuzz.bin
```
To make life easier, I also have a bash script which takes each of these lines, and starts a new `screen(1)` with each of the lines:

```bash
$ python3 generate.py -n 32 --fuzz-out "/dev/shm/fuzz" --corpus "/dev/shm/corpus" --fuzz-loc ~/fuzz.bin --san-fuzz-loc ~/fuzz.san.bin --cmp-fuzz-loc ~/fuzz.cmplog.bin  | ./run.sh

screen -dmS screen_main bash -c AFL_FINAL_SYNC=1 AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 AFL_KEEP_TIMEOUTS=1 afl-fuzz -a binary -p lin -i /dev/shm/corpus -o /dev/shm/fuzz -M main /Users/opera_user/fuzz.bin; exec bash
screen -dmS screen_main1 bash -c AFL_AUTORESUME=1 afl-fuzz -P explore -P exploit -a binary -a binary -p fast -i /dev/shm/corpus -o /dev/shm/fuzz -S main1 -l 2 /Users/opera_user/fuzz.cmplog.bin; exec bash
screen -dmS screen_main2 bash -c AFL_AUTORESUME=1 AFL_DISABLE_TRIM=1 afl-fuzz -P explore -a binary -a binary -p explore -i /dev/shm/corpus -o /dev/shm/fuzz -S main2 -l 2 /Users/opera_user/fuzz.cmplog.bin; exec bash
.....
```

You can therefore just run
```bash
$ python3 generate.py -n 32 --fuzz-out "/dev/shm/fuzz" --corpus "/dev/shm/corpus" --fuzz-loc ~/fuzz.bin --san-fuzz-loc ~/fuzz.san.bin --cmp-fuzz-loc ~/fuzz.cmplog.bin  | ./run.sh | bash
```
to execute everything.
