---
layout: post
title: "Attacking a scripting language's cryptographic functions with Wycheproof"
author: "Joshua Rogers"
categories: security
---

**Introduction**

In 2016, Google released Project Wycheproof. Put into simple terms, Wycheproof is a set of testcases for cryptographic libraries which have been formulated to pick up mistakes and pitfalls of certain cryptographic algorithms. If any of the testcases fail, it may indicate a vulnerability in the cryptographic library. If any of the testcases fail, it may indicate a vulnerability in the cryptographic library. A recent example of such a pitfall is [CVE-2022-21449/"Psychic Signatures" Java Vulnerability ](https://neilmadden.blog/2022/04/19/psychic-signatures-in-java/) -- something that Wycheproof would have picked up if anybody had bothered to use it.

Note: this research was conducted for/while working at Opera Software.

[Nettle](https://www.lysator.liu.se/~nisse/nettle/) is a Cryptographic library written in C, offering capabilities for a variety of different algorithms. Nettle is the default (and only supported) cryptographic library used by Pike for its crypto-functions.

[Pike](https://pike.lysator.liu.se) is a general-purpose, high-level, dynamic programming language, with a syntax similar to that of C. It has bindings for many different libraries, including some cryptographic functionality.


**PikeProof**

To test both Nettle and Pike for defects, I created a Pike project which uses Wycheproof's testcases where possible (not all tests concern algorithms that are supported in Pike) and reports any failures. This project was named PikeProof (also known as _nettle-wycheproof-testsuite_.)
Note: although this project can check for issues in Pike, it does not guarantee that some issues do not exist in Nettle -- Pike's glue may 'hide' the issues in Nettle.

When writing the script, it quickly became apparent that I had to create a modular system that would plug-and-play different algorithms. This is because different algorithms require different initialisations, instructions, and designs. One of the biggest issues I had in creating this project was finding out how some algorithms are supposed to work -- I'm no cryptography expert, so it took quite a long time to learn about how these algorithms should be used.

**Importing Data**

The testcases come in the form of JSON-formatted files. The Pikeproof script first imports the JSON files into an array, discarding any results that it does not know what to do with. This means that we have a list of algorithms that Pike supports which is checked (optionally, a 'forced mode' is included which only imports testcases from a specific algorithm), which can be easily added to.

Once the testcases have been imported, each testcase is iterated over, based on their so-called [_schema_](https://github.com/google/wycheproof/blob/master/doc/files.md) (i.e. the definition of the data for each of the imported files). A lookup table is used to determine which type of test and algorithm the testcases corresponds to.

**Design**

Each schema may represent more than one algorithm. For example, both algorithms _AES-EAX_ and _AES-CCM_ use the same structure for the data of the testcases. Generally, this means the same tests/functions can be re-used for similar algorithms (i.e. the method of encrypting and decrypting are the same -- just with a different state function used at the beginning), with the exact algorithm's state function being dynamically called (using another lookup table).

For each algorithm, there is one main function which prepares all of the data from the imported testcases, before iterating over each of the testcases and running the individual tests/checks. Any failures are then recorded.

**Exception Handling**

As mentioned, the same functions may be used for multiple, similar algorithms. This means that the same instructions for, say, handling _AES-EAX_ tests, are performed for those of _AES-CCM_ -- simply the initialisation of the state class differs.  The assumption that functions could be shared for similar algorithms did not always hold, however.  In the case of the _AES-GCM_ algorithm (a test falling under the _aead_test_schema.json_ schema), the 16-byte "tag size" could not manually be set by the caller, or Pike would produce an error -- in the case of every other algorithm falling within that schema, the tag size could be set.

Instead of simply changing the script to handle the single exception of _AES-GCM_ for the _aead_test_schema.json_ testing function, I instead made a more dynamic and modular function, called `handle_special_actions`, which _every_ testing function runs at the beginning, while the data is being handled. `handle_special_actions` loops through a table mapping specific algorithms to special functions which handle the exceptions needed. In the case of _AES-GCM_, we can see that the function `unset_digest_size` will only be run for data corresponding to the algorithm _AES-GCM_.
```pike
void handle_special_actions(mapping test, string algorithm) {
   foreach (special_action_table; string index; function value) {
      if(index == algorithm) {
         value(test);
      }
   }
}
```
```pike
mapping(string:function) special_action_table = ([
   /* GCM only allows a tag size of 16, therefore set the DigestSize to "null" */
   "AES-GCM": unset_digest_size,
]);
```
```pike
void unset_digest_size(mapping test) {
   test["tagSize"] = "null";
}
```

Because `handle_special_actions` is called at the beginning of every test, it is easy to add new exception functions where needed, by simply adding an algorithm:function pair to the `special_action_table` table.

**Results**

In total, five _major_ vulnerabilities were discovered in Pike's crypto handling (note: none of these bugs were due to issues in the Nettle library):
1. Null Pointer Dereference in [Crypto.AES.CCM](https://git.lysator.liu.se/pikelang/pike/-/issues/10072)
2. Incorrect Digest [Crypto.AES.CCM](https://git.lysator.liu.se/pikelang/pike/-/issues/10074)
3. Infinite Loop [Crypto.DSA](https://git.lysator.liu.se/pikelang/pike/-/issues/10075)
4. Incorrect Signature Verification [Crypto.DSA](https://git.lysator.liu.se/pikelang/pike/-/issues/10077)
5. Incorrect Signature Verification [Crypto.ECC.SECP_521R1](https://git.lysator.liu.se/pikelang/pike/-/issues/10078)

Some other minor issues were found, however, are likely not worth noting.

**Conclusion**

Based on a suggestion from [Guido Vranken](https://guidovranken.com), I also tried running this script on a set of different architectures, since Nettle has assembly optimization for different CPUs. In the end, however, no extra issues were found.

The whole project itself was certainly something fun to work with -- learning about different cryptographic algorithms, how they work and what they're used for, and how to script in Pike.

The source code for this project can be found [on GitHub](https://github.com/operasoftware/nettle-wycheproof-testsuite).
