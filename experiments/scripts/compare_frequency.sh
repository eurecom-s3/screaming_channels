#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

#git checkout ches20

RADIO=USRP_B210
DEVICE=/dev/ttyACM0
DISTANCE=10cm
CHIP=ble2 #firmware at ches20.1 (Firmware A)

NTRACES_TEMPLATE=5000
NTRACES_ATTACK=2000

FOLDER=$TRACES_CHES20/ches20/compare_frequencies/$CHIP/$RADIO/$DISTANCE/

CHANNELS=( "0" "0" "2" "2" "26" "26" "80" "80" )
FREQS=( "2.528e9" "2.528e9" "2.530e9" "2.530e9" "2.554e9" "2.554e9" "2.608e9" "2.608e9")
FIXED=( "false" "true" "false" "true" "false" "true" "false" "true" ) 
NTRACES=( "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" )

# Collect

# Uncomment if you want to collect the traces
# WARNING: If unmodified it will rewrite the traces in the TRACES_CHES20/ches20 folder

#mkdir -p $FOLDER
#
#for ((i=0;i<${#CHANNELS[@]};++i)); do
#    channel=${CHANNELS[i]};
#    freq=${FREQS[i]};
#    fixed=${FIXED[i]};
#    ntraces=${NTRACES[i]};
#    folder=$FOLDER/$channel/$freq/$fixed;
#    echo $channel $freq $fixed $ntraces $folder;
#    mkdir -p $folder
#
#    config=$(jq -n \
#	    --argjson fixed $fixed \
#	    --argjson freq $freq \
#	    --argjson ntraces $ntraces \
#	    --argjson channel $channel \
#    '{
#        "firmware": {
#            "mode": "tinyaes",
#            "fixed_key": $fixed,
#            "modulate": true
#        },
#        "collection": {
#	    "channel": $channel,
#            "target_freq": $freq,
#            "sampling_rate": 5e6,
#            "num_points": $ntraces,
#            "num_traces_per_point": 500,
#            "bandpass_lower": 1.95e6,
#            "bandpass_upper": 2.02e6,
#            "lowpass_freq": 5e3,
#            "drop_start": 50e-3,
#            "trigger_rising": true,
#            "trigger_offset": 100e-6,
#            "signal_length": 300e-6,
#            "template_name": "templates/tiny_anechoic_10m_080618.npy",
#            "min_correlation": 0.00,
#            "hackrf_gain_if": 35,
#            "hackrf_gain_bb": 39,
#            "usrp_gain": 50
#        }
#    }')
#    echo $config > $folder/config.json
#
#    sc-experiment --radio $RADIO \
#	          --device $DEVICE \
#		  collect --max-power \
#		          $folder/config.json \
#			  $folder;
#done

# Profile
for ((i=0;i<${#CHANNELS[@]};++i)); do
    channel=${CHANNELS[i]};
    freq=${FREQS[i]};
    fixed=${FIXED[i]};
    ntraces=${NTRACES[i]};
    folder=$FOLDER/$channel/$freq/$fixed;
    if [ $fixed == "true" ] 
    then
    continue
    fi
    echo $channel $freq $fixed $ntraces $folder;
    sc-attack --norm --data-path $folder --num-traces $NTRACES profile $folder/r/ --variable p_xor_k --pois-algo r --num-pois 1;
done

# Compute comparison table
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
#    if path.isfile(path.join(dir, "PROFILE_MIS.npy")):
#        MIS = np.load(path.join(dir, "PROFILE_MIS.npy"))
#    else:
#	MIS = np.zeros(2)
    return MEAN_TRACE, MEANS[0], STDS[0], POIS[0], RS, RZS#, MIS

index = [""]+["\\\boldmath\$P_{%d}\$"%i for i in range(4)]
channels = ["\\\textbf{channel f (GHz)}", "2.400", "2.402", "2.426", "2.608"]
freqs = ["\\\textbf{tune f (GHz)}", "2.528", "2.530", "2.554", "2.480"]

mean_trace, means, stds, pois, rs, rzs  = load_profile("$FOLDER/0/2.528e9/false/r/")
reference = means

distorsion = ["\\\boldmath$\\\hat{r}(P_{i},P_{2})$, \\\textbf{-log10(p)}"]
info = ["\\\boldmath\$max \\\rho,r_{z}$"]

for dir in ["$FOLDER/0/2.528e9/false","$FOLDER/2/2.530e9/false","$FOLDER/26/2.554e9/false","$FOLDER/80/2.608e9/false"]:
    mean_trace, means, stds, pois, rs_rho, rzs_rho = load_profile(path.join(dir,"r"))
    r,p = pearsonr(reference, means)
    distorsion.append("%.2f, %.2f"%(r,-np.log10(p)))

    rmax = np.max(rs_rho)
    amx = np.unravel_index(rs_rho.argmax(), rs_rho.shape)
    rzmax = rzs_rho[amx]
    info.append("%.2f, %.2f"%(rmax,rzmax))

table = [index, channels, freqs, distorsion, info]
print(tabulate(list(zip(*table)), tablefmt="latex_raw", floatfmt=".2f"))
END
