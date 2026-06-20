---
layout: post
title: "Hacking fun with zip-slips, tar-slips, symlinks, hardlinks, collisions, and more"
tags: [security, appsec]
description: "A tool and walk-through for building zip, tar, 7z, and rar archives that trigger zip-slip and tar-slip edge-cases: path traversal, symlink and hardlink collisions, read-only files, and more, for testing extractors during a pentest."
---

I was recently reading Max Justicz's blog [post](https://justi.cz/security/2018/05/23/cdn-tar-oops.html), where he outlined how he was able to hack the `unpkg.com` CDN by getting the service to extract a tar file which contained:

1. A symlink to a directory on the system, followed by a file in the symlink/directory,
2. A hardlink pointing to a known file on the system, followed by a file named the same as that hardlink.

In practical terms, this, respectively, means:

1. Create a symlink to `/tmp` called `link`, and then extract a file to `link/oops.txt`,
2. Make a hardlink `foo` to a file (`/etc/passwd` for example) that exists and unpack a regular file named `foo`. This will overwrite `/etc/passwd`.

These attacks are pretty similar to the classic zip-slip vulnerabilities, which typically entail just having some type of archive that contains a file path like `../../some/target/file` or `/some/target/file`, causing the extractor to write outside of the intended destination directory. Sometimes symlinks are involved in the classic zip-slip vulnerabilities, but those are normally in the vein of "write a symlink, then upload a second archive which writes into the symlink". Generally speaking, you shouldn't be _able_ to extract a symlink that links to another directory, then -- in the exact same archive -- write _into_ that symlink. But what they say shouldn't be possible, is rarely impossible :-).

What that post lacked was a script to build archives which actually tickled these edge-cases, and which could be used to test an application during a pentest. I vibe-coded an application which generates archives that hit various edgecases. The repository is available in [MegaManSec/zip-slip-tar-slip-generator](https://github.com/MegaManSec/zip-slip-tar-slip-generator), and it includes a generator (and the generated archives) for the zip, tar, 7z, rar (and gzip/xz/zstd through just compressing the respective archives) archive format types.

In addition to read / write primitives, I was also interested in an archive which extracts a file which couldn't easily be deleted. On Unix, this means a file with 0444 permissions, and on DOS this means the read-only attribute. Probably setting 0000 permissions could surface some interesting error messages on Unix, but I didn't look more into this, and it all depends on the application and library anyways.

---

The following types of archives and "tricks" are available for testing.

## Symlink collisions (zip, tar, 7z, rar)

This is the trick from Justicz' blog. You extract a symlink that points at `/tmp`, then a second entry in the same archive collides with it, so the payload gets written through the link and lands outside the root.

Some extractors already try to spot that `foo` is a symlink before writing `foo/something`, so I came up with a few different ways of slipping through a collision:

  - `toctou` ships a real directory `d/sub/`, then a symlink `d/sub` to `/tmp`, then a file `d/sub/PWNED.txt`. An extractor that checks `d/sub` once, decides it's a safe directory, and writes the third entry without looking again writes through the link.
  - `case` names the symlink `LINK` and writes to `link/PWNED.txt`. On a case-insensitive filesystem those are one path; a case-sensitive comparison sees two different names.
  - `unicode` uses `café` in NFC form for the symlink (the `é` is a single code point) and `café/PWNED.txt` in NFD form for the file (`e` plus a combining accent). These are the same thing on most screens, just different bytes, and some filesystems fold them back together.
  - `unicode-nfkc` uses the `ﬁ` ligature (U+FB01) in a symlink named `ﬁle`, then writes to a plain `file/PWNED.txt`. They only collide if the extractor runs an [NFKC pass](https://en.wikipedia.org/wiki/Unicode_equivalence) somewhere.

## Baseline traversal (zip, tar, 7z, rar)

This is just the normal zip-slip, where the path does all the work and no link is involved. There are three:

  - `dotdot` is a file named `../../../../../../tmp/PWNED.txt`. The archive extractor just glues that onto the output directory without checking and the file walks straight out.
  - `abs` uses an absolute path, `/tmp/PWNED.txt`, for the extractor that forgets to strip a leading slash.
  - `backslash` is `..\..\..\tmp\PWNED.txt`. On Unix it's a filename with some odd characters in it but on Windows the backslashes are separators, so a check that only splits on `/` lets it past.

## Hard-link overwrite (tar and rar only)

Hard-links are kind of special, and zip and 7z can't work with them. But rar and tar work. This one makes a hardlink `hl` to a file that already exists, like `/tmp/VICTIM.txt`, then unpack a regular file also named `hl`.
A vulnerable extractor will extract the link, open "the file" to write its contents, and the bytes go into the hardlink destination. This can only ever overwrite (aka cannot create a file).

## Exfiltration via symlink (zip, tar, 7z, rar)

This one just uses simple symlinks to point to some file/directory. The archive just carries symlinks that survive extraction and sit there: `passwd -> /etc/passwd`, `env -> /proc/self/environ`, `root -> /`.
If whatever unpacked the archive later serves or reads one of those paths, it hands back whatever the link points at.

## Exfiltration via hardlink (tar, rar)

So instead of a symlink, these make a single hardlink. After extraction, `passwd` and `/etc/passwd` are two names for the same inode. There's no link to follow this time, so anything that reads `passwd` reads the file itself, which is what gets you past the symlinks-are-refused problem above.

This is the same deal as the hardlink overwrite: zip and 7z can't store a hardlink, so this is tar and rar only. And like all hardlinks it only works within a single filesystem, and on Linux with `protected_hardlinks` turned on you can only link a file you own or can write to, so `/etc/passwd` really only can be accessed when the extractor runs as root.

## Read-only files (zip, tar, 7z, rar)

This one creates files that come out `0444` on Unix, or with the DOS read-only attribute set in the zip, 7z, and rar versions. Tar has no DOS attribute field, so it only does the `0444` flavor. This doesn't really achieve much except for (maybe) annoying sysadmins. Annoying sysadmins is fun.
