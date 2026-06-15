import pytest

from ye_ruka.glove.protocol import GloveProtocol, GloveProtocolError


def test_array_packet():
    values = GloveProtocol("array").parse("[0,512,1024,2048,3072,4095]", 6)
    assert values == [0.0, 512.0, 1024.0, 2048.0, 3072.0, 4095.0]


def test_prefixed_packet_with_sequence_and_count():
    values = GloveProtocol("prefixed").parse("@GLV1,00125,6,10,20,30,40,50,60*ABCD", 6)
    assert values == [10.0, 20.0, 30.0, 40.0, 50.0, 60.0]


def test_auto_csv_packet():
    assert GloveProtocol("auto").parse("1,2,3,4", 4) == [1.0, 2.0, 3.0, 4.0]


def test_too_few_channels():
    with pytest.raises(GloveProtocolError):
        GloveProtocol("auto").parse("[1,2]", 3)
