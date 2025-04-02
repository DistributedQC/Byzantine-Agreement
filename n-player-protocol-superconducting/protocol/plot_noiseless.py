import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import re
import numpy as np
from collections import defaultdict

# Read and parse the data
file_path = 'noiseless_simulation_results.txt'

with open(file_path, 'r') as file:
    lines = file.readlines()

pattern = re.compile(r'M=(\d+), N=(\d+), Loyal_Aborts=(\d+) \| Lieutenant Decisions = \[(.*)\]')
abort_data = defaultdict(lambda: defaultdict(list))

for line in lines:
    match = pattern.search(line)
    if match:
        M, N, loyal_aborts, _ = match.groups()
        M, N, loyal_aborts = int(M), int(N), int(loyal_aborts)
        loyal_lieutenants = (2 * N) // 3 - 1
        abort_ratio = loyal_aborts / loyal_lieutenants if loyal_lieutenants > 0 else 0
        abort_data[M][N].append(abort_ratio)

# Aggregate data
aggregated_data = []
for M in sorted(abort_data.keys()):
    for N in sorted(abort_data[M].keys()):
        abort_list = abort_data[M][N]
        segment_size = max(1, len(abort_list) // 5)

        segment_means = [np.mean(abort_list[i:i+segment_size]) for i in range(0, len(abort_list), segment_size)]

        mean_abort = np.mean(segment_means) * 100
        std_abort = np.std(segment_means) * 100 / np.sqrt(5)

        aggregated_data.append({'M': M, 'N': N, 'percent_aborts': mean_abort, 'percent_std': std_abort})

# Create DataFrame for plotting
df = pd.DataFrame(aggregated_data)

# Plotting
sns.set(style='whitegrid')
plt.figure(figsize=(10, 6))

# Plot curves for each value of M
for M, group_df in df.groupby('M'):
    plt.errorbar(group_df['N'], group_df['percent_aborts'], yerr=group_df['percent_std'], label=f'M={M}', capsize=5, marker='o')

plt.xlabel('Number of Players (N)', fontsize=14)
plt.ylabel('Pr(Loyal Defection)', fontsize=14)
plt.title('Probability of Loyal Defection Across SC Wire Lengths', fontsize=16)
plt.legend(title='Entangled Pairs per Lieutenant (M)')
plt.tight_layout()
plt.savefig('plot_noiseless_2.png', dpi=300)
plt.show()