# !/usr/bin/env python

import sys
import threading
import json

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
        self.start()

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

        try:
            self.lp.LedAllOn(0)
        except AttributeError:
            sys.exit("The launchpad is not plugged in. Please plug in the device and try again.")

    # displays leds based on workspace
    def workspace_control(self, event, data, subscription):
        letter_buttons = {8: 'a', 24: 'b', 40: 'c', 56: 'd', 72: 'e', 88: 'f', 104: 'g', 120: 'h'}

        self.lp.LedAllOn(0)

        for workspace in data:
            if workspace['focused']:
                self.lp.LedCtrlXY(workspace['num'] - 1, 0, 0, 2)
            else:
                self.lp.LedCtrlXY(workspace['num'] - 1, 0, 0, 1)

        for key, val in letter_buttons:
            if val == self.mode:
                self.lp.LedCtrlXY(key, 0, 2, 0)
            else:
                self.lp.LedCtrlXY(key, 0, 1, 0)

    # runs i3 controls based on the button pressed
    def i3_menu(self, event, data, subscription):
        print(data)
        letter_buttons = {8: 'a', 24: 'b', 40: 'c', 56: 'd', 72: 'e', 88: 'f', 104: 'g', 120: 'h'}

        if data[1] is True and 200 <= data[0] <= 207:
            i3.command('workspace {}'.format(data[0] - 199))

        # menu for a to h buttons
        elif letter_buttons.get(data[0]) is not None:
            self.mode = letter_buttons.get(data[0])
            self.lp.LedCtrlString(letter_buttons.get(data[0]), 1, 1, 50)
            self.lp.LedAllOn(0)

        # menu for the normal buttons: behavior changes depending on menu and config file
        elif data[1] == True and self.mode == 'a':
            coord = [data[0] / 16 + 1, data[0] % 16]
            print(coord)

            if data[0] >= 64:
                self.lp.LedCtrlRaw(data[0], 0, 2)
                i3.command('exec termite')
            else:
                self.lp.LedCtrlRaw(data[0], 2, 0)
                i3.command('kill')

    # Starts the event listeners responsible for detecting button changes on the Launchpad.
    def main(self):
        if self.lp.Open():
            self.workspace_control(False, i3.get_workspaces(), False)

            button_monitor = Subscription(self.i3_menu, self.lp)
            workspace_monitor = i3.Subscription(self.workspace_control, 'workspace')


if __name__ == '__main__':
    lp = LaunchpadOs()
    lp.main()
