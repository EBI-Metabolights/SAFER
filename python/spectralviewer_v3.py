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
        for i in range(len(spectra_ds))
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
    dcc.Graph(
        id="spectra-plot", 
        config={'scrollZoom': True, 'modeBarButtonsToAdd': ['select2d']},  # ✅ Ensures Box Select button appears
        figure=create_initial_figure()
    ),
    dcc.Store(id="zoom-range", data={"ppm_min": float(ppm.min()), "ppm_max": float(ppm.max())}),  # ✅ Preserve zoom
    html.Div(id="selected-region")  # ✅ Display selected region details
])

@app.callback(
    Output("spectra-plot", "figure"),
    Output("zoom-range", "data"),  # Preserve zoom range across updates
    Input("spectra-plot", "relayoutData"),  # ✅ Detect zoom changes
    State("zoom-range", "data"),  # ✅ Get previous zoom range
    prevent_initial_call=True
)
def update_plot(relayoutData, zoom_data):
    """Handles zoom updates while preserving relayout functionality."""

    # ✅ Ignore autosize events (prevents unwanted resets)
    if relayoutData is None or "autosize" in relayoutData:
        return dash.no_update, zoom_data

    # ✅ Handle Double-Click Reset
    if "xaxis.autorange" in relayoutData:
        return create_initial_figure(), {"ppm_min": ppm.min(), "ppm_max": ppm.max()}

    # ✅ Extract zoom ranges
    ppm_min, ppm_max = zoom_data["ppm_min"], zoom_data["ppm_max"]

    if "xaxis.range" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range"]
    elif "xaxis.range[0]" in relayoutData and "xaxis.range[1]" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]

    # ✅ Mask data within the zoom range
    mask = (ppm >= ppm_min) & (ppm <= ppm_max)
    ppm_zoom, spectra_zoom = downsample_spectra(ppm[mask], spectra[:, mask], num_points=3000)

    # ✅ Create WebGL traces
    traces = [
        go.Scattergl(x=ppm_zoom, y=spectra_zoom[i, :], mode="lines", line=dict(width=1)) 
        for i in range(len(spectra_zoom))
    ]

    # ✅ Return updated plot + updated zoom range
    return {
        "data": traces,
        "layout": {
            "title": "NMR Spectra Viewer",
            "xaxis": {
                "title": "Chemical Shift (ppm)",
                "range": [ppm_min, ppm_max],  # ✅ Explicitly set zoom range
                "autorange": False  # ✅ Prevents Plotly from resetting
            },
            "yaxis": {"title": "Intensity"},
            "showlegend": False
        }
    }, {"ppm_min": ppm_min, "ppm_max": ppm_max}

@app.callback(
    Output("selected-region", "children"),
    Input("spectra-plot", "selectedData")
)
def display_selected_region(selectedData):
    """Handles region selection and prints the selected region."""
    if not selectedData or "range" not in selectedData:
        return "No region selected"
    
    ppm_range = selectedData["range"]["x"]
    intensity_range = selectedData["range"]["y"]

    print(f"Selected PPM Range: {ppm_range}")
    print(f"Selected Intensity Range: {intensity_range}")

    return f"Selected PPM Range: {ppm_range[0]:.4f} to {ppm_range[1]:.4f}, " \
           f"Intensity Range: {intensity_range[0]:.2f} to {intensity_range[1]:.2f}"

if __name__ == "__main__":
    app.run_server(debug=True)
