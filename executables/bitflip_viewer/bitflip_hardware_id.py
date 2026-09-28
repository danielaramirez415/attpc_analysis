# SECTION: Address paths with Json and terminal variables
import sys 
from pathlib import Path 
from json import load 


# Instead of input configuration: do a default run 

json_path = Path("./default/bitflip.json") 
with open(json_path, "r") as json_file: 
    json_data = load(json_file) 
    trace_path = Path(json_data["trace_path"])
    run_number = json_data["run_number"]
    event_number = json_data["event_number"]
    cutoff_diff = json_data["cutoff_diff"]




# SECTION: Import libraries uses NUMBA! 
print("Importing libraries.")
import h5py as h5 
from spyral import GetParameters, ARGONNE2023_MAP
from spyral.core.config import AVAILABLE_MAPS
from spyral.core.hardware_id import fix_array_with_padmap, hardware_id_from_array
from numba import njit
import numpy as np
import matplotlib.pyplot as plt 
import tkinter as tk 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import colormaps


# import from /src/
src_path = Path.cwd().parents[2]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from attpc_analysis.src.load.compatibility import find_merger_version
from attpc_analysis.src.tinker.canvas_commands import make_on_select_x, check_pos, reset_x_axis_to_original, zoom_x_axis

cmap = colormaps['rainbow']
# -----------------------------------------(work in progress)-----------------------------------
# this must be interactive? 
get_params = GetParameters(
    trace_version = "v0",
    padmap = ARGONNE2023_MAP,
    baseline_window_scale=20,
    peak_separation=10, # 10
    peak_prominence=20, # 5
    peak_max_width=150,
    peak_threshold=20 # 40  
)
# ----------------------------------------------------------------------------------------------



# SECTION: Trace reader config 
trace_file_path = trace_path / f"run_{run_number:04d}.h5"
merger_version = find_merger_version(trace_file_path, run_number)
if merger_version != 'MergerLegacyReader':
    print("Your dataset is not compatible with the python script (yet)")
    print("Try again in the future :) \n ~ Dani")
    sys.exit(1)

 
def transform_data_to_5d(raw_data: np.ndarray, 
                         nCobos: int = 11, nAsAds: int=4, nAGets: int=4, nChannels: int=68) -> np.ndarray: 
    """
    It is more efficient to transform the raw data into a 5d array 
    10 Cobos, 4 Asads, 4 AGets, 64 Channels, 512 tb
    Cobo 10 is not activated for a2066 exp 
    IMPORNTANT: Ignore pad number for the moment! 
    """
    grid_5d = np.zeros((nCobos, nAsAds, nAGets, nChannels, 512))

    # extract hardward id 
    cobos_ids = raw_data[:,0].astype(np.int32)
    asads_ids = raw_data[:,1].astype(np.int32)
    agets_ids = raw_data[:,2].astype(np.int32)
    channels_ids = raw_data[:,3].astype(np.int32)
    waveforms = raw_data[:,5:]

    # map grid 
    grid_5d[cobos_ids,asads_ids,agets_ids,channels_ids,:] = waveforms

    return grid_5d

@njit 
def cobo_delta_trace(raw_data: np.ndarray, cobo: int, asad: int, aget: int)-> np.ndarray:
    # note: 1 cobo-> 4 asad -> 4 x (4 aget) -> 4 x 4 x (64 aget channels)
    # shape of the grid: 
    # (Cobo, AsAd, AGet, Channel)
    
    # Select AGet Circuit Board (64 x 512)  
    cobo_asad_aget = raw_data[cobo,asad,aget,:,:]

    # Save delta trace difference into new array 
    new_cobo_grid = np.zeros((len(cobo_asad_aget),511))
    
    # Loop over the 64 Channels
    for ichannel in range(cobo_asad_aget.shape[0]): 
        # Loop over the traces
        for i in range(cobo_asad_aget.shape[1]-1): 
            dtb = abs(cobo_asad_aget[ichannel,i+1] - cobo_asad_aget[ichannel,i])
            if 2**3 < dtb < cutoff_diff: 
                new_cobo_grid[ichannel,i] = dtb 
    
    return new_cobo_grid



 
# SUBSECTION : Open file and match padmap with real data
print("Default run and event number is running...") 



# Main Tkinter Window 
window = tk.Tk()
window.attributes("-fullscreen")
window.title(f"Bit-flip 10 Cobos: Cutoff Diff = {cutoff_diff}")

# Create frame for the input values 
top_row = tk.Frame(window) 
top_row.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)


