# Instructions

[Detailed Instructions](https://eurecom-s3.github.io/screaming_channels/#Native)

# Experiments with BLE Nano 2 #

This directory contains scripts to reproduce our measurements. Make sure that
GNUradio is installed, then change into the `src` directory and install the
package with `python2 setup.py install`; optionally pass `--user` to install
locally instead of system-wide, or use `python2 setup.py develop --user` to
install in development mode (i.e. changes to the source become effective
immediately).

After installation, you can run `sc-experiment --help` and `sc-attack --help`
for usage information. A full command would be, for example, `sc-experiment
cw_with_regswitch --plot`. (Note that in development mode the location of the
scripts might not be on your `PATH`; on Linux it is typically `~/.local/bin`.
