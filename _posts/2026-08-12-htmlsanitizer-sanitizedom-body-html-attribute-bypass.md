---
layout: post
title: "HtmlSanitizer bypass via a second body tag"
tags: [security, vuln_research, web_platform]
description: "HtmlSanitizer's SanitizeDom(string) wraps its input in its own html and body elements and only sanitizes what's inside the body. HTML5 merges the attributes of any extra body or html tag onto those wrapper elements, so <body onload=alert(1)> came out of the sanitizer with its event handler intact."
---

[HtmlSanitizer](https://github.com/mganss/HtmlSanitizer) is probably the most widely used HTML sanitizer in the .NET world. It's built on top of [AngleSharp](https://github.com/AngleSharp/AngleSharp), a spec-compliant HTML5 parser, and works the way you'd expect: parse the input into a DOM, walk every element, and remove any tag or attribute that isn't on the allowlist.

A couple of months ago, I found a small bypass in it, where an `onload` handler could survive sanitization by riding on the `<body>` element.

---

## Wrapping the input

HtmlSanitizer's main entry point, `Sanitize(string)`, takes an HTML fragment and returns a sanitized string. Under the hood, it calls `SanitizeDom(string)`, which is also public, and returns the sanitized AngleSharp `IHtmlDocument` itself for callers who want to keep working with the DOM:

```csharp
public IHtmlDocument SanitizeDom(string html, string baseUrl = "")
{
    var parser = HtmlParserFactory();
    var dom = parser.ParseDocument("<!doctype html><html><body>" + html);

    if (dom.Body != null)
        DoSanitize(dom, dom.Body, baseUrl);

    return dom;
}
```

The fragment gets glued onto a `<!doctype html><html><body>` prefix, parsed as a full document, and then sanitized with `dom.Body` as the context. `DoSanitize()` then finds the elements to clean up like so:

```csharp
foreach (var tag in context.QuerySelectorAll("*").Where(t => !IsAllowedTag(t)).ToList())
```

with the same `context.QuerySelectorAll("*")` loop used again for attributes. Called on an element, `QuerySelectorAll` returns that element's descendants. It doesn't return the element itself, and it certainly doesn't return the `<html>` or `<head>` above it. That's fine, as long as `<html>`, `<head>`, and `<body>` are purely the sanitizer's own scaffolding. They come from a hard-coded prefix with no attributes, so there's nothing on them to check.

## A second body tag

Except, the scaffolding isn't completely the sanitizer's. In HTML5 tree construction, a `<body>` start tag that turns up when there's already a body doesn't create a new element. It's a parse error, but the parser doesn't throw it away entirely either: [for each attribute on the token](https://html.spec.whatwg.org/multipage/parsing.html#parsing-main-inbody), if the existing body doesn't already have that attribute, it gets added to it. A stray `<html>` start tag does the same thing to the root `<html>` element.

So if the input is:

```html
<body onload=alert(1)><p>hi</p>
```

the parser sees `<!doctype html><html><body><body onload=alert(1)><p>hi</p>`. The second `<body>` gets merged into the first, and since the wrapper has no attributes of its own, every attribute from the input lands on it. The sanitizer then cleans everything below the body (the `<p>` is fine), but the body's own attributes are never passed to `IsAllowedAttribute()`:

```csharp
var s = new HtmlSanitizer();
IHtmlDocument dom = s.SanitizeDom("<body onload=alert(1)><p>hi</p>");
Console.WriteLine(dom.ToHtml());
```

```
<!DOCTYPE html><html><head></head><body onload="alert(1)"><p>hi</p></body></html>
```

The same `onload` on a `<p>` or an `<img>` would have been stripped. On the body, it went straight through. Oops!

## Who was affected

Not everyone. `Sanitize(string)`, which is probably what most people call, only serializes the body's children:

```csharp
var output = dom.Body.ChildNodes.ToHtml(outputFormatter ?? OutputFormatter);
```

so the poisoned `<body>` itself never makes it into the output. `SanitizeDocument()`, for full documents, uses the document itself as the context, so `<html>`, `<head>`, and `<body>` are all descendants there and get checked like everything else.

So it'z only a direct call to the (public) API `SanitizeDom(string)`. If you took the returned document and serialized more than the body's children, say `dom.ToHtml()`, `dom.DocumentElement.OuterHtml`, or `dom.Body.OuterHtml`, you got the event handler back.

## The fix

It was fixed in [96afbc8](https://github.com/mganss/HtmlSanitizer/commit/96afbc818e64de7571ea17954a05d523e819c56f) by stripping every attribute from `<html>`, `<head>`, and `<body>` before sanitizing. The prefix never adds any attributes, so anything found on those elements must have come from the input:

```csharp
foreach (var wrapper in new IElement?[] { dom.DocumentElement, dom.Head, dom.Body })
{
    if (wrapper == null) continue;

    foreach (var attribute in wrapper.Attributes.ToList())
        RemoveAttribute(wrapper, attribute, RemoveReason.NotAllowedAttribute);
}
```

The removals go through `RemoveAttribute()` like any other, so `RemovingAttribute` event handlers still get to see them. The fix shipped [9.2.1039](https://github.com/mganss/HtmlSanitizer/releases/tag/v9.2.1039) (and [10.0.1037-beta](https://github.com/mganss/HtmlSanitizer/releases/tag/v10.0.1037-beta)).
