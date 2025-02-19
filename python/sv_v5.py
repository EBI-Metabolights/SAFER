import pandas as pd
import numpy as np
import datashader as ds
import holoviews as hv
from holoviews.operation.datashader import datashade
from bokeh.server.server import Server
from bokeh.layouts import layout
from bokeh.models import Panel, Tabs
import holoviews.plotting.bokeh

hv.extension("bokeh")

# Load spectral data
def load_spectral_data_npz(file_path="spectral_data.npz"):
    data = np.load(file_path)
    return data["ppm"], data["spectra"]

npz_file_path = "/Users/mjudge/Downloads/spectral_data.npz"
ppm, spectra = load_spectral_data_npz(npz_file_path)

# Convert spectra to DataFrame
df = pd.DataFrame(spectra.T)
df["ppm"] = ppm

# Set default plot range
x_range = (ppm.min(), ppm.max())
y_range = (1.2 * df.min().min(), 1.2 * df.max().max())

# Create Datashader plot
ndoverlay = hv.NdOverlay({c: hv.Curve((df["ppm"], df[c])) for c in df.columns[:-1]})  # Skip "ppm"
plot = datashade(ndoverlay, cnorm="linear", aggregator=ds.mean()).opts(
    hv.opts.RGB(
        width=1600,
        height=800,
        title="NMR Spectra Viewer",
        xlabel="Chemical Shift ∂ (ppm)",
        ylabel="Spectral Intensity",
    )
)

# Convert to Bokeh
bokeh_layout = layout([hv.render(plot)])

# Bokeh application function
def modify_doc(doc):
    doc.add_root(bokeh_layout)

# Run the Bokeh server
server = Server({'/': modify_doc})
server.start()

print("Running Bokeh server... open http://localhost:5006/ in your browser.")

server.io_loop.add_callback(server.show, "/")
server.io_loop.start()
