#!/usr/bin/python2
# The collection script has to use Python 2 for GNUradio, so keep using it here.

import click
import numpy as np
from matplotlib import pyplot as plt
from scipy.stats import multivariate_normal, linregress, norm, pearsonr, entropy

SMALL_SIZE = 8*4
MEDIUM_SIZE = 10*4
BIGGER_SIZE = 12*4

plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

import os
from os import path
from scipy.stats import multivariate_normal, linregress, norm, pearsonr, entropy
from scipy import signal
import pickle

PLOT = None

POIS_1 = None
NUM_KEY_BYTES = None
RS_1 = None
RZS_1 = None
MEANS_1 = None
STDS_1 = None
COVS_1 = None
MEAN_TRACE_1 = None

POIS_2 = None
RS_2 = None
RZS_2 = None
MEANS_2 = None
STDS_2 = None
COVS_2 = None
MEAN_TRACE_2 = None

POIS_3 = None
RS_3 = None
RZS_3 = None
MEANS_3 = None
STDS_3 = None
COVS_3 = None
MEAN_TRACE_3 = None

PLOT = None
NUM_KEY_BYTES = None
CLASSES = None

D3 = False

def correlate(a, b):
      cov = np.correlate(a - np.average(a),
              b - np.average(b),
                         mode='full')
      cor = cov / (len(a) * np.std(a) *
              np.std(b))
      return cor[len(a)-1]
 
@click.group()
@click.argument("template_dir_1", type=click.Path(file_okay=False, writable=True))
@click.argument("template_dir_2", type=click.Path(file_okay=False, writable=True))
@click.option("--template-dir-3", type=click.Path(file_okay=False, writable=True))
@click.option("--plot/--no-plot", default=False, show_default=True,
              help="Visualize relevant data (use only with a small number of traces.")
@click.option("--align/--no-align", default=False, show_default=True,
              help="Align profiles w.r.t. POIs")
@click.option("--remove-dc/--no-remove-dc", default=False, show_default=True,
              help="Remove dc component from profiles")
@click.option("--num-pois", default=0, show_default=True,
              help="Number of points of interest.")
@click.option("--num-key-bytes", default=16, show_default=True,
              help="Number of bytes.")
def cli(template_dir_1, template_dir_2, template_dir_3, plot, align, remove_dc, num_pois, num_key_bytes):
    """
    Compare 2 profiles.
    """
    global POIS_1, RS_1, RZS_1, MEANS_1, COVS_1, MEAN_TRACE_1, STDS_1
    global POIS_2, RS_2, RZS_2, MEANS_2, COVS_2, MEAN_TRACE_2, STDS_2
    global POIS_3, RS_3, RZS_3, MEANS_3, COVS_3, MEAN_TRACE_3, STDS_3
    global PLOT, NUM_KEY_BYTES, CLASSES, NUM_POIS, NUM_POIS
    global D3

    if plot:
        PLOT = True

    if template_dir_3:
        D3 = True

    # load first profile
    POIS_1 = np.load(path.join(template_dir_1, "POIS.npy"))
    RS_1 = np.load(path.join(template_dir_1, "PROFILE_RS.npy"))
    RZS_1 = np.load(path.join(template_dir_1, "PROFILE_RZS.npy"))
    MEANS_1 = np.load(path.join(template_dir_1, "PROFILE_MEANS.npy"))
    STDS_1 = np.load(path.join(template_dir_1, "PROFILE_STDS.npy"))
    COVS_1 = np.load(path.join(template_dir_1, "PROFILE_COVS.npy"))
    MEAN_TRACE_1 = np.load(path.join(template_dir_1, "PROFILE_MEAN_TRACE.npy"))

    # load second profile
    POIS_2 = np.load(path.join(template_dir_2, "POIS.npy"))
    RS_2 = np.load(path.join(template_dir_2, "PROFILE_RS.npy"))
    RZS_2 = np.load(path.join(template_dir_2, "PROFILE_RZS.npy"))
    MEANS_2 = np.load(path.join(template_dir_2, "PROFILE_MEANS.npy"))
    STDS_2 = np.load(path.join(template_dir_2, "PROFILE_STDS.npy"))
    COVS_2 = np.load(path.join(template_dir_2, "PROFILE_COVS.npy"))
    MEAN_TRACE_2 = np.load(path.join(template_dir_2, "PROFILE_MEAN_TRACE.npy"))

    # load third profile
    if template_dir_3:
        POIS_3 = np.load(path.join(template_dir_3, "POIS.npy"))
        RS_3 = np.load(path.join(template_dir_3, "PROFILE_RS.npy"))
        RZS_3 = np.load(path.join(template_dir_3, "PROFILE_RZS.npy"))
        MEANS_3 = np.load(path.join(template_dir_3, "PROFILE_MEANS.npy"))
        STDS_3 = np.load(path.join(template_dir_3, "PROFILE_STDS.npy"))
        COVS_3 = np.load(path.join(template_dir_3, "PROFILE_COVS.npy"))
        MEAN_TRACE_3 = np.load(path.join(template_dir_3, "PROFILE_MEAN_TRACE.npy"))

    NUM_KEY_BYTES = num_key_bytes #min(len(POIS_1), len(POIS_2))
    CLASSES = range(0, len(MEANS_1[0]))
    if num_pois == 0:
        NUM_POIS = min(len(POIS_1[0]), len(POIS_2[0]))
    else:
        NUM_POIS = num_pois

    # align
    if align:
        start_1 = POIS_1[0,0]
        start_2 = POIS_2[0,0]
        length_1 = len(MEAN_TRACE_1)
        length_2 = len(MEAN_TRACE_2)
        length = min(length_1, length_2)# - abs(start_2 - start_1)

        if start_1 < start_2:
            b1 = 0
            e1 = length
            b2 = start_2-start_1
            e2 = start_2-start_1+length
            POIS_2 = POIS_2 - b2
        else:
            b1 = start_1-start_2
            e1 = start_1-start_2+length
            b2 = 0
            e2 = length
            POIS_1 = POIS_1 - b1

        MEAN_TRACE_1 = MEAN_TRACE_1[b1:e1]
        MEAN_TRACE_2 = MEAN_TRACE_2[b2:e2]
        RS_1 = RS_1[:,b1:e1]
        RS_2 = RS_2[:,b2:e2]
        RZS_1 = RZS_1[:,b1:e1]
        RZS_2 = RZS_2[:,b2:e2]

    # remove dc
    if remove_dc:
        for bnum in range(NUM_KEY_BYTES):
            for poi in range(NUM_POIS):
                dc_1 = np.average(MEANS_1[bnum,:,poi])
                MEANS_1[bnum,:,poi] = MEANS_1[bnum,:,poi] - dc_1
                dc_2 = np.average(MEANS_2[bnum,:,poi])
                MEANS_2[bnum,:,poi] = MEANS_2[bnum,:,poi] - dc_2
 
