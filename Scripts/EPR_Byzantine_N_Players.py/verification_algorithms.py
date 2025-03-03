import numpy as np

M = 64
e = 2 * np.sqrt(M / 4)

# This command returns a set of indices, where each index corresponds to a pair in the command vector that is of the form (x, y)
def P(x, y, command_vec):
    ret = set()
    for i in range(0, 2*M, 2):
        if (command_vec[i] == x and command_vec[i+1] == y):
            ret.add(M - (i // 2) - 1)
    return ret

# This is used by B and C to check the validity of A's command vector with its bit sent.
def checkAlice(i, c, v_a, l):
    # e = M/8
    pcca = len(P(c, c, v_a))
    # print(pcca)
    if (not (pcca >= (M/4) - e and pcca <= (M/4) + e)):
        print("Check Alice 1 failed")
        return False

    pcia = len(P((c+1)%2 ^ i, c ^ i, v_a))
    if (not (pcia >= (M/4) - e and pcia <= (M/4) + e)):
        print("Check Alice 2 failed")
        return False
        
    for k in range(M):
        if (v_a[2*k + i] == l[2*k + i]):
            print("Check 3 failed")
            return False
    return True

# This is used by B/C when they have consistent data to check C/B's decision.
def checkWCV(i, j, c, v, v_a):
    # e = M/8
    
    pccv = len(P(c, c, v))
    # print(pccv)
    if (not (pccv >= (M/4) - e and pccv <= (M/4) + e)):
        print("Check WCV 1 failed")
        return False

    pcjv = len(P((c+1)%2 ^ j, c ^ j, v))
    # print(pcjv)
    if (not (pcjv >= (M/4) - e and pcjv <= (M/4) + e)):
        print("Check WCV 2 failed")
        return False
    

    pccjva = P((c+1)%2 ^ j, c ^ j, v_a)
    pccjv = P((c+1)%2 ^ j, c ^ j, v)
    pccjvav = len(pccjva.symmetric_difference(pccjv))
    # print(pccjvav)
    if (not (pccjvav <= e)):
        print("Check WCV 3 failed")
        return False

    return True

# This is used by B/C when they do not have consistent data to check C/B's data.
def checkWBV(i, j, c, v, l):
    # e = M/8
    
    pccv = len(P(c, c, v))
    # print(pccv)
    if (not (pccv >= (M/4) - e and pccv <= (M/4) + e)):
        print("Check WBV 1 failed")
        return False
    
    pcjv = len(P((c+1)%2 ^ j, c ^ j, v))
    # print(pcjv)
    if (not (pcjv >= (M/4) - e and pcjv <= (M/4) + e)):
        print("Check WBV 2 failed")
        return False
    
    for k in range(M):
        v_t = list(reversed(v)) # use v_t, l_t when using the hardcoded example
        l_t = list(reversed(l))
        if (v[2*k+i] == l[2*k+i]):
            print("Check WBV 3 failed")
            print(v)
            print(l)
            print(k)
            return False
            
    return True