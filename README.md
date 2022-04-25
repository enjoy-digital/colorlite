```
                                     _____     __         __   _ __
                                    / ___/__  / /__  ____/ /  (_) /____
                                   / /__/ _ \/ / _ \/ __/ /__/ / __/ -_)
                                   \___/\___/_/\___/_/ /____/_/\__/\__/
                                     Copyright (c) 2020-2022, EnjoyDigital
                                             Powered by LiteX
```
![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)

<p align="center"><img src="https://raw.githubusercontent.com/enjoy-digital/colorlite/master/doc/board.jpg"></p>

[> Intro
--------
This small project is an attempt to use a $15 FPGA board to do some remote control/monitoring over an Ethernet network. It can be convenient to power on/power off systems remotely and/or do some monitoring. This has been created in this strange COVID-19 period to avoid moving all the lab equipment to home and ease remote work, but this is also a practical example of a very simple LiteX SoC built with full open-source tools. Similar things can be easily done with Arduino, Rapsberry Pi, ESP32 for almost the same price or even cheaper but here the fun is to use our tools for that... and maybe extend this project to something more powerful in the future (Remote logic analyzer with 1Gbps link? :)).

<p align="center"><img src="https://raw.githubusercontent.com/enjoy-digital/colorlite/master/doc/architecture.png"></p>

[> Prerequisites
----------------
- Yosys/Nextpnr ECP5 toolchain installed.
- An OpenOCD compatible JTAG cable.
- A ColorLight 5A-75B board (can be found on Amazon/eBay/AliExpress/...).
- A USB charger and USB cable that can be cut to power the board on the 5V/GND connector.

[> Installing LiteX
-------------------
```sh
$ wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
$ chmod +x litex_setup.py
$ sudo ./litex_setup.py init install
```

[> Build and Flash the bitstream
--------------------------------
```sh
$ ./colorlite.py --ip-address=192.168.1.20 --flash
```

[> Open LiteX server
--------------------
```sh
$ litex_server --udp --udp-ip=192.168.1.20
```

[> Enjoy :)
-----------
```sh
$ cd scripts
$ ./test_blink.py (will blink the Led)
$ ./test_gpios.py (will toggle the 2 GPIOs)
$ ./test_flash.py (will read the first bytes of the SPI Flash)
```

In our usecase, we use a two channel relay module that can be easily found on Amazon/eBay/AliExpress to emulate the power and reboot switch of a computer:

<p align="center"><img src="https://lastminuteengineers.com/wp-content/uploads/arduino/relay-module-pinout.png"></p>

- *In1* is connected to *J4/R0* HUB75 connector of the FPGA board and *Relay1* is emulating the power switch.
- *In2* is connected to *J4/G0* HUB75 connector of the FPGA board and *Relay2* is emulating the reboot switch.

We then easily control the power off/on, reboot of a computer with:
```sh
$ ./test_power_on.py (will do a short pulse on power switch)
$ ./test_gpios.py (will do a short long pulse on power switch)
$ ./test_flash.py (will do a short pulse on reboot switch)
```

> **Note**: It is recommended to operate this on a local network. It's possible to expose/use it over Internet through a Router but the protocol is not secured at all, so don't use it to control sensitive equipments or at your own risk!

End of the tutorial, time to power off! :)

<p align="center"><img src="https://raw.githubusercontent.com/enjoy-digital/colorlite/master/doc/power_off.jpg"></p>