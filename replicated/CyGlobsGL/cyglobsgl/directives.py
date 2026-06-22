"""Validated directive packets replicated from CyGlobsGL."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import math
import struct
from typing import Iterable, Sequence, TypeVar

DEFAULT_RADIUS = 0.62
_PACKET = struct.Struct(">BBhhh")
_T = TypeVar("_T")


class Opcode(IntEnum):
    SORT = 0x1
    TRANSLATE = 0x2
    ROTATE = 0x3
    SCALE = 0x4


DOMAIN_BY_OPCODE = {
    Opcode.SORT: "Jecht",
    Opcode.TRANSLATE: "Daq",
    Opcode.ROTATE: "MVP",
    Opcode.SCALE: "Cap",
}


@dataclass(frozen=True, slots=True)
class Directive:
    opcode: Opcode
    object_id: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    flags: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.object_id <= 0xFF:
            raise ValueError("object_id must fit in one byte")
        if not 0 <= self.flags <= 0x0F:
            raise ValueError("flags must fit in four bits")
        for name, value in (("x", self.x), ("y", self.y), ("z", self.z)):
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if not -128.0 <= value <= 127.99609375:
                raise ValueError(f"{name} is outside signed Q8.8 range")

    @property
    def domain(self) -> str:
        return DOMAIN_BY_OPCODE[self.opcode]


@dataclass(frozen=True, slots=True)
class DirectivePacket:
    directive: Directive

    def pack(self) -> bytes:
        d = self.directive
        return _PACKET.pack(
            (int(d.opcode) << 4) | d.flags,
            d.object_id,
            int(round(d.x * 256.0)),
            int(round(d.y * 256.0)),
            int(round(d.z * 256.0)),
        )

    def to_hex(self) -> str:
        return self.pack().hex()

    @classmethod
    def unpack(cls, raw: bytes) -> "DirectivePacket":
        if len(raw) != _PACKET.size:
            raise ValueError(f"directive packet must be exactly {_PACKET.size} bytes")
        opcode_flags, object_id, x, y, z = _PACKET.unpack(raw)
        try:
            opcode = Opcode(opcode_flags >> 4)
        except ValueError as exc:
            raise ValueError(f"unknown directive opcode: 0x{opcode_flags >> 4:x}") from exc
        return cls(Directive(opcode, object_id, x / 256.0, y / 256.0, z / 256.0, opcode_flags & 0x0F))

    @classmethod
    def from_hex(cls, value: str) -> "DirectivePacket":
        return cls.unpack(bytes.fromhex(value))


def sort_jecht(values: Iterable[_T]) -> list[_T]:
    return sorted(values)


def translate_daq(position: Sequence[float], directive: Directive) -> tuple[float, float, float]:
    if directive.opcode is not Opcode.TRANSLATE or len(position) != 3:
        raise ValueError("translate_daq requires a 3D TRANSLATE directive")
    return tuple(float(value) + delta for value, delta in zip(position, (directive.x, directive.y, directive.z)))


def scale_cap(position: Sequence[float], directive: Directive | None = None) -> tuple[float, float, float]:
    if len(position) != 3:
        raise ValueError("position must contain exactly three values")
    factors = (DEFAULT_RADIUS,) * 3 if directive is None else (directive.x, directive.y, directive.z)
    if directive is not None and directive.opcode is not Opcode.SCALE:
        raise ValueError("scale_cap requires a SCALE directive")
    return tuple(float(value) * factor for value, factor in zip(position, factors))
