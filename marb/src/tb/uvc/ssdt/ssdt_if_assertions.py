# ruff: noqa: T201
""" SSDT interface asserations wrapper"""

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge
from cocotb.types import LogicArray


class if_ssdt_assert_check:

    def __init__(self,vif = None, name = "if_ssdt_assert_check"):

        self.name  = name

        self.vif = vif

        # Set as false if any assertion fail
        self.passed = True


    async def check_assertions(self):
        # await reset to have a valid value
        while not self.vif.rst.value.is_resolvable:
            await RisingEdge(self.vif.clk)
            await ReadOnly()

        # await deactivation of reset
        while self.vif.rst.value == 1:
            await RisingEdge(self.vif.clk)
            await ReadOnly()

        as_reset_values = cocotb.start_soon(self.reset_values())
        as_data_value = cocotb.start_soon(self.data_value())
        as_stable_data = cocotb.start_soon(self.stable_data())

        # detecting synchronous reset
        while self.vif.rst.value == 0:
            await RisingEdge(self.vif.clk)
            await ReadOnly()

        as_reset_values.kill()
        as_data_value.kill()
        as_stable_data.kill()

    # Reset requirement (PR 1):
    # If RST = 1, then VALID cannot be 1
    # NOTE: Check is sync to the clock
    async def reset_values(self):
        while True:
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            try:
                if int(self.vif.rst.value) == 1:
                    assert int(self.vif.valid.value) != 1, \
                        f"When reset, valid was {self.vif.valid.value}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    # Data valitidy requirement (PR 2):
    # NOTE: Check is sync to the clock
    # If VALID = 1, then DATA cannot be X
    async def data_value(self):
        while True:
            await RisingEdge(self.vif.clk)
            await ReadOnly()
            try:
                if (self.vif.valid.value) == 1:
                    # .is_resolvable is True if all elements of the array are
                    # 0,1,L or H
                    # See https://docs.cocotb.org/en/v2.0.1/library_reference.html#cocotb.types.LogicArray.is_resolvable
                    assert self.vif.data.value.is_resolvable , \
                        f"When valid, data was {self.vif.data.value}"
            except AssertionError as msg:
                self.passed = False
                print(msg)

    # Data invalidity requirement (PR 3):
    # NOTE: Check is sync to the clock
    # If VALID = 0, then DATA must be 0
    async def stable_data(self):
        while True:
            await RisingEdge(self.vif.clk)
            await ReadOnly()

            try:
                if self.vif.valid.value == 0:
                    assert self.vif.data.value == LogicArray('0' * len(self.vif.data)), \
                        f"When not valid, data was {self.vif.data.value}"
            except AssertionError as msg:
                self.passed = False
                print(msg)
