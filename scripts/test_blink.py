#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

print("Toggling Led...")
for i in range(2):
    wb.regs.led_out.write(1)
    time.sleep(0.5)
    wb.regs.led_out.write(0)
    time.sleep(0.5)

# # #

wb.close()
