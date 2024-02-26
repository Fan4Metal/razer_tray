# Razer Tray Charge Notification

## Introduction
![Screenshot](images/screenshot.png)<br>

This is a script for **Windows** written in Python 3.10+ with `wxPython` and `pyusb` that gets the battery level of a Razer Wireless mouse (Razer Viper V2 Pro by default) and shows it in system tray.<br>

## Instruction

1. Clone this repository.
2. Go to the [website](https://libusb.info/) of `libusb` to download the Latest Windows Binaries.
3. Extract `\VS2019\MS64\dll\libusb-1.0.dll` and place it next to script file.
4. Install dependencies: `pip install -r requirements.txt`
5. By default script is set up to work with **Razer Viper V2 Pro**. If you want to use it with different Razer mouse, see next chapter.   

## How to adapt the script for different Razer mouse

**Warning: TRY AT YOUR OWN RISK!**<br>
To adapt the script for your Razer mouse, follow the steps below: 
1. Get the `PIDs` of your mouse in both the wireless and wired mode:<br>
You can find VID:PID pairs [here](https://github.com/openrazer/openrazer?tab=readme-ov-file#mice), or you can find it by yourself: 


> Go to Device Manager -> Find your mouse -> Right click -> Properties -> Details -> Hardware Ids -> Repeat in the other state
  * e.g. for **Razer Viper V2 Pro**, in wireless state, the entries of Hardware Ids contain `VID_1532&PID_00A6`, then 0x00A6 is the PID in the wireless state
  * In wired state, the entries contain `VID_1532&PID_00A5`, then 0x00A6 is the PID in the wired state
2. Get `transaction_id.id` for your mouse from [here](https://github.com/openrazer/openrazer/blob/85e81ae3ba08f2af33031e8a08a4f0ecc6adee91/driver/razermouse_driver.c#L1132)
3. If the name of your mouse appears inside the switch statement, write down the `transaction_id.id`
  * e.g., I see `USB_DEVICE_ID_RAZER_VIPER_V2_PRO_WIRELESS` inside the switch statement, so the `transaction_id.id` for my mouse is `0x1f`
  * If you do not see your mouse name inside, then the `transaction_id.id` is `0xff`
4. Modify these lines of the script:
```python
MODEL = "Razer Viper V2 Pro" # your mouse name
WIRELESS_RECEIVER = 0x00A6   # PID in wireless mode
WIRELESS_WIRED = 0x00A5      # PID in wired mode
TRAN_ID = b"\x1f"            # transaction_id.id for your mouse
```
5. Done!

## Settings
You can modify these settings variables:
1. `poll_rate` in seconds - how often battery charge is read. 30 sec by default.
2. `foreground_color` - color of indicator text. Tuple with RGB data.
3. `backgroung_color` - color of indicator background. Transparent by default (0, 0, 0, 0).
4. `font` - indicator font.

## Credit

Based on this work: https://github.com/hsutungyu/razer-mouse-battery-windows<br>
Quote from [hsutungyu](https://github.com/hsutungyu):
> This script is written by looking into [OpenRazer](https://github.com/openrazer/openrazer), a GNU/Linux driver for controlling razer devices.<br>
Also, I have referenced the [blog post](https://rsmith.home.xs4all.nl/hardware/setting-the-razer-ornata-chroma-color-from-userspace.html) and the [script](https://github.com/rsmith-nl/scripts/blob/main/set-ornata-chroma-rgb.py) by Roland Smith in the process of writing this script.