@cli.command()
def compare():
    """
    Compare 2 profiles.
    """

    # correlation between templates, if possible
    if np.shape(MEANS_1[0,:,0]) == np.shape(MEANS_2[0,:,0]):
        correlation_templates = np.zeros((NUM_KEY_BYTES, NUM_POIS))
        p_templates = np.zeros((NUM_KEY_BYTES, NUM_POIS))
        print "Correlation between templates"
        for poi in range(NUM_POIS):
            for i in range(NUM_KEY_BYTES):
                #cor = correlate(MEANS_1[i,:,poi], MEANS_2[i,:,poi])
                r, p = pearsonr(MEANS_1[i,:,poi], MEANS_2[i,:,poi])
                correlation_templates[i, poi] = r
                p_templates[i, poi] = p
                print "POI %2d, BYTE %2d, COR %.2f, -LOG10(p) %.2f"%(poi, i, r, -np.log10(p))


    # correlation among bytes
    print ""
    print "Correlation among models of subkeys, for each template"
    correlation_bytes_1 = np.zeros((NUM_KEY_BYTES, NUM_KEY_BYTES, NUM_POIS))
    correlation_bytes_2 = np.zeros((NUM_KEY_BYTES, NUM_KEY_BYTES, NUM_POIS))
    for poi in range(NUM_POIS):
        for i in range(NUM_KEY_BYTES):
            for j in range(i):
                cor1 = correlate(MEANS_1[i,:,poi], MEANS_1[j,:,poi])
                cor2 = correlate(MEANS_2[i,:,poi], MEANS_2[j,:,poi])
                correlation_bytes_1[i, j, poi] = cor1
                correlation_bytes_2[i, j, poi] = cor2
                print "POI %2d, BYTE A %2d, BYTE B %2d, COR %.2f %.2f"%(poi, i, j,
                        cor1, cor2)


    if PLOT:
        for spine in plt.gca().spines.values():
                spine.set_visible(False)
      
        num_plots = 3
        plt.subplots_adjust(hspace = 1) 

        # mean
        plt.subplot(num_plots, 1, 1)
        #plt.title("Mean trace")
        plt.xlabel("samples")
        plt.ylabel("normalized\namplitude")
        plt.plot(MEAN_TRACE_1, 'g')
        plt.plot(MEAN_TRACE_2, 'r')
        if D3:
            plt.plot(MEAN_TRACE_3, 'orange')

        # correlation
        plt.subplot(num_plots, 1, 2)
        #plt.title("Correlation")
        plt.xlabel("samples")
        plt.ylabel("r")
        for r_1, r_2 in zip(RS_1[0:NUM_KEY_BYTES], RS_2[0:NUM_KEY_BYTES]):
            plt.plot(r_1, color='g')
            plt.plot(r_2, color='r')
        if D3:
            for r_3 in RS_3[0:NUM_KEY_BYTES]:
                plt.plot(r_3, color='orange')
        for bnum in range(NUM_KEY_BYTES):
            for poi in range(NUM_POIS):
                if POIS_1[bnum,poi] < len(RS_1[bnum]):
                    if POIS_1[bnum,poi] > 0:
                        plt.plot(POIS_1[bnum,poi], RS_1[bnum][POIS_1[bnum,poi]], 'g*')
        for bnum in range(NUM_KEY_BYTES):
            for poi in range(NUM_POIS):
                if POIS_2[bnum,poi] < len(RS_2[bnum]):
                    if POIS_2[bnum,poi] > 0:
                        plt.plot(POIS_2[bnum,poi], RS_2[bnum][POIS_2[bnum,poi]], 'r*')
        if D3:
            for bnum in range(NUM_KEY_BYTES):
                for poi in range(NUM_POIS):
                    if POIS_3[bnum,poi] < len(RS_3[bnum]):
                        if POIS_3[bnum,poi] > 0:
                            plt.plot(POIS_3[bnum,poi], RS_3[bnum][POIS_3[bnum,poi]], color='orange', marker='*')


        # confidence
        plt.subplot(num_plots, 1, 3)
        #plt.title("Confidence")
        plt.xlabel("samples")
        plt.ylabel("r_z")
        for rz_1, rz_2 in zip(RZS_1[0:NUM_KEY_BYTES], RZS_2[0:NUM_KEY_BYTES]):
            plt.plot(rz_1, 'g')
            plt.plot(rz_2, 'r')
        if D3:
            for rz_3 in RZS_3[0:NUM_KEY_BYTES]:
                plt.plot(rz_3, 'orange')
        plt.axhline(y=5, label="5", color='blue')
        plt.axhline(y=-5, label="-5", color='blue')
        plt.legend(loc='upper right')
 
        plt.show()

        if np.shape(MEANS_1[0,:,0]) == np.shape(MEANS_2[0,:,0]):
            # profiles
            plt.subplots_adjust(hspace = 0.6)
            for i in range(NUM_POIS):
                plt.subplot(NUM_POIS, 1, i+1)
                plt.title("Profiles (poi %d)"%(i))
                plt.xlabel("samples")
                plt.ylabel("normalized amplitude")
 
                for bnum in range(0,NUM_KEY_BYTES):
                    plt.errorbar(CLASSES,
                                 MEANS_1[bnum][:, i],
                                 yerr=STDS_1[bnum][:, i],
                                 fmt='--o',
                                 label="subkey %d"%bnum,
                                 color='g')
                for bnum in range(0,NUM_KEY_BYTES):
                    plt.errorbar(CLASSES,
                                 MEANS_2[bnum][:, i],
                                 yerr=STDS_2[bnum][:, i],
                                 fmt='--o',
                                 label="subkey %d"%bnum,
                                 color='r')
 
                plt.legend(loc='upper right')

            plt.show()
 
            # coorrelation between templates
            plt.subplots_adjust(hspace = 0.6)
            for i in range(NUM_POIS):
                plt.subplot(NUM_POIS, 1, i+1)
                plt.title("Correlation between profiles (poi %d)"%(i))
                plt.xlabel("byte")
                plt.ylabel("correlation")
 
                plt.plot(correlation_templates[:, i])

            plt.show()
 
        # coorrelation between bytes
        plt.subplots_adjust(hspace = 0.6)
        for poi in range(NUM_POIS):
            plt.subplot(NUM_POIS*2, 1, 1 + poi)
            plt.title("Correlation between bytes template 1 (poi %d)"%(poi))
            plt.xlabel("byte")
            plt.ylabel("byte")
            plt.imshow(correlation_bytes_1[:,:,poi])

            plt.subplot(NUM_POIS*2, 1, 1 + NUM_POIS + poi)
            plt.title("Correlation between bytes template 2 (poi %d)"%(poi))
            plt.xlabel("byte")
            plt.ylabel("byte")
            plt.imshow(correlation_bytes_2[:,:,poi])

        plt.show()


if __name__ == "__main__":
    cli()
