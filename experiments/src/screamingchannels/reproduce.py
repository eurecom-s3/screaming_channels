#!/usr/bin/python2

# We need to use Python 2 for GNUradio.

import click
import collections
import enum
import json
import os
from os import path, system
import serial
import sys
import time
import logging

from gnuradio import blocks, gr, uhd
import osmosdr

import numpy as np

import analyze

logging.basicConfig()
l = logging.getLogger('reproduce')

Radio = enum.Enum("Radio", "USRP USRP_mini HackRF bladeRF")
FirmwareMode = collections.namedtuple(
    "FirmwareMode",
    [
        "mode_command",         # command for entering the test mode
        "repetition_command",   # command for triggering repeated execution (or None)
        "action_command",       # command for starting (single or repeated) action
        "have_keys",            # whether the test mode works with keys
    ])


# These are the firmware modes we support; they can be selected with the "mode"
# key in the "firmware" section of the config file.
TINY_AES_MODE = FirmwareMode(
    have_keys=True, mode_command='n', repetition_command='n', action_command='r')
HW_CRYPTO_MODE = FirmwareMode(
    have_keys=True, mode_command='u', repetition_command='n', action_command='r')
MASK_AES_MODE = FirmwareMode(
    have_keys=True, mode_command='w', repetition_command='n', action_command='r')
MASK_AES_MODE_SLOW = FirmwareMode(
    have_keys=True, mode_command='w', repetition_command=None, action_command='e')
TINY_AES_MODE_SLOW = FirmwareMode(
    have_keys=True, mode_command='n', repetition_command=None, action_command='e')
HW_CRYPTO_MODE_SLOW = FirmwareMode(
    have_keys=True, mode_command='u', repetition_command=None, action_command='e')
POWER_ANALYSIS_MODE = FirmwareMode(
    have_keys=False, mode_command='v', repetition_command=None, action_command='s')


# The config file's "firmware" section.
FirmwareConfig = collections.namedtuple(
    "FirmwareConfig",
    [
        # Algorithm to attack: tinyaes[_slow], hwcrypto[_slow], power; slow
        # modes use individual serial commands to trigger.
        "mode",
        # True to use a fixed key or False to vary it for each point.
        "fixed_key",
        # True to modulate data or False to use just the carrier.
        "modulate",

        # Mode-specific options

        # If a masked version of AES is used, this decides which mode
        "mask_mode",
        # The sleep time between individual encryptions in slow mode collections
        "slow_mode_sleep_time",
    ])


# The config file's "collection" section.
CollectionConfig = collections.namedtuple(
    "CollectionConfig",
    [
        # Frequency to tune to, in Hz.
        "target_freq",
        # Sampling rate, in Hz.
        "sampling_rate",
        # How many different plaintext/key combinations to record.
        "num_points",
        # How many traces to use.
        "num_traces_per_point",
        # Multiplier to account for traces dropped due to signal processing
        "traces_per_point_multiplier",
        # Lower cut-off frequency of the band-pass filter.
        "bandpass_lower",
        # Upper cut-off frequency of the band-pass filter.
        "bandpass_upper",
        # Cut-off frequency of the low-pass filter.
        "lowpass_freq",
        # How much to drop at the start of the trace, in seconds.
        "drop_start",
        # How much to include before the trigger, in seconds.
        "trigger_offset",
        # True for triggering on a rising edge, False otherwise.
        "trigger_rising",
        # Length of the signal portion to keep, in seconds, starting at
        # trigger - trigger_offset.
        "signal_length",
        # Name of the template to load, or None.
        "template_name",
        # Traces with a lower correlation will be discarded.
        "min_correlation",
    ])


# Global settings, for simplicity
DEVICE = None
BAUD = None
OUTFILE = None
RADIO = None
RADIO_ADDRESS = None
COMMUNICATE_SLOW = None
YKUSH_PORT = None


class EnumType(click.Choice):
    """Teach click how to handle enums."""
    def __init__(self, enumcls):
        self._enumcls = enumcls
        click.Choice.__init__(self, enumcls.__members__)

    def convert(self, value, param, ctx):
        value = click.Choice.convert(self, value, param, ctx)
        return self._enumcls[value]


@click.group()
@click.option("-d", "--device", default="/dev/ttyACM0", show_default=True,
              help="The serial dev path of device tested for screaming channels")
@click.option("-b", "--baudrate", default=115200, show_default=True,
              help="The baudrate of the serial device")
@click.option("-y", "--ykush-port", default=0, show_default=True,
              help="If set, use given ykush-port to power-cycle the device")
@click.option("-s", "--slowmode", is_flag=True, show_default=True,
              help=("Enables slow communication mode for targets with a small"
                    "serial rx-buffer"))
