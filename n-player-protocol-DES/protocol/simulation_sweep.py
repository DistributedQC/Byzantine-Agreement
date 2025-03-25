import aqnsim
from protocol.distributor import Distributor, DistributorProtocol
from protocol.lieutenants import Lieutenant, LieutenantProtocol
from protocol.commander import Commander, CommanderProtocol
from protocol.simulation import setup_network
import random
import time
import numpy as np
import sqlite3
import datetime
from protocol.config import SimulationConfig, NoiseType
from protocol.simulation import print_game_stats
from results.database import fetch_sweep_shots, store_sweep_result



def run_sweep2(sweep_param, sweep_vals, exp_name, num_shots):
    run_sim_fn = aqnsim.generate_run_simulation_fn(setup_sim_fn=setup_network, logging_level=0, log_to_file=False)
    
    for shot in range(1, num_shots+1):
        res = aqnsim.run_simulations(run_sim_fn, sweep_vals)
        for pt in res:
            latest_results = {k: v[-1] if v else None for k, v in pt.items()}
            print(latest_results)
            commands_sent_bool = latest_results['Alice'][0]['orders']
            commands_sent = ["1" if i else "0" for i in commands_sent_bool]
            initial_votes = []
            intermediate_votes = []
            final_votes = []
            is_traitor = []
            
            # This is all just logs to the console
            print("SHOT", shot)
            print("M", latest_results["M"][0])
            print("NOISE", latest_results["Config"][0].NOISE_VALS)
            print("Num_Traitors", len(latest_results["Config"][0].TRAITOR_INDICES))
            print()
            print(f"Commander's orders: {commands_sent}")
            print(f"Commander is {'TRAITOR' if latest_results['Alice'][0]['is_traitor'] else 'loyal'}")
            print()
            print("Lieutenant Results:")
            for key, value in latest_results.items():
                if (key == "M" or key == "Config"):
                    continue
                if "orders" not in latest_results[key][0]: 
                    print(f"Traitor: {'Yes' if latest_results[key][0]['is_traitor'] else 'No'} {latest_results[key][0]['final_decision']}")
                    print(f"  Received Order: {latest_results[key][0]['received_order']}")
                    initial_votes.append("1" if latest_results[key][0]['initial_decision'] == True else "0" if latest_results[key][0]['initial_decision'] == False else "N")
                    intermediate_votes.append("1" if latest_results[key][0]['intermediate_decision'] == True else "0" if latest_results[key][0]['intermediate_decision'] == False else "N")
                    final_votes.append("1" if latest_results[key][0]['final_decision'] == True else "0" if latest_results[key][0]['final_decision'] == False else "N")
                    is_traitor.append("1" if latest_results[key][0]['is_traitor'] else "0")
            print("===============================================\n")
            # This is storing the traitor sweep to simulation_results.db
            # store_sweep_result(exp_name, sweep_param, str(len(latest_results["Config"][0].TRAITOR_INDICES)), shot, " ".join(commands_sent), " ".join(initial_votes), " ".join(intermediate_votes), " ".join(final_votes), latest_results["Config"][0])
            
            # This is storing the puali sweep data to noisy_simulation_results.db
            store_sweep_result(exp_name, sweep_param, str(len(latest_results["Config"][0].TRAITOR_INDICES)), shot, " ".join(commands_sent), " ".join(initial_votes), " ".join(intermediate_votes), " ".join(final_votes), latest_results["Config"][0], db_path="noisy_simulation_results.db")
        #   pt[sweep_param][0][0]
    
    # print(res[0])
    # print(res)
    # for run in res:
    #     print(run["M"])
    # print(res[0]["M"])
        
if __name__ == "__main__":
    old_time = time.time()
    
    # This is the code for the traitor sweep
    # params = [[SimulationConfig(M=i, COMMANDER_IS_TRAITOR=False, LOYAL_COMMANDER_ORDER=(True if random.random() < 0.5 else False))] for i in [4, 8, 12, 16, 24, 32, 48, 64, 80, 96, 112]] # , 32, 64, 128, 192, 256, 384, 512
    # for m in [16, 32, 48, 64, 80, 96, 112, 128, 144, 160]:
    #     start_time = time.time()
    #     params = [[SimulationConfig(M=m, 
    #                                 COMMANDER_IS_TRAITOR=False, 
    #                                 LOYAL_COMMANDER_ORDER=(True if random.random() < 0.5 else False), 
    #                                 LIEUTENANT_NAMES=[str(j) for j in range(10)],
    #                                 TRAITOR_INDICES=random.sample(range(10), i)
    #                                 )] for i in range(10)]
    #     run_sweep2("Num Traitors", params, f"Traitors_Sweep_1_M_{m}", num_shots=50)
    #     print(time.time() - start_time)
    #     start_time = time.time()
    
    # This is the pauli sweep - this is what's taking 48+ hours on my computer
    p0 = 1-.025
    params = []
    for pct1 in np.arange(0, 1.01, .1):
        for pct2 in np.arange(0, 1.01, .1):
            p1 =  (1-p0) * pct1
            p2 = (1-p0-p1) * pct2
            p3 = (1-p0-p1-p2)
            params.append([SimulationConfig(COMMANDER_IS_TRAITOR=False,
                                            LOYAL_COMMANDER_ORDER=(True if random.random() < 0.5 else False),
                                            M=112,
                                            LIEUTENANT_NAMES=[str(j) for j in range(10)],
                                            TRAITOR_INDICES=random.sample(range(10), 2),
                                            NOISE_TYPE=NoiseType.Pauli,
                                            NOISE_VALS=[p0, p1, p2, p3])])
            
    run_sweep2("Pauli Noise", params, f"Pauli_Sweep_1", num_shots=50)
    
        
    print(time.time() - old_time)
    
    
    
    