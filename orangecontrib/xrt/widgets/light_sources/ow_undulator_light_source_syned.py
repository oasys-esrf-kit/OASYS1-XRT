import sys, numpy,  scipy.constants as codata

from PyQt5.QtWidgets import QMessageBox

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from syned.storage_ring.magnetic_structures.undulator import Undulator

from orangecontrib.xrt.widgets.gui import ow_insertion_device

from PyQt5.QtWidgets import QTextEdit

from syned.widget.widget_decorator import WidgetDecorator
from syned.beamline.beamline import Beamline as SynedBeamline
from syned.storage_ring.light_source import LightSource as SynedLightSource

from orangecontrib.xrt.util.xrt_data import XRTData


m2ev = codata.c * codata.h / codata.e

VERTICAL = 1
HORIZONTAL = 2
BOTH = 3

class OWUndulatorLightSource(ow_insertion_device.OWInsertionDevice, WidgetDecorator):

    name = "Undulator Light Source with SYNED"
    description = "XRT: Undulator Light Source with SYNED"
    icon = "icons/undulator.png"
    priority = 2.1

    inputs = []
    WidgetDecorator.append_syned_input_data(inputs)

    auto_energy = Setting(0.0)
    auto_harmonic_number = Setting(1)

    center  = Setting("[0,0,0]")
    targetE = Setting(18.07e3)
    eMin    = Setting(17000.0)
    eMax    = Setting(18500.0)
    nrays   = Setting(20000)


    def __init__(self):
        super().__init__()

        tab_raytracing = oasysgui.createTabPage(self.tabs_setting, "Ray Tracing Setting")
        self.populate_tab_raytracing(tab_raytracing)

        tab_xrtcode = oasysgui.createTabPage(self.tabs_setting, "XRT code")
        self.populate_tab_xrtcode(tab_xrtcode)

        tab_util = oasysgui.createTabPage(self.tabs_setting, "Utility")
        self.populate_tab_utility(tab_util)


    def populate_tab_raytracing(self, tab_raytracing):

        oasysgui.lineEdit(tab_raytracing, self, "targetE", "Target (central) energy [eV]: ",
                          labelWidth=250,
                          valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(tab_raytracing, self, "eMin", "Min energy [eV]: ",
                          labelWidth=250,
                          valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(tab_raytracing, self, "eMax", "Max energy [eV]: ",
                          labelWidth=250,
                          valueType=float,
                          orientation="horizontal")

        oasysgui.lineEdit(tab_raytracing, self, "nrays", "Number of rays: ",
                          labelWidth=250,
                          valueType=int,
                          orientation="horizontal")

        oasysgui.lineEdit(tab_raytracing, self, "center", "center: ",
                          labelWidth=250,
                          valueType=str,
                          orientation="horizontal")

    def populate_tab_xrtcode(self, tab_util):
        left_box_0 = oasysgui.widgetBox(tab_util, "XRT code to be sent", addSpace=False, orientation="vertical", height=450)
        gui.button(left_box_0, self, "Update XRT code", callback=self.update_xrtcode)

        self.xrtcode_id = oasysgui.textArea(height=380, width=415, readOnly=True)
        left_box_0.layout().addWidget(self.xrtcode_id)

    def populate_tab_utility(self, tab_util):
        left_box_0 = oasysgui.widgetBox(tab_util, "Undulator calculated parameters", addSpace=False, orientation="vertical", height=450)
        gui.button(left_box_0, self, "Update info", callback=self.update_info)

        self.info_id = oasysgui.textArea(height=380, width=415, readOnly=True)
        left_box_0.layout().addWidget(self.info_id)

        left_box_1 = oasysgui.widgetBox(tab_util, "Auto Setting of Undulator", addSpace=False, orientation="vertical", height=120)

        oasysgui.lineEdit(left_box_1, self, "auto_energy", "Set Undulator at Energy [eV]",
                          labelWidth=250, valueType=float, orientation="horizontal")
        oasysgui.lineEdit(left_box_1, self, "auto_harmonic_number", "As Harmonic #",  labelWidth=250, valueType=int, orientation="horizontal")

        button_box = oasysgui.widgetBox(left_box_1, "", addSpace=False, orientation="horizontal")

        gui.button(button_box, self, "Set Kv value and Target (central) energy", callback=self.auto_set_undulator_V)
        # gui.button(button_box, self, "Set Kh value", callback=self.auto_set_undulator_H)
        # gui.button(button_box, self, "Set Both K values", callback=self.auto_set_undulator_B)

    def update_xrtcode(self):
        self.xrtcode_id.setText(self.get_xrt_code())


    def get_xrt_code(self):
        syned_light_source = self.get_light_source()
        syned_electron_beam = syned_light_source.get_electron_beam()
        syned_undulator = syned_light_source.get_magnetic_structure()

        sigma_x, sigma_xp, sigma_z, sigma_zp = syned_electron_beam.get_sigmas_all()

        xrtcode_parameters = {
            "name":self.source_name,
            "center":self.center,
            "period":1e3 * syned_undulator.period_length(),
            "n":int(syned_undulator.number_of_periods()),
            "eE":self.electron_energy_in_GeV,
            "eI":syned_electron_beam.current(),
            "eEpsilonX":1e9 * sigma_x * sigma_xp,
            "eEpsilonZ":1e9 * sigma_z * sigma_zp,
            "eEspread":syned_electron_beam._energy_spread, # TODO in syned: define getter
            "eSigmaX":1e6 * sigma_x,
            "eSigmaZ":1e6 * sigma_z,
            "distE":'eV',
            "targetE":self.targetE,
            "eMin":self.eMin,
            "eMax":self.eMax,
            "nrays":self.nrays,
                }

        return self.xrtcode_template().format_map(xrtcode_parameters)
        # self.xrtcode_id.setText(self.xrtcode_template().format_map(xrtcode_parameters))

    def xrtcode_template(self):
        return \
"""
from xrt.backends.raycing import BeamLine
from xrt.backends.raycing.sources import Undulator
xrt_component = Undulator(
    BeamLine(),
    name="{name}",
    center={center},
    period={period},
    n={n},
    eE={eE},
    eI={eI},
    eEpsilonX={eEpsilonX},
    eEpsilonZ={eEpsilonZ},
    eEspread={eEspread},
    eSigmaX={eSigmaX},
    eSigmaZ={eSigmaZ},
    distE="{distE}",
    targetE=[{targetE}, 1],
    eMin={eMin},
    eMax={eMax},
    nrays={nrays},
    )

"""

    def update_info(self):

        syned_light_source = self.get_light_source()
        syned_electron_beam = syned_light_source.get_electron_beam()
        syned_undulator = syned_light_source.get_magnetic_structure()

        gamma = self.gamma()

        info_parameters = {
            "electron_energy_in_GeV":self.electron_energy_in_GeV,
            "gamma":"%8.3f"%self.gamma(),
            "ring_current":"%4.3f "%syned_electron_beam.current(),
            "K_horizontal":syned_undulator.K_horizontal(),
            "K_vertical": syned_undulator.K_vertical(),
            "period_length": syned_undulator.period_length(),
            "number_of_periods": syned_undulator.number_of_periods(),
            "undulator_length": syned_undulator.length(),
            "resonance_energy":"%6.3f"%syned_undulator.resonance_energy(gamma,harmonic=1),
            "resonance_energy3": "%6.3f" % syned_undulator.resonance_energy(gamma,harmonic=3),
            "resonance_energy5": "%6.3f" % syned_undulator.resonance_energy(gamma,harmonic=5),
            "B_horizontal":"%4.2F"%syned_undulator.magnetic_field_horizontal(),
            "B_vertical": "%4.2F" % syned_undulator.magnetic_field_vertical(),
            "cc_1": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,1)),
            "cc_3": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,3)),
            "cc_5": "%4.2f" % (1e6*syned_undulator.gaussian_central_cone_aperture(gamma,5)),
            # "cc_7": "%4.2f" % (self.gaussian_central_cone_aperture(7)*1e6),
            "sigma_rad": "%5.2f"        % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=1)[0]),
            "sigma_rad_prime": "%5.2f"  % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=1)[1]),
            "sigma_rad3": "%5.2f"       % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=3)[0]),
            "sigma_rad_prime3": "%5.2f" % (1e6*syned_undulator.get_sigmas_radiation(gamma,harmonic=3)[1]),
            "sigma_rad5": "%5.2f" % (1e6 * syned_undulator.get_sigmas_radiation(gamma, harmonic=5)[0]),
            "sigma_rad_prime5": "%5.2f" % (1e6 * syned_undulator.get_sigmas_radiation(gamma, harmonic=5)[1]),
            "first_ring_1": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=1, ring_order=1)),
            "first_ring_3": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=3, ring_order=1)),
            "first_ring_5": "%5.2f" % (1e6*syned_undulator.get_resonance_ring(gamma, harmonic=5, ring_order=1)),
            "Sx": "%5.2f"  % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[0]),
            "Sy": "%5.2f"  % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[1]),
            "Sxp": "%5.2f" % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[2]),
            "Syp": "%5.2f" % (1e6*syned_undulator.get_photon_sizes_and_divergences(syned_electron_beam)[3]),
            "und_power": "%5.2f" % syned_undulator.undulator_full_emitted_power(gamma,syned_electron_beam.current()),
            "CF_h": "%4.3f" % syned_undulator.approximated_coherent_fraction_horizontal(syned_electron_beam,harmonic=1),
            "CF_v": "%4.3f" % syned_undulator.approximated_coherent_fraction_vertical(syned_electron_beam,harmonic=1),
            "CF": "%4.3f" % syned_undulator.approximated_coherent_fraction(syned_electron_beam,harmonic=1),
            }

        self.info_id.setText(self.info_template().format_map(info_parameters))

    def info_template(self):
        return \
