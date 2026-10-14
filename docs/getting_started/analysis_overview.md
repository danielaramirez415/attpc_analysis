# Analysis Overview

The workflow of the project is heavily relies in the `/src/` files which holds the usable classes. 

``` mermaid
graph LR
    Repository["<b>AT-TPC Analysis Repository</b> <br/><br/>• Open HDF5<br/>• Physics Classes"];
    Executables["<b>Executables</b> <br/><br/>• Cluster Viewer<br/>• Two Body Spectrum<br/>• Bit Flip Diagnosis"];
    Notebooks["<b>Notebooks Template</b>" <br/><br/>• Examine Analysis <br/> • Examine Fusion];

    Repository --> Executables;
    Repository --> Notebooks;
    User((("User input"))) -->|"<b>Config</b>"| Executables & Notebooks;
    Executables --> Outcome["Your Physics Result"];
    Notebooks --> Outcome[["Your Physics Result"]];
```

Therefore, you will need to keep track of your configuration files inputs, rather than manually writing the data in the notebooks. 