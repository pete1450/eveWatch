# eveWatch

This is gross and thrown together. Most code is used, some may not be and is left over from trying things and never cleaned up.

## Install
1. Install python. I use 3.10
2. Install Tesseract
3. Install everything from the imports
4. Set up a discord bot and save the token. [like this](https://discordpy.readthedocs.io/en/stable/discord.html#discord-intro)
5. Start the game, make small images of the following. I've included mine as examples but your screen resolution may be different.
    a. Exclamation icon
	b. Minus icon
	c. Equals icon
6. Update and values in the config section of the script.
    * you need to find several bounding boxes for things on your screen based on upper left point then width/height.
7. Update instances of "somethingfriendly" for harcoded corp names to ignore
8. Run the script
9. Don't move/cover your emulator


## Behavior
The script is constantly watching the local counts and when it sees a number that doesn't OCR to a zero it assumes there's something to report. At this point it waits for something to appear in the grid list. 

Currently there are some hardcodes to ignore any toon names in the alliance. This only works when it makes the assumption that any text is reads is an alternating sequence of toon name then ship type. Somethimes this messes up...

All toons are stored in a map and a flag is set when they are reported on so they only show once. 

At the point that the script finds no hostile count it empties the map so they are reported on if they come back through. Message is sent alerting that the system is empty.

## Other functionality
* play wav file when hostiles found
* send heartbeats to an endpoint that can ideally alert when not recieved. Lets you know if the cam is down.
* mqtt message that can be used for reading and triggering automations like flashing lights
