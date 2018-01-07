from decimal import Decimal
from quickbats.shared import csv_rows
from quickbats.shared import to_dec


def test_csv_rows():
    for row in csv_rows("tests/data/iris.csv"):
        assert "sepal_length" in row


def test_stop_after():
    for i, row in enumerate(csv_rows("tests/data/iris.csv", stop_after=10)):
        pass
    assert i==9


def test_to_dec_positive():
    assert to_dec("$1.00") == Decimal(1.0)


def test_to_dec_negative():
    assert to_dec("($1.00)") == Decimal(-1.0)
