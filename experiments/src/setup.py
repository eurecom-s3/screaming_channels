from setuptools import setup, find_packages

setup(
    name="ScreamingChannels",
    version="1.0",
    packages=find_packages(),
    python_requires=">=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*",
    entry_points={
        "console_scripts": [
            "sc-experiment = screamingchannels.reproduce:cli",
            "sc-attack = screamingchannels.attack:cli",
        ]
    },
    install_requires=[
        "click",
        "numpy",
        "scipy",
        "pyserial",
        "matplotlib",
    ],

    author="S3@EURECOM",
    author_email="camurati@eurecom.fr, poeplau@eurecom.fr, muench@eurecom.fr",
    description="Code for our screaming channel attacks",
    license="GNU General Public License v3.0"
    # TODO URLs
)
