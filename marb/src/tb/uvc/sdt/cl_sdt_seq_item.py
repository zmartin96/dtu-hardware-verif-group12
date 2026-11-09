"""SDT-UVC sequence item. Contrained random verification methodology using PyVSC."""

import vsc
from pyuvm import uvm_sequence_item


@vsc.randobj
class cl_sdt_seq_item(uvm_sequence_item):
    """Common base sequence item for the SDT agent"""

    def __init__(self, name = "sdt_item", addr_width=1, data_width=1):
        uvm_sequence_item.__init__(self, name)

        #  Configuration settings
        self.no_producer_consumer_delays = vsc.rand_bit_t(1)
        self.max_consumer_delay_rdwr1_ack1 = 5

        # Transaction members
        self.access = vsc.rand_bit_t(1)
        self.addr = vsc.rand_bit_t(addr_width)
        self.data = vsc.rand_bit_t(data_width)

        # Cycle delays
        self.consumer_delay_rdwr1_ack1 = vsc.rand_uint32_t()

    ########################
    #  Soft constraints
    #######################
    @vsc.constraint
    def c_default_consumer_delay_cycles(self):
        """Default consumer delay cycle of 1"""
        vsc.soft(self.consumer_delay_rdwr1_ack1 == 0)

    @vsc.constraint
    def c_consumer_delay_cycles(self):
        self.no_producer_consumer_delays <= 1

        with vsc.if_then(self.no_producer_consumer_delays == 1):
            self.consumer_delay_rdwr1_ack1 == 0
        with vsc.else_if(self.no_producer_consumer_delays != 1):
            self.consumer_delay_rdwr1_ack1 <= self.max_consumer_delay_rdwr1_ack1

    def do_copy(self, rhs):
        """Defines how copy of the SDT sequence item is done

        Used when calling clone() of SDT sequence item"""

        super().do_copy(rhs)

        # Ranomizable item members
        self.access = rhs.access
        self.addr = rhs.addr
        self.data = rhs.data

        # Cycle delays
        self.consumer_delay_rdwr1_ack1 = rhs.consumer_delay_rdwr1_ack1

        # Configuration settings
        self.no_producer_consumer_delays = rhs.no_producer_consumer_delays
        self.max_consumer_delay_rdwr1_ack1 = rhs.max_consumer_delay_rdwr1_ack1

    def __eq__(self, other) -> bool:
        # Defines how sequence items are compared
        if isinstance(other, cl_sdt_seq_item):
            return self.access == other.access and self.addr == other.addr \
                and self.data == other.data
        return False

    def __str__(self) -> str:
        # Defines output string when printing sequence item
        if self.data is None:
            self.data = 0

        if self.access == 0:
            return f"{self.get_name()} : access = AccessType.RD, addr = {self.addr}, data = {self.data}"
        if self.access == 1:
            return f"{self.get_name()} : access = AccessType.WR, addr = {self.addr}, data = {self.data}"
        msg = f"Unkown access value: {self.access}"
        raise ValueError(msg)
