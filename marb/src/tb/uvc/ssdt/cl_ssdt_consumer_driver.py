from cocotb.triggers import ReadOnly, RisingEdge

from .cl_ssdt_base_driver import cl_ssdt_base_driver


class cl_ssdt_consumer_driver(cl_ssdt_base_driver):
    def __init__(self, name, parent):
        super().__init__(name, parent)

    async def driver_loop(self):

        self.logger.debug("Running CONSUMER loop...")
        self.logger.debug(f"CONSUMER (req): data = {self.req}")

        while True:
            await ReadOnly()
            if (self.vif.valid.value == 1):
                self.rsp.data = int(self.vif.data.value)
                await RisingEdge(self.cfg.vif.clk)
                break
            await RisingEdge(self.cfg.vif.clk)
        self.logger.debug(f"CONSUMER (rsp): data = {self.rsp}")
