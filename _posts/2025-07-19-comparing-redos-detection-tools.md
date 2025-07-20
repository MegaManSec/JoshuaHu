---
layout: post
title: "A Comparison of Tools to Detect ReDoS-vulnerable Expressions"
author: "Joshua Rogers"
categories: security
---

I recently compared various tools for identifying regular expressions which are vulnerable to Regular Expression Denial of Service ([ReDoS](https://en.wikipedia.org/wiki/ReDoS)), as I wanted to build a small worfflow which would flag vulnerable expressions for me.

I tested out the following unique tools:

- [semgrep](https://semgrep.dev/r?q=javascript.lang.security.audit.detect-redos)
- [safe-regex](https://www.npmjs.com/package/safe-regex)
- [safe-regex2](https://www.npmjs.com/package/safe-regex2)
- [regexploit](https://github.com/doyensec/regexploit)
- [seccamp-redos](https://github.com/n4o847/seccamp-redos)
- [RegexStaticAnalysis](https://github.com/NicolaasWeideman/RegexStaticAnalysis)
- [redos-detector](https://github.com/tjenkinson/redos-detector)
- [CodeQL](https://codeql.github.com/codeql-query-help/javascript/js-redos/)

The following 13 expressions were chosen to be tested:

```
(ht|f)tp(s?)\:\/\/[0-9a-zA-Z]([-.a-zA-Z_]*[0-9a-zA-Z])*(:(0-9)*)?(\/?)([a-zA-Z0-9\-\.\?\,\:\'\/\\\+=&amp;%\$#_]*)?
(.*)<1>(.*)<\/1>(.*)<2>(.*)<\/2>(.*)
(?<head>.*)<1>(?<tou>.*)<\/1>(?<center>.*)<2>(?<privacy>.*)<\/2>(?<tail>.*)
(a+){10}y
\.(woff2?|eot|ttf|otf)(\?.*)?$
\/+$
^(function)?\s*[^\(]*\(\s*([^\)]*)\)
minimum .* amount
{(?:\w+\.?)+}
^((mailto:)?[\w.%+-]+@([\w-]+\.)+[\w-]{2,}|https?:\/\/([\da-z.-]+)\.([a-z.]{2,6})([/\w =%?.-]*)*\/?)$
^(-?(?:[_a-z]|(?:\\[0-9a-f]+ ?))(?:[_a-z0-9\-]|\\(?:\\[0-9a-f]+ ?))*)\s*:
^\'(?:[^\n\r\f\\\']|\\(?:\r\n?|\n|\f)|\\[\s\S])*\'
^\/a\/b\/c\/d\/e\/(temp|((img|k|n|m\/excl)\/(\d+)\/(\d+)))\/(.*)\.(.*)$
```

The results were the following. X marks a detection.

|Expression|Semgrep|CodeQL|seccamp-redos|regexploit|safe-regex|safe-regex2|RegexStaticAnalysis|redos-detector|recheck|
|------------------------------------------------------------------------------------------------------------------|-------|-------|-----------|----------|----------|-------------|-------------------|-----------------|------|
|`(ht|f)tp(s?)\:\/\...`     |X| |X|X|X|X|X| | |
|`(.*)<1>(.*)<\/1>(...`     | | |X| | | | |X|X|
|`(?<head>.*)<1>(?<...`     | | |X| |X| | | |X|
|`(a+){10}y`                |X| | | |X|X| |X|X|
|`\.(woff2?&|eot|tt...`     | | | | |X|X| |X|X|
|`\/+$`                     | | | | | | | |X|X|
|`^(function)?\s*[^...`     | | | | | | |X|X|X|
|`minimum .* amount`        | | | | | | | |X|X|
|`{(?:\w+\.?)+}`            |X|X|X|X|X|X|X|X|X|
|`^((mailto:)?[\w.%...`     | |X| |X|X|X|X|X|X|
|`^(-?(?:[_a-z]|?:\...`     | |X| | | | |X|X|X|
|`^\'(?:[^\n\r\f\\\...`     | |X| | | | |X|X|X|
|`^\/a\/b\/c\/d\/e\...`     | | | | | | | |X|X|


All of these expressions are vulnerable to ReDoS. I do not offer any analysis of these results, nor whether any of the tools produce false-positives.
