import cocotb
from pyuvm import ConfigDB, uvm_env

from cl_marb_tb_reg_model import cl_marb_tb_reg_model
from cl_marb_tb_virtual_sequencer import cl_marb_tb_virtual_sequencer
from uvc.apb import cl_apb_agent, if_apb_assert_check


class cl_marb_tb_env(uvm_env):
    def __init__(self, name, parent):
        super().__init__(name, parent)

        # Configuration object handle
        self.cfg = None

        # Virtual sequencer
        self.virtual_sequencer = None

        self.reg_model = None


        self.apb_agent = None

    def build_phase(self):
        self.logger.info("Start build_phase() -> MARB env")
        super().build_phase()

        # Get the configuration object
        self.cfg = ConfigDB().get(
            context    = self,
            inst_name  = "",
            field_name = "cfg",
        )

        # Create virtual_sequencer and pass handler to cfg
        ConfigDB().set(
            context    = self,
            inst_name  = "virtual_sequencer",
            field_name = "cfg",
            value      = self.cfg,
        )
        self.virtual_sequencer = cl_marb_tb_virtual_sequencer.create(
            name   = "virtual_sequencer",
            parent = self,
        )
        self.reg_model = cl_marb_tb_reg_model("reg_model")


        # Instantiate the APB UVC and pass handler to cfg
        ConfigDB().set(
            context    = self,
            inst_name  = "apb_agent",
            field_name = "cfg",
            value      = self.cfg.apb_cfg,
        )
        self.apb_agent = cl_apb_agent.create(
            parent = self,
            name = "apb_agent",
        )

        # Assertions checkers

        self.assert_check_apb = if_apb_assert_check(
            vif = self.cfg.apb_cfg.vif,
        )
        self.assert_check_apb.cfg = self.cfg.apb_cfg


        self.logger.info("End build_phase() -> MARB env")

    def connect_phase(self):
        self.logger.info("Start connect_phase() -> MARB env")
        super().connect_phase()

        self.virtual_sequencer.apb_agent_sequencer = self.apb_agent.sequencer
        self.virtual_sequencer.reg_model = self.reg_model


        self.logger.info("End connect_phase() -> MARB env")

    async def run_phase(self):

        # Start APB IF assertion checker
        cocotb.start_soon(self.assert_check_apb.check_assertions())

    def check_phase(self):
        assert self.assert_check_apb.passed, "APB IF assertions failed"
