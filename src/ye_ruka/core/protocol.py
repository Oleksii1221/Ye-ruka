from __future__ import annotations

from dataclasses import dataclass


class ProtocolError(ValueError):
    pass


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


@dataclass(slots=True)
class DecodedPacket:
    sequence: int
    values: list[int]


class SerialProtocol:
    SIMPLE = "simple"
    EXTENDED = "extended"

    def __init__(self, mode: str = EXTENDED) -> None:
        self.mode = mode

    def encode(self, sequence: int, values: list[int]) -> str:
        if self.mode == self.SIMPLE:
            return "[" + ",".join(str(int(value)) for value in values) + "]\n"
        body = f"YR1,{sequence % 100000:05d},{len(values)}," + ",".join(str(int(value)) for value in values)
        checksum = crc16_ccitt(body.encode("ascii"))
        return f"@{body}*{checksum:04X}\n"

    def decode(self, line: str) -> DecodedPacket:
        text = line.strip()
        if text.startswith("[") and text.endswith("]"):
            inner = text[1:-1].strip()
            values = [] if not inner else [int(part.strip()) for part in inner.split(",")]
            return DecodedPacket(0, values)
        if not text.startswith("@") or "*" not in text:
            raise ProtocolError("Некоректний початок пакета")
        payload, checksum_text = text[1:].rsplit("*", 1)
        try:
            received = int(checksum_text, 16)
        except ValueError as exc:
            raise ProtocolError("Некоректна CRC") from exc
        expected = crc16_ccitt(payload.encode("ascii"))
        if received != expected:
            raise ProtocolError("CRC не збігається")
        parts = payload.split(",")
        if len(parts) < 4 or parts[0] != "YR1":
            raise ProtocolError("Невідома версія протоколу")
        try:
            sequence = int(parts[1])
            count = int(parts[2])
            values = [int(part) for part in parts[3:]]
        except ValueError as exc:
            raise ProtocolError("Поля пакета не є числами") from exc
        if count != len(values):
            raise ProtocolError("Кількість каналів не збігається")
        return DecodedPacket(sequence, values)
