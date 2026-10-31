import logging
import argparse
from app.core.database import SessionLocal, Base, engine
from scripts.seed_parts.catalog_subs import seed as seed_catalog_subs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("brightloop.seed")


def main():
    parser = argparse.ArgumentParser(description="Seed Brightloop database")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()

    if args.reset:
        logger.info("Dropping all existing database tables...")
        Base.metadata.drop_all(bind=engine)

    logger.info("Ensuring all database tables exist...")
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        logger.info("Seeding Catalog and Subscriptions domain data...")
        counts = seed_catalog_subs(session)
        logger.info("Seeded: %s", counts)
    finally:
        session.close()


if __name__ == "__main__":
    main()
