import pytest
import importlib

def test_loyal_commander(monkeypatch):
    import eprq_dba.config as config
    test_LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis"]
    test_N = 1 + len(test_LIEUTENANT_NAMES)
    test_M = 150  # Use a higher M for better statistical consistency
    test_loyal_commander_order = True
    monkeypatch.setattr(config, "COMMANDER_IS_TRAITOR", False)
    monkeypatch.setattr(config, "TRAITOR_INDICES", [])
    monkeypatch.setattr(config, "LIEUTENANT_NAMES", test_LIEUTENANT_NAMES)
    monkeypatch.setattr(config, "N", test_N)
    monkeypatch.setattr(config, "M", test_M)
    monkeypatch.setattr(config, "LOYAL_COMMANDER_ORDER", test_loyal_commander_order)

    import eprq_dba.players as players
    import eprq_dba.simulation as simulation
    importlib.reload(players)
    importlib.reload(simulation)

    results = simulation.run_simulation()
    alice = results["alice"]
    lieutenants = results["lieutenants"]

    for i, lt in enumerate(lieutenants):
        if not lt.is_traitor:
            expected = alice.orders[i]
            assert lt.final_decision == expected, (
                f"Lieutenant {lt.name} final decision ({lt.final_decision}) does not match expected {test_loyal_commander_order}."
            )

def test_traitor_commander(monkeypatch):
    import eprq_dba.config as config
    test_LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis"]
    test_N = 1 + len(test_LIEUTENANT_NAMES)
    test_M = 150
    monkeypatch.setattr(config, "COMMANDER_IS_TRAITOR", True)
    monkeypatch.setattr(config, "TRAITOR_INDICES", [])
    monkeypatch.setattr(config, "LIEUTENANT_NAMES", test_LIEUTENANT_NAMES)
    monkeypatch.setattr(config, "N", test_N)
    monkeypatch.setattr(config, "M", test_M)
    monkeypatch.setattr(config, "LOYAL_COMMANDER_ORDER", True)

    import eprq_dba.simulation as simulation
    importlib.reload(simulation)

    results = simulation.run_simulation()
    alice = results["alice"]
    lieutenants = results["lieutenants"]

    loyal_final_decisions = [lt.final_decision for lt in lieutenants if not lt.is_traitor]

    assert len(set(loyal_final_decisions)) == 1, (
        "Loyal lieutenants did not all reach the same final decision."
    )

# TODO: test_loyal_commander_with_various_traitor_counts (use pytest parameterize on traitor_indices)
# TODO: test_traitor_commander_with_various_traitor_counts