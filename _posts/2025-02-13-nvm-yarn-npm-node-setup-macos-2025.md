---
layout: post
title: "NodeJS, nvm, yarn, and npm on MacOS in 2025"
tags: [dev_tools, macos, programming]
description: "Setting up a JavaScript dev environment on MacOS in 2025? Here is a simple guide for installing Node.js, nvm, npm, and yarn without the bloat."
---

Apparently these days I'm back on MacOS. And with it, I had to set up a javascript development environment. Online resources seem to be outdated and overly complicated (why?), so I thought I would document the process of installation here. It's as simple as:

```shell
brew install nvm
mkdir ~/.nvm
nvm install --lts
npm install -g yarn
```

If a directory has a `.nvmrc` file, you can type `nvm install` to install the correct version, and `nvm use` to use it. To install the correct version of yarn, use `npm install -g yarn`. 

You can insert the following in your bashrc or whatever to use the correct nvm version automatically:

```shell
export NVM_DIR="$HOME/.nvm"
export PATH="$PATH:$(yarn global bin)" # For anything installed by yarn
[ -s "/opt/homebrew/opt/nvm/nvm.sh" ] && \. "/opt/homebrew/opt/nvm/nvm.sh" # This loads nvm
[ -s "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/opt/homebrew/opt/nvm/etc/bash_completion.d/nvm" # This loads nvm bash_completion

enter_directory() {
  if [[ "$PWD" == "$PREV_PWD" ]]; then
    return
  fi

  PREV_PWD="$PWD"
  if [[ -r ".nvmrc" ]]; then
    nvm use
    NVM_DIRTY=true
  elif [[ $NVM_DIRTY = true ]]; then
    nvm use default
    NVM_DIRTY=false
  fi
}

export PROMPT_COMMAND="$PROMPT_COMMAND; enter_directory"
```
