from __future__ import annotations

import json
import math
import re


class GloveProtocolError(ValueError):
    pass


_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)")


class GloveProtocol:
    MODES = {"auto", "array", "csv", "prefixed"}

    def __init__(self, mode: str = "auto") -> None:
        self.mode = mode if mode in self.MODES else "auto"

    def parse(self, line: str, expected_channels: int = 0) -> list[float]:
        text = line.strip()
        if not text:
            raise GloveProtocolError("Порожній пакет")
        if len(text) > 4096:
            raise GloveProtocolError("Пакет рукавиці занадто довгий")
        parser_order = {
            "array": (self._array,),
            "csv": (self._csv,),
            "prefixed": (self._prefixed,),
            "auto": (self._array, self._prefixed, self._csv),
        }[self.mode]
        errors: list[str] = []
        for parser in parser_order:
            try:
                values = parser(text, expected_channels)
                if not values:
                    raise GloveProtocolError("Пакет не містить значень")
                if any(not math.isfinite(value) for value in values):
                    raise GloveProtocolError("Пакет містить NaN або нескінченне значення")
                if expected_channels and len(values) < expected_channels:
                    raise GloveProtocolError(
                        f"Очікується щонайменше {expected_channels} значень, отримано {len(values)}"
                    )
                return values
            except (GloveProtocolError, ValueError, json.JSONDecodeError) as exc:
                errors.append(str(exc))
        raise GloveProtocolError(errors[-1] if errors else "Невідомий формат пакета")

    @staticmethod
    def _array(text: str, expected_channels: int) -> list[float]:
        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end <= start:
            raise GloveProtocolError("Масив у квадратних дужках не знайдено")
        payload = json.loads(text[start : end + 1])
        if not isinstance(payload, list):
            raise GloveProtocolError("Очікується масив")
        values = [float(item) for item in payload]
        return values[:expected_channels] if expected_channels else values

    @staticmethod
    def _prefixed(text: str, expected_channels: int) -> list[float]:
        clean = text.split("*", 1)[0]
        if ":" in clean:
            clean = clean.split(":", 1)[1]
        elif clean.startswith("@"):
            clean = clean.lstrip("@").split(",", 1)[1] if "," in clean else ""
        numbers = [float(token) for token in _NUMBER.findall(clean)]
        if not numbers:
            raise GloveProtocolError("Числові значення після префікса не знайдено")
        if expected_channels and len(numbers) >= expected_channels + 2:
            possible_count = int(numbers[-expected_channels - 1])
            if possible_count == expected_channels:
                numbers = numbers[-expected_channels:]
        return numbers[:expected_channels] if expected_channels else numbers

    @staticmethod
    def _csv(text: str, expected_channels: int) -> list[float]:
        if any(char in text for char in "[]{}"):
            raise GloveProtocolError("CSV не повинен містити дужки")
        clean = text.split("*", 1)[0]
        if clean.startswith("@") and "," in clean:
            clean = clean.split(",", 1)[1]
        parts = [part.strip() for part in re.split(r"[,;\s]+", clean) if part.strip()]
        values = [float(part) for part in parts]
        return values[:expected_channels] if expected_channels else values
