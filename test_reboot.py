#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

print("Reboot...")
wb.regs.gpio1_out.write(1)
time.sleep(0.5)
wb.regs.gpio1_out.write(0)

# # #

wb.close()
