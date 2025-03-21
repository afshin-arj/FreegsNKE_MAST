import os
import pickle
import gc
# import freegsnke
import xarray as xr
import pandas as pd
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from PIL import Image as PILImage
import math


def load_efm_data(shot_id, base_dir, group_efm):
    zarr_path = os.path.join(base_dir, f"{shot_id}.zarr", group_efm)
    if not os.path.exists(zarr_path):
        raise FileNotFoundError(f"Zarr directory for shot {shot_id} not found at {zarr_path}.")
    
    dataset = xr.open_zarr(zarr_path)
    print(f"Successfully loaded EFM data for shot {shot_id}.")
    return dataset


# --- Create active coil structure for MAST ---
# --- Active Coils (given) ---
eta_copper = 1.55e-8  # resistivity in Ohm*m

active_coils_dict = {}


# P2 definition
active_coils_dict["P2"] = {}

# Coil parameters
total_turns = 20
dR = 0.023
dZ = 0.035
spacing_R = 0.004
spacing_Z = 0.005
rect_width = 0.125
rect_height = 0.290
center_R = 0.49
center_Z = 1.76

# Compute R and Z boundaries
R_min = center_R - rect_width / 2
R_max = center_R + rect_width / 2
Z_min = center_Z - rect_height / 2
Z_max = center_Z + rect_height / 2

# Define the spacing constraints
left_boundary_spacing = 0.0215
right_boundary_spacing = 0.0
bottom_boundary_spacing = 0.0350
upper_boundary_spacing = 0.0200

# Compute available width and height for turn placement
available_width = rect_width - (left_boundary_spacing + right_boundary_spacing)
available_height = rect_height - (bottom_boundary_spacing + upper_boundary_spacing)

# Determine number of layers and turns per layer
layers_config = [4, 4, 4, 4, 2, 2]  # Bottom 4 layers (4 turns each), top 2 layers (2 turns each)
num_layers = len(layers_config)

# Calculate horizontal positions (R)
R_start = R_min + left_boundary_spacing
bottom_R_positions = [R_start + i * (dR + spacing_R) for i in range(4)]
top_R_positions = bottom_R_positions[:2]  # Top layers align with leftmost bottom turns

# Calculate vertical positions (Z)
Z_start = Z_min + bottom_boundary_spacing
layer_heights = [Z_start + i * (available_height / num_layers) for i in range(num_layers)]

# Initialize lists for coil positions
R_list = []
Z_list = []

# Distribute turns in each layer
for row, turns in enumerate(layers_config):
    row_Z = layer_heights[row]  # Assign Z position
    R_positions = bottom_R_positions if turns == 4 else top_R_positions  # Align top layers with left turns
    
    for R_pos in R_positions:
        R_list.append(R_pos)
        Z_list.append(row_Z)

# Store the coil data
active_coils_dict["P2"]["upper"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}
active_coils_dict["P2"]["lower"] = {
    "R": R_list,
    "Z": [-1 * z for z in Z_list],
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}


# P3 definition
active_coils_dict["P3"] = {}

total_turns_P3 = 8
dR = 0.020
dZ = 0.049
spacing_R = 0.004
spacing_Z = 0.005
rect_width = 0.112
rect_height = 0.216
center_R = 1.1
center_Z = 1.1

# Determine grid size
n_columns_P3 = math.floor(rect_width / (dR + spacing_R))  # in R direction
n_rows_P3 = math.ceil(total_turns_P3 / n_columns_P3)  # in Z direction

# Calculate the actual occupied space
actual_width = n_columns_P3 * (dR + spacing_R) - spacing_R
actual_height = n_rows_P3 * (dZ + spacing_Z) - spacing_Z

# Calculate rectangle edges
R_min_P3 = center_R - rect_width / 2
Z_min_P3 = center_Z - rect_height / 2

# Adjusted starting positions to center turns
R_min_adjusted = R_min_P3 + (rect_width - actual_width) / 2
Z_min_adjusted = Z_min_P3 + (rect_height - actual_height) / 2

# Build positions
R_list = []
Z_list = []

turn = 0
for row in range(n_rows_P3):
    for col in range(n_columns_P3):
        if turn >= total_turns_P3:
            break
        R_pos = R_min_adjusted + col * (dR + spacing_R)
        Z_pos = Z_min_adjusted + row * (dZ + spacing_Z)
        R_list.append(R_pos)
        Z_list.append(Z_pos)
        turn += 1

