---
layout: post
title: "Bypassing Zscaler, Kandji MDM, and Apple Business Manager for Fun and Lulz"
author: "Joshua Rogers"
categories: security
---

## MacOS Endpoint Management and MDM Systems

This post outlines how easy it is to remove Zscaler, Kandji Extension Manager, and Kandji Endpoint Management, as well as how to render Apple's Business Manager (ABM) ineffective. Indeed, as the saying goes, "_not your hardware, not your system_".

There are two situations that concern these MDM systems, and depending on how your Mac has been purchased, only one may apply to you.

If your system was purchased by a company and then hand-administred by somebody in the company, it is likely that it was on-boarded in Apple's "Business Management" system, which is a type of endpoint management system that allows the company to remotely control the system in one way or another -- and track it via GPS, force installation of certain programs, and so on (ABM can only be set up with physical access to the system). This cannot be "disabled", and even a factory reset cannot get rid of it, as it's burnt into a trusted computing zone  (a signed region of memory in the hardware that only Apple's key is trusted for making changes). When first booting a system like this, the user is introduced with the non-closable popup, "Remote Management. [..] can automatically configure your computer". A company can "disown" the system to remove the business management hold on the system if it likes to. Since it cannot be "removed", we need to find a way to ... render it useless.

This guide assumes a factory-reset MacOS system, however it does not need to be reset. Some of the menus and so on may be different, and some extra or fewer steps may be necessary but somebody competent should manage.

Note-to-self: the output of the command `system_profiler SPConfigurationProfileDataType` will reveal a lot of interesting changes that your MDM does to your system.

## Apple Business Manager (ABM)

When your system is started for the first time after a factory reset, MacOS forces you to connect the system to the internet. Without connecting to the internet, you cannot do the typical MacOS setup procedure. Once connected to the internet, the system retrieves a profile from Apple's servers, and follows whatever instructions have been configured by the business your system is registered to, such as installing further MDM / EDM solutions. The idea is that ABM facilitates the installation of an external MDM system.

You can check if your system is registered in ABM by running the following command:

```
profiles show -type enrollment
```

There are three possible outcomes of the above command:

- "Error fetching Device Enrollment configuration: Client is not DEP enabled", meaning the system is not registered in ABM.
- An empty configuration, meaning your system is registered in ABM but is unassigned to anybody.
- A configuration which lists an MDM servers, meaning your system is actively configured and is being forced to use some MDM.

If your system is not registered in ABM, you can skip this section and continue on to the Zscaler / Kandji section.

The bypass is to simply .. disallow the system from connecting to Apple's MDM servers. DNS to the rescue!

We have two options:

1. Configure a custom DNS server, and block any DNS traffic on the network other than your DNS server during installation/setup.
2. Allow installation of whatever the MDM profile desires, disable DNS traffic, and then manually remove the profile that was installed.

Although both options can be performed on a freshly re-installed system, the latter option can be fully performed on an already-installed system.

In both cases, the goal is to block any connections to Apple's servers which host the MDM profiles. The system, in a new state, knows that it **must** be enrolled in some MDM system, but it doesn't have the MDM profile yet. However, it has a pitfall: if the system cannot download the MDM profile (while connected to the internet), it fail-opens, allowing you to continue setup even though MDM profile installation failed -- with the idea that the profile will forcibly be installed later.

For option one, hosting a DNS resolver which blocks connections would work. For option two, which is functionally easier, the idea is to simply allow the profile to install whatever junk it wants, and then once the system is set up, block DNS by editing `/etc/hosts` and then remove all of the junk that was installed (which will not be re-installed, due to the `/etc/hosts` rules).

I'll go through option 2.

Note I have been made aware that there is a simple script on GitHub which does most of what is outlined in this post, which can be found here: [https://github.com/assafdori/bypass-mdm](https://github.com/assafdori/bypass-mdm). Based on reading the script, it performs most of the actions here (and some more) related the Apple Business Management bypass. I would recommend just using the script for this section.

Once the system is installed, you can simply edit `/etc/hosts` with your favorite editor, and add the following:

```
0.0.0.0 iprofiles.apple.com
0.0.0.0 mdmenrollment.apple.com
0.0.0.0 deviceenrollment.apple.com
```

... annnndddddd it's done. Apple Business MDM will no longer be able to be re-installed. So, let's uninstall the junk. OK, it's not really _that_ easy. So let's go through the full guide.

You need to make sure that your laptop will not connect to the internet on reboot. So, turn off your wifi.

You need to shut down the system now, and hold down the power button to enter recovery mode, and then enter your credentials. In recovery mode, open the terminal (top left; under "Utilities"), and type the following commands:

```
csrutil disable

diskutil apfs list # Find your SSD / HDD, in the format of diskXsY
diskutil apfs unlockVolume diskXsY -passphrase "YOUR_FILEVAULT_PASSWORD" # Type your password

cd "/Volumes/Macintosh HD - Data/var/db/ConfigurationProfiles/Settings"

rm -rf ./.*
rm -rf ./*

touch .cloudConfigProfileInstalled
touch .cloudConfigRecordNotFound
touch .profilesAreInstalled

cd "/Volumes/Macintosh HD - Data/var/db/ConfigurationProfiles/Store"

rm -rf ./.*
rm -rf /*

touch "/Volumes/Macintosh HD - Data/var/db/.AppleSetupDone"

echo "0.0.0.0 deviceenrollment.apple.com" >> "/Volumes/Macintosh HD - Data/etc/hosts"
echo "0.0.0.0 mdmenrollment.apple.com"   >> "/Volumes/Macintosh HD - Data/etc/hosts"
echo "0.0.0.0 iprofiles.apple.com"       >> "/Volumes/Macintosh HD - Data/etc/hosts"

diskutil apfs updatePreboot diskXsY

reboot
```

This disables Apple's SIP, and temporarily removes the MDM profiles downloaded from Apple's servers. It also edits the `/etc/hosts` file on your live system, blocking the downloading of MDM profiles in the future.  Once that's done, reboot into the normal system again.

And that's really it for taking care of ABM. Since ABM is responsible for ensuring that the MDM profiles are installed (i.e. re-installing them as soon as they're uninstalled), we can now remove the MDM profiles and extensions and agents with ease.

By the way, I found that there was some "Enroll your Mac!" popup that would occur once or twice after setting up this custom `/etc/hosts` file and removing the MDM services, but by connecting to WiFi, it's possible to just skip this screen and it doesn't come back.

## Uninstalling Zscaler and Kandji MDM

If you did not need to follow the instructions for bypassing Apple Business Manager, do the following:

1. Reboot, and hold down the power button to enter recovery mode.
2. Enter recovery mode by entering your password, and find the terminal in Utilities (top left) -> Terminal.
3. Run the command `csrutil disable`

Reboot into the normal system, and then open the terminal again, running the following commands (as root):

```
cd /var/db/ConfigurationProfiles
rm -rf *
mkdir Settings
touch Settings/.profilesAreInstalled
```

Now let's continue.

When Zscaler and Kandji are installed, they install their own "extensions" and agents, which are not easily uninstalled (i.e. cannot be done unless SIP is disabled).

Running the follwing commands as root, we can get rid of them completely. If any of these commands fail, try removing the entries in `/etc/hosts` (if you followed the above steps) -- but don't forget to add the entries as soon as you run all of these commands. Note: some of these commands may need to be run multiple times.

List all of the installed extensions:

```
systemextensionsctl list
```

You'll see something like this:

```
*	*	P3FGV63VK7	io.kandji.KandjiAgent.ESF-Extension (1.8.44/801)	Kandji ESF Extension	[activated enabled]
```

Now uninstall it, making sure you change `P3FGV63VK7` if it's different:

```
systemextensionsctl uninstall P3FGV63VK7 io.kandji.KandjiAgent.ESF-Extension
```

Do the same thing for Zscaler.

Next, get the process IDs of running Kandji:
```
ps ax -o pid,command | grep -i kandji # find Kandji running
kill -11 pid pid
```

Now delete all profiles if possible:

```
profiles -D
profiles -d
```

Find the directory for the Kandji ESF extension:

```
cd /Library/SystemExtensions/EndpointSecurity/
ls */
```

Remove it:

```
rm -rf /Library/SystemExtensions/83EDEB4F-FCDB-4D19-AC4E-3878CDA2C860/io.kandji.KandjiAgent.ESF-Extension.systemextension/Contents/
```

Do the same for the Zscaler extension.

Now, remove everything else from Kandji:

```
rm -rf /Applications/Utilities/Kandji\ Extension\ Manager.app/ /Library/Application\ Support/Kandji/  /Library/Kandji/
```

Also remove the LaunchAgents:

```
cd /Library/LaunchAgents/
ls ./
rm -rf io.kandji.*
```

Also remove the LaunchDaemons:

```
cd /Library/LaunchDaemons/
ls ./
rm -rf io.kandji.*
```

If you find any references to Zscaler, you can do this too -- but if you need to use Zscaler's _application_ (as a proxy/VPN), then don't delete that.

You can now reboot.

## Deleting Other Junk

It's very likely that your system administrator has installed other junk on your system. If you see any more junk in `systemextensionsctl list`, `/Library/SystemExtensions/EndpointSecurity/`, `/Library/SystemExtensions/`, `/Library/LaunchAgents/`, or `/Library/LaunchDaemons/`, just follow the above instructions and do similar actions.

## Restoring SIP

Reboot again into recovery mode (reboot, hold down the power button, and enter your password when prompted) and open the terminal. Type `csrutil enable`. Reboot.

On the next startup, the system may act strangely for a bit (changed background, some the "Setup Assistant" and so on, but you can get through all of this (just connect to wifi, and .. continue; it will error out, but fail-open.

## Restoring Password Policies

These MDM tools are often accompanied by some ridiculous password policy, which can be identified by running `pwpolicy getaccountpolicies`. For example:

```
$ pwpolicy getaccountpolicies
Getting global account policies
[..]
	<key>policyCategoryPasswordContent</key>
[..]
			<string>policyAttributePassword matches '.{4,}+'</string>
[..]
				<key>en_AU</key>
				<string>Enter a password that is four characters or more.</string>
[..]
```

I, for one, like my passwords 3 characters long. To reset the password policy, on the normal system, run:

```
sudo pwpolicy -clearaccountpolicies
```

## Conclusion

All of this is a bit of work, but it is easy to render Apple Business Manager useless, and uninstall all of this MDM junk. If you have a semi-competent team that manages all of this in your company, it's possible they will set up some monitoring to catch any device which hasn't reported to the MDM servers in some time. An easy solution to this is to simply install the MDM profile in a virtual machine. If you need to install the MDM in order to get access to some proxy/VPN, installing it in a virtual machine is an excellent solution, because you can then run `sshd(1)`, and simply connect with `ssh -D9000 user@vm-ip`, creating a SOCKS5 proxy in the VM, which you can use for all of your connections on the real system.

P.S: Apparently I offer "off-boarding security consulting" these days, as well as Enterprise Security Testing of Ineffective Security Controls. So if you're reading this, please let me know where I should send the invoice for services rendered :-).

