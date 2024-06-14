import bisect
import itertools
import math
from typing import List, Tuple
import exqalibur as xq

BasicState = xq.FockState

# m le nombre de modes est fixe
# notons '*' pour un photon, et '|' pour un separateur de modes (on compte celui de la fin)
# exemple : |0, 2, 1> c'est |**|*|

# on enumere les etats a 0 photon, puis a 1 photon, puis a 2, etc...
# ce qui nous interesse ce sont les emplacements des changements de mode
# |0,0,0> = |||    = 0,1,2    0
# |0,0,1> = ||*|   = 0,1,3    1
# |0,1,0> = |*||   = 0,2,3    2
# |1,0,0> = *|||   = 1,2,3    3
# |0,0,2> = ||**|  = 0,1,4    4
# |0,1,1> = |*|*|  = 0,2,4    5
# |1,0,1> = *||*|  = 1,2,4    6
# |0,2,0> = |**||  = 0,3,4    7
# |1,1,0> = *|*||  = 1,3,4    8
# |2,0,0> = **|||  = 2,3,4    9
# |0,0,3> = ||***| = 0,1,5   10
# ...

# https://en.wikipedia.org/wiki/Combinatorial_number_system
# nous dit qu'on passe des emplacements au numero avec
# la formule implementee dans getIndex(separatorIndices : List[int], m : int)
# Ils expliquent meme pourquoi et c'est d'ailleurs assez simple
#
# Ils donnent aussi l'algorithme pour l'autre transformation,
# celle implementee dans getSeparatorIndices(index : int, m : int)
# Il y a aussi les explications, ce n'est pas beaucoup plus complique

def combin(n : int, k : int) -> int:
    return  math.comb(n, k)

def getMaxCombinLessThan(value : int, k : int) -> Tuple[int, int]:
    # Amelioration possible ?
    # precalculer le vecteur des [combin(j, k) for j in 0..infinity]
    # et utiliser bisect.bisect()
    if value == 0:
        return k-1, 0
    result = k
    current = 1
    i = 1
    while True:
        next = (current * (result + 1)) // i
        if next > value:
            return result, current
        i += 1
        result += 1
        current = next

def getSeparatorIndices(index : int, m : int) -> List[int]:
    result = []
    while m > 0:
        currentvalue, currentIndex = getMaxCombinLessThan(index, m)
        result.insert(0, currentvalue)
        index -= currentIndex
        m -= 1
    return result

def getIndex(separatorIndices : List[int], m : int) -> int:
    k = 1
    result = 0
    for ck in separatorIndices:
        result += combin(ck, k)
        k += 1
    return result

def getPhotonIndices(separatorIndices : List[int], m : int) -> List[int]:
    # ici on travaille avec les separations de mode, FockState veut les photons
    # c'est le complementaire
    photonIndices = []
    currentIndex = 0
    currentPhotonIndex = 0
    for separatorIndex in separatorIndices:
        while currentIndex < separatorIndex:
            photonIndices.append(currentPhotonIndex)
            currentIndex += 1
        currentIndex += 1
        currentPhotonIndex += 1
    return photonIndices

def getFS(index : int, m : int) -> BasicState:
    separatorIndices = getSeparatorIndices(index, m)
    # if m != len(separatorIndices):
    #     raise "Error computing separator indices"
    photonIndices = getPhotonIndices(separatorIndices, m)
    # photonIndices contient ce qu'il faut pour construire le FS, mais c'est un vector<int> et pas un unsigned char*
    # On fait la transformation ici puis dans l'autre sens, c'est dommage
    state = [0]* m
    for photon in photonIndices:
        state[photon] += 1
    return BasicState(state)

def add(index1 : int, index2 : int, m : int) -> int:
    separatorIndices1 = getSeparatorIndices(index1, m)
    separatorIndices2 = getSeparatorIndices(index2, m)
    print("   {}   {}".format(separatorIndices1, getPhotonIndices(separatorIndices1, m)))
    print("   {}   {}".format(separatorIndices2, getPhotonIndices(separatorIndices2, m)))
    sepIndices = merge(separatorIndices1, separatorIndices2)
    print("   {}   {}".format(sepIndices, getPhotonIndices(sepIndices, m)))
    return getIndex(sepIndices, m)

def merge(separatorIndices1 : List[int], separatorIndices2 : List[int]):
    # if len(separatorIndices1) != len(separatorIndices1):
    #     raise "Cannot merge FockStates of different mode count"
    it1 = iter(separatorIndices1)
    it2 = iter(separatorIndices2)
    offset1 = 0
    offset2 = 0
    sepIndex = 0
    result = []
    si1 = next(it1)
    si2 = next(it2)
    try:
        while True:
            if sepIndex == si1 and sepIndex == si2:
                result.append(sepIndex)
                si1 = next(it1) + offset1
                si2 = next(it2) + offset2
                sepIndex += 1
            else:
                curr = sepIndex
                if curr != si1:
                    offset2 += 1
                    si2 += 1
                    sepIndex += 1
                if curr != si2:
                    offset1 += 1
                    si1 += 1
                    sepIndex += 1
    except StopIteration:
        pass
    # if len(result) != len(separatorIndices1):
    #     raise "Error during merge of FockStates"
    return result

m = 4
i = 3
j = 7
print("{} = {}".format(i, getFS(i, m)))
print("{} = {}".format(j, getFS(j, m)))
sum = add(3, 7, m)
print("{} = {}".format(sum, getFS(sum, m)))
