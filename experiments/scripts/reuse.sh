#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

#git checkout ches20

# acquisition
# using old firmware
# 2400MHz

RADIO=USRP_B210
DEVICE=/dev/ttyACM0
DISTANCE=10cm
CHIP=ble2conv

NTRACES_TEMPLATE=5000
NTRACES_ATTACK=2000

CHIPS=( "ble_a" "ble_a" \
        "ble_b" "ble_b" \
	    "ble_c" "ble_c" \
	    "ble_d" "ble_d" \
	    "ble_e" "ble_e" \
        "ble_f" "ble_f" \
        "ble_f_dap" "ble_f_dap" \
        "ble_b_retake" "ble_b_retake" \
        "ble_c_retake" "ble_c_retake" \
        "ble_e_retake" "ble_e_retake" )

FIXED=( "false" "true" \
	    "false" "true" \
	    "false" "true" \
	    "false" "true" \
	    "false" "true" \
	    "false" "true" \
	    "false" "true" \
        "false" "true" \
	    "false" "true" \
	    "false" "true" )

NTRACES=( "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
          "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
          "$NTRACES_TEMPLATE" "$NTRACES_ATTACK" \
	      "$NTRACES_TEMPLATE" "$NTRACES_ATTAKC" \
          "$NTRACES_TEMPLATE" "$NTRACES_ATTACK"	)

REPETITIONS=( 7 7 \
              1 1 \
	          1 1 \
	          1 1 \
	          1 1 \
	          1 1 \
	          1 1 \
              1 1 \
	          1 1 \
	          1 1 )

FOLDER=$TRACES_CHES20/ches20/compare_reuse/

mkdir -p $FOLDER

# Uncomment to collect
# WARNING: It will overwrite the folder

#for ((i=0;i<${#CHIPS[@]};++i)); do
#    chip=${CHIPS[i]};
#    fixed=${FIXED[i]};
#    ntraces=${NTRACES[i]};
#    repetitions=${REPETITIONS[i]};
#
#    echo "Please insert device $chip"
#    read -n 1
#    echo "Compiling and flashing"
#    TOOLCHAIN=/home/giovanni/phd/tools/gcc-arm-none-eabi-7-2017-q4-major/bin/
#    make GNU_INSTALL_ROOT=$TOOLCHAIN -C $SC/../firmware/blenano2_ches20.1/blank/armgcc/ clean
#    make GNU_INSTALL_ROOT=$TOOLCHAIN -C $SC/../firmware/blenano2_ches20.1/blank/armgcc/
#    cp $SC/../firmware/blenano2_ches20.1/blank/armgcc/_build/nrf52832_xxaa.hex /media/giovanni/DAPLINK
#    sleep 30
#    echo "Starting"
#
#    for repetition in $(seq 0 $repetitions); do
#        folder=$FOLDER/$chip/$repetition/$fixed;
#        echo $chip $fixed $ntraces $folder;
#        mkdir -p $folder;
#
#        config=$(jq -n \
#    	    --argjson fixed $fixed \
#    	    --argjson ntraces $ntraces \
#        '{
#            "firmware": {
#                "mode": "tinyaes",
#                "fixed_key": $fixed,
#                "modulate": true
#            },
#            "collection": {
#                "target_freq": 2.528e9,
#                "sampling_rate": 5e6,
#                "num_points": $ntraces,
#                "num_traces_per_point": 500,
#                "bandpass_lower": 1.95e6,
#                "bandpass_upper": 2.02e6,
#                "lowpass_freq": 5e3,
#                "drop_start": 50e-3,
#                "trigger_rising": true,
#                "trigger_offset": 100e-6,
#                "signal_length": 300e-6,
#                "template_name": "templates/tiny_anechoic_10m_080618.npy",
#                "min_correlation": 0.00,
#                "hackrf_gain_if": 35,
#                "hackrf_gain_bb": 39,
#                "usrp_gain": 50
#            }
#        }')
#
#    
#        echo $config > $folder/config.json;
#    
#        sc-experiment --radio $RADIO \
#		      --device $DEVICE \
#    		      collect --max-power \
#    		              $folder/config.json \
#    			      $folder;
#        done
#done


