import argparse
import sys
import time
from app.core.clock import today
from app.core.db import SessionLocal
from app.subscriptions.jobs import (
    activate_due,
    auto_close_expired,
    expire_quotes,
    flag_upcoming_renewals,
)
from app.billing.engine import run_billing


def run_all_jobs(verbose: bool = True):
    session = SessionLocal()
    try:
        t = today()
        if verbose:
            print(f"[{t}] Starting scheduled worker jobs...")

        res_act = activate_due(session, t)
        if verbose:
            print(f"  - Auto-activated subscriptions: {res_act}")

        res_exp = expire_quotes(session, t)
        if verbose:
            print(f"  - Expired quotations: {res_exp}")

        res_cls = auto_close_expired(session, t)
        if verbose:
            print(f"  - Auto-closed expired subscriptions: {res_cls}")

        res_ren = flag_upcoming_renewals(session, t)
        if verbose:
            print(f"  - Flagged upcoming renewals: {res_ren}")

        session.commit()

        # Run Billing Run
        run_id = run_billing(SessionLocal, as_of=t)
        if verbose:
            print(f"  - Executed automated billing run: {run_id}")

        if verbose:
            print(f"[{t}] Worker cycle completed successfully.")
    except Exception as e:
        session.rollback()
        print(f"Error in worker run: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Brightloop Background Worker")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--interval", type=int, default=3600, help="Interval in seconds for daemon mode")
    args = parser.parse_args()

    if args.once:
        run_all_jobs()
        return

    print(f"Brightloop Worker daemon started (interval: {args.interval}s)...")
    while True:
        try:
            run_all_jobs()
        except Exception as e:
            print(f"Worker iteration error: {e}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
