from pathlib import Path
import h5py as h5 

def find_merger_version(path: Path ,run_number: int)->str:
    """Finds the Merger Version used for the experiment"""
    file = h5.File(path,"r")
    if "meta" in file: 
        version : str =  "MergerLegacyReader"
    elif "events" in file: 
        version: str = file["events"].attrs["version"]
        print(version, "open trace_reader.py line 42 to see which folder you use")
    file.close()
    return version