import aqnsim

# ---------------------------
# User-defined Parameters
# ---------------------------
COMMANDER_NAME = "Alice"
LIEUTENANT_NAMES = ["Bob", "Charlie", "David"]

# Number of tuples (or entangled pairs) per lieutenant
M = 50

# Traitor configuration
COMMANDER_IS_TRAITOR = False
# Indices of lieutenants who are traitors: must be a subset of valid indices (0 to len(LIEUTENANT_NAMES)-1)
TRAITOR_INDICES = []  

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

# Easy To Read
NUM_PLAYERS = N
NUM_ROUNDS = M
NUM_LIEUTENANTS = N - 1
COMMANDER_QMEMORY_ADDR = N - 1  # Derived parameter; do not change


SEND_ORDER_ACTION = "SEND_ORDER"
SEND_CV_ACTION = "SEND_CV"
ROUND2_ACTION = "ROUND2_ACTION"
ROUND3_ACTION = "ROUND3_ACTION"

DISTRIBUTOR_NAME = "Distributor"


SEC = aqnsim.SECOND
QSOURCE_NOISE_MODEL = None
QUANTUM_CHANNEL_DELAY = 1 * SEC
QUANTUM_CHANNEL_NOISE = 0.0
CLASSICAL_CHANNEL_DELAY = 1 * SEC