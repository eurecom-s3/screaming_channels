#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

#git checkout ches20

# T-test
for i in $(seq 10 10 900); do \
	echo "number $i"; \
        sc-attack --num-key-bytes 1 --norm \
        --data-path $TRACES_CHES20/ches20/eurecom_corridor_060719/10m/s3net/fixed_vs_fixed_500/ \
        --num-traces $i profile --pois-algo t --variable fixed_vs_fixed /tmp
done \
| awk '{ printf "%s ", $0 } !(NR%2) { print "" }' \
| awk '{print $2, $4, $6}' OFS="," \
> ttest_10m.csv

for i in $(seq 10 10 2000); do \
	echo "number $i"; \
        sc-attack --num-key-bytes 1 --norm \
        --data-path $TRACES_CHES20/ches20/eurecom_corridor_070719/34m/s3net/fixed_vs_fixed/ \
        --num-traces $i profile --pois-algo t --variable fixed_vs_fixed /tmp
done \
| awk '{ printf "%s ", $0 } !(NR%2) { print "" }' \
| awk '{print $2, $4, $6}' OFS="," \
> ttest_34m.csv


# Plot
python << END
import numpy as np
import matplotlib.pyplot as plt
import csv

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

types = ["10m", "34m"]
for style, type in zip(["-.","-*"],types):
    n = []
    t = []
    p = []
    with open('ttest_%s.csv'%type,'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            n.append(int(row[0]))
            t.append(float(row[1]))
            p.append(float(row[2]))
    #plt.plot(n, t, label=type)
    if type == "s3net":
        type = "network"
    plt.plot(n, -np.log10(p), style, label=type,linewidth=5.0,markersize=15)
plt.axhline(y=-np.log10(0.00001), linestyle='--',color='g', label="p=0.00001",linewidth=5.0,markersize=15)

plt.title('Leakage Detection')
plt.ylabel('-log10(p)')
plt.xlabel('Number of Traces')
plt.legend()
plt.show()
END

#plot 2
sc-attack --plot --num-key-bytes 1 --norm --data-path $TRACES_CHES20/ches20/eurecom_corridor_070719/34m/s3net/fixed_vs_fixed/ --num-traces 4000 profile --pois-algo t --variable fixed_vs_fixed /tmp/s3net
