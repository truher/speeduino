#!/bin/sh

platformio run -e megaatmega2560 -v

cp .pio/build/megaatmega2560/firmware.elf pins.elf