active_coils_dict["P3"]["upper"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}
active_coils_dict["P3"]["lower"] = {
    "R": R_list,
    "Z": [-1 * z for z in Z_list],
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}


# P4 definition
active_coils_dict["P4"] = {}

total_turns = 23
dR = 0.022
dZ = 0.034
spacing_R = 0.0048
spacing_Z = 0.0065
rect_width = 0.176
rect_height = 0.248
center_R = 1.51
center_Z = 1.095

# Determine grid size
n_columns = math.floor(rect_width / (dR + spacing_R))  # in R direction
n_rows = math.ceil(total_turns / n_columns)  # in Z direction

# Calculate the actual occupied space
actual_width = n_columns * (dR + spacing_R) - spacing_R
actual_height = n_rows * (dZ + spacing_Z) - spacing_Z

# Calculate rectangle edges
R_min = center_R - rect_width / 2
Z_min = center_Z - rect_height / 2

# Adjusted starting positions to center turns
R_min_adjusted = R_min + (rect_width - actual_width) / 2
Z_min_adjusted = Z_min + (rect_height - actual_height) / 2

# Build positions
R_list = []
Z_list = []

turn = 0
for row in range(n_rows):
    for col in range(n_columns):
        if turn >= total_turns:
            break
        R_pos = R_min_adjusted + col * (dR + spacing_R)
        Z_pos = Z_min_adjusted + row * (dZ + spacing_Z)
        R_list.append(R_pos)
        Z_list.append(Z_pos)
        turn += 1

active_coils_dict["P4"]["upper"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}
active_coils_dict["P4"]["lower"] = {
    "R": R_list,
    "Z": [-1 * z for z in Z_list],
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}


# P5 definition
active_coils_dict["P5"] = {}

total_turns = 23
dR = 0.022
dZ = 0.035
spacing_R = 0.005
spacing_Z = 0.005
rect_width = 0.177
rect_height = 0.245
center_R = 1.66
center_Z = 0.52

# Determine grid size
n_columns = math.floor(rect_width / (dR + spacing_R))  # in R direction
n_rows = math.ceil(total_turns / n_columns)  # in Z direction

# Calculate actual occupied space by turns
actual_width = n_columns * (dR + spacing_R) - spacing_R
actual_height = n_rows * (dZ + spacing_Z) - spacing_Z

# Calculate rectangle edges
R_min = center_R - rect_width / 2
Z_min = center_Z - rect_height / 2

# Adjusted starting positions to center turns
R_min_adjusted = R_min + (rect_width - actual_width) / 2
Z_min_adjusted = Z_min + (rect_height - actual_height) / 2

# Build positions
R_list = []
Z_list = []

turn = 0
for row in range(n_rows):
    for col in range(n_columns):
        if turn >= total_turns:
            break
        R_pos = R_min_adjusted + col * (dR + spacing_R)
        Z_pos = Z_min_adjusted + row * (dZ + spacing_Z)
        R_list.append(R_pos)
        Z_list.append(Z_pos)
        turn += 1

active_coils_dict["P5"]["upper"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}
active_coils_dict["P5"]["lower"] = {
    "R": R_list,
    "Z": [-1 * z for z in Z_list],
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}


# P6 definition
active_coils_dict["P6"] = {}

total_turns = 4
dR = 0.019
dZ = 0.047
spacing_R = 0.004
spacing_Z = 0.016
rect_width = 0.052
rect_height = 0.130
center_R = 1.445
center_Z = 0.9

# Determine grid size
n_columns = math.floor(rect_width / (dR + spacing_R))  # in R direction
n_rows = math.ceil(total_turns / n_columns)  # in Z direction

# Calculate actual occupied space by turns
actual_width = n_columns * (dR + spacing_R) - spacing_R
actual_height = n_rows * (dZ + spacing_Z) - spacing_Z

# Calculate rectangle edges
R_min = center_R - rect_width / 2
Z_min = center_Z - rect_height / 2

# Adjusted starting positions to center turns
R_min_adjusted = R_min + (rect_width - actual_width) / 2
Z_min_adjusted = Z_min + (rect_height - actual_height) / 2

# Build positions
R_list = []
Z_list = []

