from pyuvm import uvm_object

from uvc.apb import cl_apb_config



class cl_marb_tb_config(uvm_object):
    def __init__(self, name = "cl_marb_tb_config"):
        super().__init__(name)

        self.apb_cfg             = cl_apb_config.create("apb_cfg")


        # Delay to avoid a hazard when updating the dynamic priority
        self.dprio_reg_write_delay = 6
