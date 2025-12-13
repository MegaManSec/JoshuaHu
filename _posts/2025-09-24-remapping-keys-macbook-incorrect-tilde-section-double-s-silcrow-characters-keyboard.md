---
layout: post
title: "Swapping/Remapping the silcrow (§) key for a tilde on international Macbooks"
description: "Fix the misplaced tilde and silcrow (§) keys on international MacBooks. A guide to remapping keys using hidutil and LaunchAgents."
categories: security
---

On every single keyboard I've used in my whole life, the tilde (\`) character has been on the top left of the keyboard -- until today. Apparently some Macbooks have a strange character called a silcrow (§) (or section key, or double-s key) where the tilde normally is, and there is no easy setting to change the mapping of this character in MacOS.

| ![Macbook with a Russian Keyboard Layout](/files/mac-russian-keyboard.jpg) |
|:--:|
| *Russian Keyboard on a Macbook* |


Some online guides recommend some software called Karabiner, but I don't really want to install some behemoth just to remap one key. There is a better way! Running the following command remaps the keys:

```
hidutil property --set '
{
  "UserKeyMapping": [{
          "HIDKeyboardModifierMappingSrc":0x700000035,
          "HIDKeyboardModifierMappingDst":0x700000064},
          {"HIDKeyboardModifierMappingSrc":0x700000064,
          "HIDKeyboardModifierMappingDst":0x700000035
         }]
}
'
```

Running this command in the terminal requires giving the terminal full permissions to monitor all key activity -- something I don't want to do either. So, we can instead create a LaunchAgent that does this on boot.

Creating the file `~/Library/LaunchAgents/local.hidutilKeyMapping.plist`, we add the following:

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>local.hidutilKeyMapping</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/hidutil</string>
        <string>property</string>
        <string>--set</string>
        <string>{
            "UserKeyMapping": [
                {
                    "HIDKeyboardModifierMappingSrc":0x700000035,
                    "HIDKeyboardModifierMappingDst":0x700000064
                },
                {
                    "HIDKeyboardModifierMappingSrc":0x700000064,
                    "HIDKeyboardModifierMappingDst":0x700000035
                }
            ]
        }</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>LimitLoadToSessionType</key>
    <array>

    <string>StandardIO</string>
    </array>
</dict>
</plist>
```

Load the agent using `launchctl load ~/Library/LaunchAgents/local.hidutilKeyMapping.plist`, and reboot. It _should_ work.

By the way, [this website](https://web.archive.org/web/20250831004645/https://hidutil-generator.netlify.app/) allows you to work out the correct Mapping IDs.
