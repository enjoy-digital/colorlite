#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

print("Toggling GPIO0...")
for i in range(2):
    wb.regs.gpio0_out.write(1)
    time.sleep(0.5)
    wb.regs.gpio0_out.write(0)
    time.sleep(0.5)

print("Toggling GPIO1...")
for i in range(2):
    wb.regs.gpio1_out.write(1)
    time.sleep(0.5)
    wb.regs.gpio1_out.write(0)
    time.sleep(0.5)

# # #

wb.close()
