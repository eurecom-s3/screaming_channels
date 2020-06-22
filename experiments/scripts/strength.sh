#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# git checkout ches20

### Profile
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1100 --end-point 1700 --num-traces 5000 profile --num-pois 11 --poi-spacing 1 --variable p_xor_k --pois-algo r /tmp/information/conventional/r/
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_cable/ro_test_template/ --start-point 900 --end-point 1500 --num-traces 5000 profile --variable p_xor_k --pois-algo r --num-pois 11 /tmp/information/cable/r/
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ --start-point 0 --end-point 0 --num-traces 5000 profile --variable p_xor_k --pois-algo r --num-pois 11 /tmp/information/10cm/r/
#sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ --start-point 1100 --end-point 1700 --num-traces 5000 profile --num-pois 15 --poi-spacing 1 --variable p_xor_k --pois-algo r /tmp/information/conventional/r15/

### Figure 4
python src/screamingchannels/sc-compare.py --plot --align /tmp/information/conventional/r/ /tmp/information/cable/r/ compare
python src/screamingchannels/sc-compare.py --plot --align /tmp/information/conventional/r/ /tmp/information/10cm/r/ compare

### Attacks

#### Conventional
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 3 --bruteforce attack --num-pois 11 --variable p_xor_k /tmp/information/conventional/r/ --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 5 --bruteforce attack --num-pois 11 --variable p_xor_k /tmp/information/conventional/r/ --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 9 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/information/conventional/r/
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 9 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/information/conventional/r/ --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/information/conventional/r/
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_conventional/64MHz_attack/ --start-point 1100 --end-point 1700 --num-traces 14 --bruteforce attack --num-pois 1 --variable p_xor_k /tmp/information/conventional/r/ --attack-algo pdf --pooled-cov

#### 10cm
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 130 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/information/10cm/r
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 130 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/information/10cm/r --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/information/10cm/r
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ --start-point 0 --end-point 0 --num-traces 1273 --bruteforce attack --variable p_xor_k --num-pois 1 /tmp/information/10cm/r --attack-algo pdf --pooled-cov

#### Cable
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_cable/attack --start-point 937 --end-point 1500 --num-traces 1000 --bruteforce --bit-bound-end 21 attack --variable p_xor_k --num-pois 1 /tmp/information/cable/r/

### Read max values
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
    RS = np.load(path.join(dir, "PROFILE_RS.npy"))
    RZS = np.load(path.join(dir, "PROFILE_RZS.npy"))
    MEANS = np.load(path.join(dir, "PROFILE_MEANS.npy"))
    STDS = np.load(path.join(dir, "PROFILE_STDS.npy"))
    COVS = np.load(path.join(dir, "PROFILE_COVS.npy"))
    MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    return RS, RZS

dirs = [
    "/tmp/information/conventional/r/",
    "/tmp/information/cable/r/",
    "/tmp/information/10cm/r/",
]
for dir in dirs:
    r, rz = load_profile("%s"%dir)
    rmax = np.max(r)
    amx = np.unravel_index(r.argmax(), r.shape)
    rzmax = rz[amx]
    print "%s $%.2f$, $%3.0f$"%(dir, rmax, rzmax)
END
