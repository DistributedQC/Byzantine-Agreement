import aqnsim
from protocol.simulation import setup_network

from protocol.config import (
    NOISE_TIME, T1_TIME
)

def run():

    max_parallel_simulations = 16 # User limit set by Delta, <1GB per simulation so can have 1 sim per core

    batch_parameters = [[i] for i in range(max_parallel_simulations)]

    def wrapped_setup_network(sim_context, dummy_arg):
        return setup_network(sim_context)

    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=wrapped_setup_network,
        logging_level=30,
        log_to_file=False
    )

    results = aqnsim.run_simulations(
        run_simulation_fn=run_simulation,
        batch_parameters=batch_parameters,         
        batch_kwargs=None,    
        n_workers=max_parallel_simulations,
        threads_per_worker=1,
        dask_logging_level=40
    )

    for sim_results in results:

        # Here you can add more logic, logging, analysis, saving to file, etc.
        latest_results = {k: v[-1] if v else None for k, v in sim_results.items()}

        Abort_Count = 0
        Correct_Count = 0
        Incorrect_Count = 0
        N = 1
        Num_Traitors = 0

        for key, value in latest_results.items(): # PRINT LIEUTENANT INFO
            if "orders" not in latest_results[key][0]: 
                N += 1
                if not latest_results[key][0]['is_traitor']:
                    if latest_results[key][0]['final_decision'] == None:
                        Abort_Count +=1
                    else:
                        Incorrect_Count +=1

                else:
                    Num_Traitors +=1


        M = int(len(latest_results["Alice"][0]['BV']) / (N-1))

        with open("traitor_commander_simulation_results.csv", "a") as file:
            file.write(f"{M},{N},{Num_Traitors},{NOISE_TIME},{T1_TIME},{Abort_Count},{Correct_Count},{Incorrect_Count}\n")

if __name__ == "__main__":
    run()