# create frame for the plot 
plot_panel = tk.Frame(window)
# create frame for the plot 
plot_panel = tk.Frame(window)
plot_panel.pack(side=tk.BOTTOM, fill= tk.BOTH, expand =True, padx=10, pady=5) 


def initialize_file(run_number: int, event_number: int, printerbool: bool=True) -> np.ndarray: 
    if printerbool: print(f"Opening run: {run_number} and event: {event_number}.")
    event_name  = f"evt{event_number}_data" 
    file = h5.File(trace_file_path, "r") 
    get_group : h5.Group = file["get"]
    get_data : h5.Dataset = get_group[event_name]
    raw_data = get_data[:].copy()
    file.close()
    # Fix traces order using the experiment's padmap
    path_in_available_maps = False
    for nmap in AVAILABLE_MAPS:
        raw_data = fix_array_with_padmap(raw_data,nmap) 
        path_in_available_maps = True
    # Create an option in case the user has their own map, and it isn't available in the current Spyral version
    if not path_in_available_maps: 
        raw_data = fix_array_with_padmap(raw_data, get_params.padmap)
    
    # Transform data to 5d array 
    raw_data_5d = transform_data_to_5d(raw_data)   
    return raw_data_5d



def initialize_cobo_plots(raw_data_5d): 
    # Begin making it interactive 
    for ax in fig.axes: 
        ax.clear()
    # fig.selectors = []
    extract_xlims = []

    # 
    ncobo = 0 
    for nrow in range(rows):
        for ncol in range(cols): 
            cobo = [cobo_delta_trace(raw_data_5d, ncobo, i,j) for i in range(4) for j in range(4)]
            cobo = np.array(cobo).flatten()
            cobo = cobo[cobo>=2**3]
            # plot 
            ax = axs[nrow, ncol]
            ax.set_title(f"Cobo {ncobo}")
            counts, edges = np.histogram(cobo,bins=200)
            ax.stairs(counts,edges,edgecolor='black')
            ax.set_yscale("log")
            ax.set_xlim([0, cutoff_diff])
            for i, bit in enumerate(range(4,9,1)): 
                color_index = i/4 
                color = cmap(color_index)
                # only one histogram name the labels 
                if ncobo == 0: ax.axvline(2**bit,linestyle='--', label=2**bit,color=color)
                else: ax.axvline(2**bit,linestyle='--',color=color)
            extract_xlims.append(ax.get_xlim())
            ncobo+=1
            if ncobo==10: break 
        if ncobo == 10: break # just in case  

    fig.legend()
    # Save figures before creating canvas 
    print("Show plot...")
    # fig.savefig("./figures/cobos.png")
   
    # Zoom in and out 
    zoom_x_axis(fig, axs, canvas)
    # Hook the right-click event directly into Matplotlib's event manager
    reset_x_axis = reset_x_axis_to_original(canvas, cutoff_diff)
    fig.canvas.mpl_connect('button_press_event', reset_x_axis)

    


def create_aget_histograms(ncobo, nasad,raw_data_5d):
    subwin = tk.Toplevel(window)
    subfig = Figure(figsize=(16, 5), dpi=100)
    subaxs = subfig.subplots(1,4)
        
    subfig.suptitle(f"Cobo {ncobo} AsAd {nasad}")

    for n in range(4):
        aget = cobo_delta_trace(raw_data_5d,ncobo,nasad,n).flatten()
        aget = aget[aget>=2**3]
        ax = subaxs[n]
        ax.set_title(f"AGet {n}")
        counts, edges = np.histogram(aget,bins=50)
        ax.stairs(counts,edges,edgecolor='black')
        ax.set_xlim([0, cutoff_diff])
        ax.set_yscale("log")

    # fig.savefig(f"./figures/cobo_{ncobo}_asad_{nasad}.png")

    # Create subcanvas 
    subcanvas = FigureCanvasTkAgg(subfig, master = subwin)
    subcanvas_widget = subcanvas.get_tk_widget()
    subcanvas_widget.pack()#(fill=tk.BOTH, expand=True)
        
    # zoom into the x axis 
    zoom_x_axis(subfig, subaxs, subcanvas)

    for i in range(0,4): 
        for j, bit in enumerate(range(4,9,1)): 
            color_index = j/4 
            color = cmap(color_index)
            if i==0: subaxs[i].axvline(2**bit,linestyle='--', label=2**(bit),color=color)
            else: subaxs[i].axvline(2**bit,linestyle='--', color=color)
    subfig.legend()
    reset_x_axis = reset_x_axis_to_original(subcanvas, cutoff_diff)
    # Hook the right-click event directly into Matplotlib's event manager
    subfig.canvas.mpl_connect('button_press_event', reset_x_axis)
    subwin.mainloop()
        


