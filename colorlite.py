#!/usr/bin/env python3

#
# This file is part of Colorlite.
#
# Copyright (c) 2020-2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import os
import argparse
import sys

from migen import *
from migen.genlib.misc import WaitTimer
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms import colorlight_5a_75b

from litex.soc.cores.clock import *
from litex.soc.cores.spi_flash import ECP5SPIFlash
from litex.soc.cores.gpio import GPIOOut
from litex.soc.cores.led import LedChaser
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII
from litex.build.generic_platform import *

# IOs ----------------------------------------------------------------------------------------------

_gpios = [
    # GPIOs.
    ("gpio", 0, Pins("j4:0"), IOStandard("LVCMOS33")),
    ("gpio", 1, Pins("j4:1"), IOStandard("LVCMOS33")),

    # Servos.
    ("servo", 0, Pins("j3:0"), IOStandard("LVCMOS33")),
    ("servo", 1, Pins("j3:1"), IOStandard("LVCMOS33")),
    ("servo", 2, Pins("j3:2"), IOStandard("LVCMOS33")),
    ("servo", 3, Pins("j3:4"), IOStandard("LVCMOS33")),
]

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys    = ClockDomain()
        # # #

        # Clk / Rst.
        clk25 = platform.request("clk25")
        rst_n = platform.request("user_btn_n", 0)

        # PLL.
        self.submodules.pll = pll = ECP5PLL()
        self.comb += pll.reset.eq(~rst_n)
        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

# ColorLite ----------------------------------------------------------------------------------------

class ColorLite(SoCMini):
    def __init__(self, sys_clk_freq=int(50e6), with_etherbone=True, ip_address=None, mac_address=None):
        platform     = colorlight_5a_75b.Platform(revision="7.0")

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, clk_freq=sys_clk_freq)

        # Etherbone --------------------------------------------------------------------------------
        if with_etherbone:
            self.submodules.ethphy = LiteEthPHYRGMII(
                clock_pads = self.platform.request("eth_clocks"),
                pads       = self.platform.request("eth"),
                tx_delay   = 0e-9)
            self.add_etherbone(
                phy         = self.ethphy,
                ip_address  = ip_address,
                mac_address = mac_address,
                data_width  = 32,
            )

        # SPIFlash ---------------------------------------------------------------------------------
        self.submodules.spiflash = ECP5SPIFlash(
            pads         = platform.request("spiflash"),
            sys_clk_freq = sys_clk_freq,
            spi_clk_freq = 5e6,
        )

        # Led --------------------------------------------------------------------------------------
        self.submodules.leds = LedChaser(
            pads         = platform.request_all("user_led_n"),
            sys_clk_freq = sys_clk_freq)

        # GPIOs ------------------------------------------------------------------------------------
        platform.add_extension(_gpios)

        # Power switch
        power_sw_pads  = platform.request("gpio", 0)
        power_sw_gpio  = Signal()
        power_sw_timer = WaitTimer(2*sys_clk_freq) # Set Power switch high after power up for 2s.
        self.comb += power_sw_timer.wait.eq(1)
        self.submodules += power_sw_timer
        self.submodules.gpio0 = GPIOOut(power_sw_gpio)
        self.comb += power_sw_pads.eq(power_sw_gpio | ~power_sw_timer.done)

        # Reset Switch
        reset_sw_pads  = platform.request("gpio", 1)
        self.submodules.gpio1 = GPIOOut(reset_sw_pads)

        # Servos -----------------------------------------------------------------------------------
        from litex.soc.cores.pwm import PWM
        for n in range(4):
            servo_pad = platform.request("servo", n)
            servo     = PWM(servo_pad)
            setattr(self.submodules, f"servo{n}", servo)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Take control of your ColorLight FPGA board with LiteX/LiteEth :)")
    parser.add_argument("--build",       action="store_true",      help="Build bitstream")
    parser.add_argument("--load",        action="store_true",      help="Load bitstream")
    parser.add_argument("--flash",       action="store_true",      help="Flash bitstream")
    parser.add_argument("--ip-address",  default="192.168.1.20",   help="Ethernet IP address of the board (default: 192.168.1.20).")
    parser.add_argument("--mac-address", default="0x726b895bc2e2", help="Ethernet MAC address of the board (defaullt: 0x726b895bc2e2).")
    args = parser.parse_args()

    soc     = ColorLite(ip_address=args.ip_address, mac_address=int(args.mac_address, 0))
    builder = Builder(soc, output_dir="build", csr_csv="scripts/csr.csv")
    builder.build(build_name="colorlite", run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".svf"))

    if args.flash:
        prog = soc.platform.create_programmer()
        os.system("cp bit_to_flash.py build/gateware/")
        os.system("cd build/gateware && ./bit_to_flash.py colorlite.bit colorlite.svf.flash")
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".svf.flash"))

if __name__ == "__main__":
    main()
