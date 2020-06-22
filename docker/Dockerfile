FROM ubuntu:18.04
MAINTAINER Camurati Giovanni giovanni.camurati@eurecom.fr
ENV DEBIAN_FRONTEND noninteractive

# Prepare the system
RUN apt-get update && apt-get install -yq \
    git vim gnuradio python-pip gr-osmosdr \
    minicom hackrf gqrx-sdr \
    xauth sudo wget unzip \
    udiskie gcc-arm-none-eabi \
    python3-pip bluez && \
    pip install setuptools && \
    pip3 install gatt==0.2.7 pyzmq==17.1.2

# Install screaming
RUN mkdir /home/screaming \
     && cd /home/screaming \
     && git clone https://github.com/eurecom-s3/screaming_channels.git \
     && cd screaming_channels \
     && git checkout ches20 \
     && cd /home/screaming/screaming_channels/experiments/src/ \
     && python2 setup.py develop

# Install firmware
ENV NORDIC_SEMI_SDK=/home/screaming/screaming_channel/firmware/nRF5_SDK_14.2.0_17b948a/

RUN cd /home/screaming/screaming_channels/firmware/ \
    && wget https://developer.nordicsemi.com/nRF5_SDK/nRF5_SDK_v14.x.x/nRF5_SDK_14.2.0_17b948a.zip \
    && unzip nRF5_SDK_14.2.0_17b948a.zip \
    && rm nRF5_SDK_14.2.0_17b948a.zip \
    && cp boards.h nRF5_SDK_14.2.0_17b948a/components/boards/ \
    && cp Makefile.posix nRF5_SDK_14.2.0_17b948a/components/toolchain/gcc \
    && cp rblnano2.h  nRF5_SDK_14.2.0_17b948a/components/boards/

# Install nordic tools
RUN cd /home/screaming \
    && wget https://www.nordicsemi.com/-/media/Software-and-other-downloads/Desktop-software/nRF-command-line-tools/sw/Versions-10-x-x/nRFCommandLineTools1060Linuxamd64tar.gz \
    && tar xvzf nRFCommandLineTools1060Linuxamd64tar.gz \
    && dpkg -i nRF-Command-Line-Tools_10_6_0_Linux-amd64.deb

# Install python_hel
RUN apt-get install -yq \
    libntl-dev libgmp-dev \
    && cd /home/screaming/ \
    #&& git clone https://github.com/eurecom-s3/python-hel \
    && git clone https://github.com/giocamurati/python_hel.git \
    && cd python_hel \
    && cd hel_wrapper \
    && make AES_TYPE=aes_ni \
    && make install \
    && ldconfig \
    && cd ../python_hel \
    && python2 setup.py install
    #&& make TYPE=aes_simple

# Install screaming channels
RUN useradd -ms /bin/bash screaming \
    && echo "screaming:screaming" | chpasswd && adduser screaming sudo \
    && chown -R screaming:screaming /home/screaming
WORKDIR /home/screaming
USER screaming
