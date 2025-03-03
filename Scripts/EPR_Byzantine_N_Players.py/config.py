import aqnsim
import numpy as np
from enum import Enum, auto

CHANNEL_DELAY = 1e-6 * aqnsim.SECOND

NUM_SHOTS = 1

# Number of pairs of qubits in the protocol
M = 64

# Number of players in the protocol
N = 10

# Error threshold for verification algorithms - used as our tolerance in checking vectors (CheckAlice, CheckWCV, CheckWBV)
E = 2 * np.sqrt(M / 4) # 2 stddevs from M/4


# Initially undefined noise parameters
p0, p1, p2, p3 = (-1,)*4

class NoiseType(Enum):
    Depolarizing = auto()
    Pauli = auto()
    Dephasing = auto()