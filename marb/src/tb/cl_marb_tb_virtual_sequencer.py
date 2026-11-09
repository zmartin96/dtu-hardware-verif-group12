from pyuvm import ConfigDB, uvm_sequencer

from cl_marb_common import MarbMode
from uvc.apb import OpType, cl_apb_seq_item, cl_apb_single_seq

# MARB register constants

# Enable control bit is bit 0
CTRL_REG_ENABLE_MASK = 0x00000001
# Mode control bit is bit 2:1
CTRL_REG_MODE_MASK   = 0x00000006
# Control register address
CTRL_REG_ADDR = 0x0

# Dynamic priority register adress
DPRIO_REG_ADDR = 0x4
# Dynamic priority field width
DPRIO_FIELD_WIDTH = 8
# Dynamic priority field mask
DPRIO_FIELD_MASK = 2**DPRIO_FIELD_WIDTH - 1

class cl_marb_tb_virtual_sequencer(uvm_sequencer):

    def __init__(self, name, parent):
        super().__init__(name, parent)

        # Configuration object handler
        self.cfg = None

        # APB agent sequencer
        self.apb_agent_sequencer = None

        self.reg_model = None

        self.sdt_producer0_agent_sequencer = None
        self.sdt_producer1_agent_sequencer = None
        self.sdt_producer2_agent_sequencer = None
        self.sdt_consumer_agent_sequencer  = None

    def build_phase(self):
        self.logger.info("Start build_phase() -> MARB virtual sequencer")
        super().build_phase()

        # Get the configuration object
        self.cfg = ConfigDB().get(
            context    = self,
            inst_name  = "",
            field_name = "cfg",
        )

        self.logger.info("End build_phase() -> MARB virtual sequencer")


    async def write_ctrl_reg(self, enabled, mode):
        """Writes the enabled and mode field of the control register.

        Args:
            enabled (bool): Enable value.
            mode (MarbMode): Arbitration mode.

        Returns:
            None
        """

        self.logger.debug(f"Writing ctrl_reg; enable: {enabled}, mode: {MarbMode(mode)}")
        # Setting enable and mode
        ctrl_value =  (enabled & CTRL_REG_ENABLE_MASK) | \
                     ((mode << 1) & CTRL_REG_MODE_MASK)

        apb_seq = cl_apb_single_seq("write_ctrl_reg")
        apb_seq.s_item = cl_apb_seq_item(
            name       = "write_ctrl_reg.apb_item",
            addr_width = self.cfg.apb_cfg.ADDR_WIDTH,
            data_width = self.cfg.apb_cfg.DATA_WIDTH,
        )
        apb_seq.s_item.op = OpType.WR
        apb_seq.s_item.addr = CTRL_REG_ADDR
        apb_seq.s_item.data = ctrl_value

        await apb_seq.start(self.apb_agent_sequencer)
        apb_rsp = await apb_seq.get_response()
        if not apb_rsp.slverr:
            self.reg_model.enable = enabled
            self.reg_model.mode = mode
        else:
            self.logger.error("CTRL register write failed")

    async def read_ctrl_reg(self):
        """Reads the control register.

        Returns:
            LogicArray: CTRL register value.
        """
        apb_seq = cl_apb_single_seq("read_ctrl_reg")
        apb_seq.s_item = cl_apb_seq_item(
            name       = "read_ctrl_reg.apb_item",
            addr_width = self.cfg.apb_cfg.ADDR_WIDTH,
            data_width = self.cfg.apb_cfg.DATA_WIDTH,
        )
        apb_seq.s_item.op   = OpType.RD
        apb_seq.s_item.addr = CTRL_REG_ADDR

        await apb_seq.start(self.apb_agent_sequencer)
        apb_rsp = await apb_seq.get_response()
        return apb_rsp.data

    async def write_dprio_reg(self, prio0, prio1, prio2):
        """Write the priorities in the dprio register.

        Args:
            prio0 (int): CIF0 priority.
            prio1 (int): CIF1 priority.
            prio2 (int): CIF2 priority.

        Returns:
            None
        """
        self.logger.debug(f"Writign dprio_reg; PRIO0: {prio0}, PRIO1: {prio1}, PRIO2: {prio2} ")
        dprio_value =  (prio0 & DPRIO_FIELD_MASK) | \
                      ((prio1 & DPRIO_FIELD_MASK) << DPRIO_FIELD_WIDTH) | \
                      ((prio2 & DPRIO_FIELD_MASK) << 2*DPRIO_FIELD_WIDTH)
        apb_seq = cl_apb_single_seq("write_dprio_reg")
        apb_seq.s_item = cl_apb_seq_item(
            name       = "write_dprio_reg.apb_item",
            addr_width = self.cfg.apb_cfg.ADDR_WIDTH,
            data_width = self.cfg.apb_cfg.DATA_WIDTH,
        )
        apb_seq.s_item.op   = OpType.WR
        apb_seq.s_item.addr = DPRIO_REG_ADDR
        apb_seq.s_item.data = dprio_value

        await apb_seq.start(self.apb_agent_sequencer)
        apb_rsp = await apb_seq.get_response()
        if not apb_rsp.slverr:
            self.reg_model.prio0 = prio0 & DPRIO_FIELD_MASK
            self.reg_model.prio1 = prio1 & DPRIO_FIELD_MASK
            self.reg_model.prio2 = prio2 & DPRIO_FIELD_MASK
        else:
            self.logger.error("DPRIO register write failed")

    async def read_dprio_reg(self):
        """Read the value of the dprio register.

        Returns:
            LogicArray: DPRIO register value.
        """
        apb_seq = cl_apb_single_seq("read_dprio_reg")
        apb_seq.s_item = cl_apb_seq_item(
            name       = "read_dprio_reg.apb_item",
            addr_width = self.cfg.apb_cfg.ADDR_WIDTH,
            data_width = self.cfg.apb_cfg.DATA_WIDTH,
        )
        apb_seq.s_item.op   = OpType.RD
        apb_seq.s_item.addr = DPRIO_REG_ADDR

        await apb_seq.start(self.apb_agent_sequencer)
        apb_rsp = await apb_seq.get_response()
        return apb_rsp.data
