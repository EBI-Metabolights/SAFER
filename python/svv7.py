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
def downsample_spectra(ppm, spectra, num_points=3000):
    """Dynamically reduces resolution based on zoom level."""
    factor = max(len(ppm) // num_points, 1)
    return ppm[::factor], spectra[:, ::factor]

# Default full view (downsampled for performance)
ppm_ds, spectra_ds = downsample_spectra(ppm, spectra, num_points=3000)

# Create Dash app
app = dash.Dash(__name__)

# Initial plot function
def create_initial_figure(dragmode="zoom", ppm_min=None, ppm_max=None):
    """Plots all spectra using WebGL (scattergl) for performance while keeping zoom level."""
    
    # Keep current zoom range if provided
    x_range = [ppm_min, ppm_max] if ppm_min and ppm_max else [ppm.min(), ppm.max()]
    
    traces = [
        go.Scattergl(x=ppm_ds, y=spectra_ds[i, :], 
                     mode="lines", 
                     line=dict(width=1,
                               color="gray"), 
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
                style={"width": "100%", "height": "100%"}  # ✅ Allow full height scaling
            )
        ],
        id="resizable-div",
        style={
            "width": "100%",
            "height": "600px",  # Default height, but will expand
            "resize": "vertical",  # ✅ Allows vertical resizing
            "overflow": "hidden",  # ✅ Ensures plot resizes properly
            "border": "1px solid #ccc",  # Optional, for visibility
            "padding": "5px",
            "min-height": "400px",  # ✅ Prevents collapsing too much
            "max-height": "1200px",  # ✅ Set an upper bound if needed
        },
    ),
    html.Button("Switch to Selection Mode", id="toggle-mode-btn", n_clicks=0),
    dcc.Store(id="interaction-mode", data="zoom"),
    dcc.Store(id="zoom-range", data={"ppm_min": float(ppm.min()), "ppm_max": float(ppm.max())}),

    html.Label("Stack Offset (Linear)"),
    dcc.Slider(
        id="stacking-slider",
        min=0, max=50, step=1,
        value=0,  # Default offset value
        marks={i: str(i) for i in range(0, 55, 5)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Label("Stack Scaling Factor (Log)"),
    dcc.Slider(
        id="stack-scale-slider",
        min=0, max=10, step=1,
        value=4,  # Default to 10^4
        marks={i: f"10^{i}" for i in range(0, 10)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Label("Spectrum Height Scale"),
    dcc.Slider(
        id="height-scale-slider",
        min=-4, max=4, step=0.25,
        value=0,  # Default to normal height
        marks={i: f"10^{i}" for i in range(-1, 3)},
        tooltip={"placement": "bottom", "always_visible": True}
    ),

    html.Div(id="selected-region")
])

# **Unified Callback** (Handles Zooming, Panning, and Mode Toggle)
@app.callback(
    Output("spectra-plot", "figure"),
    Output("toggle-mode-btn", "children"),
    Output("interaction-mode", "data"),
    Output("zoom-range", "data"),
    Input("toggle-mode-btn", "n_clicks"),
    Input("spectra-plot", "relayoutData"),
    Input("stacking-slider", "value"),
    Input("stack-scale-slider", "value"),
    Input("height-scale-slider", "value"),
    State("spectra-plot", "figure"),
    State("interaction-mode", "data"),
    State("zoom-range", "data"),
    prevent_initial_call=True
)
def update_plot(n_clicks, relayoutData, stack_offset, stack_scale, height_scale, figure, mode, zoom_data):
    """Handles zooming, selection mode toggle, stacking, and intensity scaling (only within view)."""
    
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None
    ppm_min, ppm_max = zoom_data["ppm_min"], zoom_data["ppm_max"]

    # Step 1: Handle Mode Toggle Without Redraw
    if triggered_id == "toggle-mode-btn":
        new_mode = "select" if mode == "zoom" else "zoom"
        new_button_text = "Switch to Zoom Mode" if new_mode == "select" else "Switch to Selection Mode"
        figure["layout"]["dragmode"] = new_mode
        return figure, new_button_text, new_mode, zoom_data

    # Step 2: Handle Zoom Updates
    if relayoutData is None or "autosize" in relayoutData:
        return dash.no_update, dash.no_update, dash.no_update, zoom_data  

    if "xaxis.autorange" in relayoutData:
        return create_initial_figure(dragmode=mode), dash.no_update, mode, {"ppm_min": ppm.min(), "ppm_max": ppm.max()}

    if "xaxis.range" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range"]
    elif "xaxis.range[0]" in relayoutData and "xaxis.range[1]" in relayoutData:
        ppm_min, ppm_max = relayoutData["xaxis.range[0]"], relayoutData["xaxis.range[1]"]

    # Apply Downsampling Only to the Zoomed Region
    mask = (ppm >= ppm_min) & (ppm <= ppm_max)
    ppm_zoom, spectra_zoom = ppm[mask], spectra[:, mask]

    high_res = (ppm_max - ppm_min) < (ppm.max() - ppm.min()) / 3
    if not high_res:
        ppm_zoom, spectra_zoom = downsample_spectra(ppm_zoom, spectra_zoom, num_points=3000)

    # Compute Final Stacking Offset
    scaling_factor = 10 ** stack_scale  # Exponential scaling
    adjusted_offset = stack_offset * scaling_factor

    # Apply Stacking & Height Scaling **Only to Visible Data**
    num_spectra = len(spectra_zoom)
    stacked_spectra = [(spectra_zoom[i, :] * 10**height_scale) + (i * adjusted_offset) for i in range(num_spectra)]

    # Update Figure Data Without Resetting
    figure["data"] = [
        go.Scattergl(x=ppm_zoom, y=stacked_spectra[i], mode="lines", line=dict(width=1, color="gray"), hoverinfo="none")
        for i in range(num_spectra)
    ]
    figure["layout"]["xaxis"]["range"] = [ppm_min, ppm_max]

    return figure, dash.no_update, mode, {"ppm_min": ppm_min, "ppm_max": ppm_max}

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)