turn = 0
for row in range(n_rows):
    for col in range(n_columns):
        if turn >= total_turns:
            break
        R_pos = R_min_adjusted + col * (dR + spacing_R)
        Z_pos = Z_min_adjusted + row * (dZ + spacing_Z)
        R_list.append(R_pos)
        Z_list.append(Z_pos)
        turn += 1

active_coils_dict["P6"]["upper"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}
active_coils_dict["P6"]["lower"] = {
    "R": R_list,
    "Z": [-1 * z for z in Z_list],
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": -1,
    "multiplier": 1
}


# Solenoid definition
active_coils_dict["Solenoid"] = {}

total_turns = 720
dR = 0.014
dZ = 0.015
spacing_R = 0.001
spacing_Z = 0.001
rect_width = 0.062
rect_height = 2.90
center_R = 0.131
center_Z = 0.0

# Determine grid size
n_layers = math.floor(rect_width / (dR + spacing_R))  # in R direction (layers)
n_rows = math.ceil(total_turns / n_layers)  # in Z direction (rows)

# Calculate actual occupied space by turns
actual_width = n_layers * (dR + spacing_R) - spacing_R
actual_height = n_rows * (dZ + spacing_Z) - spacing_Z

# Calculate rectangle edges
R_min = center_R - rect_width / 2
Z_min = center_Z - rect_height / 2

# Adjusted starting positions to center turns
R_min_adjusted = R_min + (rect_width - actual_width) / 2
Z_min_adjusted = Z_min + (rect_height - actual_height) / 2

# Build positions
R_list = []
Z_list = []

turn = 0
for layer in range(n_layers):
    for row in range(n_rows):
        if turn >= total_turns:
            break
        R_pos = R_min_adjusted + layer * (dR + spacing_R)
        Z_pos = Z_min_adjusted + row * (dZ + spacing_Z)
        R_list.append(R_pos)
        Z_list.append(Z_pos)
        turn += 1

active_coils_dict["Solenoid"] = {
    "R": R_list,
    "Z": Z_list,
    "dR": dR,
    "dZ": dZ,
    "resistivity": eta_copper,
    "polarity": 1,
    "multiplier": 1
}



# --- Define output directory for pickle files ---
current_dir = os.path.dirname(os.path.abspath(__file__))
pickle_out_dir = os.path.join(current_dir, "MAST", "pickle")

if not os.path.exists(pickle_out_dir):
    os.makedirs(pickle_out_dir)

# Save active coils
active_coil_pickle_file_path = os.path.join(pickle_out_dir, "active_coils.pickle")
with open(active_coil_pickle_file_path, "wb") as f:
    pickle.dump(active_coils_dict, f)


# Resistivity typical for vessel materials (e.g., steel)
resistivity_wall = 5.5e-7


# --- Create passive coil structure for MAST ---
# Create an empty list for passive structures
passive_coils = []

