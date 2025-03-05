import pytest
import importlib

def test_entanglement(monkeypatch):

    import eprq_dba.config as config
    
    COMMANDER_NAME = "Alice"
    LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Esther"]
    test_N = 1 + len(LIEUTENANT_NAMES)
    test_M = 64
    monkeypatch.setattr(config, "N", test_N)
    monkeypatch.setattr(config, "M", test_M)

    import eprq_dba.players as players
    importlib.reload(players)
    from eprq_dba.players import Commander, Lieutenant

    alice = Commander(name=COMMANDER_NAME, orders=[1] * len(LIEUTENANT_NAMES))
    lieutenants = [
        Lieutenant(name=name, lieutenant_index=i)
        for i, name in enumerate(LIEUTENANT_NAMES)
    ]

    alice.distribute_entanglement(lieutenants)
    alice.measure_qubits()
    for lieutenant in lieutenants:
        lieutenant.measure_qubits()

    anticorrelation_verified = all(
        lieutenant.bit_vector[k * len(lieutenants) + lieutenant.lieutenant_index] !=
        alice.bit_vector[k * len(lieutenants) + lieutenant.lieutenant_index]
        for lieutenant in lieutenants
        for k in range(test_M)
    )

    assert anticorrelation_verified, "Anti-correlation failed for one or more entangled pairs."
