import sys
import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication, QMainWindow

# Load spectral data
def load_spectral_data_npz(file_path="spectral_data.npz"):
    data = np.load(file_path)
    return data["ppm"], data["spectra"]

npz_file_path = "/Users/mjudge/Downloads/spectral_data.npz"
ppm, spectra = load_spectral_data_npz(npz_file_path)

# Ensure correct orientation
if ppm.shape[0] != spectra.shape[1]:  
    spectra = spectra.T

# PyQtGraph setup
class SpectraViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create plot widget
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        # Enable mouse interaction
        self.graphWidget.setMouseEnabled(x=True, y=True)  # ✅ Allow panning & zooming
        self.graphWidget.setLimits(xMin=ppm.min(), xMax=ppm.max())

        # Reverse X-axis (chemical shift)
        self.graphWidget.invertX(True)

        # Hide legend (optional)
        self.graphWidget.showGrid(x=True, y=True)  # ✅ Grid for better readability

        # Plot the spectra
        self.plot_spectra()

    def plot_spectra(self):
        """Plots all spectra overlayed."""
        for i in range(len(spectra)):
            self.graphWidget.plot(ppm, spectra[i, :], pen=pg.mkPen(width=1))

# Run the PyQt application
app = QApplication(sys.argv)
window = SpectraViewer()
window.show()
sys.exit(app.exec())
