from dataclasses import dataclass 
from spyral_utils.nuclear import NucleusData
from spyral_utils.nuclear.target import GasTarget
from spyral_utils.constants import QBRHO_2_P
import polars as pl 
import numpy as np 
import vector 

@dataclass
class DataReactionKinematics: 
    data : pl.DataFrame
    projectile : NucleusData
    target : NucleusData
    targetlike: NucleusData
    beamlike : NucleusData
    beam_energy_entrace_tpc : float 

    def construct_target_vector(self,) ->vector: 
        target_vector = vector.array({
            "px": [0.],
            "py": [0.], 
            "pz": [0.],
            "E": [self.target.mass]
        })
        return target_vector 

    def construct_projectile_vector(self, target_material: GasTarget) -> vector: 
        vertices = self.data.select(['vertex_x', 'vertex_y', 'vertex_z']).to_numpy()
        distances = np.linalg.norm(vertices, axis=1)
        projectile_ke = self.beam_energy_entrace_tpc - target_material.get_energy_loss(self.projectile, self.beam_energy_entrace_tpc, distances)
        projectile_vector = vector.array({
            "px": np.zeros(len(projectile_ke)),
            "py": np.zeros(len(projectile_ke)),
            "pz": np.sqrt(projectile_ke * (projectile_ke + 2*self.projectile.mass)), 
            "E": projectile_ke + self.projectile.mass
            })
        return projectile_vector 

    def construct_parent_vector(self, target_material: GasTarget)-> vector:
        target_vector = self.construct_target_vector()
        projectile_vector = self.construct_projectile_vector(target_material)
        return target_vector + projectile_vector


    def construct_targetlike_vector(self) -> vector:
        """General notes: this might change** as the targetlike particle matches with the observable"""
        brho = self.data.select("brho").to_numpy().flatten()
        momentum = brho * float(self.targetlike.Z) * QBRHO_2_P
        kinetic_energy = np.sqrt(momentum**2.0 + self.targetlike.mass**2.0) - self.targetlike.mass
        polar = self.data.select('polar').to_numpy().flatten()
        az = self.data.select('azimuthal').to_numpy().flatten()
        # cs = self.data.select('redchisq').to_numpy().flatten()

        targetlike_vector = vector.array({
            "px": momentum * np.sin(polar) * np.cos(az),
            "py": momentum * np.sin(polar) * np.sin(az),
            "pz": momentum * np.cos(polar),
            "E": np.sqrt(momentum**2.0 + self.targetlike.mass**2.0)
        })

        return targetlike_vector
    
    
    def extract_kinematics_values(self, results: dict):
        brho = self.data.select("brho").to_numpy().flatten()
        momentum = brho * float(self.targetlike.Z) * QBRHO_2_P
        kinetic_energy = np.sqrt(momentum**2.0 + self.targetlike.mass**2.0) - self.targetlike.mass
        polar = self.data.select('polar').to_numpy().flatten()
        az = self.data.select('azimuthal').to_numpy().flatten()
        results["brho"] = np.append(results["brho"],brho)
        results["kinetic_energy"] = np.append(results["kinetic_energy"],kinetic_energy)
        results["polar"] = np.append(results["polar"],polar)
        results["az"] = np.append(results["az"],az)

    def invariant_mass_technique(self, particle_vectors : list[vector], compound_nucleus : NucleusData) -> np.ndarray:
        """Use the invariant mass technique with the given vectors""" 
        total_vector = vector.array({
            "px":[0.0], "py": [0.0], "pz": [0.0], "E": [0.0]
        })
        [total_vector:= total_vector + nvector for nvector in particle_vectors] # named walrus operator
        
        return total_vector.M - compound_nucleus.mass
    
    def missing_mass_technique(self,target_material: GasTarget)->vector:
        """General notes: this might change** as the beamlike particle matches with the observable"""
        parent_vector = self.construct_parent_vector(target_material)
        targetlike_vector = self.construct_targetlike_vector()
        beamlike_vector = parent_vector - targetlike_vector
        return beamlike_vector



