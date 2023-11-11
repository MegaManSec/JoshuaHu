---
layout: post
title: "Playing with SSH: carriage returns on stderr output"
author: "Joshua Rogers"
categories: security
---

We learn new things every day. Today it's about ssh. And this time it's not even about how to use it, but the format of its output.

What would you expect this command to return?

```bash
ssh -oHostkeyAlgorithms=+ssh-notrealrsa user@host 2>&1
```

If you guessed `command-line line 0: Bad key types '+ssh-notrealrsa'.` you'd be nearly right. In reality:

```bash
$ ssh -oHostkeyAlgorithms=+ssh-notrealrsa user@host 2>&1 | sed -n l
command-line line 0: Bad key types '+ssh-notrealrsa'.\r$
```

As it turns out, each line that is printed to stderr is separated by a carriage return/line feed (CRLF) pair:
```bash
ssh noidea@notreal 2>&1 | sed -n l
ssh: Could not resolve hostname notreal: Name or service not known\r$
```

ssh's source code explicitly sets the clrf:
```C
        } else if (log_on_stderr) {
                snprintf(msgbuf, sizeof msgbuf, "%s%s%.*s\r\n",
                    (log_on_stderr > 1) ? progname : "",
                    (log_on_stderr > 1) ? ": " : "",
                    (int)sizeof msgbuf - 3, fmtbuf);
```

---

Doing some code archaeology, we see that openbsd's openssh added this functionality in 1999: [8747197](https://github.com/openbsd/src/commit/8747197a4a479407167d01f46017ddb99cc3cae2) and more or less confirmed in 2017: [4e24903](https://github.com/openbsd/src/commit/4e2490386a473136b8c317720b195872d854737a).

[RFC4253 section 11.3](https://datatracker.ietf.org/doc/html/rfc4253#section-11.3) states that if debug information is displayed, lines must be separated by CRLF pairs, but that's likely not what's happening here (error messages are not debugging information).

---

Anyways, so reminder to myself: if parsing SSH output including stderr, make sure to filter out carriage return values using `tr -d '\r'` or something, otherwise if you print the output lines verbatmin you'll be looking around for an explanation of your messed up display for 30 minutes.
