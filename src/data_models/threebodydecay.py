from dataclasses import dataclass 
from spyral_utils.nuclear.nuclear_map import NucleusData
import numpy as np 


@dataclass
class dalitz_plot:
    """The particles must be plotted with axis x=s12 and y=s13"""
    m1 : NucleusData
    m2 : NucleusData
    m3 : NucleusData
    compound : NucleusData
    ex: float = 0

    def is_valid(self)->bool:
        return (self.compound.mass + self.ex) > (self.m1.mass + self.m2.mass + self.m3.mass)

    def global_s12_min(self)->float:
        return (self.m1.mass + self.m2.mass)**2

    def global_s12_max(self)->float:
        return (self.compound.mass + self.ex- self.m3.mass)**2

    def kallen_function(self, 
                        x: np.ndarray,
                        y: np.ndarray, 
                        z: np.ndarray) ->np.ndarray:
        return x**2 + y**2 + z**2 - 2*x*y - 2*x*z - 2*y*z
      
    def values_plot(self,steps: int = 10) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """We do not have to construct the vectors, but just in case 
        for future cases with p!=0"""
        if not self.is_valid():
            raise ValueError(f"M<m1+m2_m3, you need a minumum of ex={(self.m1.mass + self.m2.mass + self.m3.mass)-(self.compound.mass):0.2f} MeV")
        
        # Construct x-axis range fpr rest frame of 1+2 pair
        s12 = np.linspace(self.global_s12_min(),self.global_s12_max(),steps)
        sqrt_s12 = np.sqrt(s12)
        energy_cm_1 = (s12 + self.m1.mass**2 - self.m2.mass**2.0) / (2*sqrt_s12)
        energy_cm_3 = ((self.compound.mass+ self.ex)**2 - s12 - self.m3.mass**2.0) / (2*sqrt_s12)

        lambda_12  = np.clip(
            self.kallen_function(s12,self.m1.mass**2.0, self.m2.mass**2.0), 
            0.0,
            None
        )
        p_cm_1 = (
            np.sqrt(lambda_12)
                    / (2*sqrt_s12)
        )
        lambda_parent = np.clip(
            self.kallen_function((self.compound.mass+ self.ex)**2.0, s12, self.m3.mass**2.0),
            0.0,
            None
        )
        p_cm_3 = (np.sqrt(lambda_parent) / (2*sqrt_s12))


        default_val = self.m1.mass**2 + self.m3.mass**2 + 2*energy_cm_1*energy_cm_3
        
        s13_min =  default_val - 2* p_cm_1*p_cm_3
        
        s13_max = default_val + 2* p_cm_1*p_cm_3

        return (s12,s13_min, s13_max)
                         