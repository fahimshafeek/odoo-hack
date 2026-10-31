import argparse
import sys
import logging
from app.core.database import SessionLocal, Base, engine
import app.core.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.subscriptions.models  # noqa: F401
from app.subscriptions.jobs import (
    activate_due,
    expire_quotes,
    auto_close_expired,
    flag_upcoming_renewals,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("brightloop.worker")

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def run_job(job_name: str) -> None:
    session = SessionLocal()
    try:
        if job_name == "activate_due":
            count = activate_due(session)
            session.commit()
            logger.info("activate_due completed: %d processed", count)
        elif job_name == "expire_quotes":
            count = expire_quotes(session)
            session.commit()
            logger.info("expire_quotes completed: %d processed", count)
        elif job_name == "auto_close_expired":
            count = auto_close_expired(session)
            session.commit()
            logger.info("auto_close_expired completed: %d processed", count)
        elif job_name == "flag_upcoming_renewals":
            count = flag_upcoming_renewals(session)
            session.commit()
            logger.info("flag_upcoming_renewals completed: %d processed", count)
        elif job_name == "all":
            a = activate_due(session)
            b = expire_quotes(session)
            c = auto_close_expired(session)
            d = flag_upcoming_renewals(session)
            session.commit()
            logger.info("All jobs completed: activate=%d, expire=%d, auto_close=%d, renewals=%d", a, b, c, d)
        else:
            logger.error("Unknown job: %s", job_name)
            sys.exit(1)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Brightloop Worker & Lifecycle Jobs")
    parser.add_argument("--once", help="Run a specific job once (activate_due, expire_quotes, auto_close_expired, flag_upcoming_renewals, all)")
    args = parser.parse_args()

    if args.once:
        run_job(args.once)
    else:
        logger.info("Worker started in daemon mode. Use --once <job_name> for one-off runs.")


if __name__ == "__main__":
    main()
