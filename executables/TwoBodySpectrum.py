# Purpose of the code: 
# Selects the regions of the energy spectrum and visualize the tracks inside 



# SECTION: Assign a default path; in case the user open this file multiple times 
from pathlib import Path 
from json import load 
import sys

json_path = Path("./config/TwoBodySpectrum_default.json")
with open(json_path, "r") as json_file: 
    json_data = load(json_file)
    workspace_path = Path(json_data["workspace_path"])
    target_material_path = Path(json_data["target_path"])
    pid_path = Path(json_data["pid_path"])
    list_pids = json_data["pid_gates"]
    run_min = json_data["run_min"]
    run_max = json_data["run_max"]
    projectile_str = json_data["projectile"]
    target_str = json_data["target"]
    beam_energy = json_data["beam_energy"]
    particle_1_str = json_data["particle_1_Z_A"]
    particle_2_str = json_data["particle_2_Z_A"]

print("Importing libraries...")
import numpy as np
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import Axes3D
from spyral_utils.plot.histogram import Histogrammer
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# import from /src/
src_path = Path.cwd().parents[1]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from attpc_analysis.src.tinker.window_view import make_input_form
from attpc_analysis.src.load.io import RunSolverDataLoader, RunPointCloudDataLoader, RunClusterDataLoader, RunEstimationDataLoader
from attpc_analysis.src.data_models.physics import DataReactionKinematics, invariant_mass_technique
from attpc_analysis.src.detector_settings.energy_loss_setup import EnergyLossSetup


from spyral_utils.nuclear.nuclear_map import NuclearDataMap
from spyral_utils.nuclear.particle_id import deserialize_particle_id

import polars as pl
import matplotlib as mpl
cmap = mpl.colormaps["rainbow"]


# Create Main windows 
# SECTION: Open the window so the user can assign the input values 
import tkinter as tk 
print("Opening main window of spectrum viewer...")
window = tk.Tk()
window.attributes("-fullscreen")
window.title("Energy Spectrum using Invariant Mass")

# SUBSECTION: create frames for the input values given by the user 
top_row = tk.Frame(window)
top_row.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=5)

top_row1 = tk.Frame(top_row)
pixel = 10
top_row1.pack(side=tk.TOP, fill=tk.BOTH, expand=True,
            #    padx=(0,pixel), 
               pady=(0,2))
fields = ['Workspace Path',"Target Gas Path", "PID Path","PID Gates", 'Run min', 'Run max', "Projectile", "Target", "Beam Energy", "Particle 1 [Z,A]", "Particle 2 [Z,A]"]
entries = make_input_form(top_row1,fields)


# SUBSECTION: Create frame for the plot 
right_side = tk.Frame(window)
right_side.pack(side=tk.RIGHT, fill = tk.BOTH, expand=True, padx=10, pady=5)
plot_panel = tk.Frame(right_side)
plot_panel.pack(side=tk.TOP, fill = tk.BOTH, expand=True, padx=10, pady=5)




# Initialize 
pid_gates_string = ''
for i in list_pids: 
    if i == list_pids[-1]: 
        pid_gates_string+=i
    else:
        pid_gates_string += i +', '

entries['Workspace Path'].insert(tk.END,workspace_path)
entries["Target Gas Path"].insert(tk.END,target_material_path)
entries["PID Path"].insert(tk.END, pid_path)
entries["PID Gates"].insert(tk.END, pid_gates_string)
entries["Run min"].insert(tk.END,run_min)
entries["Run max"].insert(tk.END,run_max)
entries["Projectile"].insert(tk.END, f"{projectile_str[0]}, {projectile_str[1]}")
entries["Target"].insert(tk.END, f"{target_str[0]}, {target_str[1]}")
entries["Beam Energy"].insert(tk.END, beam_energy)
entries["Particle 1 [Z,A]"].insert(tk.END, f"{particle_1_str[0]}, {particle_1_str[1]}")
entries["Particle 2 [Z,A]"].insert(tk.END, f"{particle_2_str[0]}, {particle_2_str[1]}")



print("Working on physics procedures...")
# PREPARATIONL Create particles identities
nuclear_map = NuclearDataMap()
results = {}
particle_1 = nuclear_map.get_data(particle_1_str[0], particle_1_str[1])
particle_2 = nuclear_map.get_data(particle_2_str[0], particle_2_str[1])

def parse_za(value):
    if isinstance(value, str):
        z, a = map(int, value.replace(",", " ").split())
    else: 
        z, a = map(int,value)
    return z, a

