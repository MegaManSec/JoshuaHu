---
layout: post
title: "npm pack --ignore-scripts, .npm-extension"
tags: [appsec, supply_chain, security]
description: "A follow-up: npm 12 imports a package's .npm-extension file during npm pack --ignore-scripts, no scripts required and no flag to turn it off. The same bare Arborist runs a git dependency's extension code during npm install --ignore-scripts, and npm 10 still runs git prepare there by default. npm 12's allow-scripts list misses that same git prepare, and a hostile git ref name runs code during resolution, before any script and regardless of --ignore-scripts."
---

In my [last post](https://joshua.hu/npm-ignore-scripts-prepare-git-dependency-yarnpath), I remarked that "it's not obvious to me that `--ignore-scripts` _really_ makes `npm pack` completely benign on a local package". The context of that was [npm/cli#7211](https://github.com/npm/cli/issues/7211): someone wanted `npm pack` and `npm publish` to honour `--ignore-scripts` so that a CI publish job holding the npm token couldn't be turned into a secret-leaking machine by anybody who can edit `package.json`. npm sided with that, and npm 11 made `prepare` respect the flag (`prepack` and `postpack` already did). So, I wondered if that really achieved it.

As it turns out, perhaps unsurprisingly, it still runs code, just not calling it a "script" anymore.

## npm extensions

What does `npm pack` actually do? It's a short walk: `npm pack`, which uses `libnpmpack`, which uses `pacote`, npm's package-fetching library. `libnpmpack` is where `prepack`/`postpack` live, and they've always been gated (`if (spec.type === 'directory' && !opts.ignoreScripts)`). As in the last post, `--ignore-scripts` skipped `prepack` but ran `prepare` anyways, since it was one layer down in pacote's `DirFetcher`, and _that's_ the one npm 11 finally fixed. So the three scripts are all handled now.

So, npm catches all "scripts" so they don't get executed when using `--ignore-scripts`, but npm 12 introduced a feature which allows us to execute code a different way.

npm 12 shipped a feature called `.npm-extension`. A project can drop a `.npm-extension.mjs` or `.npm-extension.cjs` file exporting a `transformManifest(pkg, context)` function, and npm will call it to "repair" dependency manifests before Arborist (the dependency tree manager) reads their edges. It's `packageExtensions`, except imperative, which is to say _it is a JavaScript file that npm imports and runs_.

To get at the function to execute it, npm does the obvious thing:

```javascript
mod = await import(`${pathToFileURL(this.path).href}?h=${this.hash}`)
// or, for a .cjs file:
mod = require(this.path)
```

Since importing a module runs its top-level code, the file doesn't even need to define `transformManifest`, just being imported is the whole payload. There is a single protection, though: the function that reaches it is guarded by exactly one thing, `this.options.ignoreExtension`:

```javascript
async #applyNpmExtension () {
  if (this.options.ignoreExtension) {
    return
  }
  const ext = new NpmExtension({ root: this.#actualTree.realpath, ... })
  if (!ext.present) {
    return
  }
  await ext.load()   // import()/require() of the attacker's file
  ...
}
```

`--ignore-scripts` is _supposed_ to set `ignoreExtension` for you: the config flattens one into the other ("both disable root install-time code", says the comment), but...

When `pack` needs the list of files to include, pacote's `DirFetcher` (the component that turns a directory into a tarball) spins up its own Arborist and reads the on-disk tree with `loadActual()` (`pacote/lib/dir.js`):

```javascript
const arb = new this.Arborist({ path: this.resolved })
this.tree = await arb.loadActual()
```

Look at what it hands over: `{ path }`. That's it. Every option the fetcher was given (`ignoreScripts`, `ignoreExtension`, the lot) gets dropped right here. So the (naked?) Arborist running `loadActual()` has `this.options.ignoreExtension === undefined`, the guard doesn't fire, and `.npm-extension.cjs` gets `require`'d. Oops! PS: Remember `loadActual()`, because we'll talk about it again later.

Luckily(?) the exact same guard works fine during `npm install`, which builds its Arborist with the real options. `pack` just builds a fresh one and throws the flags away. Oops!

So the "exploit", if you can call it that, is a file:

```terminal
$ cat attacker-pkg/package.json
{ "name": "attacker-pkg", "version": "1.0.0" }

$ cat attacker-pkg/.npm-extension.cjs
require("fs").writeFileSync("/tmp/pwned", "pwned");
console.log("PACK_IGNORE_SCRIPTS_BYPASSED");
module.exports.transformManifest = (pkg) => pkg;

$ npm pack --dry-run --ignore-scripts ./attacker-pkg
PACK_IGNORE_SCRIPTS_BYPASSED
attacker-pkg-1.0.0.tgz

$ cat /tmp/pwned
pwned
```

So, the take-home interview task writes itself: "clone this and run `npm pack --dry-run --ignore-scripts .`, totally safe, see, `--dry-run --ignore-scripts`." My DPRK overlords send their regards.

There's also a couple other problems:

1. `--ignore-extension` doesn't help either (a flag can't reach a guard on an Arborist that never received the flag), so `npm pack --ignore-scripts --ignore-extension` _still_ runs the file,
2. `npm publish --dry-run --ignore-scripts` goes through the same `libnpmpack`, so it does the same thing, which is precisely the token-holding CI job #7211 was about.

