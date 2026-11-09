from pyuvm import uvm_object


class cl_marb_tb_reg_model(uvm_object):
    def __init__(self, name = "cl_marb_tb_reg_model"):
        super().__init__(name)

        self.enable = None
        self.mode = None
        self.prio0 = None
        self.prio1 = None
        self.prio2 = None
