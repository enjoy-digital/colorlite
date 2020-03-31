#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

print("Power On...")
wb.regs.gpio0_out.write(1)
time.sleep(0.5)
wb.regs.gpio0_out.write(0)

# # #

wb.close()
