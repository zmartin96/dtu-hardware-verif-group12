from pyuvm import uvm_report_object
import vsc
from .cl_apb_seq_item import cl_apb_seq_item

def apb_change_width(addr_width = 8, data_width = 8):
    """ Method that retuns a class definition which can be used by the UVM Factory to override the base sequence item class.
    The new class definition assures that the agent is using the correct WIDTH (from the configuration object)."""

    @vsc.randobj
    class cl_apb_seq_item_updated(cl_apb_seq_item):
        """Common base sequence item for the APB agent"""

        def __init__(self, name = "apb_item_updated", addr_width = addr_width, data_width = data_width):
            super().__init__(name, addr_width = addr_width, data_width = data_width)

    return cl_apb_seq_item_updated

# NOTE: The arguments `addr_width` and `data_width` are only used for parametization.
# They can not be set per instance. (See detailed explanation below)
# In short, they are used in the constructor of cl_apb_seq_item as parameters to create the `data` and `address` attibutes, but always retain the default value set here.

# Detailed explanation:
# All instances of cl_apb_seq_item (or subclasses) are created though the factory with the `<class>.create(name)` method.
# The factory calls the appropriate constructor of the cl_apb_seq_item or the override, but it will always call it with only the `name` argument.
# Thus no additional aruments can be given to the constructor of the individual instances.
# But since arguments with default values are optional in python, any instance created from the factory, will just take the default value.
# The subclass created in this function overwrites the default values for `addr_width` and `data_width`.

