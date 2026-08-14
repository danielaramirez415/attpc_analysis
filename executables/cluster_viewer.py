#!/usr/bin/env python3


# load configuration file 
import sys 
from pathlib import Path 
from json import load 
import polars as pl



# Import the configuration file 
if len(sys.argv)>1:
    json_path = str(sys.argv[1])
    with open(json_path,"r") as json_file: 
        json_data = load(json_file)
        workspace_path = Path(json_data["workspace_path"]) #type: str
        read_csv = json_data["read_csv"] # type: bool
        path_to_csv = Path(json_data["path_to_csv"])
        output_folder = Path(json_data["save_in_folder"]) # type: str

else: 
    raise Exception(f"Execute: python cluster_viewer.py config.json")

# Conditions for saving the pdf 
steps =  20 # Events per file : hard coded 
runs = []
events = []

if read_csv: 
    data  = pl.read_csv(path_to_csv)
    runs = data["run"].to_numpy().flatten()
    events = data["event"].to_numpy().flatten()


print("Importing all the libraries...")
import numpy as np
from spyral.geometry.circle import generate_circle_points
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt



src_path = Path.cwd().parents[1]
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
from attpc_analysis.src.load.io import RunPointCloudDataLoader, RunClusterDataLoader

# Plot details 
DEFAULT_COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
def get_color(value: int) -> str:
    color_index = value
    if color_index >= len(DEFAULT_COLORS):
        color_index = color_index % len(DEFAULT_COLORS)
    elif color_index == -1:
        return "black"
    return DEFAULT_COLORS[color_index]


# plot detector outer edge 
detector_pad_radius = 274.19204672201533 # check with Daniel
theta_range = np.linspace(0, 2*np.pi, 20)
detector_length = 1000
z_range = np.linspace(0,detector_length, 10)
edge_region = generate_circle_points(0.,0.0, detector_pad_radius)


theta_wire, z_wire = np.meshgrid(theta_range, z_range)
x_outer =  detector_pad_radius * np.cos(theta_wire)
y_outer =  detector_pad_radius * np.sin(theta_wire)

#inner region 
beam_region_radius = 25
x_beam = beam_region_radius*np.cos(theta_wire)
y_beam = beam_region_radius*np.sin(theta_wire)
beam_region = generate_circle_points(0., 0., beam_region_radius)


# Create class frames 
pointcloud_file = RunPointCloudDataLoader(
    pointcloud_result_path= workspace_path / "Pointcloud"
)

cluster_file = RunClusterDataLoader(
    cluster_result_path= workspace_path / "Cluster"
)

# Save "steps" figures per file 
total_events = len(events)
files_created =  total_events//steps if total_events%steps==0 else total_events //steps + 1

print("Events:", total_events)
print("Files to create:", files_created)



for nfile in range(0,files_created):
    single_file_path = output_folder/ f"event_viewer_{nfile}.pdf"
    events_saved = 0 
    with PdfPages(single_file_path) as pdf_pages: 
        print(f"Working on {single_file_path} pdf")
        # define parameters for the for loop in terms of the open file
        row = nfile*steps
        for idx in range(0,steps): 
            row += 1
            # print("File", nfile, "Row",row)
            # Open Point Cloud and Cluster files
            cloud = pointcloud_file.load_pointcloud(runs[row],events[row])
            clusters = cluster_file.load_clusters(runs[row],events[row])
            if cloud == None or clusters == None: 
                continue

            # Plot point cloud and cluster
            plt.close()
            fig, axs = plt.subplot_mosaic(
                """
                AAB
                """,
                per_subplot_kw={
                    "A": {
                        "projection": "3d", 
                        "box_aspect": (2,1,1),
                        "aspect": "equalxy"
                    },
                    "B" :{
                        "box_aspect": 1
                    }
                },
                figsize=(15.0, 5.0),
                constrained_layout=True
            )

            axs["A"].scatter(cloud.data[:,2], cloud.data[:,0], cloud.data[:,1],color='black', s=1)
            axs["B"].scatter(cloud.data[:,0], cloud.data[:,1],color='black', s=1)
            for cluster in clusters: 
                axs["A"].scatter(cluster.data[:,2], cluster.data[:,0], cluster.data[:,1],color=get_color(cluster.label), s=3, label=f"Cluster {cluster.label}")
                axs["B"].scatter(cluster.data[:,0], cluster.data[:,1], color=get_color(cluster.label), s=3, label=f"Cluster {cluster.label}")
            # Draw Detector: 
            axs["A"].plot_wireframe(z_wire,x_outer,y_outer, color='black', alpha=0.4)
            axs["A"].plot_wireframe(z_wire,x_beam,y_beam, color='lime', alpha=0.4)
            axs["B"].plot(beam_region[:, 0], beam_region[:, 1], color='lime')#,label="Beam Region")
            axs["B"].plot(edge_region[:, 0], edge_region[:, 1], color='lime')

            axs["A"].set_xlim3d([0,1000])
            axs["A"].set_ylim3d([-300,300])
            axs["A"].set_zlim3d([-300,300])
            axs["A"].set_xlabel("Z(mm)")
            axs["A"].set_ylabel("X(mm)")
            axs["A"].set_zlabel("Y(mm)")
            axs["A"].grid()
            axs["A"].legend()

            axs["B"].set_xlim([-300,300])
            axs["B"].set_ylim([-300,300])
            axs["B"].set_xlabel("X(mm)")
            axs["B"].set_ylabel("Y(mm)")
            axs["B"].grid()
            axs["B"].legend()
            
            # Add figure to pdf
            fig.suptitle(f"Run:{runs[row]} Event: {events[row]}")
            pdf_pages.savefig(fig)
            plt.close(fig)

            #if it reached end of csv 
            if (runs[-1]==runs[row]) and (events[-1]==events[row]): break


        # Open a new file
        pass 

print("Thanks for your patience! ")


