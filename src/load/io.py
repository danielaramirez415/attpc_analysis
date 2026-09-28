from dataclasses import dataclass 
from pathlib import Path 

from spyral_utils.nuclear import NucleusData
from spyral.core.point_cloud import PointCloud
from spyral.core.cluster import Cluster, Direction
import polars as pl
import h5py as h5


@dataclass(frozen=True)
class RunPointCloudDataLoader: 
    """Load data from the point cloud phase, and convert it to PointCloud"""
    pointcloud_result_path : Path 
    def pointcloud_path(self, run: int) -> Path: 
        return (
            self.pointcloud_result_path / f"run_{run:04d}.h5"
        )
    def load_pointcloud(self, run: int, event: int) -> PointCloud | None :
        path = self.pointcloud_path(run)
        if not path.exists():
            return None
        point_file = h5.File(path,'r')
        cloud_group : h5.Group = point_file.get("cloud")
        event_data = cloud_group[f"cloud_{event}"]
        cloud = PointCloud(event, event_data[:].copy())
        return cloud

        
    # Practical conditions to self check!
    def run_exists(self, run: int)->bool:
        return self.pointcloud_path_path(run).exists()

    
@dataclass(frozen=True)
class RunClusterDataLoader:
    """Load data from the Cluster.h5 file, and convert it to Cluster """
    cluster_result_path : Path 
    def cluster_path(self, run: int) -> Path:
        return (
            self.cluster_result_path / f"run_{run:04d}.h5"
        )
    
    def load_event_group(self, run: int, event: int) -> h5.Group | None: 
        path = self.cluster_path(run)
        if not path.exists():
            return None 
        cluster_file = h5.File(path,"r")
        cluster_group = cluster_file["cluster"]
        event_group = cluster_group[f"event_{event}"]
        return event_group
    
    def load_cluster(self, run: int, event: int, cluster_index: int) -> Cluster | None: 
        event_group = self.load_event_group(run, event)
        if event_group is None: 
            return None
        local_cluster = event_group[f"cluster_{cluster_index}"]
        cluster = Cluster(event,local_cluster.attrs["label"], Direction(local_cluster.attrs["direction"]),local_cluster["cloud"][:].copy())
        return cluster

    def load_clusters(self, run: int, event: int) -> list[Cluster] | None:
        event_group = self.load_event_group(run, event)
        if event_group is None: 
            return None
        nclusters = event_group.attrs["nclusters"]
        if nclusters ==0: 
            return None 
        clusters : list[Cluster] = []
        for i in range(nclusters):
            local_cluster = event_group[f"cluster_{i}"]
            cluster =  Cluster(
                event,
                local_cluster.attrs["label"],
                Direction(local_cluster.attrs["direction"]), 
                local_cluster["cloud"][:].copy()
                )
            clusters.append(cluster)
        return clusters 
    




@dataclass(frozen=True)
class RunEstimationDataLoader:
    """Loads data from the Estimation parquet file, and converts it into dataframe"""
    estimation_result_path: Path 
    empty_files: list[int] | None

    def estimation_path(self, run:int) ->Path:
        return (
            self.estimation_result_path / f"run_{run:04d}.parquet"
        )
    
    def load_estimation(self, run:int) -> pl.DataFrame | None: 
        path = self.estimation_path(run)
        if not path.exists():
            self.empty_files.append(run)
            return None
        
        return pl.read_parquet(path) 
    
    # Practical conditions to self check!
    def run_exists(self, run: int)->bool:
        return self.estimation_path(run).exists()


@dataclass(frozen=True)
class RunSolverDataLoader:
    """Loads Solver parquet files and convert them into dataframes"""
    solver_result_path: Path 
    particle: NucleusData 
    empty_files: list[int] | None

    def solver_path(self, run: int) -> Path: 
        return (
            self.solver_result_path / f"run_{run:04d}_{self.particle.isotopic_symbol}.parquet"
        )
    
    def load_solver(self, run: int)-> pl.DataFrame | None:
        path = self.solver_path(run)
        if not path.exists():
            self.empty_files.append(run)
            return None
        
        return pl.read_parquet(path)
    
    # Practical conditions to self check! 
    def run_exists(self, run: int) -> bool:
        return self.solver_path(run).exists()
    



