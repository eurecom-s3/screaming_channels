#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

#git checkout ches20

# Profile
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_O3_tx_500/ --start-point 300 --end-point 320 --num-traces 100000 profile --variable p_xor_k --pois-algo r --num-pois 15  /tmp/O3_100000
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ \
--start-point 400 --end-point 700 --num-traces 5000 profile /tmp/5000 \
--variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1

# Figure 15a
sc-attack --plot --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_O3_tx_500/ --start-point 0 --end-point 0 --num-traces 10 cra

# Figure 15b
python2.7 src/screamingchannels/sc-compare.py --num-pois 1 --plot /tmp/O3_100000 /tmp/O3_100000/ compare

# Table 8
python << END
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import multivariate_normal, linregress, norm, pearsonr, entropy
from os import path
from tabulate import tabulate

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

def load_profile(dir):
    POIS = np.load(path.join(dir, "POIS.npy"))
    #RS = np.load(path.join(dir, "PROFILE_RS.npy"))
    #RZS = np.load(path.join(dir, "PROFILE_RZS.npy"))
    MEANS = np.load(path.join(dir, "PROFILE_MEANS.npy"))
    STDS = np.load(path.join(dir, "PROFILE_STDS.npy"))
    #COVS = np.load(path.join(dir, "PROFILE_COVS.npy"))
    MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    return MEANS

bytes = ["\\\textbf{byte}"] + [str(i) for i in range(16)]

reference = load_profile("/tmp/5000")
means = load_profile("/tmp/O3_100000")
ps = ["\\\textbf{-log10(p)}"]
rs = ["\\\boldmath$\\\rho$"]
for i in range(16):
    r,p = pearsonr(reference[i,:,0], means[i,:,0])
    ps.append("%.2f"%-np.log10(p))
    rs.append("%.2f"%r)

table = [bytes, rs, ps]
print(tabulate(table, tablefmt="latex_raw", floatfmt=".2f"))
END

