# Configuration Files

With `Spyral` and `spyral-utils` installed, we can execute the notebooks and executables contained in the  `Github` repository. With the executables and notebooks, 
you must create a input configuration file. The templates of their respective configuration files are given in each section

- /attpc_analysis/notebooks/config/ : Configuration file used for all the notebooks. 
- /executables/config/ : Specific configuration files for each python script. 

## Notebooks Configuration File: `exp.yaml`
This configuration file will be defined in terms of your experiment. 

```yaml
paths_to_experiment: 
  workspace_path: "/path/to/your/workspace/folder/"
  trace_path: "/path/to/your/raw/data/folder"
  target_path:  "/path/to/your/json/gas/target/file"

runs: 
  run_min: 47 
  run_max: 74
  runs_to_skip : [59]

experiment_details: 
  beam_energy: 97.7 #MeV
  beam: [4,7] #[Z,A]
  target: [1,2]
  targetlike: [1,2]


detector_settings:
  ic_pressure: 600
  ic_min_val: 420
  ic_max_val : 600
```
### Paths to Experiment 
The above example lets the user write the path to their Spyral workspace, the raw data path and their gas target json path. 

### Runs
This is more intuitive. It contains which run range you would like to analyse with the option to skip some runs.

### Experiment Details 
Here goes the details of the experiment. It is suggested to check the `exp.yaml` directly as this could be one of the tabs with more changes across time. Among the experiment details, it is requested the **beam energy** in MeV, and the identity of the participant nucleus given in [Z,A]. Notice the analysis is given for **inverse kinematics**. 

### Detector Settings
The parameters given in this tab are those involved with the detector setup. In this case, in the ion chamber we got `ic_pressure`, and the allowed range to gate in the amplitude of the ic chamber with `ic_min_val` and `ic_max_val`.