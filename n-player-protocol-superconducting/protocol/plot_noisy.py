import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import re
from collections import defaultdict

noisy_file_path = 'noisy_simulation_2_results.txt'
with open(noisy_file_path, 'r') as file:
    noisy_lines = file.readlines()

noisy_pattern = re.compile(r'M=(\d+), N=(\d+), T1_INTERVALS = (\d+ / \d+) Loyal_Aborts=(\d+) \| Lieutenant Decisions = \[(.*)\]')
noisy_abort_data = defaultdict(lambda: defaultdict(list))

for line in noisy_lines:
    match = noisy_pattern.search(line)
    if match:
        _, N, T1_interval, loyal_aborts, _ = match.groups()
        N, loyal_aborts = int(N), int(loyal_aborts)
        loyal_lieutenants = (N - 1) - (N/3)  # Exclude the traitor
        abort_ratio = loyal_aborts / loyal_lieutenants
        noisy_abort_data[T1_interval][N].append(abort_ratio)

noiseless_file_path = 'noiseless_simulation_2_results.txt'
with open(noiseless_file_path, 'r') as file:
    noiseless_lines = file.readlines()

noiseless_pattern = re.compile(r'M=(\d+), N=(\d+), Loyal_Aborts=(\d+) \| Lieutenant Decisions = \[(.*)\]')
noiseless_abort_data = defaultdict(list)

for line in noiseless_lines:
    match = noiseless_pattern.search(line)
    if match:
        M, N, loyal_aborts, _ = match.groups()
        if int(M) != 5 or int(N) == 36:
            continue
        N, loyal_aborts = int(N), int(loyal_aborts)
        loyal_lieutenants = (N - 1) - (N/3)
        abort_ratio = loyal_aborts / loyal_lieutenants
        noiseless_abort_data[N].append(abort_ratio)

def compute_mean_of_means(data_list):
    segment_size = max(1, len(data_list) // 5)
    means = [np.mean(data_list[i:i+segment_size]) for i in range(0, len(data_list), segment_size)]
    return np.mean(means) * 100, np.std(means) * 100 / np.sqrt(5)

aggregated_noisy_data = []
for T1_interval in sorted(noisy_abort_data.keys(), key=lambda x: eval(x)):
    if(eval(T1_interval) < 1/8):
        continue
    for N in sorted(noisy_abort_data[T1_interval].keys()):
        abort_list = noisy_abort_data[T1_interval][N]
        mean_abort, std_abort = compute_mean_of_means(abort_list)
        aggregated_noisy_data.append({'Condition': f'{eval(T1_interval):.3f} T1', 'N': N,
                                      'percent_aborts': mean_abort, 'percent_std': std_abort})

aggregated_noiseless_data = []
for N in sorted(noiseless_abort_data.keys()):
    abort_list = noiseless_abort_data[N]
    mean_abort, std_abort = compute_mean_of_means(abort_list)
    aggregated_noiseless_data.append({'Condition': 'Noiseless', 'N': N,
                                      'percent_aborts': mean_abort, 'percent_std': std_abort})

df_combined = pd.DataFrame(aggregated_noisy_data + aggregated_noiseless_data)

sns.set(style='whitegrid')
plt.figure(figsize=(10, 6))

for condition, group_df in df_combined.groupby('Condition'):
    plt.errorbar(group_df['N'], group_df['percent_aborts'], yerr=group_df['percent_std'], label=condition, capsize=5, marker='o')

plt.xlabel('Number of Players (N)', fontsize=14)
plt.ylabel('Pr(Loyal Defection)', fontsize=14)
plt.title('Probability of Loyal Defection Across SC Wire Lengths', fontsize=16)
plt.legend(title='Wire Time (T1 intervals)')
plt.tight_layout()
plt.savefig('plot_noisy_2.png', dpi=300)
plt.show()
