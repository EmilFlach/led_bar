import logging
from pathlib import Path

import typer
from faebryk.libs.app.kicad_netlist import write_netlist
from faebryk.libs.logging import setup_basic_logging
from ledbar.app import App, pick_part_recursively

logger = logging.getLogger(__name__)


def main(variant: str = "FULL"):
    # paths
    build_dir = Path("./build")
    faebryk_build_dir = build_dir.joinpath("faebryk")
    faebryk_build_dir.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).parent.parent.parent
    kicad_prj_path = root.joinpath("source")
    netlist_path = kicad_prj_path.joinpath("main.net")
    bom_dir = kicad_prj_path.joinpath(variant)
    # bom_path = bom_dir.joinpath("bom.csv")
    # pcbfile = kicad_prj_path.joinpath("main.kicad_pcb")

    bom_dir.mkdir(parents=True, exist_ok=True)

    import faebryk.libs.picker.lcsc as lcsc

    lcsc.BUILD_FOLDER = build_dir
    lcsc.LIB_FOLDER = root / "libs"

    # graph
    app = App()
    pick_part_recursively(app)
    G = app.get_graph()

    # netlist
    write_netlist(G, netlist_path, use_kicad_designators=True)


if __name__ == "__main__":
    setup_basic_logging()
    typer.run(main)