@click.option("-r", "--radio", default="USRP", type=EnumType(Radio), show_default=True,
              help="The type of SDR to use.")
@click.option("--radio-address", default="10.0.3.40",
              help="Address of the radio (USRP only).")
@click.option("-l", "--loglevel", default="INFO", show_default=True,
              help="The loglevel to be used ([DEBUG|INFO|WARNING|ERROR|CRITICAL])")
@click.option("-o", "--outfile", default="/tmp/time", type=click.Path(), show_default=True,
              help="The file to write the GNUradio trace to.")
def cli(device, baudrate, ykush_port, slowmode, radio, radio_address,
        outfile, loglevel, **kwargs):
    """
    Reproduce screaming channel experiments with vulnerable devices.

    This script assumes that the device has just been plugged in (or is in an
    equivalent state), that it is running our modified firmware, and that an SDR
    is available. It will carry out the chosen experiment, producing a trace and
    possibly other artifacts. Make sure that the "--outfile" option points to a
    file that doesn't exist or can be safely overwritten.

    Call any experiment with "--help" for details. You most likely want to use
    "collect".
    """
    global DEVICE, OUTFILE, RADIO, RADIO_ADDRESS, BAUD, COMMUNICATE_SLOW, YKUSH_PORT
    DEVICE = device
    BAUD = baudrate
    OUTFILE = outfile
    RADIO = radio
    RADIO_ADDRESS = radio_address
    COMMUNICATE_SLOW = slowmode
    YKUSH_PORT = ykush_port

    l.setLevel(loglevel)


def _plot_outfile():
    """
    Plot the recorded data.
    """
    from matplotlib import pyplot as plt
    import scipy

    with open(OUTFILE) as f:
        data = scipy.fromfile(f, dtype=scipy.complex64)

    plt.plot(np.absolute(data))
    plt.show()


def _encode_for_device(data):
    """
    Encode the given bytes in our special format.
    """
    return " ".join(str(ord(data_byte)) for data_byte in data)


def _send_parameter(ser, command, param):
    """
    Send a parameter (key or plaintext) to the target device.

    The function assumes that we've already entered tiny_aes mode.
    """
    command_line = '%s%s\r\n' % (command, _encode_for_device(param))
    l.debug('Sending command:  %s\n' % command_line)
    if not COMMUNICATE_SLOW:
        ser.write(command_line)
    else:
        for p in command_line.split(' '):
            ser.write(p+' ')
            time.sleep(.05)

    # check = ''.join(chr(int(word)) for word in ser.readline().split(' '))
    # Quick and dirty fix
    # Error: on the pca10040 the UART sometimes hangs for unknown reasons
    # Fix: wait for a timeout and then just skip to the next trace to collect
    l.debug('Waiting check\n')
    x = ser.readline()
    if len(x) == 0:
        l.debug("WARNING: nothing received on timeout, skipping this trace")
        return 
    check = ''.join(chr(int(word)) for word in x.split(' '))
    
    # -- create check like this instead for ESP32:
    #response = ser.readline()
    #response = [ a for a in response.split(' ') if a.isdigit() ]
    #check = ''.join(chr(int(word)) for word in response)
    if check != param:
        print "ERROR\n%s\n%s" % (_encode_for_device(param),
                                 _encode_for_device(check))
        ser.write(b'q')
        sys.exit(1)
    l.debug('Check done\n')

def _send_key(ser, key):
    _send_parameter(ser, 'k', key)


def _send_plaintext(ser, plaintext):
    _send_parameter(ser, 'p', plaintext)


@cli.command()
@click.argument("config", type=click.File())
@click.argument("target-path", type=click.Path(exists=True, file_okay=False))
@click.option("--name", default="",
              help="Identifier for the experiment (obsolete; only for compatibility).")
@click.option("--average-out", type=click.Path(dir_okay=False),
              help="File to write the average to (i.e. the template candidate).")
@click.option("--plot/--no-plot", default=False, show_default=True,
              help="Plot the results of trace collection.")