# get_entries = entries["Particle 1 [Z,A]"].get()
# z1,a1 = parse_za(get_entries)
# print(z1,a1 )



def import_and_physics(workspace_path, target_material_path, run_min, run_max, projectile_str, target_str, beam_energy, particle_1_str, particle_2_str):
    # Get entries 
    projectile_za = parse_za(projectile_str)
    target_za = parse_za(target_str)
    particle_1_za = parse_za(particle_1_str)
    particle_2_za= parse_za(particle_2_str)

    global particle_1
    global particle_2
    particle_1 = nuclear_map.get_data(particle_1_za[0], particle_1_za[1])
    particle_2 = nuclear_map.get_data(particle_2_za[0], particle_2_za[1])
    projectile = nuclear_map.get_data(projectile_za[0], projectile_za[1])
    target = nuclear_map.get_data(target_za[0], target_za[1])


    solver_result_path = workspace_path/"InterpSolver"
    # Get the beam energy for the active area of the detector
    energy_loss_setup = EnergyLossSetup(
        beam_energy = beam_energy,
        projectile = projectile,
        attpc_target_path_json= target_material_path
    )

    target_material = energy_loss_setup.active_gas_target_material()
    proj_energy_start = energy_loss_setup.beam_energy_entrance_attpc()
    proj_energy_stop = energy_loss_setup.beam_energy_exit_attpc()



    # Organize the physics to do the thing I want
    empty_files = []

    # Load data loaders: for two particle's with the same value and different particles 
    if particle_1.isotopic_symbol == particle_2.isotopic_symbol: 
        data = RunSolverDataLoader(
            solver_result_path= solver_result_path,
            particle = particle_1,
            empty_files=empty_files
        )
    else: 
        data_1 = RunSolverDataLoader(
                solver_result_path,
                particle_1, 
                empty_files
        )
        data_2 = RunSolverDataLoader(
                solver_result_path,
                particle_2,
                empty_files = []
        )

    global results
    results = {}
    results["run"] = np.empty(0,int)
    results["event"] = np.empty(0,int)
    results["cluster_label"] = np.empty(0,int)
    results["cluster_index"] = np.empty(0,int)
    results["ex"] = np.empty(0,float)

    for run in range(run_min, run_max): 
        # If both particle are the same
        if particle_1.isotopic_symbol == particle_2.isotopic_symbol: 
            # Select events with two particle coincidence
            df = data.load_solver(run)
            if df is None: continue 
            events, counts = np.unique(df.select("orig_event").to_numpy().flatten(), return_counts=True)
            events = events[counts==2]
            df = df.filter(pl.col("orig_event").is_in(events))
            cluster_labels = df.select("cluster_label").to_numpy().flatten()
            cluster_index = df.select("cluster_index").to_numpy().flatten()

            # Produce Reaction
            reaction = DataReactionKinematics(
                data= df, 
                projectile= projectile,
                target=target,
                targetlike = particle_1, 
                beamlike = nuclear_map.get_data(projectile.Z+target.Z-particle_1.Z, projectile.A+target.A - particle_1.A), # not needed** 
                beam_energy_entrace_tpc= proj_energy_start
            )

            # Close dataframe 
            df = None

            # Do physics 
            targetlike_vector = reaction.construct_targetlike_vector()
            targetlike_vector1 = targetlike_vector[::2]
            targetlike_vector2 = targetlike_vector[1::2]

            energy_spectrum = invariant_mass_technique([targetlike_vector1, targetlike_vector2], nuclear_map.get_data(int(particle_1.Z*2), int(particle_2.A*2)))
        # If one particle is different that the other, 
        else:
            # Select events with the two particles 
            df_p1 = data_1.load_solver(run)
            df_p2 = data_2.load_solver(run)
            if df_p1 is None or df_p2 is None: continue
            events_p1, counts_p1 = np.unique(df_p1.select("orig_event").to_numpy().flatten(), return_counts=True)
            events_p1 = events_p1[counts_p1==1]

            events_p2, counts_p2 = np.unique(df_p2.select("orig_event").to_numpy().flatten(), return_counts=True)
            events_p2 = events_p2[counts_p2==1]

            # write coincidence events
            events = np.intersect1d(events_p1,events_p2)
            
            # Filter the data frames with events in coincidence
            df_p1 = df_p1.filter(pl.col("orig_event").is_in(events))
            cluster_labels_p1 = df_p1.select("cluster_label").to_numpy().flatten()
            cluster_index_p1 = df_p1.select("cluster_index").to_numpy().flatten()

            df_p2 = df_p2.filter(pl.col("orig_event").is_in(events))
            cluster_labels_p2 = df_p2.select("cluster_label").to_numpy().flatten()
            cluster_index_p2 = df_p2.select("cluster_index").to_numpy().flatten()

            cluster_labels = np.array([item for pair in zip(cluster_labels_p1, cluster_labels_p2) for item in pair]).flatten()
            cluster_index = np.array([item for pair in zip(cluster_index_p1, cluster_index_p2) for item in pair]).flatten()


            # Produce reaction particle 1
            reaction_p1 = DataReactionKinematics(
                    df_p1, projectile, target, particle_1, 
                    nuclear_map.get_data(projectile.Z + target.Z - particle_1.Z, projectile.A + target.A - particle_1.A), 
                    proj_energy_start
            )

            reaction_p2 = DataReactionKinematics(
                    df_p2, projectile, target, particle_2, 
                    nuclear_map.get_data(projectile.Z+target.Z - particle_2.Z, projectile.A + target.A - particle_2.A), 
                    proj_energy_start
                    )

            # Close dataframes 
            df_p1 = None 
            df_p2 = None
            # Do physics 
            targetlike_vector1 = reaction_p1.construct_targetlike_vector()
            targetlike_vector2 = reaction_p2.construct_targetlike_vector()
            energy_spectrum = invariant_mass_technique([targetlike_vector1, targetlike_vector2], nuclear_map.get_data(int(particle_1.Z) + int(particle_2.Z), int(particle_1.A) + int(particle_2.A)))
            
            
        # Save information 
        results["run"] = np.append(results["run"], np.full(len(events),run))
        results["event"] = np.append(results["event"], events)
        results["cluster_label"] = np.append(results["cluster_label"], cluster_labels)
        results["cluster_index"] = np.append(results["cluster_index"], cluster_index)
        results["ex"] = np.append(results["ex"], energy_spectrum)
    create_energy_spectrum_plot(results,10,30,100,10,30)


