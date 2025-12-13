---
layout: post
title: "One-Way Sandboxed Iframes: Creating a Read-Only Iframe Sandbox That Can't Read Back"
description: "Creating a secure, one-way sandboxed iframe. How to render untrusted HTML and execute commands safely via postMessage without risking the parent."
categories: security
---

## A one-way sandboxed iframe

Say you have a website and need to render arbitrary, untrusted HTML -- including JavaScript for its functionality -- and you also need to interact with that content using your own JavaScript (for example, something you might traditionally do with a same-origin iframe, with `iframe.contentDocument` or `iframe.contentWindow`). Generally speaking, simply rendering it on your website is not a smart idea: the untrusted data can include scripts which execute some malicious code to do whatever it wants. So the question is, how can we safely render the content, while being able to interact with it, but disallowing it from performing malicious actions in the context of our main website? Here are a few things we _can't_ do:

- We can't simply host the data on an external website, because we want to limit access to this data to authenticated users -- and we don't want to use JWTs that the main website signs, which the external website verifies (because we want a simple client-side-only solution).
- We can't simply set the HTML into the `innerHTML` property of an element, because it can contain malicious javascript that executes with full privileges in our page context.
- We can't rely on an HTML purifier to strip out malicious code, because the untrusted content may legitimately require JavaScript for its functionality, so blindly removing all scripts isn't an option.
- We can't just use a sandboxed iframe with the default sandbox attribute, because while it isolates the untrusted content, it also prevents the parent page from interacting with the iframe's content or scripts directly, and we want to be able to interact with the iframe from the parent.

