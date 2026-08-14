## ATTPC Analysis
General Comments: 
1. Not pip installed yet, therefore, you need to specify the path for this folder.  
2. Files should be saved in lowercase and underscores. 

Contains the functions with the analysis methods using the classes from `spyral-utils` and `attpc_spyral`. 
- **attpc_analysis**: Holds the functions
    - **executables**: Python scripts that can ran in the terminal
        - `cluster_viewer.py`: Reads external file or terminal command for viewing pointcloud with their cluster. 
        - **config**: 
            - `cluster_viewer.json`: Json file that runs along `cluster_viewer.py`. 
    - **notebooks** : Examples of the schematics for using the functions in **src**.
        - `examine_analysis.ipynb`: Analysis notebook post-intepolation phase. 
    - **src**: Folder necessary for pip installation ***(work in progress...)***.
        - **data_models**: Physics equations and conversions.
            - `physics.py`: Includes the handling of the reaction kinematics with their respective vector construction.
            - `threebodydecay.py` : Holds physics for three particle decay such as Dalitz plots. 
            - `calculations.py` : (TENTATIVE NAME) Contains selection rules calculations.
        - **detector_settings**: Classes that removes some detector settings code procedures 
            - `energy_loss_setup.py` : Reduced procedure for obtaining the energy loss of the detectors: IC, ATTPC and combination of both IC+ATTPC. 
        - **load**
            - `io.py`: Loads data from the point cloud, cluster, estimation and interpolation files. 


# Future Improvements 
> [!IMPORTANT]
> This are personal notes for developers
The improvements of `attpc_analysis` will be ranked by priority.
Weekly Weight-lifting tasks are strikethrough. 

1. Organize folders for pip installation.
2. Add functions for pip install 