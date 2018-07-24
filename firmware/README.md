# Platform
The following is for the [RBL Nano v2](https://redbear.cc/product/ble-nano-kit-2.html),
a board carrying the nRF52832 BLE chip, which is programmed with DAPLINK with
an MK20 USB board. The MK20 can also open a serial
interface to the BLE chip.
These instructions assume development on a linux-based OS with the GNU ARM
toolchain installed.

# Setting up SDK:
```
cd screaming-channel/nRF52832/
wget https://www.nordicsemi.com/eng/nordic/download_resource/59011/68/92912988/116085
unzip 116085
rm 116085
cp boards.h nRF5_SDK_14.2.0_17b948a/components/boards/
cp Makefile.posix nRF5_SDK_14.2.0_17b948a/components/toolchain/gcc
cp rblnano2.h  nRF5_SDK_14.2.0_17b948a/components/boards/
```

# Building

```bash
export NORDIC_SEMI_SDK="/path/to/sdk"
make -C blenano2/blank/armgcc
```

# Flashing
When the MK20 is plugged in it should mount a new directory in which you can
drop .hex files to be flashed onto the board:
```
cp blenano2/blank/armgcc/_build/nrf52832_xxaa.hex /media/$USER/DAPLINK/
```

# Radio Test
The radio_test example in the nRF5 SDK was chosen because it gives an
interactive way to configure and transmit RF. It can extended to add options
for register ops/crypto. Connect to it with minicom (115200 baud), on whatever
device is created by the MK20. For the radio_test example, press 'h' for the
list of options:

```
sudo minicom -D /dev/ttyACM0
Welcome to minicom 2.7

OPTIONS: I18n
Compiled on Feb  7 2016, 13:37:27.
Port /dev/ttyACM0, 02:20:33

Press CTRL-A Z for help on special keys

h

Usage:
a: Enter start channel for sweep/channel for constant carrier
b: Enter end channel for sweep
c: Start TX carrier
d: Enter time on each channel (1ms-99ms)
e: Cancel sweep/carrier
m: Enter data rate
o: Start modulated TX carrier
p: Enter output power
s: Print current delay, channels and so on
r: Start RX sweep
t: Start TX sweep
x: Start RX carrier

```

# Noisy Ops
Two new options were added to exercise the processor while a TX carrier is
transmitted:
```
y: Start noisy operation
z: End noisy operation
```
Right now the noisy operation is just flipping bits in a register
(NRF_POWER->GPREGRET) according to a timer. The LED on the board blinks
each time the op is performed.
