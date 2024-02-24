import time
import logging
import threading
import ctypes

import usb.core
import usb.util
from usb.backend import libusb1
from PIL import Image, ImageDraw, ImageFont
import wx
from wx.adv import TaskBarIcon

ctypes.windll.shcore.SetProcessDpiAwareness(2)

# Mouse: Razer Viper V2 Pro
MODEL = "Razer Viper V2 Pro"
WIRELESS_RECEIVER = 0x00A6
WIRELESS_WIRED = 0x00A5
TRAN_ID = b"\x1f"

# Colors
RED = (255, 0, 0)
GREEN = (71, 255, 12)
YELLOW = (255, 255, 0)

# Settings
poll_rate = 30
foreground_color = GREEN
backgroung_color = (0, 0, 0, 0)

logging.basicConfig(level=logging.INFO)


def get_mouse():
    """
    Function that checks whether the mouse is plugged in or not
    :return: [mouse, wireless]: a list that stores (1) a Device object that represents the mouse; and
    (2) a boolean for stating if the mouse is in wireless state (True) or wired state (False)
    """
    # declare backend: libusb1.0
    backend = libusb1.get_backend()
    # find the mouse by PyUSB
    mouse = usb.core.find(idVendor=0x1532, idProduct=WIRELESS_RECEIVER, backend=backend)
    # if the receiver is not found, mouse would be None
    if not mouse:
        # try finding the wired mouse
        mouse = usb.core.find(idVendor=0x1532, idProduct=WIRELESS_WIRED, backend=backend)
        # still not found, then the mouse is not plugged in, raise error
        if not mouse:
            raise RuntimeError(f"The specified mouse (PID:{WIRELESS_RECEIVER} or {WIRELESS_WIRED}) cannot be found.")
        # else we found the wired mouse, set wireless to False for waiting time
        else:
            wireless = False
    # else we found the wireless mouse, set wireless to True for waiting time
    else:
        wireless = True

    return [mouse, wireless]


def battery_msg():
    """
    Function that creates and returns the message to be sent to the device
    :return: meg: the message to be sent to the mouse for getting the battery level
    """
    # adapted from https://github.com/rsmith-nl/scripts/blob/main/set-ornata-chroma-rgb.py
    # the first 8 bytes in order from left to right
    # status + transaction_id.id + remaining packets (\x00\x00) + protocol_type + command_class + command_id + data_size
    msg = b"\x00" + TRAN_ID + b"\x00\x00\x00\x02\x07\x80"
    crc = 0
    for i in msg[2:]:
        crc ^= i
    # the next 80 bytes would be storing the data to be sent, but for getting the battery no data is sent
    msg += bytes(80)
    # the last 2 bytes would be the crc and a zero byte
    msg += bytes([crc, 0])
    return msg


def get_battery():
    """
    Function for getting the battery level of a Razer Mamba Wireless, or other device if adapted
    :return: a string with the battery level as a percentage (0 - 100)
    """
    # find the mouse and the state, see get_mouse() for detail
    try:
        [mouse, wireless] = get_mouse()
    except RuntimeError as e:
        return "-"
    # the message to be sent to the mouse, see battery_msg() for detail
    msg = battery_msg()
    logging.info(f"Message sent to the mouse: {list(msg)}")
    # needed by PyUSB
    # if Linux, need to detach kernel driver
    mouse.set_configuration()
    usb.util.claim_interface(mouse, 0)
    # send request (battery), see razer_send_control_msg in razercommon.c in OpenRazer driver for detail
    req = mouse.ctrl_transfer(bmRequestType=0x21, bRequest=0x09, wValue=0x300, data_or_wLength=msg, wIndex=0x00)
    # needed by PyUSB
    usb.util.dispose_resources(mouse)
    # if the mouse is wireless, need to wait before getting response
    if wireless:
        time.sleep(0.3305)
    # receive response
    result = mouse.ctrl_transfer(bmRequestType=0xa1, bRequest=0x01, wValue=0x300, data_or_wLength=90, wIndex=0x00)
    usb.util.dispose_resources(mouse)
    usb.util.release_interface(mouse, 0)
    logging.info(f"Message received from the mouse: {list(result)}")
    # The raw battery level is in 0 - 255, scale it to 100 for human, return integer number
    # It looks like if wireless mouse is in sleep mode, it returns "0". So we show "Zzz" indicator.
    if int(result[9] / 255 * 100) == 0:
        return "Zzz"
    else:
        return f"{int(result[9] / 255 * 100)}"


def create_icon(text: str, color):

    # Convert PIL Image to wxPython Bitmap
    def PIL2wx(image):
        width, height = image.size
        return wx.Bitmap.FromBufferRGBA(width, height, image.tobytes())

    def get_text_pos_size(text):
        if len(text) == 3:
            return (0, 28), 80
        elif len(text) == 2:
            return (4, 16), 110
        elif len(text) == 1:
            return (34, 16), 110

    image = Image.new(mode="RGBA", size=(128, 128), color=backgroung_color)
    # Call draw Method to add 2D graphics in an image
    I1 = ImageDraw.Draw(image)
    # Custom font style and font size
    text_pos, size = get_text_pos_size(text)
    myFont = ImageFont.truetype('consola.ttf', size)
    # Add Text to an image
    I1.text(text_pos, text, font=myFont, fill=color)
    return PIL2wx(image)


class MyTaskBarIcon(TaskBarIcon):

    def __init__(self, frame):
        super().__init__()
        self.frame = frame
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.OnClick)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        item_settings = wx.MenuItem(menu, wx.ID_ANY, "Settings")
        self.Bind(wx.EVT_MENU, self.OnTaskBarActivate, id=item_settings.GetId())
        item_exit = wx.MenuItem(menu, wx.ID_ANY, "Exit")
        self.Bind(wx.EVT_MENU, self.OnTaskBarExit, id=item_exit.GetId())
        # menu.Append(item_settings)
        menu.Append(item_exit)
        return menu

    def OnTaskBarActivate(self, event):
        if not self.frame.IsShown():
            self.frame.Show()

    def OnTaskBarExit(self, event):
        self.Destroy()
        self.frame.Destroy()

    def OnClick(self, event):
        if self.frame.battery == "Zzz":
            self.frame.battery = get_battery()
            logging.info(f"Battery level obtained: {self.frame.battery}")
            self.frame.tray_icon.SetIcon(create_icon(self.frame.battery, foreground_color),
                                         "No Mouse Detected" if self.frame.battery == "-" else MODEL)


class MyFrame(wx.Frame):

    def __init__(self, parent, title):
        super().__init__(parent, title=title, pos=(-1, -1), size=(290, 280))
        self.SetSize((350, 250))
        self.tray_icon = MyTaskBarIcon(self)
        self.battery = get_battery()
        logging.info(f"Battery level obtained: {self.battery}")
        self.tray_icon.SetIcon(create_icon(self.battery, foreground_color), "No Mouse Detected" if self.battery == "-" else MODEL)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Centre()

        self.thread = threading.Thread(target=self.Polling, daemon=True)
        self.thread.start()

    def OnClose(self, event):
        if self.IsShown():
            self.Hide()

    def Polling(self):
        while True:
            time.sleep(poll_rate)
            self.battery = get_battery()
            logging.info(f"Battery level obtained: {self.battery}")
            self.tray_icon.SetIcon(create_icon(self.battery, foreground_color), "No Mouse Detected" if self.battery == "-" else MODEL)


class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, title='Razer Tray settings')
        frame.Show(False)
        self.SetTopWindow(frame)
        return True


def main():
    app = MyApp()
    app.MainLoop()


if __name__ == "__main__":
    main()