def collect(config, target_path, name, average_out, plot):
    """
    Collect traces for an attack.

    The config is a JSON file containing parameters for trace analysis; see the
    definitions of FirmwareConfig and CollectionConfig for descriptions of each
    parameter.
    """
    # NO-OP defaults for mode dependent config options for backwards compatibility
    cfg_dict = json.load(config)
    cfg_dict["firmware"].setdefault(u'mask_mode', 0)
    cfg_dict["firmware"].setdefault(u'slow_mode_sleep_time', 0.001)
    cfg_dict["collection"].setdefault(u'traces_per_point_multiplier', 1.2)

    collection_config = CollectionConfig(**cfg_dict["collection"])
    firmware_config = FirmwareConfig(**cfg_dict["firmware"])

    if firmware_config.mode == "tinyaes":
        firmware_mode = TINY_AES_MODE
    elif firmware_config.mode == "tinyaes_slow":
        firmware_mode = TINY_AES_MODE_SLOW
    elif firmware_config.mode == "maskaes":
        firmware_mode = MASK_AES_MODE
    elif firmware_config.mode == "maskaes_slow":
        firmware_mode = MASK_AES_MODE_SLOW
    elif firmware_config.mode == "hwcrypto":
        firmware_mode = HW_CRYPTO_MODE
    elif firmware_config.mode == "hwcrypto_slow":
        firmware_mode = HW_CRYPTO_MODE_SLOW
    elif firmware_config.mode == "power":
        firmware_mode = POWER_ANALYSIS_MODE
    else:
        raise Exception("Unsupported mode %s; this is a bug!" % firmware_config.mode)

    assert (not plot) or (collection_config.num_traces_per_point <= 200), \
        "Plotting a lot of data might lock up the computer! Consider reducing " \
        "num_traces_per_point in the configuration file or enforce limits on resource consumption..."

    # Signal post-processing will drop some traces when their quality is
    # insufficient, so let's collect more traces than requested to make sure
    # that we have enough in the end.
    num_traces_per_point = int(collection_config.num_traces_per_point * collection_config.traces_per_point_multiplier)

    # number of points
    num_points = int(collection_config.num_points)

    # Generate the plaintexts
    plaintexts = [os.urandom(16) for _trace in range(num_points)]
    with open(path.join(target_path, 'pt_%s.txt' % name), 'w') as f:
        f.write('\n'.join(p.encode('hex') for p in plaintexts))

    # Generate the key(s)
    if firmware_mode.have_keys:
        keys = [os.urandom(16)
                for _key in range(1 if firmware_config.fixed_key else num_points)]
        with open(path.join(target_path, 'key_%s.txt' % name), 'w') as f:
            f.write('\n'.join(k.encode('hex') for k in keys))

    # If requested, reset target
    if YKUSH_PORT != 0:
        l.debug('Resetting device using ykush port %d' % YKUSH_PORT)
        system("ykushcmd -d %d" % YKUSH_PORT)
        system("ykushcmd -u %d" % YKUSH_PORT)
        time.sleep(3)



    with _open_serial_port() as ser:
        if YKUSH_PORT != 0:
            print ser.readline()

        # tmp increase power
        #l.debug('POWERPOWER')
        #ser.write(b'p')
        #print ser.readline()
        #ser.write(b'0')
        #print ser.readline()


        if firmware_config.modulate:
            l.debug('Starting modulated wave')
            ser.write(b'o')     # start modulated wave
            print ser.readline()
        else:
            l.debug('Starting continuous wave')
            ser.write(b'c')     # start continuous wave

        l.debug('Entering test mode')
        ser.write(firmware_mode.mode_command) # enter test mode
        print ser.readline()

        if firmware_mode.repetition_command:
            l.debug('Setting trace repitions')
            ser.write('n%d\r\n' % num_traces_per_point)
            print ser.readline()

        if firmware_mode.have_keys and firmware_config.fixed_key:
            # The key never changes, so we can just set it once and for all.
            _send_key(ser, keys[0])

        if firmware_config.mode == 'maskaes' or firmware_config.mode == 'maskaes_slow':
            l.debug('Setting masking mode to %d', firmware_config.mask_mode)
            ser.write('%d\r\n' % firmware_config.mask_mode)
            print ser.readline()


        l.debug('Starting GNUradio')
        gnuradio = GNUradio(collection_config.target_freq,
                            collection_config.sampling_rate)
        with click.progressbar(plaintexts) as bar:
            for index, plaintext in enumerate(bar):
                if firmware_mode.have_keys and not firmware_config.fixed_key:
                    _send_key(ser, keys[index])

                _send_plaintext(ser, plaintext)

                gnuradio.start()
                time.sleep(0.03)
                if RADIO == Radio.USRP_mini:
                    time.sleep(0.08)

                if firmware_mode.repetition_command:
                    # The test mode supports repeated actions.
                    l.debug('Start repetitions')
                    ser.write(firmware_mode.action_command)
                    ser.readline() # wait until done
                else:
                    for _iteration in range(num_traces_per_point):
                        time.sleep(firmware_config.slow_mode_sleep_time)
                        ser.write(firmware_mode.action_command) # single action
 
                time.sleep(0.09)

                gnuradio.stop()
                gnuradio.wait()

                trace = analyze.extract(OUTFILE, collection_config, average_out, plot)
                np.save(os.path.join(target_path,"avg_%s_%d.npy"%(name,index)),trace)
                gnuradio.reset_trace()

        ser.write(b'q')     # quit tiny_aes mode
        print ser.readline()
        ser.write(b'e')     # turn off continuous wave


