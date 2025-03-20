import sqlite3
import datetime
from protocol.config import SimulationConfig

# ---------------------------
# Database Setup
# ---------------------------
def create_results_table(db_path="simulation_results.db"):
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
            commander_is_traitor BOOLEAN
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

    cursor.execute('''
        INSERT INTO experiment_results (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, traitor_indices, M, N, num_traitors, commander_is_traitor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (experiment_name, swept_parameter, swept_value, shot_id, commands_sent, initial_result, intermediate_result, final_result, " ".join(traitor_inds), config.M, config.N, len(config.TRAITOR_INDICES), config.COMMANDER_IS_TRAITOR))

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


# ---------------------------
# Example: Run the Sweep
# ---------------------------
if __name__ == "__main__":
    # create_results_table()

    shots = fetch_sweep_shots("exp_M_sweep4")
    for shot in shots:
        print(shot)
