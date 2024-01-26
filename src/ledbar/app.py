import logging

from faebryk.core.core import Module, ModuleInterface
from faebryk.core.util import specialize_module
from faebryk.library.Constant import Constant
from faebryk.library.Electrical import Electrical
from faebryk.library.ElectricPower import ElectricPower
from faebryk.library.LED import LED
from faebryk.library.PoweredLED import PoweredLED
from faebryk.library.Range import Range
from faebryk.library.Resistor import Resistor
from faebryk.library.TBD import TBD
from faebryk.libs.picker.lcsc import LCSC_Part
from faebryk.libs.picker.picker import (
    PickerOption,
    has_part_picked,
    pick_module_by_params,
)
from ledbar.library.ESP32_C3_MINI_1 import ESP32_C3_MINI_1_VIND

logger = logging.getLogger(__name__)


def pick_part_recursively(module: Module):
    assert isinstance(module, Module)

    # pick only for most specialized module
    module = module.get_most_special()

    if module.has_trait(has_part_picked):
        return

    # pick mif module parts
    def _get_mif_top_level_modules(mif: ModuleInterface):
        return [n for n in mif.NODEs.get_all() if isinstance(n, Module)] + [
            m for nmif in mif.IFs.get_all() for m in _get_mif_top_level_modules(nmif)
        ]

    for mif in module.IFs.get_all():
        for mod in _get_mif_top_level_modules(mif):
            pick_part_recursively(mod)

    # switch over types
    if isinstance(module, PoweredLED):
        pick_led(module.NODEs.led.get_most_special())
        pick_resistor(module.NODEs.current_limiting_resistor)
    else:
        children = module.NODEs.get_all()
        if not children:
            logger.warning(f"Module without pick: {module}")
        for child in children:
            if not isinstance(child, Module):
                continue
            if child is module:
                continue
            pick_part_recursively(child)


def pick_resistor(resistor: Resistor):
    """
    Link a partnumber/footprint to a Resistor

    Selects only 1% 0402 resistors
    """

    pick_module_by_params(
        resistor,
        [
            PickerOption(
                part=LCSC_Part(partno="C25076"),
                params={"resistance": Constant(100)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25087"),
                params={"resistance": Constant(200)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C11702"),
                params={"resistance": Constant(1e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25879"),
                params={"resistance": Constant(2.2e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25900"),
                params={"resistance": Constant(4.7e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25905"),
                params={"resistance": Constant(5.1e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25917"),
                params={"resistance": Constant(6.8e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25744"),
                params={"resistance": Constant(10e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25752"),
                params={"resistance": Constant(12e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25771"),
                params={"resistance": Constant(27e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25741"),
                params={"resistance": Constant(100e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25782"),
                params={"resistance": Constant(390e3)},
            ),
            PickerOption(
                part=LCSC_Part(partno="C25790"),
                params={"resistance": Constant(470e3)},
            ),
        ],
    )


def pick_led(module: LED):
    pick_module_by_params(
        module,
        [
            PickerOption(
                part=LCSC_Part(partno="C72043"),
                params={
                    "color": Constant(2),
                    "max_brightness": Constant(285e-3),
                    "forward_voltage": Constant(3.7),
                    "max_current": Constant(100e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72041"),
                params={
                    "color": Constant(3),
                    "max_brightness": Constant(28.5e-3),
                    "forward_voltage": Constant(3.1),
                    "max_current": Constant(100e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
            PickerOption(
                part=LCSC_Part(partno="C72038"),
                params={
                    "color": Constant(4),
                    "max_brightness": Constant(180e-3),
                    "forward_voltage": Constant(2.3),
                    "max_current": Constant(60e-3),
                },
                pinmap={"1": module.IFs.cathode, "2": module.IFs.anode},
            ),
        ],
    )


class ColoredLED(LED):
    def __init__(self) -> None:
        super().__init__()

        class _PARAMS(LED.PARAMS()):
            color = TBD()

        self.PARAMs = _PARAMS(self)


class App(Module):
    def __init__(self) -> None:
        super().__init__()

        class _IFS(Module.IFS()):
            input_power = ElectricPower()
            input_control = Electrical()

        _esp = ESP32_C3_MINI_1_VIND()
        _led = PoweredLED()
        my_colored_led = ColoredLED()
        specialize_module(_led.NODEs.led, my_colored_led)
        my_colored_led.PARAMs.color.merge(2)
        my_colored_led.PARAMs.brightness.merge(Range.from_center(1e-3, 300e-6))

        class _NODES(Module.NODES()):
            led = _led
            esp = _esp

        self.IFs = _IFS(self)
        self.NODEs = _NODES(self)

        self.IFs.input_power.PARAMs.voltage.merge(5)
        _esp.IFs.pwr3v3.connect(self.IFs.input_power)
        _led.IFs.power.connect(self.IFs.input_power)