def create_asad_histograms(entry,raw_data_5d):
    subwin = tk.Toplevel(window)
    subfig = Figure(figsize=(16, 5), dpi=100)
    subaxs = subfig.subplots(1,4)
        
    subfig.suptitle(f"Cobo {entry}")

    for n in range(4):
        asad = [cobo_delta_trace(raw_data_5d,entry,n,i) for i in range(4)]
        asad = np.array(asad).flatten()
        asad = asad[asad>=2**3]
        ax = subaxs[n]
        ax.set_title(f"AsAd {n}")
        counts, edges = np.histogram(asad,bins=200)
        ax.stairs(counts,edges,edgecolor='black')
        ax.set_yscale("log")
        ax.set_xlim([0, cutoff_diff])

    # fig.savefig(f"./figures/cobo_{entry}_asad.png")

    # Create subcanvas 
    subcanvas = FigureCanvasTkAgg(subfig, master = subwin)
    subcanvas_widget = subcanvas.get_tk_widget()
    subcanvas_widget.pack()#(fill=tk.BOTH, expand=True)
        
    # zoom into the x axis 
    zoom_x_axis(subfig, subaxs, subcanvas)

    for i in range(0,4): 
        for j, bit in enumerate(range(4,9,1)): 
            color_index = j/4 
            color = cmap(color_index)
            if i==0: subaxs[i].axvline(2**bit,linestyle='--', label=2**bit,color=color)
            else: subaxs[i].axvline(2**bit,linestyle='--', color=color)

    subfig.legend()
    reset_x_axis = reset_x_axis_to_original(subcanvas, cutoff_diff)
    # Hook the right-click event directly into Matplotlib's event manager
    subfig.canvas.mpl_connect('button_press_event', reset_x_axis)
    

    # Create Cobo Entry
    tk.Label(subwin, text="AsAd: ").pack(ipadx=0, ipady=0)
    entry_asad = tk.Entry(subwin)
    entry_asad.pack(ipadx=1, ipady=0)
    button = tk.Button(subwin, text="Show", command= lambda: create_aget_histograms(entry, int(entry_asad.get()),raw_data_5d))
    button.pack(ipadx=0, ipady=1, pady=20)

    subwin.mainloop()


# Create Cobo Entry
fields = ('Run', 'Event', 'Cobo') 
def makeform(window, fields): 
    entries = {} 
    for field in fields: 
        row = tk.Frame(window) 
        label = tk.Label(row, text=field+":",anchor='w') 
        entry = tk.Entry(row, width=10) 
        row.pack(side = tk.TOP, fill=tk.X, pady=2) 
        label.pack(side=tk.LEFT) 
        entry.pack(side=tk.LEFT, padx=5, fill= tk.X) 
        entries[field] = entry 
    return entries 

entries = makeform(top_row, fields) 

#Initialize run and event 
entries["Run"].insert(0,run_number)
entries["Event"].insert(0,event_number)

data = {
    "raw_data_5d" : initialize_file(int(entries["Run"].get()), int(entries["Event"].get()))
}

def update_run():
    data["raw_data_5d"] = initialize_file(int(entries["Run"].get()), int(entries["Event"].get()))
    initialize_cobo_plots(data["raw_data_5d"])


# Update Run
frame_row = tk.Frame(top_row)
frame_row.pack(side=tk.TOP,fill=tk.X, padx=5) 
button = tk.Button(frame_row, text="Update Run", command = update_run)
button.pack(side = tk.LEFT, pady=10)

# Show Specific Cobo
button = tk.Button(frame_row, text="Show Cobo", command = lambda: create_asad_histograms(int(entries["Cobo"].get()),data["raw_data_5d"]))
button.pack(side =tk.LEFT, pady=10)

rows, cols = 2,5
fig = Figure(figsize=(18, 12), dpi=100)
axs = fig.subplots(rows,cols)
#Create GUI - Canvas 
canvas = FigureCanvasTkAgg(fig, master = plot_panel)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()#(fill=tk.BOTH, expand=True)

# initialize the first time 
initialize_cobo_plots(data["raw_data_5d"])

# allow the window to not shutdown 
window.mainloop()





