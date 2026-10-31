# Payments package


def __getattr__(name: str):
    if name in ("record_payment", "mock_pay"):
        from app.payments import service
        return getattr(service, name)
    if name == "Payment":
        from app.payments.models import Payment
        return Payment
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
