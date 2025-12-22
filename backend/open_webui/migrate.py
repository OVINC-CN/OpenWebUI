from open_webui.env import OPEN_WEBUI_DIR, log
from open_webui.internal.db import Session
from sqlalchemy import text


# Function to run the alembic migrations
def run_migrations():
    log.info("Running migrations")
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")

        # Set the script location dynamically
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        log.exception(f"Error running migrations: {e}")


def run_extra_migrations():
    """
    Only create table or index is allowed here.
    """
    custom_migrations = [
        {"base": "3781e22d8b01", "upgrade_to": "1403e6d80d1d"},
        {"base": "d31026856c01", "upgrade_to": "97c08d196e3d"},
    ]
    log.info("Running extra migrations")
    # do migrations
    try:
        # load version from db
        current_version = Session.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

        # init alembic
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config(OPEN_WEBUI_DIR / "alembic.ini")
        migrations_path = OPEN_WEBUI_DIR / "migrations"
        alembic_cfg.set_main_option("script_location", str(migrations_path))

        # do migrations
        for migration in custom_migrations:
            try:
                command.stamp(alembic_cfg, migration["base"])
                command.upgrade(alembic_cfg, migration["upgrade_to"])
            except Exception as err:
                err = str(err)
                if err.index("already exists") != -1 or err.index("duplicate") != -1:
                    log.info(
                        "skip migrate %s to %s: already exists",
                        migration["base"],
                        migration["upgrade_to"],
                    )
                    continue
                log.warning(
                    "failed to migrate %s to %s: %s",
                    migration["base"],
                    migration["upgrade_to"],
                    err,
                )

        # stamp to current version
        command.stamp(alembic_cfg, current_version)
    except Exception as e:
        log.exception("Error running extra migrations: %s", e)


if __name__ == "__main__":
    run_migrations()
    run_extra_migrations()