index_view = 0
events_to_view = 0

def create_energy_spectrum_plot(data,min_bin,max_bin, bin_width_keV,min_cut, max_cut):  
    print("cleaning plots")
    for ax in fig.axes:
        ax.clear()
    global particle_1
    global particle_2
    # Fill spectrum with new first event 
    #Initialize point cloud 
    mask = (data["ex"]> min_cut ) & (data["ex"]<max_cut)
    mask2 = [item for pair in zip(mask,mask) for item in pair]
    global index_view
    index_view =0 
    global events_to_view
    events_to_view = sum(mask)
    pointcloud_viewer(data["run"][mask][index_view], data["event"][mask][index_view], data["cluster_label"][mask2])
    #Empty the input
    cluster_entries["run"].delete(0,tk.END)
    cluster_entries["event"].delete(0,tk.END)

    cluster_entries["run"].insert(tk.END,data["run"][mask][0])
    cluster_entries["event"].insert(tk.END, data["event"][mask][0])


    # fill complete spectrum
    bins = int((max_bin-min_bin)/(bin_width_keV/1000))
    bin_width_keV =  1000*(max_bin-min_bin)/(bins)
    grammer.add_hist1d("invariant_mass", bins,(min_bin,max_bin))
    grammer.fill_hist1d("invariant_mass",data["ex"])
    hist = grammer.get_hist1d("invariant_mass")

    ax_spectrum.set_title(f"Events inside gate: {events_to_view}")
    ax_spectrum.stairs(hist.counts,edges=hist.bins)
    parent_nucleus = nuclear_map.get_data(particle_1.Z + particle_2.Z, particle_1.A + particle_2.A)
    ax_spectrum.set_xlabel(f"{parent_nucleus.get_latex_rep()} Energy Spectrum")
    ax_spectrum.set_ylabel(f"Counts / {bin_width_keV:0.2f} keV")
    ax_spectrum.axvline(min_cut, linestyle='--',color='black')
    ax_spectrum.axvline(max_cut, linestyle='--',color="black")
    canvas.draw_idle()


