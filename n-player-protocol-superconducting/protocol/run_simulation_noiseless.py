import aqnsim
from protocol.simulation import setup_network

def run():
    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=setup_network,
        logging_level=20,
        log_to_file=False
    )
    results = run_simulation()
    # Here you can add more logic, logging, analysis, saving to file, etc.
    latest_results = {k: v[-1] if v else None for k, v in results.items()}

    correct_decisions = 0
    incorrect_decisions = 0
    N = 1

    loyal_commander_order = latest_results['Alice'][0]['orders'][0] # loyal orders all same

    lieutenant_decisions = []

    for key, value in latest_results.items(): # PRINT LIEUTENANT INFO
        if "orders" not in latest_results[key][0]: 
            N += 1
            if not latest_results[key][0]['is_traitor']:
                lieutenant_decisions.append(latest_results[key][0]['final_decision'])
                if latest_results[key][0]['final_decision'] == loyal_commander_order:
                    correct_decisions +=1
                else:
                    incorrect_decisions +=1
            else:
                lieutenant_decisions.append(f"Traitor")


    M = int(len(latest_results["Alice"][0]['BV']) / (N-1))

    with open("noiseless_simulation_2_results.txt", "a") as file:
        file.write(f"M={M}, N={N}, Loyal_Aborts={incorrect_decisions} | Lieutenant Decisions = {lieutenant_decisions}\n")


if __name__ == "__main__":
    run()
