import aqnsim

# ---------------------------
# User-defined Parameters
# ---------------------------
# COMMANDER_NAME = "Alice"
# LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis"]
# DISTRIBUTOR_NAME = "Distributor"

# # Number of tuples (or entangled pairs) per lieutenant
# M = 250

# # Traitor configuration
# COMMANDER_IS_TRAITOR = True
# # Indices of lieutenants who are traitors: must be a subset of valid indices (0 to len(LIEUTENANT_NAMES)-1)
# TRAITOR_INDICES = [0,1] 

# # Order that a loyal commander sends (if not traitor)
# LOYAL_COMMANDER_ORDER = False

# # Action names
# SEND_ORDER_ACTION = "SEND_ORDER"
# SEND_CV_ACTION = "SEND_CV"
# ROUND2_ACTION = "ROUND2_ACTION"
# ROUND3_ACTION = "ROUND3_ACTION"

# # Channel params
# SEC = aqnsim.SECOND
# QSOURCE_NOISE_MODEL = None
# QUANTUM_CHANNEL_DELAY = 1 * SEC
# QUANTUM_CHANNEL_NOISE = 0.0
# CLASSICAL_CHANNEL_DELAY = 1 * SEC

# # ---------------------------
# # Derived Parameters & Validation
# # ---------------------------
# # Total number of players (commander plus lieutenants)
# N = 1 + len(LIEUTENANT_NAMES)

# # Commander qubit sits in N'th slot of Distributor's QMemory
# COMMANDER_QMEMORY_ADDR = N - 1 

# # Easy To Read Options
# NUM_PLAYERS = N
# NUM_LIEUTENANTS = N - 1

# # Validate that TRAITOR_INDICES is a subset of valid indices
# valid_indices = set(range(len(LIEUTENANT_NAMES)))
# assert set(TRAITOR_INDICES).issubset(valid_indices), (
#     "TRAITOR_INDICES must be a subset of valid lieutenant indices!"
# )

class SimulationConfig:
    def __init__(self,
                 COMMANDER_NAME="Alice",
                 LIEUTENANT_NAMES=None,
                 DISTRIBUTOR_NAME="Distributor",
                 M=250,
                 COMMANDER_IS_TRAITOR=True,
                 TRAITOR_INDICES=None,
                 LOYAL_COMMANDER_ORDER=False,
                 SEC=aqnsim.SECOND,
                 QSOURCE_NOISE_MODEL=None,
                 QUANTUM_CHANNEL_DELAY=None,
                 QUANTUM_CHANNEL_NOISE=0.0,
                 CLASSICAL_CHANNEL_DELAY=None):
        
        # Default values for mutable arguments
        if LIEUTENANT_NAMES is None:
            LIEUTENANT_NAMES = ["Bob", "Charlie", "David", "Eve", "Francis"]
        if TRAITOR_INDICES is None:
            TRAITOR_INDICES = [0, 1]
        if QUANTUM_CHANNEL_DELAY is None:
            QUANTUM_CHANNEL_DELAY = 1 * SEC
        if CLASSICAL_CHANNEL_DELAY is None:
            CLASSICAL_CHANNEL_DELAY = 1 * SEC
        
        # User-defined parameters
        self.COMMANDER_NAME = COMMANDER_NAME
        self.LIEUTENANT_NAMES = LIEUTENANT_NAMES
        self.DISTRIBUTOR_NAME = DISTRIBUTOR_NAME
        self.M = M
        self.COMMANDER_IS_TRAITOR = COMMANDER_IS_TRAITOR
        self.TRAITOR_INDICES = TRAITOR_INDICES
        self.LOYAL_COMMANDER_ORDER = LOYAL_COMMANDER_ORDER
        
        # Action names
        self.SEND_ORDER_ACTION = "SEND_ORDER"
        self.SEND_CV_ACTION = "SEND_CV"
        self.ROUND2_ACTION = "ROUND2_ACTION"
        self.ROUND3_ACTION = "ROUND3_ACTION"
        
        # Channel parameters
        self.SEC = SEC
        self.QSOURCE_NOISE_MODEL = QSOURCE_NOISE_MODEL
        self.QUANTUM_CHANNEL_DELAY = QUANTUM_CHANNEL_DELAY
        self.QUANTUM_CHANNEL_NOISE = QUANTUM_CHANNEL_NOISE
        self.CLASSICAL_CHANNEL_DELAY = CLASSICAL_CHANNEL_DELAY
        
        # Derived parameters
        self.N = 1 + len(self.LIEUTENANT_NAMES)
        self.COMMANDER_QMEMORY_ADDR = self.N - 1
        self.NUM_PLAYERS = self.N
        self.NUM_LIEUTENANTS = self.N - 1
        
        # Validation
        valid_indices = set(range(len(self.LIEUTENANT_NAMES)))
        assert set(self.TRAITOR_INDICES).issubset(valid_indices), (
            "TRAITOR_INDICES must be a subset of valid lieutenant indices!"
        )