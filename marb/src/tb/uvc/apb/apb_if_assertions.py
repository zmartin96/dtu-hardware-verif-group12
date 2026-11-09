from pyuvm import *
import cocotb
from cocotb.triggers import RisingEdge, FallingEdge, ReadOnly
from cocotb.simtime import get_sim_time

class if_apb_assert_check:
    def __init__(self, vif):
        """Connecting the signals to the assertion class"""
        # Interface handle
        self.vif = vif

        # Config
        self.cfg = None

        # Set as false if any assertion fail
        self.passed = True

    async def check_assertions(self):
        while True:
            # await deactivation of reset
            if self.cfg.active_low_reset:
                while self.vif.rst.value == 0:
                    await RisingEdge(self.vif.clk)
            else:
                while self.vif.rst.value == 1:
                    await RisingEdge(self.vif.clk)

            # start all assertions
            as_valid_sel    = cocotb.start_soon(self.valid_signal_always(self.vif.sel, "sel"))
            as_valid_enable = cocotb.start_soon(self.valid_signal_always(self.vif.enable, "enable"))
            as_valid_ready  = cocotb.start_soon(self.valid_signal_always(self.vif.ready, "ready"))
            as_valid_addr   = cocotb.start_soon(self.valid_signal_when_sel(self.vif.addr, "addr", self.cfg.ADDR_WIDTH))
            as_valid_op     = cocotb.start_soon(self.valid_signal_when_sel(self.vif.wr, "wr", 1))
            as_valid_slverr = cocotb.start_soon(self.valid_slverr())
            as_valid_data   = cocotb.start_soon(self.valid_data())
            as_valid_rdata  = cocotb.start_soon(self.valid_rdata())

            as_stable_addr  = cocotb.start_soon(self.stable_signal_when_sel(self.vif.addr, "addr"))
            as_stable_wdata = cocotb.start_soon(self.stable_signal_when_sel(self.vif.wdata, "wdata"))
            as_stable_wr    = cocotb.start_soon(self.stable_signal_when_sel(self.vif.wr, "wr"))
            as_stable_sel   = cocotb.start_soon(self.stable_sel())
            as_stable_strb  = cocotb.start_soon(self.stable_strb())

            as_no_enable            = cocotb.start_soon(self.no_enable())
            as_enable_life_cycle    = cocotb.start_soon(self.enable_life_cycle())

            # detecting asynchronous reset (active low or active high)
            if self.cfg.active_low_reset:
                await FallingEdge(self.vif.rst)
            else:
                await RisingEdge(self.vif.rst)

            # kill all assertions
            as_valid_sel.kill()
            as_valid_addr.kill()
            as_valid_enable.kill()
            as_valid_op.kill()
            as_valid_ready.kill()
            as_valid_slverr.kill()
            as_valid_data.kill()
            as_valid_rdata.kill()
            as_stable_addr.kill()
            as_stable_wdata.kill()
            as_stable_wr.kill()
            as_stable_sel.kill()
            as_stable_strb.kill()
            as_no_enable.kill()
            as_enable_life_cycle.kill()

    async def valid_signal_always(self, signal, signal_name):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # <signal> must always be valid
            try:
                assert str(signal.value) != 'x',\
                        f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                        f"{signal_name} must always be valid, was {str(signal.value)}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def valid_signal_when_sel(self, signal, signal_name, signal_size):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # If sel, then <signal> cannot be X
            try:
                if str(self.vif.sel.value) == '1' :
                    assert str(signal.value) != 'x' * signal_size,\
                        f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                        f"when sel = 1: {signal_name} must be valid, was {str(signal.value)}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def valid_slverr(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # If sel & enable & ready, then slverr cannot be X
            try:
                if str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and str(self.vif.ready.value) == '1':
                    assert str(self.vif.slverr.value) != 'x',\
                        f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                        f"when sel, enable & ready: slverr must be valid, "\
                        f"was {str(self.vif.slverr.value)}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def valid_rdata(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # If sel & enable & ready & ~wr, then rdata cannot be X
            try:
                if (str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and
                    str(self.vif.ready.value) == '1' and str(self.vif.wr.value) == '0'):
                    # when slverr = 1, the data can be invalid
                    if str(self.vif.slverr.value) == '0':
                        assert str(self.vif.rdata.value) != 'x' * self.cfg.DATA_WIDTH,\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"when sel, enable & ready & ~wr: "\
                            f"rdata must be valid, was {str(self.vif.rdata.value)}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def valid_data(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # If sel & wr & strb[i], then rdata cannot be X
            for i in range(self.cfg.STRB_WIDTH):
                try:
                    if str(self.vif.sel.value) == '1' and str(self.vif.wr.value) == '1' and str(self.vif.strb.value)[i] == '1':
                        assert str(self.vif.wdata.value)[8*i:8*i+7] != 'x' * 8,\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"when sel, wr & strb[i]: wdata[8*i : 8*i+7] "\
                            f"must be valid, was {str(self.vif.wdata.value)}"
                except AssertionError as msg:
                    self.passed = False
                    print(msg)

    async def stable_signal_when_sel(self, signal, signal_name):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # while sel , then <signal> must be stable
            try:
                if str(self.vif.sel.value) == '1':
                    prev_signal = str(signal.value)

                    while str(self.vif.sel.value) == '1':
                        assert prev_signal == str(signal.value),\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"while sel, then {signal_name} must be stable,"\
                            f"but changed from {prev_signal} to {str(signal.value)}"

                        # Wait 1 clk cycle
                        await RisingEdge(self.vif.clk)
                        await ReadOnly()
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def stable_sel(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # when sel and enable, sel must remain stable until one clock cycle after ready
            try:
                if (str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and
                       str(self.vif.ready.value) == '0'):
                    # Wait 1 clk cycle
                    await RisingEdge(self.vif.clk)
                    await ReadOnly()

                    while (str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and
                       str(self.vif.ready.value) == '0'):

                        assert str(self.vif.sel.value) == '1',\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"when sel and enable, sel must remain stable until one clock cycle "\
                            f"after ready. Changed from 1 to {str(self.vif.sel.value)}"

                        # Wait 1 clk cycle
                        await RisingEdge(self.vif.clk)
                        await ReadOnly()
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def stable_strb(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # strb must be stable while sel and enable until ready
            try:
                if (str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and
                       str(self.vif.ready.value) == '0'):
                    prev_strb = str(self.vif.strb.value)

                    # Wait 1 clk cycle
                    await RisingEdge(self.vif.clk)
                    await ReadOnly()

                    while (str(self.vif.sel.value) == '1' and str(self.vif.enable.value) == '1' and
                       str(self.vif.ready.value) == '0'):

                        assert str(self.vif.strb.value) == prev_strb,\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"strb must be stable while sel and enable until ready "\
                            f"changed from {prev_strb} to {str(self.vif.strb.value)}"

                        # Wait 1 clk cycle
                        await RisingEdge(self.vif.clk)
                        await ReadOnly()

            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def no_enable(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # if ~sel then ~enable
            try:
                if str(self.vif.sel.value) == '0':
                    assert str(self.vif.enable.value) == '0',\
                            f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                            f"when ~sel then enable should be '0', but enable is '{str(self.vif.enable.value)}'"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    async def enable_life_cycle(self):
        while True:
            # Wait 1 clk cycle
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            # one clock cycle after rising edge of sel, enable must remain high with sel
            try:
                if str(self.vif.sel.value) == '1':
                    assert str(self.vif.enable.value) == '0',\
                                f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                                f"enable must be 0 at rising edge of sel, but was enable={str(self.vif.enable.value)}"
                    # Wait 1 clk cycle
                    await RisingEdge(self.vif.clk)
                    await ReadOnly()

                    while str(self.vif.sel.value) == '1':
                        assert str(self.vif.enable.value) == '1',\
                                f"APB ASSERTION ERROR ({round(get_sim_time('ns'))}ns): "\
                                f"enable must be 1 throughout sel, but was enable={str(self.vif.enable.value)}"
                        # Wait 1 clk cycle
                        await RisingEdge(self.vif.clk)
                        await ReadOnly()
            except AssertionError as msg:
                self.passed = False
                print(msg)
