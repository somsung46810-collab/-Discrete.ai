from dataclasses import dataclass
from enum import IntEnum
import struct

DEFAULT_RADIUS = 0.62
_PACKET = struct.Struct(">BBhhh")

class Opcode(IntEnum):
    SORT = 1
    TRANSLATE = 2
    ROTATE = 3
    SCALE = 4

@dataclass(frozen=True)
class Directive:
    opcode: Opcode
    object_id: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    flags: int = 0

@dataclass(frozen=True)
class DirectivePacket:
    directive: Directive

    def to_hex(self) -> str:
        item = self.directive
        raw = _PACKET.pack(
            (int(item.opcode) << 4) | item.flags,
            item.object_id,
            round(item.x * 256),
            round(item.y * 256),
            round(item.z * 256),
        )
        return raw.hex()
