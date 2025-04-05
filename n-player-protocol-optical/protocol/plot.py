import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

csv_file_path = 'loyal_commander_simulation_results.csv'
df = pd.read_csv(csv_file_path, skipinitialspace=True)

df['Loyal_Lieutenants'] = df['N'] - df['Num_Traitors'] - 1  # exclude traitors and commander
df['Abort_Ratio'] = df['Abort_Count'] / df['Loyal_Lieutenants']

grouped_df = df.groupby(['Channel_Length', 'M']).agg(
    Mean_Abort_Ratio=('Abort_Ratio', 'mean'),
    Std_Error=('Abort_Ratio', lambda x: np.std(x, ddof=1) / np.sqrt(len(x)))
).reset_index()

sns.set(style='whitegrid')
plt.figure(figsize=(10, 6))

for M_val, sub_df in grouped_df.groupby('M'):
    plt.errorbar(
        sub_df['Channel_Length'],
        sub_df['Mean_Abort_Ratio'] * 100,  # percentage
        yerr=sub_df['Std_Error'] * 100,
        marker='o',
        capsize=5,
        label=f'M = {M_val}'
    )

plt.xscale('log', base=2)
plt.xlabel('Channel Length', fontsize=14)
plt.ylabel('Abort Ratio (%)', fontsize=14)
plt.title('Abort Ratio vs. Channel Length', fontsize=16)
plt.legend(title='M')
plt.tight_layout()

plt.savefig('abort_ratio_vs_channel_length.png', dpi=300)
plt.show()
