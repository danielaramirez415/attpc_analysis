from dataclasses import dataclass
from spyral_utils.nuclear import NuclearDataMap, NucleusData
from spyral_utils.nuclear.target import SolidTarget, GasTarget, load_target
from pathlib import Path
import numpy as np

@dataclass 
class EnergyLossIC:
    def __init__(
        self,
        ic_window_compound: list[list[int]] = None,
        ic_window_thickness: float = 1422.312,
        ic_gas_compound: list[list[int]] = None,
        ic_gas_thickness: float = 0.035,
        ic_gas_pressure: float = 600.0
    ):
        # Standard Python pattern to prevent mutable default argument bugs
        if ic_window_compound is None: 
            self.ic_window_compound = [[1,1,14],[6,12,14],[7,14,4],[8,16,4]]
        self.ic_window_thickness = ic_window_thickness
        if ic_gas_compound is None:
            self.ic_gas_compound =  [[6,12,1],[9,18,4]]
        self.ic_gas_thickness = ic_gas_thickness
        self.ic_gas_pressure = ic_gas_pressure

    def ic_window_material(self) -> SolidTarget: 
        return ( 
            SolidTarget(
                compound = self.ic_window_compound, 
                thickness = self.ic_window_thickness,
                nuclear_data = NuclearDataMap()
                )
                )
    def ic_gas_material(self) -> GasTarget: 
        return (
            GasTarget(
                compound=self.ic_gas_compound, 
                pressure = self.ic_gas_pressure,
                nuclear_data=NuclearDataMap() 
            )
        )
    def beam_energy_after_ic(self, beam_energy: float, projectile:float) -> np.ndarray:
        beam_energy_ic_window = beam_energy - self.ic_window_material().get_energy_loss(projectile, beam_energy, np.array([0.0]))[0]
        beam_energy_ic_gas = beam_energy_ic_window - self.ic_gas_material().get_energy_loss(projectile, beam_energy_ic_window, np.array([self.ic_gas_thickness]))[0]
        beam_energy_ic =  beam_energy_ic_gas - self.ic_window_material().get_energy_loss(projectile, beam_energy_ic_gas, np.array([0.0]))[0]
        return  beam_energy_ic

@dataclass 
class EnergyLossATTPC: 

    def __init__(
            self, 
            attpc_target_path_json: Path = Path("./"),
            attpc_window_compound:  list[list[int]] = None,
            attpc_window_thickness : float = 1422.312,
            attpc_length : float = 1.0,
            ):
        self.attpc_target_path_json = attpc_target_path_json
        if attpc_window_compound is None: 
            self.attpc_window_compound = [[1,1,14],[6,12,14],[7,14,4],[8,16,4]]
        self.attpc_window_thickness = attpc_window_thickness
        self.attpc_length = attpc_length


    def attpc_gas_material(self)-> GasTarget | None: 
        """This is a little redundant**"""
        target_material = load_target(self.attpc_target_path_json, NuclearDataMap())
        if not isinstance(target_material, GasTarget):
            return None 
        return target_material
    
    def attpc_window_material(self)->SolidTarget: 
        return (
            SolidTarget(
                compound=self.attpc_window_compound, 
                thickness=self.attpc_window_thickness,
                nuclear_data=NuclearDataMap()
            )
        )
    def beam_energy_entrance_gas_attpc(self,  beam_energy: float, projectile:float) -> np.ndarray:
        return ( 
            beam_energy 
            - self.attpc_window_material().get_energy_loss(projectile, beam_energy,np.array([0.0]))[0]
        )
    def beam_energy_exit_gas_attpc(self, beam_energy: float, projectile:float) -> np.ndarray:
        return (
            beam_energy 
            - self.attpc_gas_material().get_energy_loss(projectile, beam_energy,np.array([self.attpc_length]))[0]
        )
    

@dataclass 
class EnergyLossSetup: 
    beam_energy : float 
    projectile : NucleusData 
    attpc_target_path_json: Path
    attpc_window_compound: list[list[int]] = None
    attpc_window_thickness : float = 1422.312
    attpc_length: float = 1.0
    ic_window_compound : list[list[int]] = None
    ic_window_thickness : float = 1422.312
    ic_gas_compound :  list[list[int]] = None
    ic_gas_thickness : float = 0.035
    ic_gas_pressure : float = 600.0

    def import_detectors(self) -> tuple[EnergyLossIC, EnergyLossATTPC]:
        ic_details = EnergyLossIC(
            self.ic_window_compound,
            self.ic_window_thickness,
            self.ic_gas_compound,
            self.ic_gas_thickness
        )

        attpc_details = EnergyLossATTPC(
            self.attpc_target_path_json,
            self.attpc_window_compound,
            self.attpc_window_thickness,
            self.attpc_length
        )
        return [ic_details, attpc_details]
    
    def beam_energy_entrance_attpc(self)->np.ndarray:
        ic_details, attpc_details = self.import_detectors()
        ic_beam_after = ic_details.beam_energy_after_ic(self.beam_energy, self.projectile)
        return attpc_details.beam_energy_entrance_gas_attpc(ic_beam_after, self.projectile)
    
    def beam_energy_exit_attpc(self)->np.ndarray:
         ic_details, attpc_details = self.import_detectors()
         beam_entrance = self.beam_energy_entrance_attpc()
         return attpc_details.beam_energy_exit_gas_attpc(beam_entrance,self.projectile)
    
    def active_gas_target_material(self)->GasTarget:
        ic_details, attpc_details = self.import_detectors()
        return attpc_details.attpc_gas_material()