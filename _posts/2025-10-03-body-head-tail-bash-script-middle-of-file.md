---
layout: post
title: "body: A bash script to get the middle of a file, instead of head | tail"
tags: [bash]
description: "Meet 'body': A faster, smarter alternative to 'head | tail' for extracting and printing the middle lines of a large file in Bash."
---

`body` is a small bash script that replaces a common two-shot command that I find myself running from time to time: `head -n5000 file.txt | tail -n1`. Basically, I want to view approximately the middle of a file, to see the middle contents. I realized that there must be a better way, and that's why I made a small script that does what I want: it's not `head`, it's not `tail`, it's `body`: for when you want to print (around) the middle of a file.

The source code is available at [https://github.com/megamansec/body](https://github.com/megamansec/body).

I ended up fitting the script up with a bit more functionality which is more in-line with what I would usually use `head | tail` for. Namely, the following flags are available:

```
  Context control:
    -A NUM   print NUM lines of trailing context
    -B NUM   print NUM lines of leading context
    -C NUM   print NUM lines of output context

    --color=WHEN   use markers to highlight the matching strings;
                   WHEN is 'always', 'never', or 'auto'

  Output control:
    -n       do not print line number with output lines
    -N       do not print file name with output lines
```

These flags generally follow their similar usage in GNU grep. `-A` prints some lines after the middle line, `-B` before the middle line, and `-C` in both directions. `--color` is supported similar to grep. If multiple files are printed using `body`, their filenames are shown in the results; something that `-N` can disable. All results include line numbers, unless `-n` is specified, in which case no line numbers are printed.

How does it actually work? There's a million ways to get the middle contents of a file (middle, measured by _newlines_, not bytes), and I wasn't sure which would be the fastest with a simple bash script. So, I benchmarked. On a Linux server, I ran the following:

```bash
#!/bin/bash

file="/var/log/auth.log.1"

benchmark_command() {
  local start_time=$(date +%s.%N)
  for i in {1..20}; do
   eval "$1" >/dev/null
   echo 3 > /proc/sys/vm/drop_caches
  done
  local end_time=$(date +%s.%N)
  local elapsed_time=$(echo "$end_time - $start_time" | bc -l)
  local average_time=$(echo "$elapsed_time / 10" | bc -l)
  printf "%.6f " "$average_time"
}
echo 3 > /proc/sys/vm/drop_caches

benchmark_command "lines=\$(wc -l < $file); lines=\$((lines/2)); head -n\$lines $file | tail -n1"

benchmark_command "lines=\$(wc -l < $file); lines=\$((lines/2)); cat -n $file | head -n\$lines | tail -n1"

benchmark_command "lines=\$(wc -l < $file); lines=\$((lines/2)); sed \$lines,\$lines'!d;=' $file | sed 'N;s/\\n/ /'"

benchmark_command "lines=\$(wc -l < $file); lines=\$((lines/2)); awk 'NR==$lines{print NR\" \"\$0}' $file"

benchmark_command "lines=\$(wc -l < $file); lines=\$((lines/2)); cat -n $file | sed -n \$lines,\${lines}p"

echo
```

20 times, and averaged the results:

```bash
 for i in {1..20}; do bash /tmp/test; done  | awk '{
    for (i = 1; i <= NF; i++) {
        sum[i] += $i
        count[i]++
    }
}
END {
    for (i = 1; i <= NF; i++) {
        printf "avg %d: %.2f\n", i, sum[i] / count[i]
    }
}'
avg 1: 0.12
avg 2: 0.14
avg 3: 0.13
avg 4: 0.17
avg 5: 0.17
```

Perhaps unsurprisingly, using `head | tail` was the fastest. However, I wanted to print the line numbers, so that wouldn't work. Piping the output of `cat -n` (which prints the line numbers prior to each line of a file) into `head | tail` was also quick, but the quickest was using `sed` directly on the file. So in its most simple form, `body` runs this:

```bash
sed "$start_line,$end_line"'!d;=' "$filename" | sed "N;s/\n/:/"
```

In reality, the speed of all of these commands don't matter at all; they're going to be fast either way, but it's interesting to see which is the fastest. It also likely depends on the file size.

I imagine this could be an excellent optimization challenge in a competition where people compete for the lowest processing time for this type of functionality (like The Billion Row Challenge), and I'm sure there's some cool bit-twiddling that could really shine. But in the meantime, I'm happy with my bash script.
