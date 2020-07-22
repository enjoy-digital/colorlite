#!/usr/bin/env python3

import time

from litex import RemoteClient

wb = RemoteClient()
wb.open()

# # #

CTRL_START     = (1 << 0)
CTRL_LENGTH    = (1 << 8)
STATUS_DONE    = (1 << 0)
STATUS_ONGOING = (1 << 0)

# Registers
READ_ID = 0x9F
READ    = 0x03
WREN    = 0x06
WRDI    = 0x04
PP      = 0x02
SE      = 0xD8
BE      = 0xC7
RDSR    = 0x05
WRSR    = 0x01
RDNVCR  = 0xB5
WRNVCR  = 0xB1

# Flags

WIP = 0x01

def format_mosi(cmd, addr=None, data=0):
    if addr is None:
        return (cmd<<32) | (data<<24)
    else:
        return (cmd <<32) | (addr<<8) | data

class SPIFlash:
    def __init__(self, regs):
        self.regs = regs

    def spi_xfer(self, length, mosi):
        self.regs.spiflash_spi_mosi.write(mosi)
        self.regs.spiflash_spi_control.write((length*CTRL_LENGTH) | CTRL_START)
        while not (self.regs.spiflash_spi_status.read() & STATUS_DONE):
            pass
        return self.regs.spiflash_spi_miso.read()

    def read_id(self):
        return (self.spi_xfer(32, format_mosi(cmd=READ_ID))) & 0xffffff

    def write_enable(self):
        self.spi_xfer(8, format_mosi(cmd=WREN))

    def write_disable(self):
        self.spi_xfer(8, format_mosi(cmd=WRDI))

    def read_status(self):
        return (self.spi_xfer(16, format_mosi(cmd=RDSR))) & 0xff

    def write_status(self, value):
        self.spi_xfer(16, format_mosi(cmd=WRSR, data=value))

    def erase_sector(self, addr):
        self.spi_xfer(32, format_mosi(cmd=SE, addr=addr))

    def read_sector_lock(self, addr):
        return (self.spi_xfer(40, format_mosi(cmd=RDSR, addr=addr))) & 0xff

    def write_sector_lock(self, addr, byte):
        self.spi_xfer(40, format_mosi(cmd=WRSR, addr=addr, data=byte))

    def read(self, addr):
        return (self.spi_xfer(40, format_mosi(cmd=READ, addr=addr))) & 0xff

    def write(self, addr, byte):
        self.spi_xfer(40, format_mosi(cmd=PP, addr=addr, data=byte))

    def read_nvcr(self):
        return (self.spi_xfer(24, format_mosi(cmd=RDNVCR))) & 0xffff

    def write_nvcr(self, data):
        self.spi_xfer(24, format_mosi(cmd=WRNVCR, data=data))

spiflash = SPIFlash(wb.regs)
print("{:08x}".format(spiflash.read_id()))

for i in range(16):
    print("{:02x}".format(spiflash.read(i)))

# # #

wb.close()
