""" SSDT interface wrapper
"""

class cl_ssdt_interface:
    """ Python interface wrapper for SSDT.
    """

    def __init__(self, name="ssdt_interface", clk_signal = None, rst_signal = None):

        self.name  = name

        self.clk   = clk_signal
        self.rst   = rst_signal

        self.valid = None
        self.data  = None

    def connect(self, valid_signal, data_signal):
        """ Connecting the data signals to the interface.
        """

        self.valid  = valid_signal
        self.data   = data_signal
