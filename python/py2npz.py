import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
import numpy as np
import pandas as pd
import pickle  # assuming your RDS file is converted to a Python-friendly format
import os

def load_spectral_data(pkl_file_path):
    # Replace with the actual path and loading mechanism
    with open(pkl_file_path, 'rb') as f:
        data = pickle.load(f)
        data.columns = data.iloc[0]
        data = data[1:].reset_index(drop=True)
        data = data.apply(pd.to_numeric, errors='coerce')
        ppm = data.columns.astype(float)
        spectra = data.to_numpy()
        print("Processed spectral data:", spectra.shape)
        print("PPM range:", ppm.min(), "to", ppm.max())
        if not isinstance(spectral_data, pd.DataFrame):
            print("dataset was not converted to a pandas dataframe")

    return ppm, spectra
 
def plot_spectra(ppm, spectra):
    import matplotlib.pyplot as plt
    # After loading the spectral data, add the following code to create a static plot
    plt.figure(figsize=(10, 6))  # Set the figure size
    # for i in range(spectra.shape[0]):
    for i in range(min(5,spectra.shape[0])):
        plt.plot(ppm, spectra[i, :], label=f'Spectrum {i+1}')  # Plot each spectrum

    plt.title('Overlay of NMR Spectra')  # Set the title
    plt.xlabel('Chemical Shift (ppm)')  # Set x-axis label
    plt.ylabel('Intensity')  # Set y-axis label
    plt.gca().invert_xaxis()  # Invert x-axis for chemical shift
    plt.legend()  # Show legend
    plt.show()  # Display the plot

def save_spectral_data(ppm, spectra, file_path='spectral_data.npz'):
    np.savez(file_path, ppm=ppm, spectra=spectra)

def load_spectral_data_npz(file_path="spectral_data.npz"):
    data = np.load(file_path)
    return data["ppm"], data["spectra"]

###########################################################################################
# Read the data #####
pkl_file_path = "/Users/mjudge/Downloads/spectral_data.pkl"
with open(pkl_file_path, "rb") as f:
    spectral_data = pickle.load(f)

# Print key info for debugging
# print(f"PPM shape: {ppm.shape}")
# print(f"Spectra shape: {spectra.shape}")
# print(f"First few PPM values: {ppm[:10]}")
# print(f"First row of spectra: {spectra[0, :10]}")  # Print first 10 intensity values

# For this example, assume you have converted your RDS file into a pickle file 
# with a dictionary containing "ppm" and "spectra" keys.
ppm, spectra = load_spectral_data(pkl_file_path)
# plot_spectra(ppm, spectra)
npz_file_path = os.path.join(os.path.dirname(pkl_file_path), "spectral_data.npz")

save_spectral_data(ppm, spectra, 
                   file_path=npz_file_path)
