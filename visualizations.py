import matplotlib.pyplot as plt
import numpy as np
import sqlite3

def fetch_sweep_shots(experiment_name, t_val, db_path="simulation_results.db"):
    """Retrieves all shots for a given parameter sweep value."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info(experiment_results)")
    columns = cursor.fetchall()
    # print([c[1] for c in columns])

    cursor.execute("SELECT * FROM experiment_results WHERE experiment_name = ? AND swept_value = ?", 
                   (experiment_name, t_val))
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

def traitors_sweep():
    for t in range(10):
        m_vals = [16, 32, 48, 64, 80, 96, 112, 128, 144]
        # s_vals = np.zeros(len(m_vals))
        s_vals = [[] for _ in range(len(m_vals))]
        for i, m in enumerate(m_vals):
            name = f"Traitors_Sweep_1_M_{m}"
            shots = fetch_sweep_shots(name, float(t))
            
            cnt = 0
            avg = 0
            for shot in shots:
                # print(shot)
                param_val = float(shot[5])
                traitors = shot[10].split()
                final_votes = shot[9].split()
                commands_sent = shot[6].split()
                avg += return_metric(commands_sent, final_votes, traitors)[0]
                cnt += 1

                if (cnt == 10):
                    s_vals[i].append(avg / 10.)
                    cnt = 0
                    avg = 0
                    
        averages = [np.average(i) for i in s_vals]
        errs = [np.std(i) for i in s_vals]
        plt.errorbar(m_vals, averages, yerr=errs, capsize=3, ecolor="black", label=f"T/N={t / 10}")
    plt.grid()
    plt.xticks(list(range(0, 160, 16)))
    plt.xlabel("M")
    plt.ylabel("Success")
    plt.title("Effect of Traitor Density on Optimal M for Success")
    plt.legend()
    plt.show()

def M_sweep():
    m_vals = [4, 8, 12, 16, 24, 32, 48, 64, 80, 96, 112]
    s_vals = [[] for _ in range(len(m_vals))]
    for i, m in enumerate(m_vals):
        shots = fetch_sweep_shots("M_sweep_real_fine_1", float(m))
        
        cnt = 0
        avg = 0
        for shot in shots:
            # print(shot)
            param_val = float(shot[5])
            traitors = shot[10].split()
            final_votes = shot[9].split()
            commands_sent = shot[6].split()
            avg += return_metric(commands_sent, final_votes, traitors)[0]
            cnt += 1

            if (cnt == 10):
                s_vals[i].append(avg / 10.)
                cnt = 0
                avg = 0
                    
    averages = [np.average(i) for i in s_vals]
    errs = [np.std(i) for i in s_vals]
    plt.errorbar(m_vals, averages, yerr=errs, capsize=3, ecolor="black")
    plt.grid()
    plt.xlabel("M")
    plt.ylabel("Success")
    plt.title("Effect of number of Qubit Tuples (M) on Success")
    # plt.legend()
    plt.show()

# traitors_sweep()

M_sweep()