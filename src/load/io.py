from dataclasses import dataclass 
from pathlib import Path 

from spyral_utils.nuclear import NucleusData
from spyral.core.point_cloud import PointCloud
from spyral.core.cluster import Cluster, Direction
import polars as pl
import h5py as h5


@dataclass(frozen=True)
class RunPointCloudDataLoader: 
    """
    Load data from the point cloud phase, and convert it to PointCloud

    Attributes
    ----------
    pointcloud_result_path: Path
        Path to your pointcloud folder
    """
    pointcloud_result_path : Path 
    def pointcloud_path(
            self, 
            run: int
        ) -> Path: 
        """
        Opens the PointCloud hdf5 of the given run.

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        Path
            Path to the file.
        """
        return (
            self.pointcloud_result_path / f"run_{run:04d}.h5"
        )
    def load_pointcloud(
            self, 
            run: int, 
            event: int
        ) -> PointCloud | None :
        """
        Loads PointCloud class from Spyral of the given run and event. 

        Parameters
        ----------
        run: int
            Run of the experiment.
        event: int 
            Event of interest. 

        Returns
        -------
        PointCloud | None
            PointCloud of the event of interest. 
        """
        path = self.pointcloud_path(run)
        if not path.exists():
            return None
        point_file = h5.File(path,'r')
        cloud_group : h5.Group = point_file.get("cloud")
        event_data = cloud_group[f"cloud_{event}"]
        cloud = PointCloud(event, event_data[:].copy())
        return cloud

        
    # Practical conditions to self check!
    def run_exists(
            self, 
            run: int
        )->bool:
        """
        Confirms if the Point Cloud file exists.  

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        bool
            File exist or not.
        """
        return self.pointcloud_path_path(run).exists()

    
@dataclass(frozen=True)
class RunClusterDataLoader:
    """
    Load data from the Cluster.h5 file, and convert it to Cluster

    Attributes
    ----------
    cluster_result_path: Path
        Path to your Cluster folder
    """
    cluster_result_path : Path 
    def cluster_path(
            self,
            run: int
        ) -> Path:
        """
        Opens the Cluster hdf5 of the given run.

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        Path
            Path to the file.
        """
        return (
            self.cluster_result_path / f"run_{run:04d}.h5"
        )
    
    def load_event_group(
            self, 
            run: int, 
            event: int
        ) -> h5.Group | None: 
        """
        Loads the h5.Group of the clusters from an event.

        Parameters
        ----------
        run: int
            Run of the experiment.
        event: int 
            Event of interest. 

        Returns
        -------
        h5.Group | None
            Clusters group.
        """
        path = self.cluster_path(run)
        if not path.exists():
            return None 
        cluster_file = h5.File(path,"r")
        cluster_group = cluster_file["cluster"]
        event_group = cluster_group[f"event_{event}"]
        return event_group
    
    def load_cluster(
            self, 
            run: int, 
            event: int, 
            cluster_index: int
        ) -> Cluster | None: 
        """
        Loads specific cluster.

        Parameters
        ----------
        run: int
            Run of the experiment.
        event: int 
            Event of interest. 
        cluster_index: int 
            Index of the cluster (careful with labels).

        Returns
        -------
        Cluster | None
            Extracts the specific cluster 
        """
        event_group = self.load_event_group(run, event)
        if event_group is None: 
            return None
        local_cluster = event_group[f"cluster_{cluster_index}"]
        cluster = Cluster(event,local_cluster.attrs["label"], Direction(local_cluster.attrs["direction"]),local_cluster["cloud"][:].copy())
        return cluster

    def load_clusters(
            self, 
            run: int, 
            event: int
        ) -> list[Cluster] | None:
        """
        Gets Cluster list of all the found clusters in an event.

        Parameters
        ----------
        run: int
            Run of the experiment.
        event: int 
            Event of interest. 

        Returns
        -------
        list[Cluster] | None
            All the cluster class of the event.
        """
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
    """
    Loads data from the Estimation parquet file, and converts it into dataframe.

    Attributes
    ----------
    estimation_result_path: Path
        Path to your Estimation folder with parquet files.
    empty_files: list
        List where you would like to hold the information of the runs without your particle of interest.
    """
    estimation_result_path: Path 
    empty_files: list[int] | None

    def estimation_path(
            self, 
            run:int
        ) ->Path:
        """
        Opens the Estimation parquet file of the given run.

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        Path
            Path to the file.
        """
        return (
            self.estimation_result_path / f"run_{run:04d}.parquet"
        )
    
    def load_estimation(
            self, 
            run:int
        ) -> pl.DataFrame | None: 
        """
        Loads Estimation file and converts it into a polars data frame. 

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        pl.DataFrame | None
            Estimate output
        """
        path = self.estimation_path(run)
        if not path.exists():
            self.empty_files.append(run)
            return None
        
        return pl.read_parquet(path) 
    
    # Practical conditions to self check!
    def run_exists(
            self, 
            run: int
        )->bool:
        """
        Confirms if the estimation parquet file exists.  

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        bool
            File exist or not.
        """
        return self.estimation_path(run).exists()


@dataclass(frozen=True)
class RunSolverDataLoader:
    """
    Loads Solver parquet files and convert them into dataframes.

    Attributes
    ----------
    solver_result_path: Path
        Path to your Estimation folder with parquet files.
    particle: NucleusData 
        Nucleus to analyse. 
    empty_files: list
        List where you would like to hold the information of the runs without your particle of interest.
    """
    solver_result_path: Path 
    particle: NucleusData 
    empty_files: list[int] | None

    def solver_path(
        self, 
        run: int) -> Path:
        """
        Opens the Solver parquet file of the given run and nucleus.

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        Path
            Path to the file.
        """ 
        return (
            self.solver_result_path / f"run_{run:04d}_{self.particle.isotopic_symbol}.parquet"
        )
    
    def load_solver(
            self, 
            run: int
        )-> pl.DataFrame | None:
        """
        Loads Solver parquet file and converts it into a polars data frame. 

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        pl.DataFrame | None
            Solver output.
        """
        path = self.solver_path(run)
        if not path.exists():
            self.empty_files.append(run)
            return None
        
        return pl.read_parquet(path)
    
    # Practical conditions to self check! 
    def run_exists(
            self, 
            run: int
        ) -> bool:
        """
        Confirms if the solver parquet file exists.  

        Parameters
        ----------
        run: int
            Run of the experiment.

        Returns
        -------
        bool
            File exist or not.
        """
        return self.solver_path(run).exists()
    



