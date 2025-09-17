from PyQt5.QtWidgets import QDialog, QGridLayout, QWidget
from oasys.util.oasys_util import read_surface_file
from srxraylib.metrology import profiles_simulation
from silx.gui.plot import Plot2D

class ShowImageErrorDataFileDialog(QDialog):
    def __init__(self, parent=None, file_name=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle('Surface Error Profile')
        # self.setFixedHeight(700)
        layout = QGridLayout(self)

        dataX, dataY, data2D = read_surface_file(file_name) # parent.ms_defect_file_name)

        ##################
        zz_slopes = data2D.T

        sloperms = profiles_simulation.slopes(zz_slopes, dataX, dataY, return_only_rms=1)

        title = ' Slope error rms in X: %g $\mu$rad' % (sloperms[0]*1e6) +  \
                ' in Y: %g $\mu$rad' % (sloperms[1]*1e6) + '\n' + \
                ' Figure error rms: %g nm' % (data2D.std()*1e9)
        ##################

        origin = (dataX[0], dataY[0])
        scale = (dataX[1] - dataX[0], dataY[1] - dataY[0])

        colormap = {"name": "temperature", "normalization": "linear",
                    "autoscale": True, "vmin": 0, "vmax": 0, "colors": 256}


        tmp = Plot2D()
        tmp.resetZoom()
        tmp.setXAxisAutoScale(True)
        tmp.setYAxisAutoScale(True)
        tmp.setGraphGrid(False)
        tmp.setKeepDataAspectRatio(True)
        tmp.yAxisInvertedAction.setVisible(False)
        tmp.setXAxisLogarithmic(False)
        tmp.setYAxisLogarithmic(False)
        tmp.getMaskAction().setVisible(False)
        tmp.getRoiAction().setVisible(False)
        tmp.getColormapAction().setVisible(True)
        tmp.setKeepDataAspectRatio(False)
        tmp.addImage(data2D, legend="1", scale=scale, origin=origin, colormap=colormap, replace=True)
        tmp.setActiveImage("1")
        tmp.setGraphXLabel("X [m] (%d pixels)" % dataX.size)
        tmp.setGraphYLabel("Y [m] (%d pixels)" % dataY.size)
        tmp.setGraphTitle("Z [m]\n" + title)

        widget = QWidget(parent=self)

        layout.addWidget(tmp, 0, 0)
        layout.addWidget(widget, 1, 0)

        self.setLayout(layout)