def pointcloud_viewer(run, event, cluster_labels):
    global particle_1
    global particle_2
    
    pointcloud_file = RunPointCloudDataLoader(
        pointcloud_result_path= workspace_path /"Pointcloud"
    )
    cluster_file = RunClusterDataLoader(
        cluster_result_path=workspace_path /"Cluster"
    )

    estimation_file = RunEstimationDataLoader(
        estimation_result_path = workspace_path/"Estimation",
        empty_files=[]
    )
    # Open files 
    cloud = pointcloud_file.load_pointcloud(run, event)
    clusters = cluster_file.load_clusters(run,event)
    # Import estimation data frame 
    df = estimation_file.load_estimation(run)
    df = df.filter(pl.col("orig_event")==event)

    if cloud == None or clusters == None: 
        print(f"Problem with run {run} and event {event}!")
        return None

    # Clear plots
    ax_padxy.clear()
    ax_pid.clear()
    # Fill plots: first pointcloud plot
    ax_padxy.scatter(cloud.data[:,0], cloud.data[:,1], color='black', s=1)
    
    for cluster in clusters: 
        if len(cluster.data[:,2]) < 30: continue
        if cluster.label == cluster_labels[0]: 
            ax_padxy.scatter(cluster.data[:,0], cluster.data[:,1], s=3, 
                    label=f"Cluster {cluster.label}: {particle_1.get_latex_rep()}",color='red')
        elif cluster.label == cluster_labels[1]: 
            ax_padxy.scatter(cluster.data[:,0], cluster.data[:,1], s=3, 
                    label=f"Cluster {cluster.label}: {particle_2.get_latex_rep()}",color='blue')
        else:
            ax_padxy.scatter(cluster.data[:,0], cluster.data[:,1], s=3, label=f"Cluster {cluster.label}")

    # second pid plot 
    estimation_clusters = df.select("cluster_label").to_numpy().flatten()
    estimation_dedx = df.select("sqrt_dEdx").to_numpy().flatten()
    estimation_brho = df.select("brho").to_numpy().flatten()
    for row in range(len(estimation_clusters)):
        if int(estimation_clusters[row]) == cluster_labels[0]: 
            ax_pid.scatter(estimation_dedx[row],estimation_brho[row], color='red',label=f'Cluster {estimation_clusters[row]}')
        elif int(estimation_clusters[row]) == cluster_labels[1]: 
            ax_pid.scatter(estimation_dedx[row],estimation_brho[row], color='blue',label=f'Cluster {estimation_clusters[row]}')
        else: 
            ax_pid.scatter(estimation_dedx[row],estimation_brho[row],label=f'Cluster {estimation_clusters[row]}')


    # If you wanna see the old gates 

    colors = cmap(np.linspace(0,1,len(list_pids)))
    for i in range(len(list_pids)):
        pid= deserialize_particle_id(pid_path/list_pids[i], nuclear_map)
        x_array,y_array = [],[]
        for x,y in pid.cut.get_vertices():
            x_array.append(x)
            y_array.append(y)
        ax_pid.plot(x_array,y_array,linestyle='--', linewidth=3,color=colors[i],label=pid.nucleus.get_latex_rep())

    global index_view
    global events_to_view
    ax_padxy.set_title(f"Event Viewed {index_view+1}/{events_to_view}")
    ax_padxy.legend()
    ax_padxy.set_xlim([-300,300])
    ax_padxy.set_ylim([-300,300])
    ax_padxy.set_aspect('equal')

    ax_pid.set_ylim(0,2)
    ax_pid.set_xlim(0,80)
    ax_pid.legend()




def next_pointcloud(data, min_cut,max_cut):
    # Select in the data
    mask = (data["ex"]> min_cut ) & (data["ex"]<max_cut)
    mask2 = [item for pair in zip(mask,mask) for item in pair]

    # Extract global 
    global index_view
    index_view+=1
    pointcloud_viewer(data["run"][mask][index_view], data["event"][mask][index_view], data["cluster_label"][mask2][2*index_view:2*index_view+2])
    #Empty the input
    cluster_entries["run"].delete(0,tk.END)
    cluster_entries["event"].delete(0,tk.END)
    # Insert details of new event
    cluster_entries["run"].insert(tk.END,data["run"][mask][index_view])
    cluster_entries["event"].insert(tk.END, data["event"][mask][index_view])
    canvas.draw_idle()



