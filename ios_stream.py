#!/usr/bin/env python3

#
# This file is part of Colorlite.
#
# Copyright (c) 2020-2022 Florent Kermarrec <florent@enjoy-digital.fr>
# SPDX-License-Identifier: BSD-2-Clause

import sys
import argparse

from migen import *
from migen.genlib.resetsync import AsyncResetSynchronizer

from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import OpenOCDJTAGProgrammer

from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *

# IOs ----------------------------------------------------------------------------------------------

_io = [("clk25", 0, Pins("P6"), IOStandard("LVCMOS33"))]

# Platform -----------------------------------------------------------------------------------------

class Platform(LatticePlatform):
    default_clk_name   = "clk25"
    default_clk_period = 1e9/25e6

    def __init__(self, **kwargs):
        LatticePlatform.__init__(self, "LFE5U-25F-6BG256C", _io, **kwargs)

    def create_programmer(self):
        return OpenOCDJTAGProgrammer("openocd_colorlight_5a_75b.cfg")

# CRG ----------------------------------------------------------------------------------------------

class _CRG(Module):
    def __init__(self, platform, sys_clk_freq):
        self.clock_domains.cd_sys = ClockDomain()
        self.clock_domains.cd_por = ClockDomain(reset_less=True)

        # # #

        # Clk / Rst
        clk25 = platform.request("clk25")
        platform.add_period_constraint(clk25, 1e9/25e6)

        # PLL
        self.submodules.pll = pll = ECP5PLL()
        pll.register_clkin(clk25, 25e6)
        pll.create_clkout(self.cd_sys, sys_clk_freq)

# IOStreamer ---------------------------------------------------------------------------------------

class IOStreamer(Module):
    """Stream an identifier string over UART"""
    def __init__(self, identifier, pad, sys_clk_freq, baudrate):
        from litex.soc.cores.uart import RS232PHYTX
        assert len(identifier) <= 4
        for i in range(4-len(identifier)):
            identifier += " "

        # UART
        pads = Record([("tx", 1)])
        self.comb += pad.eq(pads.tx)
        phy = RS232PHYTX(pads, int((baudrate/sys_clk_freq)*2**32))
        self.submodules += phy

        # Memory
        mem  = Memory(8, 4, init=[ord(identifier[i]) for i in range(4)])
        port = mem.get_port()
        self.specials += mem, port
        self.comb += phy.sink.valid.eq(1)
        self.comb += phy.sink.data.eq(port.dat_r)
        self.sync += If(phy.sink.ready, port.adr.eq(port.adr + 1))

# IOsStreamSoC -------------------------------------------------------------------------------------

class IOsStreamSoC(SoCMini):
    def __init__(self, sys_clk_freq=int(25e6)):
        platform = Platform(toolchain="trellis")

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = _CRG(platform, sys_clk_freq)

        # SoC Mini ---------------------------------------------------------------------------------
        SoCMini.__init__(self, platform, sys_clk_freq)

        # Get IOs from JSON database ---------------------------------------------------------------
        import json
        json_file = open("iodb.json")
        json_data = json.load(json_file)
        json_file.close()
        ios = list(json_data["packages"]["CABGA256"].keys())

        # Exclude some IOs -------------------------------------------------------------------------
        excludes = []
        excludes += ["P6"]
        for exclude in excludes:
            ios.remove(exclude)

        # Reduce number of IOs ---------------------------------------------------------------------
        ios = ios[0*len(ios)//4:1*len(ios)//4]
        #ios = ios[1*len(ios)//4:2*len(ios)//4]
        #ios = ios[2*len(ios)//4:3*len(ios)//4]
        #ios = ios[3*len(ios)//4:4*len(ios)//4]

        # Create platform IOs ----------------------------------------------------------------------
        for io in ios:
            platform.add_extension([(io, 0, Pins(io), IOStandard("LVCMOS33"), Misc("DRIVE=4"))])

        # Stream IOs' identifiers to IOs -----------------------------------------------------------
        for io in ios:
            io_streamer = IOStreamer(io, platform.request(io), sys_clk_freq, baudrate=9600)
            self.submodules += io_streamer

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build bitstream")
    parser.add_argument("--load", action="store_true", help="load bitstream")
    args = parser.parse_args()

    soc     = IOsStreamSoC()
    builder = Builder(soc, output_dir="build")
    builder.build(build_name="ios_stream", run=args.build)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(os.path.join(builder.gateware_dir, soc.build_name + ".svf"))

if __name__ == "__main__":
    main()