# --- Polygonal Passive Structures ---
# These polygons model extended conducting structures, for example the vessel walls.
# The coordinates below outline different segments of the MAST vacuum vessel.
coils_data = [
    (1, [0.132576, 0.166667, 0.166667, 0.132576], [2.20598, 2.20598, 2.28904, 2.28904]),
    (2, [0.25, 0.333333, 0.333333, 0.25], [2.17276, 2.17276, 2.21927, 2.21927]),
    (3, [0.333333, 0.333333, 1.99621, 1.99621], [2.21927, 2.19601, 2.19601, 2.21927]),
    (4, [2.00379, 2.09091, 2.09091, 2.00379], [2.21927, 2.21927, 2.07641, 2.07641]),
    (5, [2.00379, 2.02652, 2.02652, 2], [2.07309, 2.07309, -2.07309, -2.07309]),
    (6, [1.59091, 1.59091, 1.72727, 1.72727], [2.01329, 2, 2, 2.01329]),
    (7, [1.6553, 1.66667, 1.66667, 1.6553], [1.99668, 1.99668, 1.89369, 1.89369]),
    (8, [1.59091, 1.59091, 1.72727, 1.72727], [1.89037, 1.8804, 1.8804, 1.89037]),
    (9, [0.723485, 0.723485, 0.856061, 0.856061], [2.01329, 2, 2, 2.01329]),
    (10, [0.787879, 0.799242, 0.799242, 0.787879], [1.99668, 1.99668, 1.89369, 1.89369]),
    (11, [0.723485, 0.723485, 0.856061, 0.856061], [1.89037, 1.8804, 1.8804, 1.89037]),
    (12, [0.193182, 0.215909, 0.215909, 0.193182], [1.86711, 1.86711, 1.84385, 1.84385]),
    (13, [0.170455, 0.185606, 0.185606, 0.170455], [1.86711, 1.86711, 1.71761, 1.71761]),
    (14, [0.181818, 0.280303, 0.280303, 0.181818], [1.70764, 1.70764, 1.59801, 1.59801]),
    (15, [0.193182, 0.193182, 0.242424, 0.242424], [1.59468, 1.57807, 1.57807, 1.59468]),
    (16, [0.181818, 0.280303, 0.280303, 0.181818], [1.57475, 1.57475, 1.37542, 1.37542]),
    (17, [0.193182, 0.193182, 0.242424, 0.242424], [1.37209, 1.35548, 1.35548, 1.37209]),
    (18, [0.181818, 0.280303, 0.280303, 0.181818], [1.35216, 1.35216, 1.19934, 1.19934]),
    (19, [0.181818, 0.215909, 0.215909, 0.181818], [1.19601, 1.19601, 1.08306, 1.08306]),
    (20, [0.181818, 0.19697, 0.19697, 0.181818], [1.07973, 1.07973, -1.07641, -1.07641]),
    (21, [0.170455, 0.17803, 0.17803, 0.170455], [1.71429, 1.71429, -1.71429, -1.71429]),
    (22, [0.291667, 0.291667, 0.412879, 0.412879], [1.70431, 1.65780, 1.54485, 1.58803]),
    (23, [0.416667, 0.57197, 0.57197, 0.416667], [1.6113, 1.6113, 1.57475, 1.57475]),
    (24, [0.416667, 0.416667, 0.602273, 0.602273], [1.57143, 1.54485, 1.54485, 1.57143]),
    (25, [0.575758, 0.575758, 0.670455, 0.670455], [1.61130, 1.57475, 1.65117, 1.68772]),
    (26, [0.575758, 0.62047, 0.79029, 0.74177], [1.57475, 1.57475, 1.72388, 1.72388]),
    (27, [0.146523, 0.188983, 0.333333, 0.290873], [1.87036, 1.87036, 2.17176, 2.17176]),
]


for number, R, Z in coils_data:
    passive_coils.append({
        "R": R,
        "Z": Z,
        "resistivity": resistivity_wall,
        "name": f"(upper) passive No. {number}",
        "min_refine_per_area": 100,
        "min_refine_per_length": 50
    })
    
    # Add mirrored coil (except for 5 and 20)
    if number not in {5, 20}:
        passive_coils.append({
            "R": R,
            "Z": [-z for z in Z],
            "resistivity": resistivity_wall,
            "name": f"(lower) passive No. {number}",
            "min_refine_per_area": 100,
            "min_refine_per_length": 50
        })

# --- Save the Passive Structures ---
# Define the output directory relative to the current file location.
# --- Define output directory for pickle files ---
pickle_out_dir = os.path.join(current_dir, "MAST", "pickle")

if not os.path.exists(pickle_out_dir):
    os.makedirs(pickle_out_dir)

# Save active coils
passive_coils_pickle_file_path = os.path.join(pickle_out_dir, "passive_coils.pickle")
with open(passive_coils_pickle_file_path, "wb") as f:
    pickle.dump(passive_coils, f)
    
    