def previous_pointcloud(data, min_cut,max_cut):
    # Select in the data
    mask = (data["ex"]> min_cut ) & (data["ex"]<max_cut)
    mask2 = [item for pair in zip(mask,mask) for item in pair]

    # Extract global 
    global index_view
    index_view-=1
    pointcloud_viewer(data["run"][mask][index_view], data["event"][mask][index_view], data["cluster_label"][mask2][2*index_view:2*index_view+2])
    #Empty the input
    cluster_entries["run"].delete(0,tk.END)
    cluster_entries["event"].delete(0,tk.END)
    # Insert details of new event
    cluster_entries["run"].insert(tk.END,data["run"][mask][index_view])
    cluster_entries["event"].insert(tk.END, data["event"][mask][index_view])
    canvas.draw_idle()

button = tk.Button(top_row1,text="Upload",
                   command = lambda: import_and_physics( 
                       Path(entries['Workspace Path'].get()),
                       Path(entries["Target Gas Path"].get()),
                       int(entries["Run min"].get()),
                       int(entries["Run max"].get()),
                       entries["Projectile"].get(), 
                       entries["Target"].get(), 
                       float(entries["Beam Energy"].get()), 
                       entries["Particle 1 [Z,A]"].get(),
                       entries["Particle 2 [Z,A]"].get()
                       )
                    )

button.pack(side=tk.BOTTOM, pady=10)



# Insert plot 
fig = Figure(figsize=(18,14), dpi=100)
grid_plot = fig.add_gridspec(2,3)
ax_spectrum = fig.add_subplot(grid_plot[:2,:2]) # section for the spectrum 
ax_padxy = fig.add_subplot(grid_plot[0,2]) 
ax_pid = fig.add_subplot(grid_plot[1,2])
# ax_pad3d = fig.add_subplot(grid_plot[1,2], projection='3d')
canvas = FigureCanvasTkAgg(fig, master = plot_panel)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack()
grammer = Histogrammer()



# SUBSECTION: create frames for the input values given by the user 
# Show spectrum
top_row2 = tk.Frame(top_row)
top_row2.pack(side=tk.TOP, fill=tk.BOTH, expand=True, 
            #   padx=pixel/2, 
              pady=2)
fields = ['bin min','bin max', 'bin width (keV)', 'Ex min', 'Ex max']
spectrum_entries = make_input_form(top_row2,fields)

spectrum_entries['bin min'].insert(tk.END,10)
spectrum_entries['bin max'].insert(tk.END,30)
spectrum_entries['bin width (keV)'].insert(tk.END,100)
spectrum_entries['Ex min'].insert(tk.END,10)
spectrum_entries['Ex max'].insert(tk.END,30)


button = tk.Button(top_row2,text="Update Spectrum",
                   command = lambda: update_spectrum( 
                       int(spectrum_entries['bin min'].get()),
                       int(spectrum_entries['bin max'].get()),
                       float(spectrum_entries['bin width (keV)'].get()),
                       float(spectrum_entries['Ex min'].get()),
                       float(spectrum_entries['Ex max'].get())
                       ))

button.pack(side=tk.BOTTOM, pady=10)



# Create cluster view 
top_row3 = tk.Frame(top_row)
top_row3.pack(side=tk.TOP, fill=tk.BOTH, expand=True, 
            #   padx=(pixel,0), 
              pady=(2,0))
fields = ["run","event"]
cluster_entries = make_input_form(top_row3,fields)
#Next button 
top_row3_col1 = tk.Frame(top_row)
top_row3_col1.pack(side=tk.RIGHT, padx=(2,2))
button = tk.Button(top_row3_col1, text="Next",  
                   command = lambda : next_pointcloud(
                       results, 
                       float(spectrum_entries['Ex min'].get()),
                       float(spectrum_entries['Ex max'].get()))
                   )

button.pack(side=tk.BOTTOM, pady=10)


# Previous button 
top_row3_col2 = tk.Frame(top_row)
top_row3_col2.pack(side=tk.LEFT, padx=(2,2))
button = tk.Button(top_row3_col2, text="Previous",  
                   command = lambda : previous_pointcloud(
                       results, 
                       float(spectrum_entries['Ex min'].get()),
                       float(spectrum_entries['Ex max'].get()))
                   )

button.pack(side=tk.BOTTOM, pady=10)

# initialize and do magic
import_and_physics(workspace_path,target_material_path,run_min, run_max, projectile_str, target_str, beam_energy, particle_1_str, particle_2_str)



def update_spectrum(min_bin,max_bin, bin_width_keV,min_cut, max_cut):
    create_energy_spectrum_plot(results,min_bin,max_bin, bin_width_keV,min_cut, max_cut)





window.mainloop()
