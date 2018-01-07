from quickbats.shared import csv_rows

def test_csv_rows():
    for row in csv_rows("tests/data/iris.csv"):
        assert "sepal_length" in row

def test_stop_after():
    for i, row in enumerate(csv_rows("tests/data/iris.csv", stop_after=10)):
        pass
    assert i==9
