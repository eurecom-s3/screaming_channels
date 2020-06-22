#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# git checkout ches20

# Profile
SIZE=5000

LIST="\
        $TRACES_CHES20/ches20/hackrf_conventional/64MHz_template/ \
	$TRACES_CHES20/ches20/hackrf_cable/ro_test_template \
	$TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ \
	$TRACES_CHES20/ches20/hackrf_20cm/template_tx_500/ \
	$TRACES_CHES20/ches20/shannon_080719/1m/switched/template_tx_500/ \
	$TRACES_CHES20/ccs18/anechoic_5m_template/ \
	$TRACES_CHES20/ccs18/tinyaes_anechoic_10m_080618_template \
"

i=0
for path in $LIST
do
echo $i;
sc-attack --norm --data-path $path --num-traces $SIZE profile --variable p_xor_k --pois-algo r --num-pois 1 /tmp/distance/r/$i;
let i++;
done

# Print Table 4
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
    return MEAN_TRACE, MEANS[0], STDS[0], POIS[0], RS, RZS

#index = ["", "\$P_{0}\$", "\$P_{1}\$", "\$P_{2}\$", "\$P_{3}\$", "\$P_{4}\$", "\$P_{5}\$", "\$P_{6}\$"]
index = [""]+["\\\boldmath\$P_{%d}\$"%i for i in range(7)]
distances = ["\\\textbf{d (m)}", "0.00", "0.00", "0.10", "0.20", "1.00", "5.00", "10.00"]
types = ["\\\textbf{environment}", "conventional", "cable", "home", "home", "office", "anechoic", "anechoic"]
antennas = ["\\\textbf{antenna}", "loop probe", "n.a.", "standard", "standard", "directed", "directed", "directed"]

mean_trace, means, stds, pois, rs, rzs = load_profile("/tmp/distance/r/2")
reference = means
#ps = ["\\\textbf{-log10(p)}"]
#rs = ["\\\boldmath$\\\hat{r}(P_{i},P_{2})$"]

distorsion = ["\\\boldmath$\\\hat{r}(P_{i},P_{2})$, \\\textbf{-log10(p)}"]
info = ["\\\boldmath\$max \\\rho,r_{z}$"]

for i in range(7):
    mean_trace, means, stds, pois, rs_rho, rzs_rho = load_profile("/tmp/distance/r/%d"%i)
    #plt.plot(mean_trace[pois[0]-150:pois[0]+150])
    #plt.plot(means-np.average(means))
    r,p = pearsonr(reference, means)
    #ps.append("%.2f"%-np.log10(p))
    #rs.append("%.2f"%r)
    distorsion.append("%.2f, %.2f"%(r,-np.log10(p)))

    rmax = np.max(rs_rho)
    amx = np.unravel_index(rs_rho.argmax(), rs_rho.shape)
    rzmax = rzs_rho[amx]
    info.append("%.2f, %.2f"%(rmax,rzmax))

table = [index, distances, types, antennas, distorsion, info]
print(tabulate(list(zip(*table)), tablefmt="latex_raw", floatfmt=".2f"))
END

