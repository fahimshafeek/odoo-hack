import uuid
from decimal import Decimal
from typing import Sequence, List, Dict
from pydantic import BaseModel, Field
from app.core.money import Money, q2, to_decimal
from app.core.errors import AppError


class VariantSelection(BaseModel):
    attribute: str
    value: str
    extra_price: Money


class VariantSnapshot(BaseModel):
    selections: List[VariantSelection] = Field(default_factory=list)


def resolve_variant(product, value_ids: Sequence[uuid.UUID]) -> VariantSnapshot:
    """
    Resolve given attribute value IDs against the product's attributes.
    Enforces:
    1. Every value_id must belong to one of product's attributes (foreign ids rejected).
    2. At most one value per attribute (multiple values of the same attribute rejected).
    Returns a VariantSnapshot with selections.
    """
    if not value_ids:
        return VariantSnapshot(selections=[])

    # Map value_id -> (attribute_name, value_name, extra_price, attribute_id)
    allowed_values: Dict[uuid.UUID, tuple[str, str, Decimal, uuid.UUID]] = {}
    for attr in product.attributes:
        for val in attr.values:
            allowed_values[val.id] = (attr.name, val.name, to_decimal(val.extra_price), attr.id)

    seen_attrs: Dict[uuid.UUID, str] = {}
    selections: List[VariantSelection] = []

    for val_id in value_ids:
        # Check foreign
        if val_id not in allowed_values:
            raise AppError(
                "validation_error",
                f"Variant value {val_id} does not belong to product '{product.name}'",
                422,
                fields={"variant_value_ids": f"Value {val_id} is foreign to this product"},
            )

        attr_name, val_name, extra, attr_id = allowed_values[val_id]

        # Check duplicate attribute
        if attr_id in seen_attrs:
            raise AppError(
                "validation_error",
                f"Multiple values selected for attribute '{attr_name}'",
                422,
                fields={"variant_value_ids": f"Duplicate value for attribute '{attr_name}'"},
            )

        seen_attrs[attr_id] = attr_name
        selections.append(
            VariantSelection(
                attribute=attr_name,
                value=val_name,
                extra_price=q2(extra),
            )
        )

    # Sort selections by attribute name for deterministic snapshots
    selections.sort(key=lambda s: s.attribute)
    return VariantSnapshot(selections=selections)


def unit_price(product, snapshot: VariantSnapshot) -> Decimal:
    """Compute line unit price: product.sales_price + sum(variant extra prices)."""
    base = to_decimal(product.sales_price)
    extra_sum = sum((to_decimal(s.extra_price) for s in snapshot.selections), Decimal("0.00"))
    return q2(base + extra_sum)


def line_amount(quantity: int, unit_price_val: Decimal) -> Decimal:
    """Compute line gross amount: q2(quantity * unit_price)."""
    if quantity < 1:
        raise AppError("validation_error", "Quantity must be >= 1", 422, fields={"quantity": "Must be >= 1"})
    return q2(Decimal(quantity) * to_decimal(unit_price_val))
