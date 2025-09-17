import scipy
import numpy as np
from xrt.backends.raycing.oes import ToroidMirror
from oasys.util.oasys_util import read_surface_file

class ToroidMirrorDistorted(ToroidMirror):

    def __init__(self, distorsion_factor=1, fname="", *args, **kwargs):
        ToroidMirror.__init__(self, *args, **kwargs)

        try:
            x, y, z = read_surface_file(fname)
            x_dist, y_dist, z_dist = 1e3 * x, 1e3 * y, 1e3 * z.T
        except:
            raise Exception("Failed to load defect data from file %f" % fname)

        self.n_x_dist = len(x_dist)
        self.n_y_dist = len(y_dist)
        self.limPhysX = np.min(x_dist), np.max(x_dist)
        self.limPhysY = np.min(y_dist), np.max(y_dist)
        self.get_surface_limits()
        self.x_grad, self.y_grad = np.gradient(z_dist, x_dist, y_dist)
        self.x_grad = np.arctan(self.x_grad)
        self.y_grad = np.arctan(self.y_grad)
        self.z_spline = scipy.ndimage.spline_filter(z_dist)
        self.x_grad_spline = scipy.ndimage.spline_filter(self.x_grad)
        self.y_grad_spline = scipy.ndimage.spline_filter(self.y_grad)

    def local_z_distorted(self, x, y):
        coords = np.array(
            [(x-self.limPhysX[0]) /
             (self.limPhysX[1]-self.limPhysX[0]) * (self.n_x_dist-1),
             (y-self.limPhysY[0]) /
             (self.limPhysY[1]-self.limPhysY[0]) * (self.n_y_dist-1)])
        z = scipy.ndimage.map_coordinates(self.z_spline, coords,
                                          prefilter=True)
        return z

    def local_n_distorted(self, x, y):
        coords = np.array(
            [(x-self.limPhysX[0]) /
             (self.limPhysX[1]-self.limPhysX[0]) * (self.n_x_dist-1),
             (y-self.limPhysY[0]) /
             (self.limPhysY[1]-self.limPhysY[0]) * (self.n_y_dist-1)])
        a = scipy.ndimage.map_coordinates(self.x_grad_spline, coords,
                                          prefilter=True)
        b = scipy.ndimage.map_coordinates(self.y_grad_spline, coords,
                                          prefilter=True)
        return b, -a

if __name__ == "__main__":
    fname = "/users/srio/Oasys/toroidal_mirror_s4.hdf5"
    a = ToroidMirrorDistorted(fname=fname)