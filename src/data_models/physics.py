from dataclasses import dataclass 
from spyral_utils.nuclear import NucleusData
from spyral_utils.nuclear.target import GasTarget
from spyral_utils.constants import QBRHO_2_P
import polars as pl 
import numpy as np 
import vector 


# Practical functions
def invariant_mass_technique(
        daughter_vectors : list[vector], 
        compound_nucleus : NucleusData
        ) -> np.ndarray:
    """
    Calculates the excitation energy of the compound nucleus vector using the invariant mass technique by 
    summing the daughter nucleus vectors. 
    
    Parameters
    ----------
    daughter_vectors: list 
        Vectors of the compound nucleus decay products. 
    
    compound_nucleus: NucleusData
        Data for the compound/parent nucleus. 
    
    Returns
    -------
    np.ndarray
        Excitation energy of the compound nucleus in MeV. 
    """ 
    total_vector = vector.array({
        "px":[0.0], "py": [0.0], "pz": [0.0], "E": [0.0]
    })
    [total_vector:= total_vector + nvector for nvector in daughter_vectors] # named walrus operator
    
    return total_vector.M - compound_nucleus.mass


def direction_orthogonal_vector(
        v1: vector, 
        v2: vector
    )-> vector:
    """
    Gets the perpendicular unitary vector from the two given momentum vectors.

    Parameters
    ----------
    v1: vector
        Momentum vector of particle 1.
    v2: vector 
        Momentum vector of particle 2.
    
    Returns
    -------
    vector 
        Unitary vector of the perpendicular vector to particle 1 x particle 2.
    """
    v1_unit = vector.array({"px":v1.px/v1.p, "py": v1.py/v1.p, "pz":v1.pz/v1.p})
    v2_unit = vector.array({"px":v2.px/v2.p, "py": v2.py/v2.p, "pz":v2.pz/v2.p})
    return v1_unit.dot(v2_unit)


