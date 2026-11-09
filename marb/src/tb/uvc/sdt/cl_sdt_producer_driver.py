from cocotb.triggers import RisingEdge
from cocotb.types import LogicArray

from .cl_sdt_base_driver import cl_sdt_base_driver
from .sdt_common import AccessType


class cl_sdt_producer_driver(cl_sdt_base_driver):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    async def drive_reset(self):
        self.logger.debug("Producer driver reset")
        self.vif.rd.value      = 0
        self.vif.wr.value      = 0
        self.vif.addr.value    = LogicArray("X" * self.cfg.ADDR_WIDTH)
        self.vif.wr_data.value = LogicArray("X" * self.cfg.DATA_WIDTH)

    async def flushing_queue(self):
        self.logger.debug("Producer flushing queue")
        # Flushing data queue
        while not self.wr_data_queue.empty():
            self.wr_data_queue.get_nowait()

    async def drive_pins(self):
        # If unaligned to clock wait for clocking event
        await self.ev_last_clock.wait()

        # Drive transactions through interface
        if self.req.access == AccessType.WR:
            self.vif.wr.value      = 1
            self.vif.addr.value    = self.req.addr
            self.vif.wr_data.value = self.req.data

            # Put wr_data in data queue
            self.wr_data_queue.put_nowait(self.req.data)

        elif self.req.access == AccessType.RD:
            self.vif.rd.value     = 1
            self.vif.addr.value   = self.req.addr
            self.vif.wr_data.value = LogicArray('X' * self.cfg.DATA_WIDTH)
        else:
            self.logger.critical(f"Access type not wr or rd: access = {self.req.access}")

        # Wait for acknowledge
        while True:
            await RisingEdge(self.vif.clk)
            if self.vif.ack.value == 1:
                break

        # Capture consumer response
        if self.req.access == AccessType.RD:
            self.req.data = int(self.vif.rd_data.value)
            self.rsp.data = int(self.vif.rd_data.value)

            self.rd_data_queue.put_nowait(int(self.vif.rd_data.value))

        # Set interface back to idle values
        await self.drive_reset()

        self.logger.debug(f"REQ object: {self.req}")
        self.logger.debug(f"RSP object: {self.rsp}")
