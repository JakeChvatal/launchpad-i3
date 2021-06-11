#!/usr/bin/env python

import sys
import threading
import json

CONFIG_FILE = 'config.json'
LETTER_BUTTONS = {8: 'a', 24: 'b', 40: 'c', 56: 'd', 72: 'e', 88: 'f', 104: 'g', 120: 'h'}

try:
    import launchpad_py as launchpad
except ImportError:
    try:
        import launchpad
    except ImportError:
        sys.exit("Error loading launchpad.py. Please install the launchpad_py package and try again.")

try:
    import i3
except ImportError:
    sys.exit("Error loading i3-py. Please install the i3-py package and try again.")


"""
Detects and manages button press events received by the Launchpad.
Inspired by the similar Subscription class present in the i3 library used.
"""


class Subscription(threading.Thread):
    """
    Creates a new subscription and runs a listener loop. Calls the
    callback on event.
    Example parameters:
    callback = lambda event, data, subscription: print(data)
    """
    subscribed = False

    def __init__(self, callback, launchp, event=None):
        # Variable initialization
        if not callable(callback):
            raise TypeError('Callback must be callable')
        self.callback = callback
        self.event = event
        self.launchp = launchp

        # Thread initialization
        threading.Thread.__init__(self)
        self.listen()

    def run(self):
        """
        Wrapper method for the listen method -- handles exceptions.
        The method is run by the underlying "threading.Thread" object.
        """
        try:
            self.listen()
        except self.launchp.error:
            self.close()

    def listen(self):
        """
        Runs a listener loop until self.subscribed is set to False.
        Calls the given callback method with data and the object itself.
        If event matches the given one, then matching data is retrieved.
        Otherwise, the event itself is sent to the callback.
        In that case 'change' key contains the thing that was changed.
        """
        self.subscribed = True
        while self.subscribed:
            event = self.launchp.ButtonChanged()
            if not event:  # skip an iteration if event is None
                continue
            if not self.event or ('change' in event and event['change'] == self.event):
                data = self.launchp.ButtonStateRaw()
            else:
                data = None
            self.callback(event, data, self)
        self.close()

    def close(self):
        """
        Ends subscription loop by setting self.subscribed to False and
        closing both sockets.
        """
        self.subscribed = False


"""
Interface for i3 and the Launchpad.
"""


class LaunchpadOs:
    def __init__(self):
        self.lp = launchpad.Launchpad()
        self.mode = 'a'
        self.lp.Open()
        try:
            self.json = self.read_json(CONFIG_FILE)
        except: # TODO: find error thrown
            sys.exit("The configuration file could not be found or was not in the format specified.")

        try:
            self.lp.LedAllOn(0)
        except AttributeError:
            sys.exit("The launchpad is not plugged in. Please plug in the device and try again.")
        if self.lp.Open():

            # initial lighting
            self.workspace_control(False, i3.get_workspaces(), False)
            self.i3_menu(None, [0, 0], None)
            self.refresh_letter_buttons()
            self.refresh_grid()

            # subscribe to events
            self.button_monitor = Subscription(self.i3_menu, self.lp)
            self.workspace_monitor = i3.Subscription(self.workspace_control, 'workspace')

    # helper function to read in the json file
    def read_json(self, filepath):
        with open(filepath, encoding='utf-8-sig') as json_file:
            return json.loads(json_file.read())

    # displays leds based on the focused workspace
    def workspace_control(self, event, data, subscription):
        workspaces = [1, 2, 3, 4, 5, 6, 7, 8]

        for workspace in data:
            if workspace['focused']:
                self.lp.LedCtrlXY(workspace['num'] - 1, 0, 0, 2)
            else:
                self.lp.LedCtrlXY(workspace['num'] - 1, 0, 0, 1)
            workspaces.remove(workspace['num'])

        for i in workspaces:
            self.lp.LedCtrlXY(i, 0, 0, 0)

    # runs i3 controls based on the button pressed
    # receives message of button press in form of [button_num, button on?]
    def i3_menu(self, event, data, subscription):
        if data[1] is True:
            # controls workspaces
            if 200 <= data[0] <= 207:
                i3.command('workspace {}'.format(data[0] - 199))

            # menu for a to h buttons
            elif LETTER_BUTTONS.get(data[0]) is not None:
                self.mode = LETTER_BUTTONS.get(data[0])

                if(self.mode == 'h'):
                    self.quit()

                self.refresh_letter_buttons()
                self.refresh_grid()

            # menu for the normal buttons: behavior changes depending on menu and config file
            else:
                coord = [int(data[0]/16), data[0] % 16]
                i3.command(self.json[self.mode][coord[0]][coord[1]])

    # sets the grid according to the current mode
    def refresh_grid(self):
        try:
            grid = self.json[self.mode]
        except KeyError:
            print("This button does not have any configuration associated with it.")
            self.reset_grid()
            return

        for i in range(0, 8):
            for j in range(0, 8):
                if grid[i][j] is not None and grid[i][j] != '':
                    self.lp.LedCtrlXY(i, j + 1, 1, 1)
                else:
                    self.lp.LedCtrlXY(i, j + 1, 0, 0)

    # resets the colors of the main grid
    def reset_grid(self):
        for i in range(0, 8):
            for j in range(0, 8):
                self.lp.LedCtrlXY(i, j + 1, 0, 0)

    # refreshes the letter buttons to their proper values
    def refresh_letter_buttons(self):
        for key, val in LETTER_BUTTONS.items():
            if val == self.mode:
                self.lp.LedCtrlRaw(key, 2, 0)
            else:
                self.lp.LedCtrlRaw(key, 1, 1)

    def quit(self):
        self.lp.LedAllOn(0)
        self.lp.Close()
        self.button_monitor.close()
        self.workspace_monitor.close()


if __name__ == '__main__':
    lp = LaunchpadOs()
