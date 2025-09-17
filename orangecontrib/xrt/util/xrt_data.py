import os, copy, numpy
# from shadow4.beam.s4_beam import S4Beam

class XRTData:
    def __init__(self, code_beamline: str, parameters: dict):


        if isinstance(code_beamline, type(None)):
            self.__code_beamline = []
            self.__parameters = []
        elif isinstance(code_beamline, list):
            self.__code_beamline = code_beamline
            self.__parameters = parameters
        else:
            self.__code_beamline = [code_beamline]
            self.__parameters = [parameters]

    def duplicate(self):
        return copy.deepcopy(self)

    def append(self, code_beamline, parameters):
        self.__code_beamline.append(code_beamline)
        self.__parameters.append(parameters)

    def number_of_components(self):
        return len(self.__code_beamline)

    def components(self):
        return self.__code_beamline, self.__parameters

    def component(self, index):
        return self.__code_beamline[index], self.__parameters[index]

    def info(self):
        txt = ""
        for i in range(self.number_of_components()):
            txt += ("\n>> %d " % i) + repr(type(self.__code_beamline[i]))
        return txt

    def build_beamline_code(self, indent = "    "):

        txt = ""
        txt += "def build_beamline(name=''):\n"
        txt += "\n"
        txt += indent + "bl = BeamLine()\n"
        txt += indent + "bl.name = name\n"
        txt += "\n"

        for i in range(self.number_of_components()):
            txt_i, dict_i = self.component(i)
            txt_i_indented = "\n".join(indent + line for line in txt_i.splitlines())

            txt += "\n"
            txt += indent + "#\n"
            txt += indent + "# Component index: %d (%s)\n" % (i, dict_i["name"])
            txt += indent + "#"
            txt += txt_i_indented
            txt += "\n"

        txt += "\n"
        txt += indent + "#\n"
        txt += indent + "#\n"
        txt += indent + "#\n"
        txt += indent + "return bl\n"

        return txt

    def run_process_code(self, indent = "    "):
        txt = ""
        txt += "def run_process(bl):\n"
        txt += "\n"
        txt += indent + "import numpy as np\n"
        txt += indent + "t0 = time.time()\n"
        txt += "\n"
        txt += indent + "beams_to_plot = dict()\n"

        for i in range(self.number_of_components()):
            txt_i, dict_i = self.component(i)

            txt += "\n"
            txt += indent + "#\n"
            txt += indent + "# Component index: %d (%s: %s)\n" % (i, dict_i["name"], dict_i["class_name"],)
            txt += indent + "#\n"
            if dict_i["class_name"] == "Undulator":
                txt += indent +  "beam = bl.%s.shine()\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam)\n' % dict_i["name"]
            elif dict_i["class_name"] == "Screen":
                txt += indent +  "beam_local = bl.%s.expose(beam)\n" % dict_i["name"]
                if dict_i["use_for_plot"]:
                    txt += indent +  "beams_to_plot['%s'] = beam_local\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam)\n' % dict_i["name"]
            elif dict_i["class_name"] == "DoubleParaboloidLens":
                txt += indent +  "beam, beam_local1, beam_local2 = bl.%s.multiple_refract(beam)\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam_local1)\n' % (dict_i["name"] + "_1")
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam_local2)\n' % (dict_i["name"] + "_2")
            elif dict_i["class_name"] == "Plate":
                txt += indent +  "beam, beam_local1, beam_local2 = bl.%s.double_refract(beam)\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam_local1)\n' % (dict_i["name"] + "_1")
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam_local2)\n' % (dict_i["name"] + "_2")
            elif dict_i["class_name"] == "RectangularAperture":
                txt += indent +  "beam_local = bl.%s.propagate(beam)\n" % dict_i["name"]
                if dict_i["use_for_plot"]:
                    txt += indent +  "beams_to_plot['%s'] = beam_local\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam_local)\n' % dict_i["name"]
            elif dict_i["class_name"] == "ToroidMirrorDistorted":
                txt += indent +  "beam, _ = bl.%s.reflect(beam)\n" % dict_i["name"]
                txt += indent +  'if bl.dump_beams_flag: dump_beam(bl, "%s", beam)\n' % dict_i["name"]
            else:
                txt += indent +  "# <<<ERROR>>> not implemented component with class name: %s.\n" % dict_i["class_name"]


        txt += "\n"

        txt += indent + "#\n"
        txt += indent + "#\n"
        txt += indent + "#\n"
        txt += indent + 'dt = time.time() - t0\n'
        txt += indent + 'print("Time needed to create source and trace system %.3f sec" % dt)\n'
        txt += indent +  'if showIn3D: bl.prepare_flow()\n'
        txt += indent + "return beams_to_plot\n"

        return txt

if __name__ == "__main__":
    txt1 = """
from xrt.backends.raycing import BeamLine
from xrt.backends.raycing.sources import Undulator

xrt_component = Undulator(
    BeamLine(),
    name="ID09 IVU17c",
    center=[0, 0, 0],
    period=0.017,
    n=117.647,
    eE=6.0,
    eI=0.2,
    eEpsilonX=0.151152446676,
    eEpsilonZ=0.014131139047200002,
    eEspread=0.001,
    eSigmaX=33.46035,
    eSigmaZ=7.28154,
    distE='eV',
    targetE=[18070.0, 1],
    eMin=17000.0,
    eMax=18500.0,
    nrays=20000,
)
"""

    txt2 = """
from xrt.backends.raycing.sources import Undulator
from xrt.backends.raycing.screens import Screen

xrt_component = Screen(
    BeamLine(),
    name='sample_screen',
    center=[0, 56289, 0],
    )
"""

    oo = XRTData(txt1, {})
    print("N: ", oo.number_of_components())
    print("info: \n", oo.info())
    # print("index 0: \n", oo.component(0))

    oo.append(txt2, {})
    print("N: ", oo.number_of_components())
    print("info: \n", oo.info())
    print("index 1: \n", oo.component(1))
