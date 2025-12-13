---
layout: post
title: "Flattening Arrays, Tail Call Recursion, and Stack Overflows in JavaScript"
description: "Fixing 'Maximum call stack size exceeded' in JavaScript. How to replace recursion with iteration and local stacks when flattening arrays."
categories: security
---

Tail Call Optimization (TCO) is a programming technique which allows a supportive engine to optimize functions which may call continuously call themselves. For example, take the following code:

```javascript
function factorial(x) {
    if (x <= 0) {
        return 1
    } else {
        return x * factorial(x-1)
    }
}
```

A compiler, if it supports TCO, can optimize this function such that it doesn't actually call itself x-amount of times, but rather performs an equivalent operation with the same result. The reason for doing this is two-fold: one, it's faster, and two, stack-size is limited, and a function calling itself will eventually blow up the stack and cause problems one way or another (a crash, memory corruption, or whatever; depending on the engine).

Javascript does.. not have TCO. Or at least, it's unlikely that you'll ever use an engine that does support TCO. The whole story about TCO in JS is [quite interesting](https://stackoverflow.com/a/54721813):

>Around 2011, TC39 (the JavaScript standards committee) decided to adopt mandatory TCE for the forthcoming ES6 standard, with consensus from all major browser vendors

>In 2015, the new standard was officially adopted, under the name EcmaScript 2015. At this point, no browser had actually implemented TCE, mostly because there were too many new features in ES2015 that were deemed more important to get out

>In early 2016, both Safari and Chrome implemented TCE. Safari announced shipping it, while Chrome kept it behind an Experimental Feature flag. Other browsers (Firefox and Internet Explorer / Edge) started looking into it as well and had second thoughts. Discussion evolved whether this is a viable feature after all. Edge had problems implementing it efficiently for the Windows ABI, Firefox was concerned about the developer experience of calls "missing" from stack traces (an issue that was already discussed at length in 2011).

>At the May 2016 TC39 meeting the issue of tail calls was discussed extensively for almost an entire day with no resolution. Firefox and Edge made clear that they would not implement TCE as specified in the standard. Firefox members proposed to take it out. Safari and Chrome did not agree with that, and the Safari team made clear that they have no intention of unshipping TCE. The proposal for syntactic tail calls was rejected as well, especially by Safari. The committee was in an impasse.

So, what happens when we don't have TCO and call a function which is highly recursive? Here's the result of the above code running with Node:

```
> factorial(7514)
Infinity
> factorial(7515)
Uncaught RangeError: Maximum call stack size exceeded
    at factorial (REPL7:2:5)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
    at factorial (REPL7:5:20)
```

During some auditing, the most common functionality I have seen which can result in a stack overflow like above is in functions that attempt to flatten arrays. Approximately, the following type functions are what I've seen:

```javascript
function flatten(array) {
  if (!Array.isArray(array)) return [array]
  return array.reduce(function (a, b) {
    return a.concat(flatten(b))
  }, [])
}
```

```javascript
function flattenArray(array) {
  if (!Array.isArray(array)) {
    return [array]
  }
  const resultArr = []
  const _flattenArray = arr => {
    arr.forEach(item => {
      if (Array.isArray(item)) {
        _flattenArray(item)
      } else {
        resultArr.push(item)
      }
    })
  }
  _flattenArray(array)
  return resultArr
}
```

In both cases, a deeply nested array results in a `RangeError` exception being raised when flattening.

The solution to this is to not perform recursion at all; simply use an iterative approach with a _local_ stack, like so:

```javascript
function flatten(array) {
  if (!Array.isArray(array)) {
    return [array]
  }

  const result = []
  const stack = [array]

  while (stack.length > 0) {
    const value = stack.pop()

    if (Array.isArray(value)) {
      for (let i = value.length - 1; i >= 0; i--) {
        stack.push(value[i])
      }
    } else {
      result.push(value)
    }
  }

  return result
}
```

Not only is it faster, but it won't raise an exception for large arrays.