@dataclass
class DataReactionKinematics: 
    """
    Utility class for holding the experimental data and apply its physics. 

    Attributes
    ----------
    data: pl.DataFrame
        Default physics dataframe used in Spyral
    projectile: NucleusData
        Data for the projectile/beam nucleus. 
    target: NucleusData
        Data for the target nucleus.
    beamlike: NucleusData
        Data for the beam-like nucleus from projectile impinge of a target nucleus. 
    targetlike: NucleusData
        Data for the target-like nucleus from projectile impinge of a target nucleus. 
    beam_energy_entrance_tpc: float
        Beam energy right at the entrance of the gas area inside the tpc. 

    """
    data : pl.DataFrame
    projectile : NucleusData
    target : NucleusData
    targetlike: NucleusData
    beamlike : NucleusData
    beam_energy_entrace_tpc : float 

    def construct_target_vector(
            self
            ) ->vector: 
        """
        Calculates the target vector assuming it starts at rest. 

        Returns
        -------
        vector
            Target vector   
        """
        target_vector = vector.array({
            "px": [0.],
            "py": [0.], 
            "pz": [0.],
            "E": [self.target.mass]
        })
        return target_vector 

    def construct_projectile_vector(
            self, 
            target_material: GasTarget
        ) -> vector: 
        """
        Calculates the projectile vector from the experimental data. It also accounts for the 
        energy loss inside the AT-TPC active gas. 

        Parameters
        ---------- 
        target_material: GasTarget
            AT-TPC representation of the gas target from the experiment.

        Returns
        -------
        vector
            Projectile vector  
        """
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

    def construct_parent_vector(
            self, 
            target_material: GasTarget
        )-> vector:
        """
        Calculates the parent vector in the lab frame of the incoming nucleus (projectile) and
        target nucleus.

        Parameters
        ---------- 
        target_material: GasTarget
            AT-TPC representation of the gas target from the experiment.

        Returns
        -------
        vector
            Parent vector in the lab frame.
        """
        target_vector = self.construct_target_vector()
        projectile_vector = self.construct_projectile_vector(target_material)
        return target_vector + projectile_vector


    def construct_targetlike_vector(
            self
        ) -> vector:
        """
        Calculates the target-like vector after the reaction.

        Returns
        -------
        vector
            Target vector in the lab frame.
        """
        brho = self.data.select("brho").to_numpy().flatten()
        momentum = brho * float(self.targetlike.Z) * QBRHO_2_P
        kinetic_energy = np.sqrt(momentum**2.0 + self.targetlike.mass**2.0) - self.targetlike.mass
        polar = self.data.select('polar').to_numpy().flatten()
        az = self.data.select('azimuthal').to_numpy().flatten()

        targetlike_vector = vector.array({
            "px": momentum * np.sin(polar) * np.cos(az),
            "py": momentum * np.sin(polar) * np.sin(az),
            "pz": momentum * np.cos(polar),
            "E": np.sqrt(momentum**2.0 + self.targetlike.mass**2.0)
        })

        return targetlike_vector

    def construct_beamlike_vector(
            self,
            target_material: GasTarget
            )->vector:
        """
        Calculates the beam-like vector using the missing mass technique for inverse kinematics. 

        Parameters
        ----------
        target_material: GasTarget
            AT-TPC representation of the gas target from the experiment.

        Returns
        -------
        vector
            Beam-like residual vector
        """
        parent_vector = self.construct_parent_vector(target_material)
        targetlike_vector = self.construct_targetlike_vector()
        beamlike_vector = parent_vector - targetlike_vector
        return beamlike_vector

    def missing_mass_technique(
            self,
            target_material: GasTarget
        )->vector: 
            """
            Calculates the excitation energy of beam-like residue using the missing mass technique.

            Parameters
            ----------
            target_material: GasTarget
                AT-TPC representation of the gas target from the experiment.
                
            Returns
            -------
            np.ndarray
                Excitation energy of the beam-like residue in MeV. 
            """
            beamlike_vector = self.construct_beamlike_vector(target_material)
            return beamlike_vector.M - self.beamlike.mass

    def angular_distribution(
            self,
            target_material
        )->np.ndarray:

        """
        Gets the CM polar angle of the reaction. Notice this function uses the real definition of the CM angle
        by knowing the incoming vector and the particle equivalent outgoing vector. 

        Parameters
        ----------
        target_material: GasTarget
                AT-TPC representation of the gas target from the experiment.

        Returns
        -------
        np.ndarray 
            CM Polar angle of the reaction.

        """
        parent_vector = self.construct_parent_vector(target_material)
        beam_vector = self.construct_projectile_vector(target_material)
        beamlike_vector = self.construct_beamlike_vector(target_material)

        # Boost to the CM frame 
        beam_vector = beam_vector.boostCM_of(parent_vector)
        beamlike_vector = beamlike_vector.boostCM_of(parent_vector)

        # Get Polar CM angle 
        cos_polar_cm = direction_orthogonal_vector(beam_vector,beamlike_vector)
        return np.arccos(cos_polar_cm)



    def extract_kinematics_values(
            self, 
            results: dict,
            target_material: GasTarget
        ):
        """
        Extracts the physics from the experimantal parquet file into the input dictation. 

        !!! note "Important"
            This function adds the physics data into ``results``. The input dictation must contain:
            ``brho``, ``kinetic_energy``, ``polar_az``, ``redchisq``, ``vertex_x``, ``vertex_y``, 
            ``vertex_z``, ``ex`` and ``polar_cm``.
             
        Parameters
        ----------
        results: dict
            Storage of the physics
        target_material: GasTarget
            AT-TPC representation of the gas target from the experiment.
        


        """
        brho = self.data.select("brho").to_numpy().flatten()
        momentum = brho * float(self.targetlike.Z) * QBRHO_2_P
        kinetic_energy = np.sqrt(momentum**2.0 + self.targetlike.mass**2.0) - self.targetlike.mass
        polar = self.data.select('polar').to_numpy().flatten()
        az = self.data.select('azimuthal').to_numpy().flatten()
        ex = self.missing_mass_technique(target_material)
        polar_cm = self.angular_distribution(target_material)


        results["brho"] = np.append(results["brho"],brho)
        results["kinetic_energy"] = np.append(results["kinetic_energy"],kinetic_energy)
        results["polar"] = np.append(results["polar"],polar)
        results["az"] = np.append(results["az"],az)
        results["redchisq"] = np.append(results["redchisq"], az)
        results["vertex_x"] = np.append(results["vertex_x"], self.data.select("vertex_x").to_numpy().flatten())
        results["vertex_y"] = np.append(results["vertex_y"], self.data.select("vertex_y").to_numpy().flatten())
        results["vertex_z"] = np.append(results["vertex_z"], self.data.select("vertex_z").to_numpy().flatten())
        results["ex"] = np.append(results["ex"], ex)
        results["polar_cm"] = np.append(results["polar_cm"],polar_cm)
        
    



    def kinematic_curve(self, 
                       projectile_energy: float, 
                       beamlike_excitations: np.ndarray, 
                       ngrid: int = 1000, 
                       cm_range: tuple[float,float] = (0,np.pi)
                       )->np.ndarray:
        """ 
        Calculates the theoretical two-body kinematics curves (KE vs Polar). 

        Generates laboratory-frame kinetic energy vs polar angle for each specified excitation energy
        of the beam-like residual. 
        
        Parameters
        ----------
        projectile_energy: float
            Beam energy in MeV.
        
        beamlike_excitations: np.ndarray 
            Excitation energies of the beam-like residual in MeV.
        
        ngrid: int, optinal
            Number of angular grid points per excitation energy. 
            Default is 1000. 
        
        cm_range: np.ndarray, optional
            Lower and upper center-of-mass angular limits in radians. 
            Default is [0,pi]
        
        Returns
        -------
        np.ndarray
            Array with shape ``(n_excitations, ngrid, 2)``.
            The last axis contains:

            - ``[..., 0]``: Laboratory-frame polar angle.
            - ``[..., 1]``: Kinetic energy of the target-like ejectile in MeV.
        """
        cm_angle_range = np.linspace(cm_range[0], cm_range[1], ngrid)
        eject_kinematics = np.zeros((len(beamlike_excitations), len(cm_angle_range), 2))
        beam_vector = vector.array({
            "px": [0.0],
            "py": [0.0],
            "pz": [np.sqrt(projectile_energy*(projectile_energy + 2.0*self.projectile.mass))], 
            "E": [projectile_energy + self.projectile.mass]
        })

        parent_vector = self.construct_target_vector() + beam_vector 
        parent_vector_cm = parent_vector.boostCM_of(parent_vector)
        for idx, ex in enumerate(beamlike_excitations):
            ejectile_energy = (self.targetlike.mass**2 - (self.beamlike.mass+ex)**2 
                               + parent_vector_cm.E**2) / (2*parent_vector_cm.E)
            ejectile_momentum = np.sqrt(ejectile_energy**2 - self.targetlike.mass**2)
            ejectile_vector_cm = vector.array({
                "px": ejectile_momentum*np.sin(np.pi-cm_angle_range), 
                "py": np.zeros(len(cm_angle_range)),
                "pz": ejectile_momentum*np.cos(np.pi-cm_angle_range),
                "E": np.full(len(cm_angle_range), ejectile_energy)
            })
            ejectile_vector_lab = ejectile_vector_cm.boost(parent_vector)
            eject_kinematics[idx, :, 0] = ejectile_vector_lab.theta
            eject_kinematics[idx, :, 1] = ejectile_vector_lab.E - self.targetlike.mass
        return eject_kinematics

