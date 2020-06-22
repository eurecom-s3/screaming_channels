#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

#git checkout ches20

# Profile
for i in $(seq 10000 1000 37000); 
do
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces $i --mimo ch1 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/ch1_$i;
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces $i --mimo ch2 profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/ch2_$i;
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces $i --mimo eg profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/eg_$i
sc-attack --norm --data-path $TRACES_CHES20/ches20/spatial_diversity/10cm_parallel_template_tx_500_2/ --start-point 400 --end-point 630 --num-traces $i --mimo mr profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/mr_$i;
done

#SIZE=10000
#
## Plot
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
    #MEANS = np.load(path.join(dir, "PROFILE_MEANS.npy"))
    #STDS = np.load(path.join(dir, "PROFILE_STDS.npy"))
    #COVS = np.load(path.join(dir, "PROFILE_COVS.npy"))
    #MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    #return RS[0], RZS[0], POIS[0][0]
    return RS, RZS, POIS[0,0]

#modes = ["\\\textbf{mode}", "channel 1", "channel 2", "equal gain", "maximal ratio"]
#
#rzs = ["\\\boldmath{$r_{z}$)}"]
#rs = ["\\\boldmath$\\\rho$"]
#for i, dir in enumerate(["/tmp/ch1_$SIZE", "/tmp/ch2_$SIZE", "/tmp/eg_$SIZE", "/tmp/mr_$SIZE"]):
#    r, rz, poi = load_profile(dir)
#    plt.plot(r)
#    rs.append("%.2f"%r[poi])
#    rzs.append("%.2f"%rz[poi])
#
#plt.show()
#table = [modes, rs, rzs]
#print(tabulate(table, tablefmt="latex_raw", floatfmt=".2f"))

#fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'wspace': 0.3})
#ax1.set(ylabel='r', xlabel='Number of Traces')
#ax2.set(ylabel='r_z', xlabel='Number of Traces')
fig1, ax1 = plt.subplots()
fig2, ax2 = plt.subplots()
ax1.set(ylabel='r', xlabel='Number of Traces')
ax2.set(ylabel='r_z', xlabel='Number of Traces')

x = [i for i in range(10000, 37000, 1000)]
for style, type in zip(["-","--","-.","-*"],["ch1", "ch2", "eg", "mr"]):
    rs = []
    rzs = []
    for i in x:
        r, rz, poi = load_profile("/tmp/%s_%d"%(type,i))
        rs.append(r[0][poi])
	rzs.append(rz[0][poi])
    ax1.plot(x, rs, style, label=type, linewidth=5.0, markersize=15)
    ax2.plot(x, rzs, style, label=type, linewidth=5.0, markersize=15)
ax1.legend(loc='lower right')
plt.show()
ax2.legend(loc='lower right')
plt.show()

END

