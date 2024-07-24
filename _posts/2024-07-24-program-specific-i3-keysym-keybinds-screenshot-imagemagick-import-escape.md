---
layout: post
title: "Exclusive i3 keysyms for specific programs. or: Binding Escape on imagemagick's import"
author: "Joshua Rogers"
categories: security
---

Years ago when setting up i3 on my FreeBSD laptop, I used ImageMagick's [import(1)](https://man.freebsd.org/cgi/man.cgi?query=import&manpath=ports) to take screenshots of my X windows and save them for the future (my screenshot collection goes back to 2009; like a photo collection but of my online identity, but that's another topic for another day).

Using `import(1)`, there is no way to cancel an intiatied screenshot selection: you must screenshot _something_ for the selection to close. So what if I ended up not wanting to screenshot anything after starting a screenshot? I couldn't just bind the `Escape` key on my keyboard to kill `import`, since I use the `Escape` key for many other things like [readline](https://twobithistory.org/2019/08/22/readline.html).

The problem at hand is therefore: since the `Escape` key is already used by programs _other_ than `import(1)`, how can we exclusively bind the `Escape` key to execute a specific command (`kill`) when a screenshot is being taken using `import(1)`? 


---

i3's "[binding modes](https://i3wm.org/docs/userguide.html#binding_modes)" seems to be the solution here. As the manual states:

```
You can have multiple sets of bindings by using different binding modes. When you switch to another binding mode, all bindings from the current mode are released and only the bindings defined in the new mode are valid for as long as you stay in that binding mode.
```

To achieve our objective, we therefore:

1. Bind the `Mod4+Shift+4` key combination to both switching the a new mode named "screenshot" -- and execute a script `screenshot.sh`.
2. Inside the "screenshot" mode, bind the `Escape` key to go back to the "default" mode and kill `/usr/local/bin/import`.
3. Create a `screenshot.sh` script which calls `/usr/local/bin/import` to take the actual screenshot.

---

The i3 config of this solution looks as such:

```
bindsym Mod4+Shift+4 --release mode "screenshot" ; exec ~/scripts/screenshot.sh
mode "screenshot" {
  bindsym Escape --release mode "default" ; exec kill $(pgrep -f /usr/local/bin/import)
}
```

and the `screenshot.sh` looks like:

```
#!/bin/sh

DATE=`date +%Y-%m-%d:%H:%M:%S`
/usr/local/bin/import ~/Pictures/Screenshots/Screenshot-"${DATE}".png && \
  ln -fs ~/Pictures/Screenshots/Screenshot-"${DATE}".png /tmp/latest-screenshot.png
exit_code=$?

i3-msg mode "default"
exit $exit_code
```

`i3-msg mode "default"` in the script ensures that when a screenshot _is_ taken, i3 moves back to the "default" mode. The `mode "default"` in the `bindsym Escape` of the screenshot mode is not really necessary, but it is added for redundancy.



---

These days, I use [scrot(1)](https://www.freshports.org/graphics/scrot/) for screenshots, which comes with inbuilt functionality to exit the screenshot selection when any key is pressed:
```
bindsym Mod4+Shift+4 --release exec scrot -s /home/user/Pictures/Screenshots/Screenshot-%Y-%m-%d:%H:%M:%S.png -e 'ln -fs "$f" /tmp/latest-screenshot.png'
```

However, I still use i3 modes to set up program-specific keybinds as outlined in this post elsewhere.
