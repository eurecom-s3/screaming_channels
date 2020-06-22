#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
#cd $SC

# Profile
sc-attack --norm --data-path $TRACES_CHES20/ches20/connection/hackrf_10cm_same_usb_template_tx_500/ --num-traces 4700 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/connection_0
sc-attack --norm --data-path $TRACES_CHES20/ches20/connection/hackrf_10cm_same_power_template_tx_500/ --num-traces 4700 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/connection_1
sc-attack --norm --data-path $TRACES_CHES20/ches20/connection/hackrf_10cm_floating_template/ --num-traces 4700 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/connection_2

sc-attack --norm --data-path $TRACES_CHES20/ches20/connection/usrp_10cm_direct_ethernet_fixed_vs_fixed_500/ --start-point 400 --end-point 725 --num-traces 4700 profile --variable fixed_vs_fixed --pois-algo r --num-pois 1 /tmp/connection_3
sc-attack --norm --data-path $TRACES_CHES20/ches20/connection/usrp_10cm_direct_s3net_fixed_vs_fixed_500/    --start-point 400 --end-point 725 --num-traces 4700 profile --variable fixed_vs_fixed --pois-algo r --num-pois 1 /tmp/connection_4


# Print Table 6
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
    #COVS = np.load(path.join(dir, "PROFILE_COVS.npy"))
    MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    return RS, RZS

types = ["\\\textbf{environment}", "same usb", "same power", "floating", "direct ethernet", "building LAN"]
variables = ["\\\textbf{antenna}", "\$p \\\oplus k$", "\$p \\\oplus k$", "\$p \\\oplus k$", "fixed vs. fixed", "fixed vs. fixed"]

ps = ["\\\textbf{max} \\\boldmath\$r_{z}$"]
rs = ["\\\textbf{max} \\\boldmath$\\\rho$"]
for i in range(5):
    r, p = load_profile("/tmp/connection_%d"%i)
    r = r[~np.isnan(r)]
    p = p[~np.isnan(p)]
    r = np.max(r)
    p = np.max(p)
    ps.append("%.2f"%p)
    rs.append("%.2f"%r)

table = [types, variables, rs, ps]
print(tabulate(table, tablefmt="latex_raw", floatfmt=".2f"))
END

