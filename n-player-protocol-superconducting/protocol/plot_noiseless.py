import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

# Create plots directory if it doesn't exist
os.makedirs('noiseless_plots', exist_ok=True)

# Load CSV files
loyal_df = pd.read_csv('noiseless_loyal_commander_simulation_results.csv')
traitor_df = pd.read_csv('noiseless_traitor_commander_simulation_results.csv')

# Calculate ratio for plotting
loyal_df['Correct_Ratio'] = loyal_df['Correct_Count'] / (loyal_df['N'] - loyal_df['Num_Traitors'] - 1)
traitor_df['Abort_Ratio'] = traitor_df['Abort_Count'] / (traitor_df['N'] - traitor_df['Num_Traitors'] - 1)

# Prepare data for 3D surface plot
x = loyal_df['M']
y = loyal_df['N']
z = loyal_df['Correct_Ratio']

xi = np.linspace(x.min(), x.max(), 100)
yi = np.linspace(y.min(), y.max(), 100)
xi, yi = np.meshgrid(xi, yi)
zi = griddata((x, y), z, (xi, yi), method='cubic')

# Plot #1: Loyal, 3D Surface Plot (M, N, Correct_Ratio)
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')
surf = ax.plot_surface(xi, yi, zi, cmap='viridis', edgecolor='none')
ax.set_xlabel('M')
ax.set_ylabel('N')
ax.set_zlabel('Pr(Lieutenant agrees)')
ax.set_title('Loyal Commander: Correct Ratio by M and N')
fig.colorbar(surf, shrink=0.5, aspect=5)
plt.tight_layout()
plt.savefig('noiseless_plots/loyal_commander_3d_surface.png', bbox_inches='tight')
plt.close()

# Plot #2: Loyal, X-axis: Num_Traitors
plt.figure(figsize=(8, 6))
sns.lineplot(
    data=loyal_df,
    x='Num_Traitors',
    y='Correct_Ratio',
    marker='o',
    color='blue',
    err_style='bars'
)
plt.title('Loyal Commander (by Num_Traitors)')
plt.ylabel('Pr(Lieutenant agrees)')
plt.xlabel('Num_Traitors')
plt.grid(True)
plt.tight_layout()
plt.savefig('noiseless_plots/loyal_commander_by_Num_Traitors.png', bbox_inches='tight')
plt.close()

# Plot #3: Traitor, X-axis: M
plt.figure(figsize=(8, 6))
sns.lineplot(
    data=traitor_df,
    x='M',
    y='Abort_Ratio',
    marker='o',
    color='blue',
    err_style='bars'
)
plt.title('Traitor Commander (by M)')
plt.ylabel('Pr(Lieutenant aborts)')
plt.xlabel('M')
plt.grid(True)
plt.tight_layout()
plt.savefig('noiseless_plots/traitor_commander_by_M.png', bbox_inches='tight')
plt.close()