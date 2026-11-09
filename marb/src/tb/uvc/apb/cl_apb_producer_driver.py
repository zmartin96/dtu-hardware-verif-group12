"""APB Producer Driver
- The UVM Driver is an active entity that converts abstract transaction to design pin toggles.
- Transaction level objects are obtained from the Sequencer and the UVM Driver drives them to the design via an interface handler."""

from cocotb.triggers import RisingEdge
from cocotb.types import LogicArray
from pyuvm import *
from .apb_common import *
from .cl_apb_base_driver import cl_apb_base_driver

class cl_apb_producer_driver(cl_apb_base_driver):
    """ Signal interface producer driver for APB
    - translates transactions to pin level activity
    - transactions pulled from sequencer by the seq_item_port"""

    def __init__(self, name, parent):
        super().__init__(name, parent)

    async def drive_reset(self):
        # Reset interface values for producer
        self.cfg.vif.wr.value     = 0
        self.cfg.vif.sel.value    = 0
        self.cfg.vif.enable.value = 0
        self.cfg.vif.addr.value   = LogicArray("X" * self.cfg.ADDR_WIDTH)
        self.cfg.vif.wdata.value  = LogicArray("X" * self.cfg.DATA_WIDTH)
        self.cfg.vif.strb.value   = LogicArray("X" * self.cfg.STRB_WIDTH)

    async def drive_pins(self):
        # If unaligned to clock wait for clocking event
        await self.ev_last_clock.wait()

        self.logger.debug("Driving pins from transaction")

        # Drive transactions through interface
        if self.req.op == OpType.WR:
            self.cfg.vif.wr.value = 1
            self.cfg.vif.sel.value = 1
            self.cfg.vif.enable.value = 0
            self.cfg.vif.addr.value = self.req.addr
            self.cfg.vif.wdata.value = self.req.data

            # Enable or disable strobe-signal
            if self.cfg.enable_write_strobe:
                # Setting strb value from request
                self.cfg.vif.strb.value = self.req.strb
            else:
                # If masking not enabled, set strb-signal as all 1s
                self.cfg.vif.strb.value = LogicArray('1' * self.cfg.STRB_WIDTH)

        elif self.req.op == OpType.RD:
            self.cfg.vif.wr.value = 0
            self.cfg.vif.sel.value = 1
            self.cfg.vif.enable.value = 0
            self.cfg.vif.addr.value = self.req.addr
            self.cfg.vif.strb.value = 0
        else:
            self.logger.critical(f"Op type not WR or RD: op = {self.req.op}")

        self.logger.debug("Awaiting enable-signal")
        await RisingEdge(self.cfg.vif.clk)
        self.cfg.vif.enable.value = 1

        await RisingEdge(self.cfg.vif.clk)

        self.logger.debug("Awaiting ready-signal")
        while self.cfg.vif.ready.value != 1:
            await RisingEdge(self.cfg.vif.clk)

        self.rsp.slverr = int(self.cfg.vif.slverr.value)

        # Capture consumer response
        if self.req.op == OpType.RD:
            self.rsp.data = self.cfg.vif.rdata.value
            self.rsp.strb = self.cfg.vif.strb.value

            self.req.data = self.cfg.vif.rdata.value # Why is this here? Why are we updating the request item?

        # Return to idle
        await self.drive_reset()

        self.logger.debug(f"REQ object: {self.req}")
        self.logger.debug(f"RSP object: {self.rsp}")
