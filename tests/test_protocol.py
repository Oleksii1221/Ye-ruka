import pytest

from ye_ruka.core.protocol import ProtocolError, SerialProtocol


def test_extended_round_trip():
    protocol = SerialProtocol("extended")
    packet = protocol.encode(125, [90, 45, 180])
    decoded = protocol.decode(packet)
    assert decoded.sequence == 125
    assert decoded.values == [90, 45, 180]


def test_simple_round_trip():
    protocol = SerialProtocol("simple")
    packet = protocol.encode(0, [1, 2, 3])
    assert protocol.decode(packet).values == [1, 2, 3]


def test_crc_error():
    protocol = SerialProtocol("extended")
    packet = protocol.encode(1, [90, 90]).replace("90,90", "90,91")
    with pytest.raises(ProtocolError):
        protocol.decode(packet)
