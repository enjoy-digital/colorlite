#!/usr/bin/env python3

# This file is Copyright (c) 2020 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import argparse
import sys

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex_boards.platforms import colorlight_5a_75b

from litex.soc.cores.clock import *
from litex.soc.cores.spi_flash import ECP5SPIFlash
from litex.soc.cores.gpio import GPIOOut
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

from liteeth.phy.ecp5rgmii import LiteEthPHYRGMII
from litex.build.generic_platform import *
from litex.boards.platforms import genesys2

# IOs ----------------------------------------------------------------------------------------------

_gpios = [
    ("gpio", 0, Pins("j4:0"), IOStandard("LVCMOS33")),
    ("gpio", 1, Pins("j4:1"), IOStandard("LVCMOS33")),
]

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys    = ClockDomain()
        # # #

        # Clk / Rst
        clk25 = platform.request("clk25")
        rst_n = platform.request("user_btn_n", 0)
        platform.add_period_constraint(clk25, 1e9/25e6)

        # PLL
        self.submodules.pll = pll = ECP5PLL()

        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        self.specials += AsyncResetSynchronizer(self.cd_sys, ~pll.locked | ~rst_n)

# ColorLite ----------------------------------------------------------------------------------------

class ColorLite(SoCMini):
    def __init__(self, revision, with_etherbone=True, **kwargs):
        platform     = colorlight_5a_75b.Platform(revision=revision)
        sys_clk_freq = int(125e6)

        # SoCMini ----------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, clk_freq=sys_clk_freq, **kwargs)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # Etherbone --------------------------------------------------------------------------------
        if with_etherbone:
            self.submodules.ethphy = LiteEthPHYRGMII(
                clock_pads = self.platform.request("eth_clocks"),
                pads       = self.platform.request("eth"))
            self.add_csr("ethphy")
            self.add_etherbone(phy=self.ethphy)

        # SPIFlash ---------------------------------------------------------------------------------
        self.submodules.spiflash = ECP5SPIFlash(
            pads         = platform.request("spiflash"),
            sys_clk_freq = sys_clk_freq,
            spi_clk_freq = 5e6,
        )
        self.add_csr("spiflash")

        # Led --------------------------------------------------------------------------------------
        self.submodules.led = GPIOOut(platform.request("user_led_n"))
        self.add_csr("led")

        # GPIOs ------------------------------------------------------------------------------------
        platform.add_extension(_gpios)
        self.submodules.gpio0 = GPIOOut(platform.request("gpio", 0))
        self.submodules.gpio1 = GPIOOut(platform.request("gpio", 1))
        self.add_csr("gpio0")
        self.add_csr("gpio1")

# Load ---------------------------------------------------------------------------------------------

def load():
    import os
    f = open("openocd.cfg", "w")
    f.write(
"""
interface ftdi
ftdi_vid_pid 0x0403 0x6011
ftdi_channel 0
ftdi_layout_init 0x0098 0x008b
reset_config none
adapter_khz 25000
jtag newtap ecp5 tap -irlen 8 -expected-id 0x41111043
""")
    f.close()
    os.system("openocd -f openocd.cfg -c \"transport select jtag; init; svf build/gateware/colorlite.svf; exit\"")
    exit()

# Flash --------------------------------------------------------------------------------------------

def flash():
    import os
    os.system("cp bit_to_flash.py build/gateware/")
    os.system("cd build/gateware && ./bit_to_flash.py colorlite.bit colorlite.svf.flash")
    f = open("openocd.cfg", "w")
    f.write(
"""
interface ftdi
ftdi_vid_pid 0x0403 0x6011
ftdi_channel 0
ftdi_layout_init 0x0098 0x008b
reset_config none
adapter_khz 25000
jtag newtap ecp5 tap -irlen 8 -expected-id 0x41111043
""")
    f.close()
    os.system("openocd -f openocd.cfg -c \"transport select jtag; init; svf build/gateware/colorlite.svf.flash; exit\"")
    exit()

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Take control of your ColorLight FPGA board with LiteX")
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--revision", default="7.0", type=str, help="Board revision 7.0 (default) or 6.1")
    parser.add_argument("--eth-phy", default=0, type=int, help="Ethernet PHY 0 or 1 (default=0)")
    parser.add_argument("--load",  action="store_true", help="load bitstream")
    parser.add_argument("--flash", action="store_true", help="flash bitstream")
    args = parser.parse_args()

    if args.load:
        load()

    if args.flash:
        flash()

    soc     = ColorLite(args.revision)
    builder = Builder(soc, output_dir="build", csr_csv="csr.csv")
    builder.build(build_name="colorlite", run=args.build)

if __name__ == "__main__":
    main()
