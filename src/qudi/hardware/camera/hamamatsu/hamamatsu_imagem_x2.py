import time
import numpy as np

import pylablib 
import qudi

from qudi.core.configoption import ConfigOption
from qudi.interface.camera_interface import CameraInterface
from pylablib.devices import DCAM

class HamamatsuImagEMX2(CameraInterface):
    """
    Hardware class for the EMCCD 'Hamamatsu ImagEM X2'

    Example config for copy-paste:

    hamamatsu_imagem_x2_camera:
        module.Class: 'camera.hamamatsu.hamamatsu_imagem_x2.HamamatsuImagEMX2'
        options:
            dll_location: 'C:\Adyant\dlls' # path to library file
            default_exposure: 1.0
            default_gain: 1.0 

    Communication (via DCAM) is based on:
    self.cam.set_attribute_value(attribute_name, value)
    self.cam.get_attribute_value(attribute_name), self.cam.get_attribute(attribute_name) # for object
    """
    _dll_location = ConfigOption('dll_location') #, default = r'C:\Adyant\dlls')#, missing='error')
    _default_exposure = ConfigOption('default_exposure', 1.0)
    _default_gain = ConfigOption('default_gain', 1.0)
    _default_acquisition_mode = ConfigOption('default_acquisition_mode', 'sequence') #sequence (optional nframes=100) or snap
    _default_trigger_mode = ConfigOption('default_trigger_mode', 'int') #int, ext, software
    _default_ROI = ConfigOption('default_ROI', default=(0,1,0,1))
    _default_hbin = ConfigOption('default_hbin', 1.0)

    _gain = None
    cam = None

    def on_activate(self):
        """ Initialisation performed during activation of the module.
        """
        # 1. Set up the dynamic link libraries
        pylablib.par["devices/dlls/dcamapi"] = self._dll_location # add DCAM API dll path
        # 2. Connect to camera
        self.cam = DCAM.DCAMCamera() # self.cam.is_opened() returns True after this 
        # 3. Initiate the camera state 
        self.cam.set_exposure(self._default_exposure)
        self.set_gain(self._default_gain)       

    def on_deactivate(self):
        """ Deinitialisation performed during deactivation of the module.
        """
        self.cam.close()
        del pylablib.par["devices/dlls/dcamapi"]

    def get_name(self): 
        return " ".join(list(tuple(self.cam.get_name())))

    def get_size(self): 
        return self.cam.get_data_dimensions() 

    def support_live_acquisition(self): 
        return True 

    def start_single_acquisition(self):
        if self.get_trigger_mode() != 'int':
            self.set_trigger_mode('int')
        # TO DO: Open the shutter? 
        self.cam.setup_acquisition('snap', nframes=1)
        self.cam.start_acquisition('snap', nframes=1) # it will finish on it's own; TODO: check if we overwrite settings 
        self.cam.wait_for_frame()
        no_error = (True if (self.cam.get_status() != 'error') else False)
        return no_error #is_acquiring

    def start_live_acquisition(self):
        if self.get_trigger_mode() != 'int':
            self.set_trigger_mode('int') 
        self.cam.setup_acquisition('sequence', nframes=100) # TODO: check if needs to be run here
        self.cam.start_acquisition('sequence', nframes=100)
        no_error = (True if (self.cam.get_status() != 'error') else False)
        return no_error 

    def stop_acquisition(self):
        self.cam.stop_acquisition()
        is_acquiring = (True if self.cam.acquisition_in_progress() else False)
        return not is_acquiring

    def get_acquired_data(self):
        """ 
        NOTE: We only need to read the newest image as
        1. this function expects a 2D array as output
        2. these images are then streamed by other functions
        There is another function for reading multiple images: self.cam.read_multiple_images()
        """
        return self.cam.read_newest_image() 

    def set_exposure(self, exposure):
        """
        Units: seconds
        """
        self.cam.set_exposure(exposure)

    def get_exposure(self):
        return self.cam.get_exposure()

    def set_gain(self, gain):
        self._gain = gain

    def get_gain(self):
        return self._gain 

    # how does this differ from generaal EM Gain?
    def set_contrast_gain(self, value):
        self.cam.set_contrast_gain(value) 

    def get_contrast_gain(self):
        return self.cam.get_contrast_gain() 

    def set_sensitivity(self, value):
        self.cam.set_sensitivity(value)

    def get_sensitivity(self):
        return self.cam.get_sensitivity()

    def get_ready_state(self):
        return (True if (self.cam.get_status() == 'ready') else False)

    def set_region_of_interest(self, hstart, hend, vstart, vend, hbin):
        """
        This function will set the horizontal and vertical binning to be used when taking a full resolution image.
        Parameters
        @param int hbin: number of pixels to bin horizontally
        @param int vbin: number of pixels to bin vertically. int hstart: Start column (inclusive)
        @param int hend: End column (inclusive)
        @param int vstart: Start row (inclusive)
        @param int vend: End row (inclusive).

        @return string containing the status message returned by the function call
        """
        self.cam.set_roi(hstart, hend, vstart, vend, hbin)

    def get_ROI(self):
        return self.cam.get_roi()

    def set_trigger_mode(self, trigger_mode:str):
    # self.cam._trigger_modes = {'int': 1, 'ext': 2, 'software': 3, 'master_pulse': 4}
    # trigger modes are set as strings, e.g. trigger_mode = 'software' is valid
        self.cam.set_trigger_mode(trigger_mode)

    def get_trigger_mode(self):
        return self.cam.get_trigger_mode()

    def set_binning_value(self, bin_value):
        self._bin_value = bin_value

    def get_binning_value(self):
        return self._bin_value

    def _get_status(self):
        return self.cam.get_status()
