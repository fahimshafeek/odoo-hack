import datetime
from typing import Optional, List
from sqlalchemy import select
from app.core.clock import today as get_today, now as get_now
from app.core.errors import AppError
from app.core.deps import AuthUser
from app.catalog.models import Plan, QuotationTemplate
from app.subscriptions.models import Subscription, SubscriptionLine, SubscriptionHistory
from app.subscriptions.billing_support import add_period


CUSTOMER_ALLOWED_ACTIONS = {"pause", "resume", "close", "renew"}


def allowed_actions(sub: Subscription, plan, user: Optional[AuthUser]) -> List[str]:
    """
    Return exact list of action names that would succeed right now for this subscription,
    plan, and user role.
    """
    actions: List[str] = []
    status = sub.status
    role = user.role if user else "admin"

    if status == "draft":
        if role in ("admin", "staff"):
            # Guard: >= 1 line, plan active
            has_lines = bool(sub.lines and len(sub.lines) >= 1) if "lines" in sub.__dict__ else True
            is_plan_active = bool(plan.is_active) if plan else True
            if has_lines and is_plan_active:
                actions.append("send_quote")

    elif status == "quotation":
        if role in ("admin", "staff"):
            actions.extend(["confirm", "reject"])

    elif status == "confirmed":
        if role in ("admin", "staff"):
            actions.append("activate")

    elif status == "active":
        # Pause
        if plan and plan.allow_pause:
            if role in ("admin", "staff") or role == "customer":
                actions.append("pause")
        # Renew
        if plan and plan.allow_renew:
            if role in ("admin", "staff") or role == "customer":
                actions.append("renew")
        # Close early
        if plan and plan.allow_early_close:
            if role in ("admin", "staff") or role == "customer":
                actions.append("close")

    elif status == "paused":
        if role in ("admin", "staff") or role == "customer":
            actions.append("resume")

    return actions


def transition(
    session,
    sub: Subscription,
    action: str,
    user: Optional[AuthUser],
    note: Optional[str] = None,
) -> Subscription:
    """
    Single central transition function for Subscription state machine.
    Enforces legality, plan flags, and role permissions.
    Records history entry.
    """
    # Safely load plan, lines, template even when lazy='raise'
    if "plan" in sub.__dict__ and sub.__dict__["plan"] is not None:
        plan = sub.plan
    else:
        plan = session.get(Plan, sub.plan_id)

    role = user.role if user else "system"
    today = get_today()
    now = get_now()

    # 1. Role permission check
    if role == "customer" and action not in CUSTOMER_ALLOWED_ACTIONS:
        raise AppError("forbidden", f"Customers are not permitted to perform action '{action}'", 403)

    from_status = sub.status
    to_status: str = from_status
    extra_history_note: Optional[str] = note

    # 2. Transition rules and guards
    if from_status == "draft":
        if action == "send_quote":
            # Load lines if not loaded
            if "lines" in sub.__dict__:
                lines = sub.lines
            else:
                lines = session.execute(
                    select(SubscriptionLine).where(SubscriptionLine.subscription_id == sub.id)
                ).scalars().all()

            if not lines or len(lines) < 1:
                raise AppError("plan_rule_violation", "Quotation requires at least one line item", 409)
            if not plan or not plan.is_active:
                raise AppError("plan_rule_violation", "Cannot send quote for an inactive plan", 409)
            if plan.valid_from and sub.start_date < plan.valid_from:
                raise AppError("plan_rule_violation", f"Subscription start_date {sub.start_date} is before plan validity {plan.valid_from}", 409)
            if plan.valid_to and sub.start_date > plan.valid_to:
                raise AppError("plan_rule_violation", f"Subscription start_date {sub.start_date} is after plan validity {plan.valid_to}", 409)
            if sub.expiry_date <= sub.start_date:
                raise AppError("plan_rule_violation", "Expiry date must be after start date", 409)

            to_status = "quotation"
            # Set quote_valid_until per D24
            validity_days = 30
            if sub.quotation_template_id:
                if "template" in sub.__dict__ and sub.__dict__["template"] is not None:
                    tpl = sub.template
                else:
                    tpl = session.get(QuotationTemplate, sub.quotation_template_id)
                if tpl and tpl.validity_days:
                    validity_days = tpl.validity_days
            sub.quote_valid_until = today + datetime.timedelta(days=validity_days)
        else:
            raise AppError("invalid_transition", f"Cannot transition draft with action '{action}'", 409)

    elif from_status == "quotation":
        if action == "confirm":
            to_status = "confirmed"
        elif action == "reject":
            to_status = "closed"
        elif action == "expire-quote":  # System action
            to_status = "closed"
            extra_history_note = extra_history_note or "Quotation expired past validity date"
        else:
            raise AppError("invalid_transition", f"Cannot transition quotation with action '{action}'", 409)

    elif from_status == "confirmed":
        if action == "activate":
            to_status = "active"
            sub.next_billing_date = sub.start_date
        else:
            raise AppError("invalid_transition", f"Cannot transition confirmed with action '{action}'", 409)

    elif from_status == "active":
        if action == "pause":
            if not plan or not plan.allow_pause:
                raise AppError("plan_rule_violation", "This plan does not allow pausing", 409)
            to_status = "paused"
        elif action == "renew":
            if not plan or not plan.allow_renew:
                raise AppError("plan_rule_violation", "This plan does not allow renewal", 409)
            # D17: extends expiry_date by one original term (min 1 billing period)
            original_term = sub.expiry_date - sub.start_date
            if original_term <= datetime.timedelta(days=0):
                original_term = datetime.timedelta(days=30)
            old_expiry = sub.expiry_date
            sub.expiry_date = old_expiry + original_term
            sub.renewal_flagged_at = None
            to_status = "active"
            renew_msg = f"Renewed: expiry extended from {old_expiry} to {sub.expiry_date}"
            extra_history_note = f"{renew_msg}. {note}" if note else renew_msg
        elif action == "close":
            if not plan or not plan.allow_early_close:
                raise AppError("plan_rule_violation", "This plan does not allow early close", 409)
            to_status = "closed"
        elif action == "auto-close":  # System action
            to_status = "closed"
            extra_history_note = extra_history_note or "Auto-closed on reaching expiry date"
        else:
            raise AppError("invalid_transition", f"Cannot transition active with action '{action}'", 409)

    elif from_status == "paused":
        if action == "resume":
            to_status = "active"
            # D16: if next_billing_date < today, advance to first period start >= today
            if sub.next_billing_date and sub.next_billing_date < today:
                skipped_count = 0
                cur_next = sub.next_billing_date
                anchor = sub.start_date.day
                period_type = plan.billing_period if plan else "monthly"

                while cur_next < today:
                    skipped_count += 1
                    cur_next = add_period(cur_next, period_type, anchor)

                sub.next_billing_date = cur_next
                resume_msg = f"skipped {skipped_count} paused period(s)"
                extra_history_note = f"{resume_msg}. {note}" if note else resume_msg
        else:
            raise AppError("invalid_transition", f"Cannot transition paused with action '{action}'", 409)

    elif from_status == "closed":
        raise AppError("invalid_transition", f"Closed subscription cannot be transitioned (action '{action}')", 409)

    # 3. Apply status update
    sub.status = to_status

    # 4. Insert history log
    history_entry = SubscriptionHistory(
        subscription_id=sub.id,
        from_status=from_status,
        to_status=to_status,
        action=action,
        changed_by=user.id if user else None,
        changed_at=now,
        note=extra_history_note,
    )
    session.add(history_entry)
    session.flush()

    return sub
