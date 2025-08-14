from PyQt5.QtWidgets import QMessageBox

from orangecontrib.xrt.widgets.gui.ow_optical_element import OWOpticalElement

from syned.beamline.optical_elements.ideal_elements.screen import Screen

from orangewidget.settings import Setting

from orangecontrib.xrt.util.xrt_data import XRTData

class OWScreen(OWOpticalElement):

    name = "Screen"
    description = "XRT: Screen"
    icon = "icons/screen.png"
    priority = 4

    score_flag = Setting(1)

    def __init__(self):
        super().__init__()

    def draw_specific_box(self):

        # oasysgui.comboBox(self.tab_bas, self, "convexity", label="Convexity", labelWidth=350,
        #                   items=["Upward", "Downward"],
        #                   sendSelectedValue=False, orientation="horizontal")
        pass

    def get_optical_element(self):
        return Screen(name=self.oe_name)

    def check_data(self):
        pass

    def get_xrt_code(self):

        xrtcode_parameters = {
            "name":self.oe_name,
            "center":self.center,
                }

        return self.xrtcode_template().format_map(xrtcode_parameters)

    def xrtcode_template(self):
        return \
"""
from xrt.backends.raycing import BeamLine
from xrt.backends.raycing.screens import Screen
xrt_component = Screen(
    BeamLine(),
    name="{name}",
    center={center},
    )

"""



    def send_data(self):
        try:
            self.check_data()
            if self.xrt_data is None:
                out_xrt_data = XRTData()
            else:
                out_xrt_data = self.xrt_data.duplicate()

            out_xrt_data.append(self.get_xrt_code())

            self.send("XRTData", out_xrt_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = OWScreen()
    ow.show()
    a.exec_()


