#!/usr/bin/python2
import numpy as np

from matplotlib import pyplot as plt
from matplotlib import mlab

from scipy import signal
from scipy.signal import butter, lfilter

#
# Filter creation functions taken from https://stackoverflow.com/a/12233959
#
def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def butter_highpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='high', analog=False)
    return b, a

def butter_highpass_filter(data, cutoff, fs, order=5):
    b, a = butter_highpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y

def find_starts(config, signal):
    """
    Find the starts of interesting activity in the signal.

    The result is a list of indices where interesting activity begins, as well
    as the trigger signal and its average.
    """
    trigger = butter_bandpass_filter(
        signal, config.bandpass_lower, config.bandpass_upper,
        config.sampling_rate, 6)
    trigger = np.absolute(trigger)
    trigger = butter_lowpass_filter(
        trigger, config.lowpass_freq,config.sampling_rate, 6)

    transient = 0.0005
    start_idx = int(transient * config.sampling_rate)
    average = np.average(trigger[start_idx:])
    offset = -int(config.trigger_offset * config.sampling_rate)

    if config.trigger_rising:
        trigger_fn = lambda x, y: x > y
    else:
        trigger_fn = lambda x, y: x < y

    # The cryptic numpy code below is equivalent to looping over the signal and
    # recording the indices where the trigger crosses the average value in the
    # direction specified by config.trigger_rising. It is faster than a Python
    # loop by a factor of ~1000, so we trade readability for speed.
    trigger_signal = trigger_fn(trigger, average)[start_idx:]
    starts = np.where((trigger_signal[1:] != trigger_signal[:-1])
                      * trigger_signal[1:])[0] + start_idx + offset + 1
    if trigger_signal[0]:
        starts = np.insert(starts, 0, start_idx + offset)

    return starts, trigger, average

# Inspired by https://github.com/bolek42/rsa-sdr
def extract(capture_file, config, average_file_name=None, plot=False):
    """
    Post-process a GNUradio capture to get a clean and well-aligned trace.

    The configuration is a reproduce.AnalysisConfig tuple. The optional
    average_file_name specifies the file to write the average to (i.e. the
    template candidate).
    """
    with open(capture_file) as f:
        data = np.fromfile(f, dtype=np.complex64)

    assert len(data) != 0, "ERROR, empty data just after measuring"

    template = np.load(config.template_name) if config.template_name else None
    if template is not None and len(template) != int(
            config.signal_length * config.sampling_rate):
        print("WARNING: Template length doesn't match collection parameters. "
              "Is this the right template?")

    # cut usless transient
    data = data[int(config.drop_start * config.sampling_rate):]

    assert len(data) != 0, "ERROR, empty data after drop_start"
    
    # polar discriminator
    # fdemod = data[1:] * np.conj(data[:-1])
    # fdemod = np.angle(fdemod)
    # plt.plot(fdemod)
    # plt.show()
    # return fdemod
    # data = fdemod

    data = np.absolute(data)

    #
    # extract/aling trace with trigger frequency + autocorrelation
    #
    trace_starts, trigger, trigger_avg = find_starts(config, data)

    # extract at trigger + autocorrelate with the first to align
    traces = []
    trace_length = int(config.signal_length * config.sampling_rate)
    for start in trace_starts:
        if len(traces) >= config.num_traces_per_point:
            break

        stop = start + trace_length

        if stop > len(data):
            break

        trace = data[start:stop]
        if template is None:
            template = trace
            continue

        correlation = signal.correlate(trace**2, template**2)
        if max(correlation) <= config.min_correlation:
            continue

        shift = np.argmax(correlation) - (len(template)-1)
        traces.append(data[start+shift:stop+shift])

    # Reject outliers for each point in time.
    #
    # We reject a fixed number; while basing the decision on the standard
    # deviation would be nicer, we can't implement it with efficient numpy
    # operations: discarding a variable number of elements per column would not
    # yield a proper matrix again, so we'd need a Python loop...
    #
    # It should be enough to discard high values and keep everything on the low
    # side because interference always increases the energy (assuming that our
    # alignment is correct).
    num_reject = int(0.05 * len(traces))
    points = np.asarray(traces).T
    points.sort()
    avg = points[:, num_reject:(len(traces) - num_reject)].mean(axis=1)

    if average_file_name:
        np.save(average_file_name, avg)

    if plot:
        plot_results(config, data, trigger, trigger_avg, trace_starts, traces)

    std = np.std(traces,axis=0)

    print "Extracted "
    print "Number = ",len(traces)
    print "avg[Max(std)] = %.2E"%avg[std.argmax()]
    print "Max(u) = Max(std) = %.2E"%(max(std))
    print "Max(u_rel) = %.2E"%(100*max(std)/avg[std.argmax()]),"%"

    return avg

def plot_results(config, data, trigger, trigger_average, starts, traces):
    plt.subplot(5, 1, 1)

    plt.plot(data)
    plt.title("Capture")

    plt.plot(trigger)
    plt.axhline(y=trigger_average, color='y')
    trace_length = int(config.signal_length * config.sampling_rate)
    for start in starts:
        stop = start + trace_length
        plt.axvline(x=start, color='r', linestyle='--')
        plt.axvline(x=stop, color='g', linestyle='--')

    plt.subplot(5, 1, 2)
    plt.specgram(
        data, NFFT=128, Fs=config.sampling_rate, Fc=0, detrend=mlab.detrend_none,
        window=mlab.window_hanning, noverlap=127, cmap=None, xextent=None,
        pad_to=None, sides='default', scale_by_freq=None, mode='default',
        scale='default')
    plt.title("Spectrogram")

    plt.subplot(5, 1, 3)
    plt.psd(
        data, NFFT=1024, Fs=config.sampling_rate, Fc=0, detrend=mlab.detrend_none,
        window=mlab.window_hanning, noverlap=0, pad_to=None,
        sides='default', scale_by_freq=None, return_line=None)

    if(len(traces) == 0):
        print "WARNING: no encryption was extracted"
    else:
        plt.subplot(5, 1, 4)
        for trace in traces:
            plt.plot(trace)
        plt.title("%d aligned traces" % config.num_traces_per_point)

        plt.subplot(5,1,5)
        plt.plot(np.absolute(np.average(traces, axis=0)))
        plt.title("Average of %d traces" % config.num_traces_per_point)

    plt.show()

if __name__ == "__main__":
    extract(True)
