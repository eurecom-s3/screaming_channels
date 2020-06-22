#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# git checkout ches20

# Baseline A
sc-attack  --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 130000 profile /tmp/baselinea --variable hw_sbox_out --pois-algo r --num-pois 1
# + see CCS18

# Less Traces
sc-attack  --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 50000 profile /tmp/baselinea2 --variable hw_sbox_out --pois-algo r --num-pois 1
sc-attack --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 3000 --bruteforce --bit-bound-end 33 attack /tmp/baselinea2/ --variable hw_sbox_out

# 1 Full profile
sc-attack  --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 50000 profile /tmp/full2 --variable p_xor_k --pois-algo r --num-pois 1
sc-attack --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 3000 --bruteforce attack /tmp/full2/ --variable p_xor_k

# 2 Norm
sc-attack  --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 50000 profile /tmp/norm1 --variable hw_sbox_out --pois-algo r --num-pois 1
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 3000 --bruteforce --bit-bound-end 33 attack /tmp/norm1/ --variable hw_sbox_out

# 2 Norm + 1
sc-attack  --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 50000 profile /tmp/norm2 --variable p_xor_k --pois-algo r --num-pois 1
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 3000 --bruteforce attack /tmp/norm2/ --variable p_xor_k


# 3 Combining + 1 +2 
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 3000 --bruteforce attack /tmp/norm2/ --variable p_xor_k --average-bytes
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 1775 attack /tmp/norm2/ --variable p_xor_k --average-bytes
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 100 --bruteforce attack /tmp/norm2/ --variable p_xor_k --average-bytes
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 35 --bruteforce attack /tmp/norm2/ --variable p_xor_k --average-bytes

# 4 Template +1 +2
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 1175 --bruteforce attack /tmp/norm2/ --variable p_xor_k --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 100 --bruteforce attack /tmp/norm2/ --variable p_xor_k --attack-algo pdf --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 35 --bruteforce attack /tmp/norm2/ --variable p_xor_k --attack-algo pdf --pooled-cov

# 5 Multivariate 
sc-attack  --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template/ --start-point 750 --end-point 950 --num-traces 50000 profile /tmp/norm3 --variable p_xor_k --pois-algo r --num-pois 5 --poi-spacing 1

sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 1775 --bruteforce attack /tmp/norm3 --variable p_xor_k --attack-algo pdf --num-pois 5 --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 100 --bruteforce attack /tmp/norm3 --variable p_xor_k --attack-algo pdf --num-pois 5 --pooled-cov
sc-attack --norm --data-path $TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_attack/ --start-point 750 --end-point 950 --num-traces 15 --bruteforce attack /tmp/norm3 --variable p_xor_k --attack-algo pdf --num-pois 5 --pooled-cov


# Plot
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
    "baselinea",
    "baselinea2",
    "full2",
    "norm1",
    "norm2",
    "norm3"
]
for dir in dirs:
    r, rz = load_profile("/tmp/%s"%dir)
    rmax = np.max(r)
    amx = np.unravel_index(r.argmax(), r.shape)
    rzmax = rz[amx]
    print "%s $%.2f$, $%3.0f$"%(dir, rmax, rzmax)
END

