#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

for i in range(16):
    wb.regs.led_out.write(~wb.regs.led_out.read())
    time.sleep(0.2)

# # #

wb.close()
