import pytest
import importlib
import random
import matplotlib.pyplot as plt

def test_run_sweep(monkeypatch):
    import config
    # sweep_vals = [2, 4, 8, 16, 32, 64]
    # sweep_vals = [4, 8, 12]
    sweep_vals = list(range(10))
    num_shots = 2
    result_vals = []
    traitor_success_vals = []
    failed_agreement_vals = []
    for sweep_val in sweep_vals:
        # monkeypatch.setattr(config, "N", sweep_val)
        
        # test_LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis"]
        test_N = 10
        test_LIEUTENANT_NAMES = [f"L{i}" for i in range(test_N-1)]
        # test_N = 1 + len(test_LIEUTENANT_NAMES)
        test_M = 150
        test_loyal_commander_order = True
        monkeypatch.setattr(config, "COMMANDER_IS_TRAITOR", False)
        # num_traitors = sweep_val // 2
        monkeypatch.setattr(config, "TRAITOR_INDICES", [random.sample(range(10-1), sweep_val)])
        monkeypatch.setattr(config, "LIEUTENANT_NAMES", test_LIEUTENANT_NAMES)
        monkeypatch.setattr(config, "M", test_M)
        monkeypatch.setattr(config, "N", test_N)
        monkeypatch.setattr(config, "LOYAL_COMMANDER_ORDER", test_loyal_commander_order)
        
        import players
        import simulation
        importlib.reload(players)
        importlib.reload(simulation)
        
        successes = 0
        traitor_successes = 0
        failed_agreements = 0
        for shot in range(num_shots):
            results = simulation.run_simulation()
            lieutenants = results["lieutenants"]
            alice = results["alice"]
            loyal_final_decisions = [lt.final_decision for lt in lieutenants if not lt.is_traitor]
            loyal_command_order = 1 if test_loyal_commander_order else 0
            if all(d == loyal_command_order for d in loyal_final_decisions):
                successes += 1
            elif all(d != loyal_command_order for d in loyal_final_decisions):
                traitor_successes += 1
            else:
                failed_agreements += 1

        result_vals.append(successes / float(num_shots))
        traitor_success_vals.append(traitor_successes / float(num_shots))
        failed_agreement_vals.append(failed_agreements / float(num_shots))

    # print(f"N={test_N}")
    print(f"NumShots={num_shots}")
    print("NumTraitor Vals")
    print(sweep_vals)
    print("Success")
    print(result_vals)
    print("Traitor Success")
    print(traitor_success_vals)
    print("Failed Agreement")
    print(failed_agreement_vals)
    
        
    plt.plot(sweep_vals, result_vals, label="success")
    plt.plot(sweep_vals, traitor_success_vals, label="traitor success")
    plt.plot(sweep_vals, failed_agreement_vals, label="failed agreement")
    plt.xlabel("Number of Traitors (n_t)")
    plt.ylabel("Rate")
    plt.title("Success with n_t Traitors, N=10, 100 shots")
    plt.legend()
    plt.show()