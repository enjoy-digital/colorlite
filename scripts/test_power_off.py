#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

print("Power Off...")
wb.regs.gpio0_out.write(1)
time.sleep(6)
wb.regs.gpio0_out.write(0)

# # #

wb.close()
