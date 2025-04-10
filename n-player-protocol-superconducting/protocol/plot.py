import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create plots directory if it doesn't exist
os.makedirs('plots', exist_ok=True)

# Load CSV files
loyal_df = pd.read_csv('loyal_commander_simulation_results.csv')
traitor_df = pd.read_csv('traitor_commander_simulation_results.csv')

# Define NOISE_TIME intervals explicitly
noise_intervals = [0.00005 * factor for factor in [0.000001, 0.00001, 0.0001, 0.001, 0.01, 0.1, 1]]

# Filter dataframes by noise_intervals
loyal_df = loyal_df[loyal_df['NOISE_TIME'].isin(noise_intervals)]
traitor_df = traitor_df[traitor_df['NOISE_TIME'].isin(noise_intervals)]

# Calculate ratio for plotting
loyal_df['Correct_Ratio'] = loyal_df['Correct_Count'] / (loyal_df['N'] - loyal_df['Num_Traitors'] - 1)
traitor_df['Correct_Ratio'] = traitor_df['Abort_Count'] / (traitor_df['N'] - traitor_df['Num_Traitors'] - 1)

# Define a plotting function with improved colors
def plot_results(df, x_col, title, filename):
    plt.figure(figsize=(8, 6))
    palette = sns.color_palette("husl", len(df['NOISE_TIME'].unique()))
    sns.lineplot(
        data=df,
        x=x_col,
        y='Correct_Ratio',
        hue='NOISE_TIME',
        marker='o',
        err_style='bars',
        palette=palette
    )
    plt.title(title)
    if "Loyal" in title:
        plt.ylabel('Pr(Lieutenant agrees)')
    else:
        plt.ylabel('Pr(Lieutenant aborts)')

    plt.xlabel(x_col)
    plt.legend(title='NOISE_TIME', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f'plots/{filename}', bbox_inches='tight')
    plt.close()

# Plot #1: Loyal, X-axis: N
plot_results(loyal_df, 'N', 'Loyal Commander (by N)', 'loyal_commander_by_N.png')

# Plot #2: Loyal, X-axis: M
plot_results(loyal_df, 'M', 'Loyal Commander (by M)', 'loyal_commander_by_M.png')

# Plot #3: Loyal, X-axis: Num_Traitors
plot_results(loyal_df, 'Num_Traitors', 'Loyal Commander (by Num_Traitors)', 'loyal_commander_by_Num_Traitors.png')

# Plot #4: Traitor, X-axis: M
plot_results(traitor_df, 'M', 'Traitor Commander (by M)', 'traitor_commander_by_M.png')
