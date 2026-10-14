from dataclasses import dataclass 
from spyral_utils.nuclear.nuclear_map import NucleusData
import numpy as np 

@dataclass 
class selection_rules_reaction:
    beam_spin: int
    beam_parity: int 
    target_spin: int
    target_parity: int 
    def conservation(self, cutoff_l: int)->tuple[float]:
        total_spin = np.arange(abs(self.beam_spin-self.target_spin), self.beam_spin+self.target_spin,1)
        angular_momentum = range(0,cutoff_l+1,1)
        total_parity = self.beam_parity*self.target_parity*(-1)**angular_momentum
        return [total_spin,total_parity]

# @dataclass 
# class selection_rules_decay:
#     parent_spin: int
#     parent_parity: int 
#     daughters_spins: tuple[int]
#     daughters_parities: tuple[int]

#     def 

