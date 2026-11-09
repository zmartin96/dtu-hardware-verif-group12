import os
import warnings
from random import randint

import cocotb
import pyuvm
import vsc
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles
from pyuvm import ConfigDB, uvm_report_object, uvm_root, uvm_test

from cl_marb_tb_config import cl_marb_tb_config
from cl_marb_tb_env import cl_marb_tb_env

from uvc import apb
from uvc.apb import cl_apb_interface

_LOG_LEVELS = ["DEBUG", "CRITICAL", "ERROR", "WARNING", "INFO", "NOTSET", "NullHandler"]

@pyuvm.test()
class cl_marb_tb_base_test(uvm_test):
    def __init__(self, name = "cl_marb_tb_base_test", parent = None):
        # ----------------------------------------------------------------------
        if os.getenv("PYUVM_LOG_LEVEL") in _LOG_LEVELS:
            _PYUVM_LOG_LEVEL = os.getenv('PYUVM_LOG_LEVEL')
        else:
            _PYUVM_LOG_LEVEL = "INFO"
            if os.getenv("PYUVM_LOG_LEVEL") is not None:
                uvm_root().logger.warning(F"{'='*50}\n   Wrong value for 'PYUVM_LOG_LEVEL' in Makefile. Changing to default value: 'INFO'.\n    {'='*50}")

        uvm_report_object.set_default_logging_level(_PYUVM_LOG_LEVEL)
        # ----------------------------------------------------------------------

        super().__init__(name, parent)

        # Access the DUT through the cocotb.top handler
        self.dut = cocotb.top


        # Interface for CRC SSDT
        self.ssdt_cons_if = None

        # APB configuration interface
        self.apb_if = None

        # Configuration object handler
        self.cfg = None

        # TB environment handler
        self.marb_tb_env = None

        # Quick fix because of warnings og PYVSC
        warnings.simplefilter("ignore")

    def build_phase(self):
        self.logger.info("Start build_phase() -> MARB base test")
        super().build_phase()

        # Create configuration object
        self.cfg = cl_marb_tb_config.create(name = "cfg")

        # APB agent configuration
        self.cfg.apb_cfg.driver                      = apb.DriverType.PRODUCER
        self.cfg.apb_cfg.seq_item_override           = apb.SequenceItemOverride.USER_DEFINED
        self.cfg.apb_cfg.enable_masked_data          = False
        self.cfg.apb_cfg.active_low_reset            = False
        self.cfg.apb_cfg.enable_write_strobe             = False


        # Set ADDR and DATA width for APB interface
        self.cfg.apb_cfg.ADDR_WIDTH  = 32
        self.cfg.apb_cfg.DATA_WIDTH  = 32
        self.cfg.apb_cfg.STRB_WIDTH  = self.cfg.apb_cfg.DATA_WIDTH // 8

        # Set enable_masked_data as false for register access
        self.cfg.apb_cfg.enable_masked_data = False

        self.apb_if = cl_apb_interface(
            clk_signal = self.dut.clk,
            rst_signal = self.dut.rst,
        )

        # Set interfaces in cfg
        self.cfg.apb_cfg.vif           = self.apb_if
        self.apb_if.set_width_parameters(
            ADDR_WIDTH = self.cfg.apb_cfg.ADDR_WIDTH,
            DATA_WIDTH = self.cfg.apb_cfg.DATA_WIDTH,
        )


        # Instantiate environment
        ConfigDB().set(
            context    = self,
            inst_name  = "marb_tb_env",
            field_name = "cfg",
            value      = self.cfg,
        )
        self.marb_tb_env = cl_marb_tb_env(
            name   = "marb_tb_env",
            parent = self,
        )


        self.logger.info("End build_phase() -> MARB base test")

    def connect_phase(self):
        self.logger.info("Start connect_phase() -> MARB base test")
        super().connect_phase()


        self.apb_if.connect(
            wr_signal     = self.dut.conf_wr,
            sel_signal    = self.dut.conf_sel,
            enable_signal = self.dut.conf_enable,
            addr_signal   = self.dut.conf_addr,
            wdata_signal  = self.dut.conf_wdata,
            strb_signal   = self.dut.conf_strb,
            rdata_signal  = self.dut.conf_rdata,
            ready_signal  = self.dut.conf_ready,
            slverr_signal = self.dut.conf_slverr,
        )

        self.logger.info("End connect_phase() -> MARB base test")

    async def run_phase(self):
        self.logger.info("Start run_phase() -> MARB base test")
        await super().run_phase()

        await self.start_clock()
        self.logger.info("clock started")
        await self.trigger_reset()

        # Start SDT IF assertions chekers for producers and consumer

        self.logger.info("End run_phase() -> MARB base test")

    async def start_clock(self):
        self.clk_period = randint(1, 5)
        Clock(self.dut.clk, self.clk_period, 'ns').start()

    async def trigger_reset(self):
        """Activation and deactivation of reset """

        # Wait randomized number of clock cyles in [0, 5]
        await ClockCycles(self.dut.clk, randint(0, 5))

        # Activate reset
        self.logger.info("Waiting for reset")
        self.dut.rst.value = 1

        # Wait randomized number of clock cycles before deactivating reset
        await ClockCycles(self.dut.clk, randint(1, 20))
        self.dut.rst.value = 0

        self.logger.info("Reset Done")

    def end_of_elaboration_phase(self):
        super().end_of_elaboration_phase()

    def report_phase(self):
        self.logger.info("Start report_phase() -> MARB base test")
        super().report_phase()

        # Creating coverage report with PyVSC in txt format
        try:
            test_number = cocotb.plusargs["test_number"]
        except KeyError:
            test_number = 0

        # Writing coverage report in txt-format
        with open(f'sim_build/{self.get_type_name()}_{test_number}_cov.txt', "w") as f:
            f.write(f"Coverage report for {self.get_type_name()} #{test_number} \n")
            f.write("------------------------------------------------\n \n")
            vsc.report_coverage(fp=f, details=True)

        # Writing coverage report in xml-format
        vsc.write_coverage_db(
            f'sim_build/{self.get_type_name()}_{test_number}_cov.xml')

        self.logger.info("End report_phase() -> MARB base test")
