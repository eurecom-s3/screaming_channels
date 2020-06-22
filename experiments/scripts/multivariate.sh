#!/urs/bin/bash

# Giovanni Camurati
# Commands to reproduce attack data in the paper

#SC=/path/to/screaming_channels
#TRACES_CHES20/ches20=path/to/ches20_tracess

# Go in the right place
cd $SC/experiments

# Profile
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/template_tx_500/ \
--start-point 400 --end-point 700 --num-traces 5000 profile /tmp/5000 \
--variable p_xor_k --pois-algo r --num-pois 15 --poi-spacing 1

## Attack
for i in $(seq 250 -10 50); do \
	echo "number $i"; \
	sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ \
	--start-point 400 --end-point 700 --num-traces $i --bruteforce attack /tmp/5000 --variable p_xor_k \
	--average-bytes
done \
| grep -E "number|BYTES: 16|actual rounded|time enum|time preprocessing" \
| sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0\ntime enum: 0\ntime preprocessing : 0/' \
| awk '{ printf "%s ", $0 } !(NR%4) { print "" }' \
| awk '{print $2, $5, $8, $12}' OFS="," \
> bruteforce_averaged.csv

for i in $(seq 250 -10 50); do \
	echo "number $i"; \
	sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ \
	--start-point 400 --end-point 700 --num-traces $i --bruteforce attack /tmp/5000 --variable p_xor_k; \
done \
| grep -E "number|BYTES: 16|actual rounded|time enum|time preprocessing" \
| sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0\ntime enum: 0\ntime preprocessing : 0/' \
| awk '{ printf "%s ", $0 } !(NR%4) { print "" }' \
| awk '{print $2, $5, $8, $12}' OFS="," \
> bruteforce_independent.csv

for pois in $(seq 1 5); do \
echo "poi $pois";
for i in $(seq 250 -10 50); do \
echo "number $i"; \
sc-attack --norm --data-path $TRACES_CHES20/ches20/hackrf_10cm/attack_tx_500/ \
--start-point 400 --end-point 700 --num-traces $i --bruteforce attack /tmp/5000 --variable p_xor_k \
--attack-algo pdf --num-pois $pois --pooled-cov; \
done \
| grep -E "number|BYTES: 16|actual rounded|time enum|time preprocessing" \
| sed 's/NUMBER OF CORRECT BYTES: 16/actual rounded: xx0\ntime enum: 0\ntime preprocessing : 0/' \
| awk '{ printf "%s ", $0 } !(NR%4) { print "" }' \
| awk '{print $2, $5, $8, $12}' OFS="," \
> bruteforce_pooled_$pois.csv; \
done

# Plot Figure 13
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

x = []
y = []
z = []

with open('bruteforce_independent.csv','r') as csvfile:
    plots = csv.reader(csvfile, delimiter=',')
    for i,row in enumerate(plots):
        x.append(int(row[0]))
        y.append(float(row[1][2:]))
        z.append(float(row[2]) + float(row[3]))
x = np.array(x)
y = np.array(y)
z = np.array(z)

x2 = [[] for _ in range(7)]
y2 = [[] for _ in range(7)]
z2 = [[] for _ in range(7)]

for poi in range(1,6):
    with open('bruteforce_pooled_%d.csv'%poi,'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        for row in plots:
            x2[poi].append(int(row[0]))
            y2[poi].append(float(row[1][2:]))
    	    z2[poi].append(float(row[2]) + float(row[3]))
    x2[poi] = np.array(x2[poi])
    y2[poi] = np.array(y2[poi])
    z2[poi] = np.array(z2[poi])


plt.plot(x,y, label="profiled correlation",linewidth=5.0,markersize=15)
styles = ["","--+","--o","--","-.","--*"]
for poi in range(1,6):
    plt.plot(x2[poi],y2[poi],styles[poi],label="template pooled %d pois"%poi,linewidth=5.0,markersize=15)

plt.xlabel('Number of Traces')
plt.ylabel('Log2(Key Rank)')
plt.title('Key Rank vs. Trace Number')
plt.legend(loc='upper right')
plt.show()

#plt.plot(x, x+z, '--*', label="profiled_correlation")
#for poi in range(2,6):
#    plt.plot(x2[poi],x2[poi]+z2[poi],styles[poi], label="template pooled %d pois"%poi)
#plt.xlabel('Number of Traces')
#plt.ylabel('Collection + Enumeration Time (s)')
#plt.title('Time for a Successful Attack')
#plt.legend()
#plt.show()
END

