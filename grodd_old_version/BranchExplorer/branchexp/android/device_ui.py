

class DeviceUi(object):
    """ Interface to a Device graphical interface and buttons. """

    def __init__(self, device):
        self.device = device

    def touch(self, x_coord, y_coord):
        """ Touch the device screen at (x_coord, y_coord). """
        touch_command = ["shell", "input", "tap", str(x_coord), str(y_coord)]
        self.device.send_command(touch_command)

    def swipe(self, x0_coord, y0_coord, x1_coord, y1_coord, duration):
        """ Do a swipe on the device screen, from (x0_coord, y0_coord) to
        (x1_coord, y1_coord). """
        swipe_command = [ "shell", "input", "swipe"
                        , str(x0_coord), str(y0_coord)
                        , str(x1_coord), str(y1_coord)
                        , str(duration) ]
        self.device.send_command(swipe_command)

    def go_back(self):
        """ Press the "back" button, whether it is physical or virtual. """
        self.device.send_key_event(4)