There's also the nice little touch that in `npm-packlist`, `/.npm-extension.mjs` and `/.npm-extension.cjs` are excluded from the published tarball. So npm decided the file is sensitive enough never to _ship_, but still imports it on your machine while building the tarball it deliberately left it out of.

## `npm install --ignore-scripts`

`npm install --ignore-scripts` is what every scanner, every Dependabot/Renovate run, and every "just fetch the deps, don't run anything" CI step uses. Does this bug affect that? No. Registry deps arrive as pre-built tarballs, get extracted, and `.npm-extension` isn't even in them (although one could probably "force" them to be there anyway). A `file:` directory dependency gets symlinked, not packed. A plain `npm install --ignore-scripts` of a registry tree is not "vulnerable" to what we've discussed, unfortunately.

But there are still git dependencies. A `git+...` dep is cloned and then re-packed through the very same `DirFetcher`. `GitFetcher` (pacote's git-dependency handler) correctly skips `prepare` under `--ignore-scripts`... and then, in the same function, does `new DirFetcher(file:${dir}, ...)` and packs the clone anyway, which means `loadActual()` (which we talked about before), which means the no-option (naked) Arborist, which means the git dependency's own `.npm-extension` runs. So one git dependency anywhere in the tree re-opens the door at install time.

Note: that needs `allow-git` turned on explicitly (npm 12 defaults to off as mentioned in the previous post, though many CI turn it on because private git deps exist).

## curated `allow-scripts` list misses

`--ignore-scripts` is the typical way to specify to the npm _cli_ not to run _any_ scripts. npm 12 added `allow-scripts`: a default-deny allowlist, where a dependency's install scripts, and `prepare` for non-registry deps, don't run unless you name the package in `allowScripts`. It can be used when you really want to allow a curated list of scripts to run.

It has the same issue as everything else here: works for `file:`, works for `link:`, but git deps still walk through it. The problem is a bit different, though. The policy lives in Arborist's rebuild queue (`isScriptAllowed(node, this.options.allowScripts)`), which runs _after_ extraction, and a git dependency's `prepare` runs _during_ extraction, in the same `DirFetcher`, where the only gate is the blunt `ignoreScripts` flag. The `allowScripts` verdict never gets turned into `ignoreScripts` for that node, so unless you literally passed `--ignore-scripts`, the `prepare` runs:

```terminal
$ npm install --foreground-scripts
> evil-gitdep@1.0.0 prepare
PACK_IGNORE_SCRIPTS_BYPASSED
added 1 package
npm warn allow-scripts 1 package had install scripts blocked because they are not covered by allowScripts:
npm warn allow-scripts   evil-gitdep@1.0.0 (prepare: node evil.js)
```

Reading the order, we see that:

1. the script runs, 
2. _then_ npm says it blocked it.

But of course, it didn't (too late!)

Amusingly, `--strict-allow-scripts` (the stricter CLI variant of the same list) does get it right. It checks the tree _before_ anything is extracted, so the `prepare` never runs at all:

```terminal
$ npm install --strict-allow-scripts
npm error code ESTRICTALLOWSCRIPTS
npm error --strict-allow-scripts: 1 package(s) have install scripts not covered by allowScripts:
npm error   evil-gitdep@1.0.0 (prepare: node evil.js)
npm error Approve them with `npm install-scripts approve`, deny them with `npm install-scripts deny`, or bypass this check with `--dangerously-allow-all-scripts`.
```

No `PACK_IGNORE_SCRIPTS_BYPASSED` this time, the script never even started. So npm _can_ work out that the script isn't allowed, it just does it too late on the normal path to matter. `--ignore-scripts` reaches the fetcher. The curated `allowScripts` list you reached for instead doesn't.

## no ~~offense~~ script intended

While writing up this post, I figured out there's another way to hit a bug like this, without any `prepare`, extension, or lifecycle, instead firing during _resolution_, while npm is still working out what the git dep even points at, well before the part `--ignore-scripts` watches.

A committish, the `#branch`, `#tag`, or `#commit` you pin on the end of a git dependency, is just a git ref, and npm takes the remote's word for which refs exist. `git ls-remote` runs through `@npmcli/git`'s `lines-to-revs.js`, and anything that isn't a tag, head, pull, or `HEAD` is kept verbatim. `npm-package-arg` is no more suspicious, storing a committish that starts with `-` as-is. So nothing objects when `clone.js` goes to check the ref out:

```javascript
const fetchOrigin = ['fetch', 'origin', revDoc.rawRef]
```

Since neither `--end-of-options` nor `--` is used, and there's nothing between `origin` and a ref name the server chose, a repo advertising a ref called `--upload-pack=/tmp/payload` turns that into `git fetch origin --upload-pack=/tmp/payload`:

```terminal
$ cat app/.npmrc
ignore-scripts=true
allow-git=all
$ npm install --ignore-scripts
npm error command git --no-replace-objects fetch origin --upload-pack=/tmp/payload
npm error fatal: Could not read from remote repository.
$ cat /tmp/pwned
pwned
```

git reads the ref as a flag, because it looks exactly like one, and `--upload-pack` on a `file://` remote means "run this program." The fetch dies a line later, but the payload already ran, with `ignore-scripts=true` in the `.npmrc` _and_ `--ignore-scripts` on the command line, because there was never even a script for either to catch. git won't let you _name_ a ref `--upload-pack=...`, but a hostile server doesn't ask git, it writes `packed-refs` by hand. This is documented on my other site as an [Argument Injection](https://gtfoargs.github.io/gtfoargs/git/) vector.

This affects npm 10, 11, 12, and probably earlier versions too.

## summing up

- npm 10.9.x: `pack` runs a local `prepare` under `--ignore-scripts`. `install` runs a git dependency's `prepare`, by default, no flags.
- npm 11.x: It got the `prepare` fix and never got `.npm-extension`. The ref trick above works.
- npm 12.x (I checked 12.0.0 and 12.2.2): `pack` still runs `.npm-extension` under `--ignore-scripts`, and no flag stops it. `install` runs a git dependency's `.npm-extension` if `allow-git` is on, and the same git dependency's `prepare` runs past `allowScripts`, warned about after it's already run. The root project's `.npm-extension` on `install` is correctly gated.
