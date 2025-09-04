import pytest
import importlib

def test_entanglement(monkeypatch):

    import eprq_dba.config as config
    
    COMMANDER_NAME = "Alice"
    LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Esther", "Francis", "George"]
    M = 10
    COMMANDER_IS_TRAITOR = False
    TRAITOR_INDICES = [0]  
    LOYAL_COMMANDER_ORDER = False
    N = 1 + len(LIEUTENANT_NAMES)
    # Validate that TRAITOR_INDICES is a subset of valid indices
    valid_indices = set(range(len(LIEUTENANT_NAMES)))
    assert set(TRAITOR_INDICES).issubset(valid_indices), (
        "TRAITOR_INDICES must be a subset of valid lieutenant indices!"
    )
    # Easy To Read
    NUM_PLAYERS = N
    NUM_ROUNDS = M
    NUM_LIEUTENANTS = N - 1

    monkeypatch.setattr(config, "COMMANDER_NAME", COMMANDER_NAME)
    monkeypatch.setattr(config, "LIEUTENANT_NAMES", LIEUTENANT_NAMES)
    monkeypatch.setattr(config, "M", M)
    monkeypatch.setattr(config, "COMMANDER_IS_TRAITOR", COMMANDER_IS_TRAITOR)
    monkeypatch.setattr(config, "TRAITOR_INDICES", TRAITOR_INDICES)
    monkeypatch.setattr(config, "LOYAL_COMMANDER_ORDER", LOYAL_COMMANDER_ORDER)
    monkeypatch.setattr(config, "N", N)
    monkeypatch.setattr(config, "NUM_PLAYERS", NUM_PLAYERS)
    monkeypatch.setattr(config, "NUM_ROUNDS", NUM_ROUNDS)
    monkeypatch.setattr(config, "NUM_LIEUTENANTS", NUM_LIEUTENANTS)

    import protocol
    importlib.reload(protocol)
    from protocol import setup_network

    run_simulation = aqnsim.generate_run_simulation_fn(
        setup_sim_fn=setup_network, logging_level=20, log_to_file=False
    )
    results = run_simulation()
    
    # for key, value in results.items():
    #     print(value, key)

    # TODO: EDIT SO THAT INSTEAD OF STRING ANALYSIS WE CAN ACCESS THE VALUES LIKE THIS

    anticorrelation_verified = all(
        lieutenant.bit_vector[k * len(lieutenants) + lieutenant.lieutenant_index] !=
        alice.bit_vector[k * len(lieutenants) + lieutenant.lieutenant_index]
        for lieutenant in lieutenants
        for k in range(test_M)
    )

    assert anticorrelation_verified, "Anti-correlation failed for one or more entangled pairs."