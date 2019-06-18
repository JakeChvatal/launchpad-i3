# launchpad-i3
An interface for controlling the i3 window manager with a Novation Launchpad MIDI device.

The buttons labeled 1 through 8 manage i3's windows, able to switch to display the window with the a number corresponding to the number on the Launchpad device (only 8 workspaces are accessable at any given time, as the Launchpad only has 8 of these buttons). 
The buttons labeled a through g change the mode available to the 64 main pads, with the actions controlled from that mode easily configurable through the provided configuration file. The 'h' button quits the program safely.

### Dependencies
- Python 3
- pygame
- launchpad_py
- i3

## Run
To run, ensure you are using Python 3 and that the Launchpad is plugged into your system.

```
$ git clone https://github.com/JakeChvatal/launchpad-i3.git
$ pip install pygame launchpad_py i3
$ ./launchpad-linux.py
```

## Configuration
The [configuration file](config.json) follows the following pattern:
``` javascript
{ "mode letter": {[["command1", "command2"], ["command3", "command4"]] } 
```
where the mode letter corresponds to one of the letters 'a' through 'g' available on the launchpad, and 'command' represents a command to be sent to i3-msg, i3's control and messaging system, to be executed by the window manager. Prefacing a command with 'exec' will run a bash command through your terminal emulator; a long list of command arguments may require a String after the exec line with escape characters (i.e. "exec \"git reset --HARD\""). 
