from quickbats.qbo import QBO

qbo = QBO()
qbo.connect()

def test_get_item_by_name():
    item = qbo.get_item_by_name("Design")
    assert item.Name == "Design"
    assert "Item:Design" in qbo._cache
