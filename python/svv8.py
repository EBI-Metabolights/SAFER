import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import numpy as np

# Load spectral data
def load_spectral_data_npz(file_path="spectral_data.npz"):
    data = np.load(file_path)
    return data["ppm"], data["spectra"]

npz_file_path = "/Users/mjudge/Downloads/spectral_data.npz"
ppm, spectra = load_spectral_data_npz(npz_file_path)

# Ensure correct orientation
if ppm.shape[0] != spectra.shape[1]:  
    spectra = spectra.T

# Smart downsampling function
def downsample_spectra(ppm, spectra, num_points=1000):
    """Dynamically reduces resolution based on zoom level."""
    factor = max(len(ppm) // num_points, 1)
    return ppm[::factor], spectra[:, ::factor]

# Default full view (downsampled for performance)
ppm_ds, spectra_ds = downsample_spectra(ppm, spectra, num_points=1000)

# Create Dash app
app = dash.Dash(__name__)

# Initial plot function
def create_initial_figure(dragmode="zoom", ppm_min=None, ppm_max=None, fill_active=False):
    """Plots all spectra using WebGL (scattergl) for performance while keeping zoom level."""
    
    # Keep current zoom range if provided
    x_range = [ppm_min, ppm_max] if ppm_min and ppm_max else [ppm.min(), ppm.max()]
    
    fill_style = "tozeroy" if fill_active else None

    traces = [
        go.Scattergl(x=ppm_ds, y=spectra_ds[i, :], 
                     mode="lines", 
                     fill=fill_style,  # ✅ Apply fill if active
                     fillcolor="white",  # ✅ Solid white fill
                     line=dict(width=1, color="gray"), 
                     hoverinfo="none")
        for i in range(len(spectra_ds))  # ✅ Show all spectra
    ]
    
    return {
        "data": traces,
        "layout": {
            "title": "NMR Spectra Viewer (Full Spectra)",
            "xaxis": {"title": "Chemical Shift (ppm)", "range": x_range, "autorange": False},
            "yaxis": {"title": "Intensity"},
            "showlegend": False,
            "dragmode": dragmode,  # ✅ Toggle between "zoom" and "select"
        }
    }

# Layout
app.layout = html.Div([
    html.Div(
        children=[
            dcc.Graph(
                id="spectra-plot",
                config={"scrollZoom": True},
                figure=create_initial_figure(),
                style={"width": "100%", "height": "100%"}
            )
        ],
        id="resizable-div",
        style={
            "width": "100%",
            "height": "600px",
            "resize": "vertical",
            "overflow": "hidden",
            "border": "1px solid #ccc",
            "padding": "5px",
            "min-height": "400px",
            "max-height": "1200px",
        },
    ),
    html.Button("Switch to Selection Mode", id="toggle-mode-btn", n_clicks=0),
    html.Button("Toggle Fill", id="fill-toggle-btn", n_clicks=0),
    
    dcc.Store(id="interaction-mode", data="zoom"),
    dcc.Store(id="zoom-range", data={"ppm_min": float(ppm.min()), "ppm_max": float(ppm.max())}),
    dcc.Store(id="fill-active", data=False),  # Store fill state

    html.Label("Stack Offset (Linear)"),
    dcc.Slider(id="stacking-slider", min=0, max=50, step=1, value=0,
               marks={i: str(i) for i in range(0, 55, 5)}, 
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Stack Scaling Factor (Log)"),
    dcc.Slider(id="stack-scale-slider", min=0, max=10, step=1, value=4,
               marks={i: f"10^{i}" for i in range(0, 10)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Label("Spectrum Height Scale"),
    dcc.Slider(id="height-scale-slider", min=-4, max=4, step=0.25, value=0,
               marks={i: f"10^{i}" for i in range(-1, 3)},
               tooltip={"placement": "bottom", "always_visible": True}),

    html.Div(id="selected-region"),
    dcc.Interval(id="debounce-interval", interval=500, n_intervals=0),  # 500ms debounce

    html.Label("Resolution (Number of Points)"),
    dcc.Slider(
        id="resolution-slider",
        min=100, max=5000, step=100, value=1000,  # Default: 1000 points
        marks={i: str(i) for i in range(100, 5100, 1000)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),
])

# **Unified Callback** (Handles Zooming, Panning, Mode Toggle, Fill, and Scaling)
@app.callback(
    Output("spectra-plot", "figure"),
    Output("toggle-mode-btn", "children"),
    Output("interaction-mode", "data"),
    Output("zoom-range", "data"),
    Output("fill-active", "data"),
    Input("toggle-mode-btn", "n_clicks"),
    Input("fill-toggle-btn", "n_clicks"),
    Input("spectra-plot", "relayoutData"),
    Input("spectra-plot", "selectedData"),
    Input("stacking-slider", "value"),
    Input("stack-scale-slider", "value"),
    Input("height-scale-slider", "value"),
    Input("resolution-slider", "value"),  # ✅ New slider input
    State("spectra-plot", "figure"),
    State("interaction-mode", "data"),
    State("zoom-range", "data"),
    State("fill-active", "data"),
    prevent_initial_call=True
)
def update_plot(n_clicks, fill_n_clicks, relayoutData, selectedData, stack_offset, stack_scale, height_scale, target_points, figure, mode, zoom_data, fill_active):
    """Handles zooming, selection mode toggle, stacking, and optionally fills spectra."""

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    ppm_min, ppm_max = zoom_data["ppm_min"], zoom_data["ppm_max"]

    # Step 1: Handle Mode Toggle Without Redraw
    if triggered_id == "toggle-mode-btn":
        new_mode = "select" if mode == "zoom" else "zoom"
        new_button_text = "Switch to Zoom Mode" if new_mode == "select" else "Switch to Selection Mode"
        figure["layout"]["dragmode"] = new_mode
        return figure, new_button_text, new_mode, zoom_data, fill_active

    # Step 2: Handle Fill Toggle
    if triggered_id == "fill-toggle-btn":
        fill_active = not fill_active  # Toggle state

    # Step 3: Handle Zoom Updates
    if relayoutData is None or "autosize" in relayoutData:
        return dash.no_update, dash.no_update, dash.no_update, zoom_data, fill_active  

    if "xaxis.autorange" in relayoutData:
        return create_initial_figure(dragmode=mode, fill_active=fill_active), dash.no_update, mode, {"ppm_min": ppm.min(), "ppm_max": ppm.max()}, fill_active

    if "xaxis.range" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range"]
    elif "xaxis.range[0]" in relayoutData and "xaxis.range[1]" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]

    # Apply Downsampling Only to the Zoomed Region
    mask = (ppm >= ppm_min) & (ppm <= ppm_max)
    ppm_zoom, spectra_zoom = ppm[mask], spectra[:, mask]

    # Use the slider value for resolution
    if target_points > len(ppm_zoom):
        target_points = len(ppm_zoom)  # Prevents errors if zoomed into very small region

    ppm_zoom, spectra_zoom = adaptive_downsample(ppm_zoom, spectra_zoom, target_points=target_points, feature_threshold=0.001)

    # Compute Final Stacking Offset
    scaling_factor = 10 ** stack_scale
    adjusted_offset = stack_offset * scaling_factor

    # Apply Stacking & Height Scaling **Only to Visible Data**
    num_spectra = len(spectra_zoom)
    stacked_spectra = [(spectra_zoom[i, :] * 10**height_scale) + (i * adjusted_offset) for i in range(num_spectra)]

    # Ensure we are working with the correct stacking order
    stacked_spectra_filled = stacked_spectra[::-1] if fill_active else stacked_spectra

    fill_style = "tozeroy" if fill_active else None

    figure["data"] = [
        go.Scattergl(
            x=ppm_zoom, 
            y=stacked_spectra_filled[i],  # ✅ Use the temporary reversed copy only if fill is active
            mode="lines", 
            fill="tozeroy" if fill_active else None, 
            fillcolor="white" if fill_active else None, 
            line=dict(width=1, color="gray"), 
            hoverinfo="none"
        ) for i in range(num_spectra)
    ]
    return figure, dash.no_update, mode, {"ppm_min": ppm_min, "ppm_max": ppm_max}, fill_active

@app.callback(
    Output("selected-region", "children"),  # Updates the text in the UI
    Input("spectra-plot", "selectedData"),  # Triggers when selection happens
    prevent_initial_call=True  # Prevents firing when app first loads
)
def display_selected_region(selectedData):
    """Handles region selection and prints the selected PPM & intensity range."""
    if not selectedData or "range" not in selectedData:
        return "No region selected"
    
    # Extract selection box coordinates
    ppm_range = selectedData["range"]["x"]  # Chemical shift (ppm)
    intensity_range = selectedData["range"]["y"]  # Intensity
    
    # Print to console for debugging
    print(f"🔹 Selected PPM Range: {ppm_range}")
    print(f"🔹 Selected Intensity Range: {intensity_range}")

    # Return as UI text
    return f"🔹 Selected PPM: {ppm_range[0]:.4f} to {ppm_range[1]:.4f}, " \
           f"Intensity: {intensity_range[0]:.2f} to {intensity_range[1]:.2f}"

import numpy as np

def adaptive_downsample(ppm, spectra, target_points=500, feature_threshold=0.001):
    """
    Downsamples the spectra while preserving peaks and valleys.
    
    - Uses second derivative to detect sharp spectral features.
    - Retains more points in peak/trough regions.
    - Dynamically adjusts the resolution based on zoom level.
    """

    num_points = len(ppm)
    if num_points <= target_points:  
        return ppm, spectra  # If already under limit, return as is

    # Compute second derivative (curvature measure)
    curvature = np.abs(np.gradient(np.gradient(spectra, axis=1), axis=1))

    # Normalize curvature across the spectrum
    norm_curvature = curvature / np.max(curvature, axis=1, keepdims=True)

    # Define importance scores (higher score = more critical to keep)
    importance = norm_curvature > feature_threshold

    # Ensure we always keep endpoints
    importance[:, [0, -1]] = True  

    # Adaptive sampling: Keep high-importance points, decimate low-importance regions
    selected_indices = np.where(np.any(importance, axis=0))[0]
    if len(selected_indices) > target_points:
        selected_indices = np.linspace(0, len(selected_indices) - 1, target_points, dtype=int)

    return ppm[selected_indices], spectra[:, selected_indices]

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
