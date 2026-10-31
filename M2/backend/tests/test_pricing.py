import uuid
from decimal import Decimal
import pytest
from app.core.errors import AppError
from app.subscriptions.pricing import resolve_variant, unit_price, line_amount, VariantSnapshot, VariantSelection


class DummyAttrValue:
    def __init__(self, id, name, extra_price):
        self.id = id
        self.name = name
        self.extra_price = extra_price


class DummyAttr:
    def __init__(self, id, name, values):
        self.id = id
        self.name = name
        self.values = values


class DummyProduct:
    def __init__(self, id, name, sales_price, attributes):
        self.id = id
        self.name = name
        self.sales_price = sales_price
        self.attributes = attributes


def test_mandatory_pricing_odoo_variant():
    """Mandatory test: base 1,000 + Brand=Odoo 560 = 1560.00"""
    val_odoo = DummyAttrValue(uuid.uuid4(), "Odoo", Decimal("560.00"))
    attr_brand = DummyAttr(uuid.uuid4(), "Brand", [val_odoo])
    product = DummyProduct(uuid.uuid4(), "Odoo ERP", Decimal("1000.00"), [attr_brand])

    snapshot = resolve_variant(product, [val_odoo.id])
    assert len(snapshot.selections) == 1
    assert snapshot.selections[0].attribute == "Brand"
    assert snapshot.selections[0].value == "Odoo"
    assert snapshot.selections[0].extra_price == Decimal("560.00")

    price = unit_price(product, snapshot)
    assert price == Decimal("1560.00")

    amount = line_amount(2, price)
    assert amount == Decimal("3120.00")


def test_two_attributes_pricing():
    """Two attributes: Brand +560, Support +200 = 1,760.00"""
    val_odoo = DummyAttrValue(uuid.uuid4(), "Odoo", Decimal("560.00"))
    attr_brand = DummyAttr(uuid.uuid4(), "Brand", [val_odoo])

    val_support = DummyAttrValue(uuid.uuid4(), "24/7 Priority", Decimal("200.00"))
    attr_support = DummyAttr(uuid.uuid4(), "Support", [val_support])

    product = DummyProduct(uuid.uuid4(), "Cloud Suite", Decimal("1000.00"), [attr_brand, attr_support])

    snapshot = resolve_variant(product, [val_odoo.id, val_support.id])
    assert len(snapshot.selections) == 2

    price = unit_price(product, snapshot)
    assert price == Decimal("1760.00")


def test_zero_extra_variant():
    """Variant with 0.00 extra price should not alter base price."""
    val_standard = DummyAttrValue(uuid.uuid4(), "Community", Decimal("0.00"))
    attr_edition = DummyAttr(uuid.uuid4(), "Edition", [val_standard])
    product = DummyProduct(uuid.uuid4(), "Standard Suite", Decimal("1000.00"), [attr_edition])

    snapshot = resolve_variant(product, [val_standard.id])
    price = unit_price(product, snapshot)
    assert price == Decimal("1000.00")


def test_foreign_value_rejected():
    """Value belonging to a different product is rejected with 422 validation_error."""
    attr_edition = DummyAttr(uuid.uuid4(), "Edition", [])
    product = DummyProduct(uuid.uuid4(), "Suite", Decimal("1000.00"), [attr_edition])

    foreign_id = uuid.uuid4()
    with pytest.raises(AppError) as exc_info:
        resolve_variant(product, [foreign_id])

    assert exc_info.value.status == 422
    assert exc_info.value.code == "validation_error"


def test_multiple_values_for_same_attribute_rejected():
    """Cannot select two values for the same attribute (e.g. 2 Brands)."""
    val1 = DummyAttrValue(uuid.uuid4(), "Odoo", Decimal("560.00"))
    val2 = DummyAttrValue(uuid.uuid4(), "Custom", Decimal("300.00"))
    attr_brand = DummyAttr(uuid.uuid4(), "Brand", [val1, val2])
    product = DummyProduct(uuid.uuid4(), "Suite", Decimal("1000.00"), [attr_brand])

    with pytest.raises(AppError) as exc_info:
        resolve_variant(product, [val1.id, val2.id])

    assert exc_info.value.status == 422
    assert "Multiple values" in exc_info.value.message