# --- Create limiter structure for MAST ---
# Here we use an elliptical approximation for the limiter (last closed flux surface).
# Adjust the center and amplitudes based on MAST geometry data.
R_limiter = [1.7889572005048,
1.78337005125967,
1.65486561862175,
1.53194833522895,
1.53753548447408,
1.53753548447408,
1.43696679806179,
1.37178339020197,
1.37178339020197,
1.37178339020197,
1.01715461172653,
1.01327464697297,
0.621398206863361,
0.419640039678211,
0.303241097071394,
0.279961308550031,
0.233401731507304,
0.233401731507304,
0.20624197823238,
0.194602083971698,
0.194602083971698,
0.194602083971698,
0.198482048725259,
0.198482048725259,
0.194602083971698,
0.194602083971698,
0.194602083971698,
0.20624197823238,
0.233401731507304,
0.233401731507304,
0.279961308550031,
0.303241097071394,
0.419640039678211,
0.621398206863361,
1.01327464697297,
1.01715461172653,
1.37178339020197,
1.37178339020197,
1.37178339020197,
1.43696679806179,
1.53753548447408,
1.53753548447408,
1.53194833522895,
1.65486561862175,
1.78337005125967,
1.7889572005048,
1.7889572005048
]
Z_limiter = [0.143504541701073,
0.380399669694467,
0.375015689512799,
0.380399669694467,
0.563454995871181,
0.751894302229562,
0.750099642169006,
0.750099642169006,
0.871239196256537,
0.934052298375997,
0.934800073401229,
1.12922157996146,
1.45076484081108,
1.45450371593724,
1.14791595559225,
1.1254827048353,
1.11052720433067,
1.02827195155518,
0.972188824662813,
0.833850444994953,
0.665601064317827,
0.418835305991375,
0.157114047160289,
-0.157114047160289,
-0.418835305991375,
-0.665601064317827,
-0.833850444994953,
-0.972188824662813,
-1.02827195155518,
-1.11052720433067,
-1.1254827048353,
-1.14791595559225,
-1.45450371593724,
-1.45076484081108,
-1.12922157996146,
-0.934800073401229,
-0.934052298375997,
-0.871239196256537,
-0.750099642169006,
-0.750099642169006,
-0.751894302229562,
-0.563454995871181,
-0.380399669694467,
-0.375015689512799,
-0.380399669694467,
-0.143504541701073,
0.143504541701073
]
# Add a small offset in R if desired (here +0.05 as in the FreeGSNKE example)
limiter = [{"R": r, "Z": z} for r, z in zip(R_limiter, Z_limiter)]

limiter_pickle_path = os.path.join(pickle_out_dir, "limiter.pickle")
with open(limiter_pickle_path, "wb") as f:
    pickle.dump(limiter, f)


# --- Create wall structure for MAST ---
# The wall is defined as a polygon outlining the vacuum vessel.
# Based on MAST data, we choose approximate coordinates.
# Initialize wall coordinates
r_wall = [1.7889572005048,
1.78337005125967,
1.65486561862175,
1.53194833522895,
1.53753548447408,
1.53753548447408,
1.43696679806179,
1.37178339020197,
1.37178339020197,
1.37178339020197,
1.01715461172653,
1.01327464697297,
1.2266727084188,
1.36635143954698,
1.58750943049994,
1.7388280558888,
1.79702752719221,
1.65346883131047,
0.912395563380403,
0.68735760767389,
0.640798030631163,
0.621398206863361,
0.419640039678211,
0.311001026578515,
0.303241097071394,
0.303241097071394,
0.279961308550031,
0.233401731507304,
0.233401731507304,
0.20624197823238,
0.194602083971698,
0.194602083971698,
0.194602083971698,
0.198482048725259,
0.198482048725259,
0.194602083971698,
0.194602083971698,
0.194602083971698,
0.20624197823238,
0.233401731507304,
0.233401731507304,
0.279961308550031,
0.303241097071394,
0.303241097071394,
0.311001026578515,
0.419640039678211,
0.621398206863361,
0.640798030631163,
0.68735760767389,
0.912395563380403,
1.65346883131047,
1.79702752719221,
1.7388280558888,
1.58750943049994,
1.36635143954698,
1.2266727084188,
1.01327464697297,
1.01715461172653,
1.37178339020197,
1.37178339020197,
1.37178339020197,
1.43696679806179,
1.53753548447408,
1.53753548447408,
1.53194833522895,
1.65486561862175,
1.78337005125967,
1.7889572005048,
1.7889572005048
]
z_wall = [0.143504541701073,
0.380399669694467,
0.375015689512799,
0.380399669694467,
0.563454995871181,
0.751894302229562,
0.750099642169006,
0.750099642169006,
0.871239196256537,
0.934052298375997,
0.934800073401229,
1.15222157996146,
1.15222157996146,
1.18783820533993,
1.18783820533993,
1.32738196164785,
1.54049784383888,
1.72370272502064,
1.71248609964216,
1.5031090925773,
1.48815359207266,
1.45076484081108,
1.45450371593724,
1.54423671896504,
1.40963721442334,
1.14791595559225,
1.1254827048353,
1.11052720433067,
1.02827195155518,
0.972188824662813,
0.833850444994953,
0.665601064317827,
0.418835305991375,
0.157114047160289,
-0.157114047160289,
-0.418835305991375,
-0.665601064317827,
-0.833850444994953,
-0.972188824662813,
-1.02827195155518,
-1.11052720433067,
-1.1254827048353,
-1.14791595559225,
-1.40963721442334,
-1.54423671896504,
-1.45450371593724,
-1.45076484081108,
-1.48815359207266,
-1.5031090925773,
-1.71248609964216,
-1.72370272502064,
-1.54049784383888,
-1.32738196164785,
-1.18783820533993,
-1.18783820533993,
-1.15222157996146,
-1.15222157996146,
-0.934800073401229,
-0.934052298375997,
-0.871239196256537,
-0.750099642169006,
-0.750099642169006,
-0.751894302229562,
-0.563454995871181,
-0.380399669694467,
-0.375015689512799,
-0.380399669694467,
-0.143504541701073,
0.143504541701073
]

