import aqnsim
from protocol.distributor import Distributor, DistributorProtocol
from protocol.lieutenants import Lieutenant, LieutenantProtocol
from protocol.commander import Commander, CommanderProtocol
from protocol.simulation import setup_network
import random
import time
import sqlite3
import datetime
from protocol.config import SimulationConfig
from protocol.simulation import print_game_stats
from results.database import fetch_sweep_shots, store_sweep_result



def run_sweep2(sweep_param, sweep_vals, exp_name, num_shots):
    run_sim_fn = aqnsim.generate_run_simulation_fn(setup_sim_fn=setup_network, logging_level=0, log_to_file=False)
    
    for shot in range(1, num_shots+1):
        res = aqnsim.run_simulations(run_sim_fn, sweep_vals)
        for pt in res:
            latest_results = {k: v[-1] if v else None for k, v in pt.items()}
            commands_sent_bool = latest_results['Alice'][0]['orders']
            commands_sent = ["1" if i else "0" for i in commands_sent_bool]
            initial_votes = []
            intermediate_votes = []
            final_votes = []
            is_traitor = []
            
            print("SHOT", shot)
            print("M", latest_results["M"][0])
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
                    initial_votes.append("1" if latest_results[key][0]['initial_decision'] == True else "0" if latest_results[key][0]['initial_decision'] == False else "N")
                    intermediate_votes.append("1" if latest_results[key][0]['intermediate_decision'] == True else "0" if latest_results[key][0]['intermediate_decision'] == False else "N")
                    final_votes.append("1" if latest_results[key][0]['final_decision'] == True else "0" if latest_results[key][0]['final_decision'] == False else "N")
                    is_traitor.append("1" if latest_results[key][0]['is_traitor'] else "0")
            print("===============================================\n")
            store_sweep_result(exp_name, sweep_param, pt[sweep_param][0][0], shot, " ".join(commands_sent), " ".join(initial_votes), " ".join(intermediate_votes), " ".join(final_votes), latest_results["Config"][0])
        
    
    # print(res[0])
    # print(res)
    # for run in res:
    #     print(run["M"])
    # print(res[0]["M"])
        
if __name__ == "__main__":
    start_time = time.time()
    params = [[SimulationConfig(M=i, COMMANDER_IS_TRAITOR=False, LOYAL_COMMANDER_ORDER=(True if random.random() < 0.5 else False))] for i in [4, 8, 16, 32, 64, 128, 192, 256, 384, 512]] # , 32, 64, 128, 192, 256, 384, 512
    run_sweep2("M", params, f"M_sweep_real_1", num_shots=50)
    print(time.time() - start_time)