# Profile
for ((i=0;i<${#CHIPS[@]};++i)); do
    chip=${CHIPS[i]};
    fixed=${FIXED[i]};
    ntraces=${NTRACES[i]};
    repetitions=${REPETITIONS[i]};

    for repetition in $(seq 0 $repetitions); do
        folder=$FOLDER/$chip/$repetition/$fixed;
        echo $chip $fixed $ntraces $folder;
        if [ $fixed == "true" ] 
        then
        continue
        fi
        echo $channel $freq $fixed $ntraces $folder;
        sc-attack --norm --data-path $folder --num-traces $ntraces profile $folder/r/ --variable p_xor_k --pois-algo r --num-pois 1;
        sc-attack --data-path $folder --num-traces $ntraces profile $folder/r_nonorm/ --variable p_xor_k --pois-algo r --num-pois 1;
        sc-attack --data-path $folder --norm2 --num-traces $ntraces profile $folder/r_norm2/ --variable p_xor_k --pois-algo r --num-pois 1;
        sc-attack --data-path $folder --norm --norm2 --num-traces $ntraces profile $folder/r_norm12/ --variable p_xor_k --pois-algo r --num-pois 1;
    done
done

## Attack
for ((i=0;i<${#CHIPS[@]};++i)); do
    chip=${CHIPS[i]};
    fixed=${FIXED[i]};
    ntraces=${NTRACES[i]};
    repetitions=${REPETITIONS[i]};

    for repetition in $(seq 0 $repetitions); do
        folder=$FOLDER/$chip/$repetition/$fixed;
        echo $chip $fixed $ntraces $folder;
        if [ $fixed == "true" ] 
        then
    	continue
        fi
        echo $channel $freq $fixed $ntraces $folder;
        sc-attack --norm --data-path $FOLDER/ble_a/0/true/ --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/reuse.txt
        sc-attack --norm --data-path $FOLDER/$chip/$repetition/true --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/same.txt
        sc-attack --norm --data-path $FOLDER/ble_a/0/true/ --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/reuse_average_bytes.txt
        sc-attack --norm --data-path $FOLDER/$chip/$repetition/true --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/same_average_bytes.txt
        sc-attack --data-path $FOLDER/ble_a/0/true/ --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/reuse_nonorm.txt
        sc-attack --data-path $FOLDER/$chip/$repetition/true --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r/ --variable p_xor_k \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/same_nonorm.txt

        sc-attack --norm2 --data-path $FOLDER/$chip/$repetition/true --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r_norm2/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/same_average_bytes_norm2.txt
        sc-attack --norm --norm2 --data-path $FOLDER/$chip/$repetition/true --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r_norm12/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/same_average_bytes_norm12.txt
        sc-attack --norm2 --data-path $FOLDER/ble_a/0/true/ --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r_norm2/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/reuse_average_bytes_norm2.txt
        sc-attack --norm --norm2 --data-path $FOLDER/ble_a/0/true/ --num-traces 2000 --bruteforce --bit-bound-end 30 attack $folder/r_norm12/ --variable p_xor_k --average-bytes \
        | grep -E "number|BYTES: 16|actual rounded|not" \
        | sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0/' \
        | sed 's/key not found/actual rounded: xx30/' \
        | awk '{print $3}' > $FOLDER/$chip/$repetition/reuse_average_bytes_norm12.txt
    done
done

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
    MEAN_TRACE = np.load(path.join(dir, "PROFILE_MEAN_TRACE.npy"))
    return MEAN_TRACE, MEANS, STDS, POIS, RS, RZS

index = [""]+["\\\boldmath\$P_{A%d}\$"%i for i in range(8)]

mean_trace, means, stds, pois, rs, rzs = load_profile("$FOLDER/ble_a/0/false/r")
reference = means

distorsion = ["\\\boldmath$\\\hat{r}(P_{i},P_{2})$, \\\textbf{-log10(p)}"]
info = ["\\\boldmath\$\\\rho,r_{z}$"]

dirs = ["$FOLDER/ble_a/%d/false/"%i for i in range(8)]
for dir in dirs:
    mean_trace, means, stds, pois, rs_rho, rzs_rho = load_profile(path.join(dir,"r"))
    rs = []
    ps = []
    for ref,mean in zip(reference, means):
        r, p = pearsonr(ref, mean)
        rs.append(r)
        ps.append(p)
    r = np.average(rs)
    p = np.average(ps)  

    distorsion.append("%.2f, %.2f"%(r,-np.log10(p)))

    ravg = np.average([rs_rho[i,pois[i]] for i in range(16)])
    rzavg = np.average([rzs_rho[i,pois[i]] for i in range(16)])
    info.append("%.2f, %.2f"%(ravg,rzavg))

table = [index, distorsion, info]
print(tabulate(list(zip(*table)), tablefmt="latex_raw", floatfmt=".2f"))

devices = ["ble_a", "ble_b", "ble_b_retake", "ble_c", "ble_c_retake", "ble_d", "ble_e", "ble_e_retake", "ble_f", "ble_f_dap"]
names = ["A", "B", "Br", "C", "Cr", "D", "E", "Er", "F", "Fd"]
repetitions = [8, 2, 2, 2, 2, 2, 2, 2, 2, 2]
#norms = ["", "_nonorm", "_norm2", "_norm12"]
norms = ["", "_nonorm"]
#colors = ["red", "green", "blue", "orange"]
colors = ["green", "red"]

def measure(names, devices, repetitions, norm, normattack):
    xlabels = []
    distortion = []
    information = []
    ranks_same = []
    ranks_reuse = []
    confidence_p = []
    confidence_rz = []
    j = 0
    for name, device, repetition in zip(names, devices, repetitions):
        for i in range(repetition):
            dir = "$FOLDER/%s/%d/"%(device, i)
            mean_trace, means, stds, pois, rs_rho, rzs_rho = load_profile(path.join(dir,"false/r%s"%norm))
            
            rs = []
            ps = []
            for ref,mean in zip(reference, means):
                r, p = pearsonr(ref, mean)
                rs.append(r)
                ps.append(p)
            r = np.average(rs)
            p = -np.log10(np.average(ps))
            confidence_p.append(p)

            ravg = np.average([rs_rho[k,pois[k]] for k in range(16)])
            rzsavg = np.average([rzs_rho[k,pois[k]] for k in range(16)])
            confidence_rz.append(rzsavg)

            xlabels.append("%s%d"%(name,i))
            distortion.append(r)
            information.append(ravg)
            j += 1
            
            print dir
            with open(path.join(dir, "same%s.txt"%normattack), "a+") as f:
                rank_same = f.readline()[2:]
                if rank_same == "":
                    rank_same = 30
                else:
                    rank_same = float(rank_same)
            with open(path.join(dir, "reuse%s.txt"%normattack), "a+") as f:
                rank_reuse = f.readline()[2:]
                if rank_reuse == "":
                    rank_reuse = 30
	        else:
                    rank_reuse = float(rank_reuse)
	        ranks_same.append(rank_same)
            ranks_reuse.append(rank_reuse)
    
    return confidence_p, confidence_rz, information, distortion, xlabels, ranks_same, ranks_reuse

p, rz, information, distortion, xlabels, rank_same, rank_reuse = measure(names, devices, repetitions, "", "")
p_nonorm, rz_nonorm, information_nonorm, distortion_nonorm, xlabels, rank_same_nonorm, rank_reuse_nonorm = measure(names, devices, repetitions, "_nonorm", "_nonorm")
x, x, information_average_bytes, distortion_average_bytes, xlabels, rank_same_average_bytes, rank_reuse_average_bytes = measure(names, devices, repetitions, "", "_average_bytes")
x, x, 
x, x, information_average_bytes_norm2, distortion_average_bytes_norm2, xlabels, rank_same_average_bytes_norm2, rank_reuse_average_bytes_norm2 = measure(names, devices, repetitions, "_norm2", "_average_bytes_norm2")
x, x, information_average_bytes_norm12, distortion_average_bytes_norm12, xlabels, rank_same_average_bytes_norm12, rank_reuse_average_bytes_norm12 = measure(names, devices, repetitions, "_norm12", "_average_bytes_norm12")

for a, b, name in zip(p,rz,names):
    print name, a, b
for a, b, name in zip(p_nonorm,rz_nonorm,names):
    print name, a, b

plt.title("Similarity")
plt.ylabel("r(Px,PA0)")
plt.plot(distortion, 'g+', label="Normalized", markersize=15)
plt.plot(distortion_nonorm, 'r*', label="Raw", markersize=15)
plt.xticks(range(len(xlabels)), xlabels, rotation=45)
plt.legend(loc='lower left')
plt.show()

plt.title("Correlation")
plt.ylabel("r(Px)")
plt.plot(information, 'g+', label="Normalized", markersize=15)
plt.plot(information_nonorm, 'r*', label="Raw", markersize=15)
plt.xticks(range(len(xlabels)), xlabels, rotation=45)
plt.legend(loc='lower left')
plt.show()

plt.ylabel("Log2(Key Rank)")
plt.title("Key Rank for different cases")

rank_reuse = [np.nan if r == 30 else r for r in rank_reuse]
rank_reuse_nonorm = [np.nan if r == 30 else r for r in rank_reuse_nonorm]
rank_reuse_average_bytes = [np.nan if r == 30 else r for r in rank_reuse_average_bytes]
rank_same_average_bytes = [np.nan if r == 30 else r for r in rank_same_average_bytes]
rank_reuse_average_bytes_norm2 = [np.nan if r == 30 else r for r in rank_reuse_average_bytes_norm2]
#rank_reuse_average_bytes_norm12 = [np.nan if r == 30 else r for r in rank_reuse_average_bytes_norm12]
rank_same_average_bytes_norm2 = [np.nan if r == 30 else r for r in rank_same_average_bytes_norm2]
rank_same_average_bytes_norm12 = [np.nan if r == 30 else r for r in rank_same_average_bytes_norm12]

plt.plot(rank_reuse, 'g+-', label="Reuse (Normalized)")
plt.plot(rank_reuse_nonorm, 'r*--', label="Reuse (Raw)")
plt.plot(rank_reuse_average_bytes, 'v-', label="Reuse (Normalized + Combine)")

plt.plot(rank_reuse_average_bytes_norm2, 'c-', label="Reuse (Z-Score + Combine)")
plt.plot(rank_same_average_bytes, 'o-', label="Same (Normalized + Combine)")

plt.xticks(range(len(xlabels)), xlabels, rotation=45)
plt.legend(loc='lower left')
plt.show()

#plt.plot(rank_reuse_nonorm, 'r*--', label="Reuse (Raw)")
#plt.plot(rank_reuse_average_bytes_norm2, 'c-', label="Reuse (Z-Score + Combine)")
#plt.plot(rank_reuse_average_bytes_norm12, 'g+-', label="Reuse (Normalized + Z-Score + Combine)")
#plt.plot(rank_reuse_average_bytes, 'v-', label="Reuse (Normalized + Combine)")
#
#plt.xticks(range(len(xlabels)), xlabels, rotation=45)
#plt.legend(loc='lower left')
#plt.show()

END