"""

================ input parameters ===========
Electron beam energy [GeV]: {electron_energy_in_GeV}
Electron current:           {ring_current}
Period Length [m]:          {period_length}
Number of Periods:          {number_of_periods}

Horizontal K:               {K_horizontal}
Vertical K:                 {K_vertical}
==============================================

Electron beam gamma:                {gamma}
Undulator Length [m]:               {undulator_length}
Horizontal Peak Magnetic field [T]: {B_horizontal}
Vertical Peak Magnetic field [T]:   {B_vertical}

Total power radiated by the undulator [W]: {und_power}

Resonances:

Photon energy [eV]: 
       for harmonic 1 : {resonance_energy}
       for harmonic 3 : {resonance_energy3}
       for harmonic 3 : {resonance_energy5}

Central cone (RMS urad):
       for harmonic 1 : {cc_1}
       for harmonic 3 : {cc_3}
       for harmonic 5 : {cc_5}

First ring at (urad):
       for harmonic 1 : {first_ring_1}
       for harmonic 3 : {first_ring_3}
       for harmonic 5 : {first_ring_5}

Sizes and divergences of radiation :
    at 1st harmonic: sigma: {sigma_rad} um, sigma': {sigma_rad_prime} urad
    at 3rd harmonic: sigma: {sigma_rad3} um, sigma': {sigma_rad_prime3} urad
    at 5th harmonic: sigma: {sigma_rad5} um, sigma': {sigma_rad_prime5} urad
    
Sizes and divergences of photon source (convolution) at resonance (1st harmonic): :
    Sx: {Sx} um
    Sy: {Sy} um,
    Sx': {Sxp} urad
    Sy': {Syp} urad
    
Approximated coherent fraction at 1st harmonic: 
    Horizontal: {CF_h}  Vertical: {CF_v} 
    Coherent fraction 2D (HxV): {CF} 

"""

    def get_magnetic_structure(self):
        return Undulator(K_horizontal=self.K_horizontal,
                         K_vertical=self.K_vertical,
                         period_length=self.period_length,
                         number_of_periods=self.number_of_periods)


    def check_magnetic_structure_instance(self, magnetic_structure):
        if not isinstance(magnetic_structure, Undulator):
            raise ValueError("Magnetic Structure is not a Undulator")

    def populate_magnetic_structure(self, magnetic_structure):
        self.K_horizontal = magnetic_structure._K_horizontal
        self.K_vertical = magnetic_structure._K_vertical
        self.period_length = magnetic_structure._period_length
        self.number_of_periods = magnetic_structure._number_of_periods

    def auto_set_undulator_V(self):
        self.auto_set_undulator(VERTICAL)

    def auto_set_undulator_H(self):
        self.auto_set_undulator(HORIZONTAL)

    def auto_set_undulator_B(self):
        self.auto_set_undulator(BOTH)

    def auto_set_undulator(self, which=VERTICAL):
        congruence.checkStrictlyPositiveNumber(self.auto_energy, "Set Undulator at Energy")
        congruence.checkStrictlyPositiveNumber(self.auto_harmonic_number, "As Harmonic #")
        congruence.checkStrictlyPositiveNumber(self.electron_energy_in_GeV, "Energy")
        congruence.checkStrictlyPositiveNumber(self.period_length, "Period Length")

        wavelength = self.auto_harmonic_number * m2ev / self.auto_energy
        K = round(numpy.sqrt(2 * (((wavelength * 2 * self.gamma()**2) / self.period_length) - 1)), 6)

        if which == VERTICAL:
            self.K_vertical = K
            self.K_horizontal = 0.0

        if which == BOTH:
            Kboth = round(K / numpy.sqrt(2), 6)
            self.K_vertical =  Kboth
            self.K_horizontal = Kboth

        if which == HORIZONTAL:
            self.K_horizontal = K
            self.K_vertical = 0.0

        self.update_info()

        # update for xrt inputs
        syned_undulator = self.get_light_source().get_magnetic_structure()
        self.targetE = syned_undulator.resonance_energy(self.gamma(), harmonic=self.auto_harmonic_number)

    def gamma(self):
        return 1e9*self.electron_energy_in_GeV / (codata.m_e *  codata.c**2 / codata.e)

    def receive_syned_data(self, data):
        if data is not None:

            if isinstance(data, SynedLightSource):
                self.populate_fields(data)
                self.targetE = round(
                    data.get_magnetic_structure().resonance_energy(data.get_electron_beam().gamma()))
            elif isinstance(data, SynedBeamline) and not data._light_source is None:
                self.populate_fields(data._light_source)
                self.targetE = round(
                    data._light_source.get_magnetic_structure().resonance_energy(data._light_source.get_electron_beam().gamma()))
            else:
                raise Exception("Input data must contain a SYNED LightSource")


    # overwrite send_data()
    def check_data(self):
        pass

    def send_data(self):
        try:
            self.check_data()

            self.send("XRTData", XRTData(component=self.get_xrt_code()))

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e.args[0]), QMessageBox.Ok)

            self.setStatusMessage("")
            self.progressBarFinished()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    a = QApplication(sys.argv)
    ow = OWUndulatorLightSource()
    ow.show()
    a.exec_()