# def add_rectangle(center_R, center_Z, rect_width, rect_height):
#     """Adds the four corners and closes the loop for a rectangle."""
#     R_min = center_R - rect_width / 2
#     R_max = center_R + rect_width / 2
#     Z_min = center_Z - rect_height / 2
#     Z_max = center_Z + rect_height / 2
    
#     # Append rectangle corners in sequence
#     r_wall.append(R_min)
#     z_wall.append(Z_min)
    
#     r_wall.append(R_max)
#     z_wall.append(Z_min)
    
#     r_wall.append(R_max)
#     z_wall.append(Z_max)
    
#     r_wall.append(R_min)
#     z_wall.append(Z_max)
    
#     # Closing the rectangle loop
#     r_wall.append(R_min)
#     z_wall.append(Z_min)

# # Add each coil's rectangle
# add_rectangle(0.49, 1.76, 0.125, 0.290)  # P2
# add_rectangle(1.1, 1.1, 0.112, 0.216)   # P3
# add_rectangle(1.51, 1.095, 0.176, 0.248) # P4
# add_rectangle(1.66, 0.52, 0.177, 0.245)  # P5
# add_rectangle(1.445, 0.9, 0.052, 0.130)  # P6
# add_rectangle(0.131, 0.0, 0.062, 2.90)   # Solenoid

wall = []
for r, z in zip(r_wall, z_wall):
    wall.append({"R": r, "Z": z})

wall_pickle_path = os.path.join(pickle_out_dir, "wall.pickle")
with open(wall_pickle_path, "wb") as f:
    pickle.dump(wall, f)
    

# --- Define output directory for pickle files ---
current_dir = os.path.dirname(os.path.abspath(__file__))
pickle_out_dir = os.path.join(current_dir, "MAST", "pickle")


# Set paths to configuration pickle files.
# (Make sure these paths match where your pickle files are located.)
os.environ["ACTIVE_COILS_PATH"] = os.path.join(pickle_out_dir, "active_coils.pickle")
os.environ["PASSIVE_COILS_PATH"] = os.path.join(pickle_out_dir, "passive_coils.pickle")
os.environ["WALL_PATH"] = os.path.join(pickle_out_dir, "wall.pickle")
os.environ["LIMITER_PATH"] = os.path.join(pickle_out_dir, "limiter.pickle")
# os.environ["PROBE_PATH"] = "../machine_configs/example/magnetic_probes.pickle"

from freegsnke import build_machine

# Build the tokamak machine using FreeGSNKE.
tokamak = build_machine.tokamak()

# Create a figure and axis for plotting.
fig1, ax1 = plt.subplots(figsize=(4, 8), dpi=80)
plt.tight_layout()

# Plot the tokamak equilibrium (and other machine elements) from the tokamak object.
tokamak.plot(axis=ax1, show=False)

# Plot the limiter (dashed line) and the wall (solid line).
ax1.plot(tokamak.limiter.R, tokamak.limiter.Z, color='k', linewidth=1.2, linestyle="--", label="Limiter")
ax1.plot(tokamak.wall.R, tokamak.wall.Z, color='k', linewidth=1.2, linestyle="-", label="Wall")

# Configure grid, aspect, limits, and labels.
ax1.grid(alpha=0.5)
ax1.set_aspect('equal')
ax1.set_xlim(0.0, 2.2)
ax1.set_ylim(-2.5, 2.5)
ax1.set_xlabel(r'Major radius, $R$ [m]')
ax1.set_ylabel(r'Height, $Z$ [m]')
ax1.legend()

# Save the figure
current_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(current_dir, "MAST_machine.png")
fig1.savefig(output_file, dpi=300, bbox_inches="tight")

# Display the plot.
plt.show()