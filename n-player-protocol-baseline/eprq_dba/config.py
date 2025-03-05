# ---------------------------
# User-defined Parameters
# ---------------------------
COMMANDER_NAME = "Alice"
LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis", "George"]

# Number of tuples (or entangled pairs) per lieutenant
M = 150 

# Traitor configuration
COMMANDER_IS_TRAITOR = False
# Indices of lieutenants who are traitors: must be a subset of valid indices (0 to len(LIEUTENANT_NAMES)-1)
TRAITOR_INDICES = [3,4,5]  

# Order that a loyal commander sends (if not traitor)
LOYAL_COMMANDER_ORDER = False

# ---------------------------
# Derived Parameters & Validation
# ---------------------------
# Total number of players (commander plus lieutenants)
N = 1 + len(LIEUTENANT_NAMES)

# Validate that TRAITOR_INDICES is a subset of valid indices
valid_indices = set(range(len(LIEUTENANT_NAMES)))
assert set(TRAITOR_INDICES).issubset(valid_indices), (
    "TRAITOR_INDICES must be a subset of valid lieutenant indices!"
)