Indeed, while using an iframe with the [sandbox attribute](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe#sandbox) may seem like a good solution, it has a few problems:

1. By default, an iframe with the `sandbox` attribute cannot run scripts at all.
2. With `sandbox=allow-scripts`, the parent cannot read or interact with the iframe after its creation, because the sandbox creates the iframe cross-origin. Attempting to interact with the iframe will result in the error `Error accessing sandboxed iframe content: DOMException: Permission denied to access property "document" on cross-origin object` or `Error accessing sandboxed iframe content: SecurityError: Failed to read a named property 'document' from 'Window': Blocked a frame with origin "null" from accessing a cross-origin frame.`.
3. With `sandbox="allow-scripts allow-same-origin"`, the protection afforded by the sandbox is completely negated, as that lets the embedded document remove the sandbox attribute, making it no more secure than not using the sandbox attribute at all.

So using a traditional sandboxed iframe isn't an option here, because it doesn't let us interact with the iframe from the parent in a unidirectional manner. So what can we do?

## postMessage to an HTML-writing sandboxed iframe

Put simply, we can create a sandboxed iframe which receives data via postMessage, and ... simply executes (or writes) whatever it receives. Since postMessage is literally intended for cross-origin communication, we are able to create a communication channel from the parent to the iframe, while the iframe is sandboxed cross-origin! The browser enforces the strict sandbox/isolation of the iframe, but continues to allow cross-origin communication if a listener is set up. In this setup, the iframe:

- Receives data (HTML) to write to its page.
- Receives commands to execute.
- Renders the data exactly as it would be viewed in any other clean context (notwithstanding the sandbox restrictions, which can be lifted with various `allow-` [attributes](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe#sandbox).
- Is cross-origin, so cannot access sensitive data or execute commands with full privileges in our parent's page context.
- Cannot access or change the parent.

The implementation is generally quite simple, and can even be self-contained:

```html
<!DOCTYPE html>
<html>
  <body>
    <iframe
      id="sandboxFrame"
      sandbox="allow-scripts allow-modals"
      width="800"
      height="600"
      srcdoc='
        <!DOCTYPE html>
        <html>
          <body>
            <div id="container"></div>
            <script>
              window.addEventListener("message", function(event) {
                let message;
                try {
                  message = JSON.parse(event.data);
                } catch (e) {
                  console.error("Invalid JSON message received:", e);
                  return;
                }
                const { type, payload } = message;
                if (type === "document") {
                  const container = document.getElementById("container");
                  if (container) {
                    container.innerHTML = payload;
                  } else {
                    console.error("Container element not found");
                  }
                } else if (type === "script") {
                  try {
                    new Function(payload)();
                  } catch (e) {
                    console.error("Error executing script:", e);
                  }
                } else {
                  console.warn("Unknown message type:", type);
                }
              });
            </script>
          </body>
        </html>
      '
    ></iframe>

    <script>
      const iframe = document.getElementById("sandboxFrame");
      iframe.onload = () => {
        const message = {
          type: "document",
          payload: '<!DOCTYPE html><html><body><h1>Hello</h1><script>alert("hello!")<\/script></body></html>',
        };
        iframe.contentWindow.postMessage(JSON.stringify(message), "*");

        const message2 = {
          type: "script",
          payload: 'alert(window.origin);'
        };
        iframe.contentWindow.postMessage(JSON.stringify(message2), "*");
      };
    </script>
  </body>
</html>
```

Note: in the above example, I specified `sandbox="allow-scripts allow-modals"`. This allows the sandbox to use `alert()`, which demonstrates that the origin of the main html page differs from the sandboxed iframe (whose origin is `null`). Unfortunately, we have to use `postMessage` with receiver set to `*` (you can't set it to `null`) -- if that's a problem in your threat model, you can use `<iframe src=..>` instead, with the receiver hosted on a separate path (`viewer.html`, for example). Or, you can use a `MessagePort` to be more secure (details can be found [here](https://github.com/MegaManSec/Security-Solutions/blob/main/Sandboxed-Iframe-Arbitrary-Html.md)).

## Not a full solution

The above example works quite well: the "Hello" is shown in the iframe, and the second message is sent to the iframe and executed (the alert with the origin, which is `null`). But wait: why isn't `<script>alert("hello!")<\/script>` firing? That's because `<script>` tags are inert when created in an `innerHTML`. The reason we use `innerHTML` is because if we simply rewrite the whole page (e.g. using `document.open(); document.write(...); document.close();`), our listener would be wiped; that's basically the equivalent of `iframe.srcdoc = ...` -- we would delete our listener and not be able to continue sending `document` or `script` messages. There are a couple solutions to this, all with varying problems of their own. I'll outline each of the ideas that I had.

### Re-insert scripts after setting innerHTML

After setting the `innerHTML` of the payload, we can simply re-insert each of the `<script>` tags dynamically, which means they will actually get executed. Our `sandboxFrame` then becomes:

```html
    <iframe
      id="sandboxFrame"
      sandbox="allow-scripts allow-modals"
      width="800"
      height="600"
      srcdoc='
        <!DOCTYPE html>
        <html>
          <body>
            <div id="container"></div>
            <script>
              window.addEventListener("message", function(event) {
                let message;
                try {
                  message = JSON.parse(event.data);
                } catch (e) {
                  console.error("Invalid JSON message received:", e);
                  return;
                }
                const { type, payload } = message;
                if (type === "document") {
                  const container = document.getElementById("container");
                  if (container) {
                    container.innerHTML = payload;

                    // Find all <script> tags in the container
                    const scripts = container.querySelectorAll("script");
                    for (const oldScript of scripts) {
                      const s = document.createElement("script");

                      // Preserve attributes of script tags
                      for (const { name, value } of Array.from(oldScript.attributes)) {
                        s.setAttribute(name, value);
                      }

                      // Inline script content
                      if (oldScript.textContent) s.append(oldScript.textContent);
                      // Replace in-place
                      oldScript.replaceWith(s);
                    }
                  } else {
                    console.error("Container element not found");
                  }
                } else if (type === "script") {
                  try {
                    new Function(payload)();
                  } catch (e) {
                    console.error("Error executing script:", e);
                  }
                } else {
                  console.warn("Unknown message type:", type);
                }
              });
            </script>
          </body>
        </html>
      '
    ></iframe>
```

This works pretty well! But ... I don't like it. `<script>` is not the only thing that's inert when setting `innerHTML`. Various things like `autofocus`, `<body onload>`, and some other things, are also inert, and manually running each of them doesn't scale

#### MutationObserver command shim

By the way, manually looping over every `<script>` tag in this way isn't necessary. We can use the new [MutationObserver](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver) API to monitor for any `<script>` nodes appearing, and cloning a fresh node (so it actually executes) automatically. That would look something like this:
```html
    <iframe
      id="sandboxFrame"
      sandbox="allow-scripts allow-modals"
      width="800"
      height="600"
      srcdoc='
        <!DOCTYPE html>
        <html>
          <body>
            <div id="container"></div>
            <script>
              const container = document.getElementById("container");
              function hydrateScripts(root) {
                // handle both inline and external scripts
                const scripts = root.querySelectorAll("script:not([data-hydrated])");
                for (const old of scripts) {
                  const s = document.createElement("script");
                  // copy attributes (type, src, async, defer, nonce, integrity, crossorigin, etc.)
                  for (const { name, value } of old.attributes) s.setAttribute(name, value);
                  if (!s.src) s.textContent = old.textContent;
                  s.dataset.hydrated = "1";
                  old.replaceWith(s); // newly created <script> executes
                }
              }

              // Observe once
              const obs = new MutationObserver((recs) => {
                for (const r of recs) {
                  for (const n of r.addedNodes) {
                    if (n.nodeType !== 1) continue; // element only
                    if (n.tagName === "SCRIPT") {
                      // single script added
                      hydrateScripts(n.parentNode);
                    } else if (n.querySelector) {
                      // element/fragment with possible nested scripts
                      hydrateScripts(n);
                    }
                  }
                }
              });
              obs.observe(container, { childList: true, subtree: true });
              window.addEventListener("message", function(event) {
                let message;
                try {
                  message = JSON.parse(event.data);
                } catch (e) {
                  console.error("Invalid JSON message received:", e);
                  return;
                }
                const { type, payload } = message;
                if (type === "document") {
                  const container = document.getElementById("container");
                  if (container) {
                    container.innerHTML = payload;
                  } else {
                    console.error("Container element not found");
                  }
                } else if (type === "script") {
                  try {
                    new Function(payload)();
                  } catch (e) {
                    console.error("Error executing script:", e);
                  }
                } else {
                  console.warn("Unknown message type:", type);
                }
              });
            </script>
          </body>
        </html>
      '
    ></iframe>
```

### Self-replacing document with a built-in bootstrap (the best solution)

Instead of playing around with rewriting scripts and so on, it seems to me that the best way to do all of this is to simply set the `srcdoc` of the `sandboxFrame` iframe to the HTML we want to display -- and just add the postMessage script-execution listener in that HTML so we can interact with it. Something like this:

```html
<!DOCTYPE html>
<html>
  <body>
    <iframe
      id="sandboxFrame"
      sandbox="allow-scripts allow-modals"
      width="800"
      height="600"
    ></iframe>
    <script>
      const BOOTSTRAP = `
        <!DOCTYPE html>
        <html>
          <head>
          <meta charset="utf-8">
          <script>
            window.addEventListener("message", function(event) {
              let message;
              try {
                message = JSON.parse(event.data);
              } catch (e) {
                console.error("Invalid JSON message received:", e);
                return;
              }
              const { type, payload } = message;
              if (type === "script") {
              try {
                new Function(payload)();
              } catch (e) {
                console.log("Error executing script:", e);
              }
            } else {
              console.warn("Unknown message type:", type);
            }
          });
          <\/script>
        </head>
        <body>
      `;
      const BOOTSTRAP_AFTER = `
          </body>
        </html>
      `;

      const iframe = document.getElementById("sandboxFrame");
      iframe.srcdoc = BOOTSTRAP + '<!DOCTYPE html><html><body><h1>Hello</h1><script>alert("hello!")<\/script></body></html>' + BOOTSTRAP_AFTER;
      iframe.onload = () => {

        const message2 = {
          type: "script",
          payload: 'alert(window.origin);'
        };
        iframe.contentWindow.postMessage(JSON.stringify(message2), "*");
      };
    </script>
  </body>
</html>
```

... and it works! On load, the iframe gets a full, valid HTML document, which includes the listener. We don't simply put the `<script>` before the arbitrary HTML, because otherwise the browser would render the page in quirks mode. The bootstrap listener is parsed early in `<head>`, so if the untrusted HTML includes a restrictive `<meta http-equiv="Content-Security-Policy">`, the listener is already installed and we can send it commands. The untrusted HTML is placed in `<body>` and executes there; if it contains its own `<html>`/`<head>`/`<meta>` elements, the HTML parser of the browser will merge them into the outer document automatically.

As mentioned, if you want to use `MessagePort` to be more secure, the slightly modified code can be found [here](https://github.com/MegaManSec/Security-Solutions/blob/main/Sandboxed-Iframe-Arbitrary-Html.md).

## Conclusion

All in all, it's surprisingly difficult to create a one-way sandbox in the browser to render arbitrary HTML and execute arbitrary javascript where the parent can choose the data and which allows the parent to interact with the child but not the other way around. However, by creating a sandboxed iframe which can receive HTML and commands and then render it, as controlled by the parent, we can achieve the goal of safely rendering arbitrary HTML.