@cli.command()
@click.option("--plot/--no-plot", default=False, show_default=True,
              help="Whether to plot the data after recording.")
def cw_with_regswitch(plot):
    """Continuous wave with register switching.

    While producing a continuous wave at baseband, enable a timer interrupt that
    repeatedly switches a register. Then disable the interrupt, and finally shut
    down the continuous wave.

    """
    with _open_serial_port() as ser:
        with GNUradio():
            time.sleep(1)
            ser.write(b'c')     # start continuous wave
            time.sleep(1)
            ser.write(b'y')     # enable timer
            time.sleep(1)
            ser.write(b'z')     # disable timer
            time.sleep(1)
            ser.write(b'e')     # disable continuous wave
            time.sleep(1)

    if plot:
        _plot_outfile()

@cli.command()
@click.option("--plot/--no-plot", default=False, show_default=True,
              help="Whether to plot the data after recording.")
def hwencryption(plot):
    """
    Hardware encryption with continuous wave.
    """
    with _open_serial_port() as ser:
        with GNUradio():
            time.sleep(0.05)
            ser.write(b'c')
            time.sleep(0.05)
            ser.write(b'l')     # start hwecryption+continuous wave
            time.sleep(0.05)
            ser.write(b'e')     # end
            time.sleep(0.05)

    if plot:
        _plot_outfile()


@cli.command()
@click.argument("output_file", click.File(mode='w'))
def create_waterfall(output_file):
    """
    Create the waterfall diagram of AES for the paper.

    The single argument is the output file; it will be overwritten.
    """
    sampling_rate = 5e6

    with _open_serial_port() as ser:
        time.sleep(0.15)
        with GNUradio(2.528e9, sampling_rate):
            ser.write(b'o')     # start modulated carrier
            time.sleep(0.011)
            ser.write(b'nn15\r\nr') # start AES
            time.sleep(0.008)

        ser.write(b'q')         # leave AES mode
        ser.write(b'e')         # stop carrier

    from matplotlib import pyplot as plt

    with open(OUTFILE) as f:
        data = np.fromfile(f, dtype=np.complex64)

    data = np.abs(data[22000:])
    plt.specgram(data, NFFT=512, Fs=sampling_rate/1000, noverlap=511, cmap='plasma')
    plt.xlabel('Time (ms)')
    plt.ylabel('Baseband frequency (kHz)')
    plt.savefig(output_file, bbox_inches='tight')
    plt.show()


def _open_serial_port():
    l.debug("Opening serial port")
    return serial.Serial(DEVICE, BAUD, timeout=5)


class GNUradio(gr.top_block):
    """GNUradio capture from SDR to file."""
    def __init__(self, frequency=2.464e9, sampling_rate=5e6):
        gr.top_block.__init__(self, "Top Block")

        if RADIO in (Radio.USRP, Radio.USRP_mini):
            radio_block = uhd.usrp_source(
                ("addr=" + RADIO_ADDRESS.encode("ascii"))
                if RADIO == Radio.USRP else "",
                uhd.stream_args(cpu_format="fc32", channels=[0]))
            radio_block.set_center_freq(frequency)
            radio_block.set_samp_rate(sampling_rate)
            radio_block.set_gain(40)
            radio_block.set_antenna("TX/RX")
        elif RADIO == Radio.HackRF or RADIO == Radio.bladeRF:
            mysdr = str(RADIO).split(".")[1].lower() #get "bladerf" or "hackrf"
            radio_block = osmosdr.source(args="numchan=1 "+mysdr+"=0")
            radio_block.set_center_freq(frequency, 0)
            radio_block.set_sample_rate(sampling_rate)
            # TODO tune parameters
            radio_block.set_freq_corr(0, 0)
            radio_block.set_dc_offset_mode(True, 0)
            radio_block.set_iq_balance_mode(True, 0)
            radio_block.set_gain_mode(True, 0)
            radio_block.set_gain(0, 0)
            radio_block.set_if_gain(44, 0)
            radio_block.set_bb_gain(40, 0)
            radio_block.set_antenna('', 0)
            radio_block.set_bandwidth(3e6, 0)
        else:
            raise Exception("Radio type %s is not supported" % RADIO)


        self._file_sink = blocks.file_sink(gr.sizeof_gr_complex, OUTFILE)
        self.connect((radio_block, 0), (self._file_sink, 0))

    def reset_trace(self):
        """
        Remove the current trace file and get ready for a new trace.
        """
        self._file_sink.open(OUTFILE)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


if __name__ == "__main__":
    cli()
