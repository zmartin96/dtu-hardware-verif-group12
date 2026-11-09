from pyuvm import ConfigDB, uvm_scoreboard, uvm_tlm_analysis_fifo


class cl_marb_scb(uvm_scoreboard):
    """Scoreboard for Memory Arbiter"""

    def __init__(self, name, parent):
        super().__init__(name, parent)

        self.cfg = None

        # Fifos for connecting to UVC analysis ports
        self.consumer_fifo   = None
        self.ref_fifo        = None

        # Recording number of successes and failures
        self.succes  = 0
        self.failure = 0


    def build_phase(self):
        self.logger.info("Start build_phase() -> Scoreboard")
        super().build_phase()

        self.cfg = ConfigDB().get(
            context    = self,
            inst_name  = "",
            field_name = "cfg",
        )

        self.consumer_fifo  = uvm_tlm_analysis_fifo(
            name   = "consumer_fifo",
            parent = self,
        )
        self.ref_fifo       = uvm_tlm_analysis_fifo(
            name   = "ref_fifo",
            parent = self,
        )

        self.logger.info("End build_phase() -> Scoreboard")

    async def run_phase(self):
        self.logger.info("Start run_phase() -> Scoreboard")
        await super().run_phase()

        # Starting data sample for each fifo

        while True:
            # Get items for queues
            consumer_item = await self.consumer_fifo.get()
            ref_item      = await self.ref_fifo.get()

            # Compare the items

        self.logger.info("End run_phase() -> Scoreboard")

    def check_phase(self):
        super().check_phase()

        self.logger.info(f"Scoreboard found {self.succes} successes and {self.failure} failures")
        assert self.failure == 0, f"the test found {self.failure} failed comparisons"
