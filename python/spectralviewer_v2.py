import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np

def load_spectral_data_npz(file_path="spectral_data.npz"):
    data = np.load(file_path)
    return data["ppm"], data["spectra"]

# Load spectral data
npz_file_path = "/Users/mjudge/Downloads/spectral_data.npz"
ppm, spectra = load_spectral_data_npz(npz_file_path)

# Ensure correct orientation
if ppm.shape[0] != spectra.shape[1]:  
    spectra = spectra.T

# Downsampling function (adaptive based on zoom level)
def downsample_spectra(ppm, spectra, num_points=2000):
    """Reduces the number of points to render based on zoom level."""
    factor = max(len(ppm) // num_points, 1)  # Adaptive factor (min=1)
    return ppm[::factor], spectra[:, ::factor]  # Return downsampled ppm & spectra

# Default full view
ppm_ds, spectra_ds = downsample_spectra(ppm, spectra, num_points=2000)

# Create Dash app
app = dash.Dash(__name__)

# Initial plot function
def create_initial_figure():
    """Creates a full-range figure for first load."""
    traces = [
        go.Scattergl(x=ppm_ds, y=spectra_ds[i, :], mode="lines", line=dict(width=1))
        for i in range(len(spectra_ds))  # Adjust if needed
    ]
    return {
        "data": traces,
        "layout": {
            "title": "NMR Spectra Viewer",
            "xaxis": {
                "title": "Chemical Shift (ppm)",
                "range": [ppm.min(), ppm.max()],  # Full range on load
                "autorange": False  # Prevents auto-reset
            },
            "yaxis": {"title": "Intensity"},
            "showlegend": False
        }
    }

# App layout
app.layout = html.Div([
    dcc.Graph(id="spectra-plot", config={'scrollZoom': True}, figure=create_initial_figure()),  #  Preload plot
    dcc.Store(id="zoom-range", data={"ppm_min": float(ppm.min()), "ppm_max": float(ppm.max())})  # Store zoom range
])

@app.callback(
    Output("spectra-plot", "figure"),
    Output("zoom-range", "data"),  # Preserve zoom range across updates
    Input("spectra-plot", "relayoutData"),  # Detect zoom changes
    State("zoom-range", "data"),  # Get previous zoom range
    prevent_initial_call=True  #  Prevents unnecessary first call
)
def update_plot(relayoutData, zoom_data):
    """Adjusts resolution dynamically based on zoom level while preserving view."""

    # Debugging: Check zoom state
    # print("Previous Zoom Data:", zoom_data)
    # print("Relayout Data:", relayoutData)

    #  Ignore `autosize` events
    if relayoutData is None or "autosize" in relayoutData:
        # print("Ignoring autosize event...")
        return dash.no_update, zoom_data  # Prevents reset

    #  Handle Double-Click Reset (autorange=True)
    if "xaxis.autorange" in relayoutData:
        # print("Double-click detected: Resetting zoom to full view...")
        return create_initial_figure(), {"ppm_min": ppm.min(), "ppm_max": ppm.max()}  #  Reset to full range

    #  Extract new zoom range, handling different key formats
    if "xaxis.range" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range"]
    elif "xaxis.range[0]" in relayoutData and "xaxis.range[1]" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]
    else:
        ppm_min, ppm_max = zoom_data["ppm_min"], zoom_data["ppm_max"]

    #  Mask data within the zoom range
    mask = (ppm >= ppm_min) & (ppm <= ppm_max)

    #  Downsample the visible portion
    ppm_zoom, spectra_zoom = downsample_spectra(ppm[mask], spectra[:, mask], num_points=3000)

    #  Create WebGL traces
    traces = [
        go.Scattergl(x=ppm_zoom, y=spectra_zoom[i, :], mode="lines", line=dict(width=1)) 
        for i in range(len(spectra_zoom))  # Adjust if needed
    ]

    #  Return updated plot + updated zoom range
    return {
        "data": traces,
        "layout": {
            "title": "NMR Spectra Viewer",
            "xaxis": {
                "title": "Chemical Shift (ppm)",
                "range": [ppm_min, ppm_max],  #  Explicitly set zoom range
                "autorange": False  #  Prevents Plotly from resetting
            },
            "yaxis": {"title": "Intensity"},
            "showlegend": False
        }
    }, {"ppm_min": ppm_min, "ppm_max": ppm_max}  #  Store zoom range persistently

if __name__ == "__main__":
    app.run_server(debug=True)
