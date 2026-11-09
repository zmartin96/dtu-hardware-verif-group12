"""APB Base Driver
- The UVM Driver is an active entity that converts abstract transaction to design pin toggles.
- Transaction level objects are obtained from the Sequencer and the UVM Driver drives them to the design via an interface handler."""

from cocotb.triggers import FallingEdge, RisingEdge, Event, Timer
from pyuvm import *
from .apb_common import *

class cl_apb_base_driver(uvm_driver):
    """ Signal interface driver for APB
    - translates transactions to pin level activity
    - transactions pulled from sequencer by the seq_item_port"""

    def __init__(self, name, parent):
        super().__init__(name, parent)

        # Handle to the configuration object
        self.cfg = None

        # Process
        self.get_and_drive_process = None

        # Record time of last clocking event
        self.ev_last_clock = None

        # Event for reset inactive If event is set, reset is inactive.
        self.reset_inactive = Event()
        # Event for reset active. If event is set, reset is active.
        self.reset_active = Event()


    def build_phase(self):
        self.logger.info("Start build_phase() -> APB driver")
        super().build_phase()

        # Get the configuration object
        self.cfg = ConfigDB().get(self, "", "cfg")

        # Creating the cocotb-triggers event object
        self.ev_last_clock = Event()

        self.logger.info("End build_phase() -> APB driver")

    async def run_phase(self):
        """Run phase:
        * Receives the sequence item.
        * For each sequence item it calls the clock_event, drive_transaction and
        handle_reset tasks in parallel in a fork join_none."""

        self.logger.info("Start run_phase() -> APB driver")
        await super().run_phase()

        # Starts coroutines in parallel
        self.clock_task = cocotb.start_soon(self.clock_event())
        self.transaction_task = cocotb.start_soon(self.drive_transaction())
        self.reset_task = cocotb.start_soon(self.handle_reset())
        self.reset_monitor = cocotb.start_soon(self.detect_reset())

    async def clock_event(self):
        while True:
            self.ev_last_clock.clear()
            await RisingEdge(self.cfg.vif.clk)
            self.ev_last_clock.set()

    async def detect_reset(self):
        """Monitors if there is an ongoing reset, if so reset_active is set to True."""
        # Handle to the reset signal
        reset_signal = self.cfg.vif.rst
        # Configured reset level
        reset_level = '0' if self.cfg.active_low_reset else '1'
        # Asyncronous edge trigger for reset
        reset_edge = FallingEdge(reset_signal) if self.cfg.active_low_reset else RisingEdge(reset_signal)

        # Wait until singal not z anymore
        while not(str(reset_signal.value) == '0' or str(reset_signal.value) == '1'):
            await RisingEdge(self.cfg.vif.clk)

        # Get the initial state:
        if str(reset_signal.value) == reset_level:
            self.reset_inactive.clear()
            self.reset_active.set()
        else:
            self.reset_inactive.set()
            self.reset_active.clear()

        while True:
            # Reset is set on async reset edge
            if self.reset_inactive.is_set():
                await reset_edge
                self.reset_inactive.clear()
                self.reset_active.set()

            # Reset is released on syncronous reset level
            elif self.reset_active.is_set():
                while str(reset_signal.value) == reset_level:
                    await RisingEdge(self.cfg.vif.clk)
                self.reset_inactive.set()
                self.reset_active.clear()


    async def handle_reset(self):
        """ Kills driver process when reset is active"""
        while True:
            # Wait for reset
            await self.reset_active.wait()

            if self.get_and_drive_process is not None:
                self.logger.debug("Killing driver process")
                self.get_and_drive_process.kill()
                self.get_and_drive_process = None
                # Ends any active items
                try:
                    self.logger.debug(f"Ending any active items")
                    self.seq_item_port.item_done()
                except UVMSequenceError:
                    self.logger.debug("No current active item")

            # Wait for reset to end
            await self.reset_inactive.wait()


    async def drive_transaction(self):
        while True:
            await self.drive_reset()

            await self.reset_inactive.wait()

            # Passes coroutine to process handle -> possible to kill() process
            self.get_and_drive_process = cocotb.start_soon(self.get_and_drive_transaction())
            # Waits for process to finish
            await self.get_and_drive_process

    async def get_and_drive_transaction(self):
        # Start driver loop
        await self.driver_loop()

    async def drive_reset(self):
        # Reset interface values according to type
        self.logger.critical(f"Driver type not handled {self.get_full_name()}")

    async def driver_loop(self):
        while True:
            self.logger.debug("APB-Driver waiting for next seq_item")

            # Waits for seq item
            self.req = await self.seq_item_port.get_next_item()
            self.logger.debug(f"APB-Driver item: {self.req}")

            # Creates clone of seq item
            self.rsp = self.req.clone()
            # Set the transaction ID
            self.rsp.set_id_info(self.req)
            # Set the response ID
            self.rsp.set_context(self.req)

            self.logger.debug("Driving pins")
            await self.drive_pins()

            self.seq_item_port.item_done(self.rsp)
