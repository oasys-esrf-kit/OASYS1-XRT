import copy, os
from PyQt5.QtWidgets import QMessageBox

from orangewidget.settings import Setting
from orangewidget import gui

from oasys.widgets import gui as oasysgui
from oasys.util.oasys_objects import OasysPreProcessorData
from oasys.util.oasys_objects import OasysSurfaceData

from orangecontrib.xrt.widgets.gui.ow_optical_element import OWOpticalElement
from orangecontrib.xrt.util.xrt_data import XRTData
from orangecontrib.xrt.widgets.gui.show_image_error_data_file_dialog import ShowImageErrorDataFileDialog

class OWToridMirrorDistorted(OWOpticalElement):

    name = "Toroid Mirror Distorted"
    description = "XRT: Toroid Mirror Distorted"
    icon = "icons/toroidal_mirror.png"
    priority = 7

    inputs = copy.deepcopy(OWOpticalElement.inputs)
    inputs.append(("Surface Data", OasysSurfaceData, "set_oasys_surface_data"))
    inputs.append(("PreProcessor_Data", OasysPreProcessorData, "set_oasys_preprocessor_data"))


    oe_name = Setting("my_mirror")
    center = Setting("[0,0,0]")
    material = Setting("Material('C', rho=3.52, kind='plate')")
    R = Setting(1000.0)
    r = Setting(10.0)
    pitch = Setting("np.pi/2")
    yaw = Setting("0.0")
    limPhysX = Setting("[-5, 5]")
    limPhysY = Setting("[-15, 15]")

    modified_surface = Setting(0)
    ms_defect_file_name = Setting("")



    def __init__(self):
        super().__init__()

    def populate_tab_setting(self):
        oasysgui.lineEdit(self.tab_bas, self, "oe_name", "O.E. Name", labelWidth=150, valueType=str, orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "center", "center: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "material", "material command: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "R", "R [mm]: ",
                          labelWidth=250,
                          valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "r", "r [mm]: ",
                          labelWidth=250,
                          valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "pitch", "pitch angle [rad]: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "yaw", "yaw angle [rad]: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")


        oasysgui.lineEdit(self.tab_bas, self, "limPhysX", "limPhysX limits [mm]: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")

        oasysgui.lineEdit(self.tab_bas, self, "limPhysY", "limPhysY limits [mm]: ",
                          labelWidth=150,
                          valueType=str,
                          orientation="horizontal")

        gui.separator(self.tab_bas, height=10)


        #
        #
        #
        gui.comboBox(self.tab_bas, self, "modified_surface", tooltip="modified_surface", label="Modification Type", labelWidth=130,
                     items=["None", "Surface Error (numeric mesh)"],
                     callback=self.modified_surface_tab_visibility, sendSelectedValue=False, orientation="horizontal")

        gui.separator(self.tab_bas, height=10)

        self.mod_surf_err_box_1 = oasysgui.widgetBox(self.tab_bas, "", addSpace=False, orientation="horizontal")

        self.le_ms_defect_file_name = oasysgui.lineEdit(self.mod_surf_err_box_1, self, "ms_defect_file_name",
                                                        "File", tooltip="ms_defect_file_name", labelWidth=40,
                                                        valueType=str, orientation="horizontal")

        gui.button(self.mod_surf_err_box_1, self, "...", callback=self.select_defect_file_name, width=30)
        gui.button(self.mod_surf_err_box_1, self, "View Img", callback=self.view_image_error_data_file, width=65,
                   tooltip="Render data in image mode [slow]")

        self.modified_surface_tab_visibility()

    def modified_surface_tab_visibility(self):
        self.mod_surf_err_box_1.setVisible(False)
        if self.modified_surface == 1: self.mod_surf_err_box_1.setVisible(True)

    def draw_specific_box(self):
        pass

    def check_data(self):
        pass

    def xrtcode_parameters(self):
        if " " in self.oe_name:
            QMessageBox.critical(self, "Error", "component names cannot have blanks: %s" % self.oe_name, QMessageBox.Ok)

        return {
            "class_name":"ToroidMirrorDistorted",
            "use_for_plot": False,
            "name":self.oe_name,
            "center":self.center,
            "material": self.material,
            "R": self.R,
            "r": self.r,
            "pitch": self.pitch,
            "yaw": self.yaw,
            "limPhysX": self.limPhysX,
            "limPhysY": self.limPhysY,
            "modified_surface": self.modified_surface,
            "fname": self.ms_defect_file_name
                }

    def get_xrt_code(self):
        if self.modified_surface == 0:
            return self.xrtcode_template().format_map(self.xrtcode_parameters())
        else:
            return self.xrtcode_template_modified_surface().format_map(self.xrtcode_parameters())

    def xrtcode_template(self):
        return \
"""
from xrt.backends.raycing.oes import ToroidMirror
bl.{name} = ToroidMirror(
    bl,
    name='{name}',
    center={center},
    material={material},
    R={R},
    r={r},
    pitch={pitch},
    yaw={yaw},
    limPhysX={limPhysX},
    limPhysY={limPhysY},
    ) 
"""

    def xrtcode_template_modified_surface(self):
        return \
"""
from orangecontrib.xrt.util.toroid_mirror_distorted import ToroidMirrorDistorted
bl.{name} = ToroidMirrorDistorted(
    fname='{fname}',
    distorsion_factor=1,
    bl=bl,
    name='{name}',
    center={center},
    material={material},
    R={R},
    r={r},
    pitch={pitch},
    yaw={yaw},
    limPhysX={limPhysX},
    limPhysY={limPhysY},
    )
"""

    def send_data(self):
        try:
            self.check_data()
            if self.xrt_data is None:
                out_xrt_data = XRTData("", {})
            else:
                out_xrt_data = self.xrt_data.duplicate()

            out_xrt_data.append(self.get_xrt_code(), self.xrtcode_parameters())

            self.send("XRTData", out_xrt_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

    #
    # manage defect file
    #

    def set_oasys_preprocessor_data(self, oasys_data: OasysPreProcessorData):
        if not oasys_data is None:
            if not oasys_data.error_profile_data is None:
                try:
                    surface_data = oasys_data.error_profile_data.surface_data

                    error_profile_x_dim = oasys_data.error_profile_data.error_profile_x_dim
                    error_profile_y_dim = oasys_data.error_profile_data.error_profile_y_dim

                    self.ms_defect_file_name = surface_data.surface_data_file
                    self.modified_surface = 1
                    self.modified_surface_tab_visibility()

                    self.congruence_surface_data_file(surface_data.xx, surface_data.yy, surface_data.zz)
                except Exception as exception:
                    self.prompt_exception(exception)

    def set_oasys_surface_data(self, oasys_data: OasysSurfaceData):
        if oasys_data is not None:
            if oasys_data.surface_data_file is not None:
                try:
                    self.ms_defect_file_name = oasys_data.surface_data_file
                    self.modified_surface = 1
                    self.modified_surface_tab_visibility()
                    self.congruence_surface_data_file(oasys_data.xx, oasys_data.yy, oasys_data.zz)
                except Exception as exception:
                    self.prompt_exception(exception)

    def select_defect_file_name(self):
        self.le_ms_defect_file_name.setText(oasysgui.selectFileFromDialog(self,
                                                                          self.ms_defect_file_name,
                                                                          "Select Defect File Name",
                                                                          file_extension_filter="Data Files (*.h5 *.hdf5)"),
                                            )

    def view_image_error_data_file(self):
        try:
            dialog = ShowImageErrorDataFileDialog(parent=self, file_name=self.ms_defect_file_name)
            dialog.show()
        except Exception as exception:
            self.prompt_exception(exception)

    def congruence_surface_data_file(self, xx=None, yy=None, zz=None):
        if not os.path.isfile(self.ms_defect_file_name): raise Exception("File %s not found." % self.ms_defect_file_name)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = OWToridMirrorDistorted()
    ow.show()
    a.exec_()


