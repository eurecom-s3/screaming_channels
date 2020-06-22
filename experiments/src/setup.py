from setuptools import setup, find_packages

setup(
    name="ScreamingChannels",
    version="2.0",
    packages=find_packages(),
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    entry_points={
        "console_scripts": [
            "sc-experiment = screamingchannels.reproduce:cli",
            "sc-attack = screamingchannels.attack:cli",
        ]
    },
    install_requires=[
        "click==6.7",
        "numpy==1.16.6",
        "scipy==1.1.0",
        "pyserial==3.4",
        "matplotlib==2.2.3",
        "enum34",
        "pmt==0.0.3",
        "pyts==0.9.0",
        "numba==0.46.0",
        "statsmodels==0.8.0",
        "pandas==0.22.0",
        "scikit-learn==0.20.3",
        "future==0.16.0",
        "pycrypto==2.6.1",
        "pyzmq==16.0.2",
        "peakutils==1.3.2",
        "tabulate==0.8.1",
        "kiwisolver==1.1.0"


# to use system packages
#        ln -s /usr/lib/python2.7/site-packages/gnuradio ../../../../screaming-channel/nRF52832/experiments/VENV_sc/lib/python2.7/site-packages
#        "gnuradio",
#        "osmosdr",
    ],

    author="S3@EURECOM",
    author_email="camurati@eurecom.fr, poeplau@eurecom.fr, muench@eurecom.fr",
    description="Code for our screaming channel attacks",
    license="GNU General Public License v3.0"
    # TODO URLs
)
