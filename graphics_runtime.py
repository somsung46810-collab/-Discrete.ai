from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import IntEnum
import hashlib
import struct
from typing import Any

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

    def pack(self) -> bytes:
        item = self.directive
        return _PACKET.pack(
            (int(item.opcode) << 4) | item.flags,
            item.object_id,
            round(item.x * 256),
            round(item.y * 256),
            round(item.z * 256),
        )

    def to_hex(self) -> str:
        return self.pack().hex()


@dataclass(frozen=True)
class GeneratedImageAsset:
    """CyGlobsGL metadata for an image returned by a generation provider."""

    image_url: str
    provider: str
    model: str
    width: int
    height: int
    output_format: str
    byte_length: int
    sha256: str
    directive_packet: str
    radius: float = DEFAULT_RADIUS
    pipeline: tuple[str, ...] = (
        "Sort/Jecht",
        "Translate/Daq",
        "Rotate/MVP",
        "Scale/Cap",
        "Image Decode",
        "Texture Surface",
        "Framebuffer",
    )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["pipeline"] = list(self.pipeline)
        return result


def generated_image_asset(
    *,
    image_url: str,
    provider: str,
    model: str,
    width: int,
    height: int,
    output_format: str,
    image_bytes: bytes | None,
    object_id: int = 7,
) -> GeneratedImageAsset:
    """Create deterministic CyGlobsGL metadata for generated image output."""

    packet = DirectivePacket(
        Directive(
            opcode=Opcode.SCALE,
            object_id=object_id,
            x=DEFAULT_RADIUS,
            y=DEFAULT_RADIUS,
            z=DEFAULT_RADIUS,
        )
    )
    content = image_bytes or b""
    return GeneratedImageAsset(
        image_url=image_url,
        provider=provider,
        model=model,
        width=width,
        height=height,
        output_format=output_format,
        byte_length=len(content),
        sha256=hashlib.sha256(content).hexdigest() if content else "",
        directive_packet=packet.to_hex(),
    )
