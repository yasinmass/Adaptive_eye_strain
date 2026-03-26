import screen_brightness_control as sbc

def adjust_brightness(strain_level):
    if strain_level == "High":
        sbc.set_brightness(40)
    elif strain_level == "Medium":
        sbc.set_brightness(60)
    else:
        sbc.set_brightness(80)