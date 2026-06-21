import importlib.util
import sys
from pathlib import Path

from graphics_runtime import Directive as ActiveDirective
from graphics_runtime import DirectivePacket as ActivePacket
from graphics_runtime import Opcode as ActiveOpcode


def load_upstream_directives():
    path = (
        Path(__file__).resolve().parents[1]
        / "vendor"
        / "cyglobsgl_upstream"
        / "cyglobsgl"
        / "directives.py"
    )
    module_name = "vendored_cyglobsgl_directives"
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_active_packet_matches_vendored_cyglobsgl():
    upstream = load_upstream_directives()
    active = ActivePacket(
        ActiveDirective(ActiveOpcode.ROTATE, 7, 0.25, 0.62, 0.0)
    ).to_hex()
    reference = upstream.DirectivePacket(
        upstream.Directive(upstream.Opcode.ROTATE, 7, 0.25, 0.62, 0.0)
    ).to_hex()
    assert active == reference


def test_vendored_packet_round_trip():
    upstream = load_upstream_directives()
    packet = upstream.DirectivePacket(
        upstream.Directive(upstream.Opcode.SCALE, 7, 0.62, 0.62, 0.62)
    )
    restored = upstream.DirectivePacket.from_hex(packet.to_hex())
    assert restored.directive.opcode is upstream.Opcode.SCALE
    assert restored.directive.object_id == 7
