---
layout: post
title: "npm --ignore-scripts, yarn --version"
tags: [appsec, supply_chain, security]
description: "Two small package manager surprises: npm 10 runs a git dependency's prepare script even with --ignore-scripts, and Yarn runs a repository's yarnPath on any command, including yarn --version."
---

## `npm pack --ignore-scripts` runs `prepare`

Running `npm pack --dry-run --ignore-scripts` is (apparently?) supposed to be benign. This surprised me:

```terminal
$ npm pack --dry-run --ignore-scripts anythingatall@someone/somerepo

> gitdep@1.0.0 prepare
> node -e "require('fs').writeFileSync('/tmp/test','PREPARE RAN')"

[...]
$ cat /tmp/test
PREPARE RAN
```

The name before the `@` doesn't matter. npm will automatically download `https://github.com/someone/somerepo`, treat it as an npm package's source, and execute its `prepare` script.

`npm pack <package>` is (apparently?) the usual way to look at an npm package's code without installing it, and for a package from the registry, that's fine: it's already built, so npm just downloads the tarball and nothing runs (with or without `--ignore-scripts` btw.) But... a git repository isn't built yet, so npm builds it first, and building it is what `prepare` is for (same goes for packing a local folder).

It isn't only `npm pack`, either: on npm 10, `npm install --ignore-scripts` with a git dependency runs its `prepare` script too.

This seems like a pretty useful vector for social engineering (hello my DPRK overlords). Getting someone (say, on a programming interview) to run `npm pack --dry-run --ignore-scripts openai@claude-codex-code/claude` (claude-codex-code is unregistered on GitHub) is ... probably not so difficult. Since the `openai` part _looks_ like it matters, it adds some extra false authority.

The backstory of this quirk is that `--ignore-scripts` skipped `prepack`, but not `prepare`, and an npm maintainer [called it](https://github.com/npm/cli/issues/7211#issuecomment-2103635859) "probably an oversight": `prepare` ran inside pacote, npm's package-fetching library, which left that decision to whoever called it, and npm forgot to make that decision (oops).

This issue's [original report](https://github.com/npm/cli/issues/7211) is pretty interesting. It isn't about git at all, but about running `npm pack` and `npm publish` on your own project in CI, where the publish job holds the npm token. The discussion in the thread is about whether npm's `--ignore-scripts` is meant to protect you from your own project's scripts, or only from your dependencies'. One side wants it to stop anybody who can edit `package.json` from running code in the publish job; the other says "this is your *own project's scripts*. If you don't want them to run, [don't have them in there](https://github.com/npm/cli/issues/7211#issuecomment-1939294503)." npm eventually sided with the first (although it's not obvious to me that `--ignore-scripts` _really_ makes `npm pack` completely benign on a local package).

Anyways, fixing it in npm counted as a breaking change, so it waited for npm 11, which [fixed it](https://github.com/npm/pacote/pull/407) in December 2024. npm 12 went further: it won't fetch git dependencies at all unless you set `allow-git` (default off), so the command above just fails with `EALLOWGIT`.

Force an older npm, though, and it's back: `nvm install 22` (Node 22 still ships npm 10.9.9), or `corepack npm@10.9.9 pack ...`.

## `yarnPath`

Yarn lets a repository pin its own copy of Yarn, in `.yarnrc.yml`:

```yaml
yarnPath: ./evil-code.js
```

Whatever that points to is what runs when you type `yarn` in that directory. Any command, including `yarn --version`.

So "clone this repository and run `yarn --version`", say, as the take-home task for a fake job interview, is exactly as dangerous as "clone this repository and run this script", except that there's no script anywhere obvious.

So, it might be obvious, but `.yarnrc.yml` CODEOWNERS'd sounds reasonable.
