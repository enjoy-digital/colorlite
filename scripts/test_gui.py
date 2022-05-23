#!/usr/bin/env python3

import time
import dearpygui.dearpygui as dpg


# Servo --------------------------------------------------------------------------------------------

class Servo:
    def __init__(self, bus, n, sys_clk_freq):
        self.enable = getattr(bus.regs, f"servo{n}_enable")
        self.width  = getattr(bus.regs, f"servo{n}_width")
        self.period = getattr(bus.regs, f"servo{n}_period")

        self.period_ticks = int(sys_clk_freq*20.0e-3)
        self.period.write(self.period_ticks)
        self.set(50)
        self.on()

    def set(self, value):
        self.width.write(int(self.period_ticks/20*(1 + value/100)))

    def on(self):
        self.enable.write(1)

    def off(self):
        self.enable.write(0)

    def callback(self, source, value):
        self.set(value)

# GUI ----------------------------------------------------------------------------------------------

from litex import RemoteClient

bus = RemoteClient()
bus.open()

dpg.create_context()
dpg.create_viewport(title="Colorlite Gui Test", max_width=800, always_on_top=True)
dpg.setup_dearpygui()

with dpg.window(autosize=True):
    dpg.add_text("Servos Control")
    for n in range(4):
        servo = Servo(bus=bus, n=n, sys_clk_freq=int(50e6))
        dpg.add_slider_int(label=f"Servo {n}", max_value=100, callback=servo.callback)

    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

bus.close()
