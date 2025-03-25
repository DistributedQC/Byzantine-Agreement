import sqlite3
import datetime
import numpy as np
from protocol.config import SimulationConfig
import matplotlib.pyplot as plt

# ---------------------------
# Database Setup
# ---------------------------
def create_results_table(db_path="noisy_simulation_results.db"):
    """Creates the SQLite database table if it does not already exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS experiment_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_name TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            shot_id INTEGER,
            swept_parameter TEXT,
            swept_value REAL,
            commands_sent TEXT,
            initial_result TEXT,
            intermediate_result TEXT,
            final_result TEXT,
            traitor_indices TEXT,
            M INTEGER,
            N INTEGER,
            num_traitors INTEGER,
            commander_is_traitor BOOLEAN,
            noise_type TEXT,
            noise_vals TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ---------------------------
# Store Results
# ---------------------------
def store_sweep_result(experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, config: SimulationConfig, db_path="simulation_results.db"):
    """Stores the result of a single shot for a given parameter sweep value."""
    traitor_inds = ["1" if i in config.TRAITOR_INDICES else "0" for i in range(config.NUM_LIEUTENANTS)]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # This is for the w/o noise database
    # cursor.execute('''
    #     INSERT INTO experiment_results (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, traitor_indices, M, N, num_traitors, commander_is_traitor)
    #     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    # ''', (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, " ".join(traitor_inds), config.M, config.N, len(config.TRAITOR_INDICES), config.COMMANDER_IS_TRAITOR))

    # This is for the w/ noise database
    cursor.execute('''
        INSERT INTO experiment_results (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, traitor_indices, M, N, num_traitors, commander_is_traitor, noise_type, noise_vals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, " ".join(traitor_inds), config.M, config.N, len(config.TRAITOR_INDICES), config.COMMANDER_IS_TRAITOR, config.NOISE_TYPE.value, " ".join([str(i) for i in config.NOISE_VALS])))


    conn.commit()
    conn.close()
    
# ---------------------------
# Query Data
# ---------------------------
def fetch_sweep_shots(experiment_name, db_path="simulation_results.db"):
    """Retrieves all shots for a given parameter sweep value."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info(experiment_results)")
    columns = cursor.fetchall()
    print([c[1] for c in columns])

    cursor.execute("SELECT * FROM experiment_results WHERE experiment_name = ?", 
                   (experiment_name,))
    rows = cursor.fetchall()

    conn.close()
    return rows

def return_metric(commands_sent, final_votes, traitors):
    # [success, traitor_success, abort]
    bad = False
    for i in range(len(commands_sent)):
        if (traitors[i] != "1" and commands_sent[i] != final_votes[i]):
            if (final_votes[i] != "N"):
                return np.array([0, 1, 0])
            else:
                bad = True
    if (bad):
        return np.array([0, 0, 1])
    return np.array([1, 0, 0]) 

def plot_experiment(shots):
    data = {}
    for shot in shots:
        param_val = float(shot[5])
        traitors = shot[10].split()
        final_votes = shot[9].split()
        commands_sent = shot[6].split()
        metric = return_metric(commands_sent, final_votes, traitors)
        if param_val in data:
            data[param_val] += metric
        else:
            data[param_val] = metric
    
    param_vals = []
    success_vals = []
    traitor_success_vals = []
    abort_vals = []
    for k, v in data.items():
        param_vals.append(k)
        success_vals.append(v[0] / np.sum(v))
        traitor_success_vals.append(v[1] / np.sum(v))
        abort_vals.append(v[2] / np.sum(v))
        
    # print(data[512.0])
        
    plt.plot(param_vals, success_vals, label="Success")
    plt.plot(param_vals, traitor_success_vals, label="Traitor Success")
    plt.plot(param_vals, abort_vals, label="Abort")
    
    plt.xlabel("M")
    plt.ylabel("%")
    plt.title("Effect of M on Metrics")
    
    plt.legend()
    
    

# ---------------------------
# Example: Run the Sweep
# ---------------------------
if __name__ == "__main__":
    # create_results_table()

    shots = fetch_sweep_shots("Traitors_Sweep_1_M_16")
    # for m in [16, 32, 48, 64, 80, 96, 112, 128, 144]:
    #     shots = fetch_sweep_shots(f"Traitors_Sweep_1_M_{m}", db_path="noisy_simulation_results.db") # "Traitors_Sweep_1_M_144"
    for shot in shots:
        print(shot)

    #     plot_experiment(shots)
    # plt.show()
