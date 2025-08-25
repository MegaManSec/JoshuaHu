---
layout: post
title: "CodeQL on MacOS"
author: "Joshua Rogers"
categories: security
---

Continuing the MacOS trend, I wanted to document the steps I took to getting CodeQL setup on my system.

```shell
brew install --cask codeql
softwareupdate --install-rosetta --agree-to-license
```

From here, we have a few options.

```shell
mkdir ~/work/
cd ~/work/
git clone --recursive https://github.com/github/codeql.git
```

The CodeQL repository comes with some pre-defined queries. They exist in `[language]/ql/src/[directories]` (`.ql` files). Alternatively, "packs" (`.qls` files) are also available in `[language]/ql/src/codeql-suites/` which will run multiple queries based on the list used.

To run CodeQL, you can run (for example) use multiple queries:

```shell
codeql database create /tmp/cql/"$(basename "$PWD")" --language=javascript --overwrite
codeql database analyze --rerun /tmp/cql/"$(basename "$PWD")" ~/work/codeql/javascript/ql/src/codeql-suites/javascript-security-extended.qls --format=sarifv2.1.0 --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif" # Specific .qls file selected. Can be multiple files. Cannot be a folder.
codeql database analyze --rerun /tmp/cql/"$(basename "$PWD")" ~/work/codeql/javascript/ql/src/ --format=sarifv2.1.0 --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif" # Uses all .ql files found in the selected folder. Can either be directory of file(s).
```

The first `database create` command statically analyzes the source code, creating a database in `/tmp/cql/"$(basename "$PWD")"`.

The final two lines query the analysis (sort of like SQL).
The first `database analyze` uses a "pack", which will use pre-specified queries, saving the results in `--output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"`. The second `database analyze` command will find all `.ql` files in the `~/work/codeql/javascript/ql/src/` directory, and use them to query the database created in `/tmp/cql/"$(basename "$PWD")`, and save them in `--output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"`.

The output file is a "sarif file". It can be viewed in various editors, or online.

If you want to create your own queries, you can do the following:

```shell
cd ~/work/
codeql pack init custom-codeql-queries
cd custom-codeql-queries/
cat <<EOF
dependencies:
  codeql/javascript-all: "*"
EOF >> qlpack.yml
codeql pack install
```

You can then create queries in that folder and either use the `codeql database analyze` command from before to work with the whole folder, or you can specify individual queries:

```shell
codeql database create /tmp/cql/"$(basename "$PWD")" --language=javascript --overwrite
codeql query run ~/work/custom-codeql-queries/query.ql --database /tmp/cql/"$(basename "$PWD")"
```

I created the following functions in my bashrc:

```shell
codeql-scan-build() {
  mkdir /tmp/cql/ &>/dev/null || true
  codeql database create /tmp/cql/"$(basename "$PWD")" --language=javascript --overwrite
}
codeql-scan-large() {
  codeql database analyze --rerun /tmp/cql/"$(basename "$PWD")" ~/work/codeql/javascript/ql/src/codeql-suites/java* --format=sarifv2.1.0 --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"
}
codeql-scan-custom() {
  codeql database analyze --rerun /tmp/cql/"$(basename "$PWD")" ~/work/custom-codeql-queries/ --format=sarifv2.1.0 --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"
}
```


---

These may also be useful (for myself):

```shell
git clone https://github.com/GitHubSecurityLab/CodeQL-Community-Packs.git
codeql database analyze /tmp/cql/"$(basename "$PWD")" --download githubsecuritylab/codeql-javascript-queries ~/work/CodeQL-Community-Packs/javascript/src/suites/* --format=sarifv2.1.0  --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"
```

```shell
codeql database analyze /tmp/cql/"$(basename "$PWD")" --download trailofbits/cpp-queries:codeql-suites/tob-cpp-full.qls --format=sarif-latest --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"
```


For Java, I do the following:

```shell
export JAVA_HOME=/opt/homebrew/opt/openjdk@21
codeql database analyze --rerun /tmp/cql/"$(basename "$PWD")" --ram=28000 ~/work/codeql-repo/java/ql/src/codeql-suites/java-* --format=sarifv2.1.0 --output=/tmp/cql/"scan-$(basename "$PWD")-$(date +%s).sarif"
codeql database create /tmp/cql/"$(basename "$PWD")" --language=java --overwrite
```
