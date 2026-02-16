#!/usr/bin/env python3
"""Database migration management script for TREFF Post-Generator.

Usage:
    python migrate.py upgrade              # Upgrade to latest version
    python migrate.py upgrade <revision>   # Upgrade to specific revision
    python migrate.py downgrade -1         # Downgrade by one revision
    python migrate.py downgrade <revision> # Downgrade to specific revision
    python migrate.py current              # Show current revision
    python migrate.py history              # Show migration history
    python migrate.py heads               # Show head revisions
    python migrate.py generate <message>   # Generate new migration (autogenerate)
    python migrate.py stamp <revision>     # Mark database as being at revision
    python migrate.py check               # Check if there are pending migrations
"""

import sys
import os
from pathlib import Path

# Ensure we're in the backend directory for imports
backend_dir = Path(__file__).resolve().parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine


def get_alembic_config():
    """Create an Alembic config pointing to our alembic.ini."""
    config = Config(str(backend_dir / "alembic.ini"))
    config.set_main_option("script_location", str(backend_dir / "migrations"))
    return config


def get_current_revision():
    """Get the current database revision."""
    db_path = str(backend_dir / "treff.db")
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        return context.get_current_revision()


def cmd_upgrade(args):
    """Upgrade database to a revision (default: head)."""
    revision = args[0] if args else "head"
    config = get_alembic_config()
    print(f"Upgrading database to: {revision}")
    command.upgrade(config, revision)
    print(f"Database upgraded to: {get_current_revision()}")


def cmd_downgrade(args):
    """Downgrade database by one step or to a specific revision."""
    if not args:
        print("Usage: python migrate.py downgrade <revision|-1>")
        sys.exit(1)
    revision = args[0]
    config = get_alembic_config()
    print(f"Downgrading database to: {revision}")
    command.downgrade(config, revision)
    print(f"Database now at: {get_current_revision()}")


def cmd_current(args):
    """Show the current database revision."""
    config = get_alembic_config()
    command.current(config, verbose=True)


def cmd_history(args):
    """Show migration history."""
    config = get_alembic_config()
    command.history(config, verbose=True)


def cmd_heads(args):
    """Show the head revisions."""
    config = get_alembic_config()
    command.heads(config, verbose=True)


def cmd_generate(args):
    """Generate a new migration script (autogenerate from model diff)."""
    if not args:
        print("Usage: python migrate.py generate <message>")
        sys.exit(1)
    message = " ".join(args)
    config = get_alembic_config()
    print(f"Generating migration: {message}")
    command.revision(config, message=message, autogenerate=True)
    print("Migration script generated. Review it before running 'upgrade'.")


def cmd_stamp(args):
    """Stamp the database as being at a specific revision without running migrations."""
    if not args:
        print("Usage: python migrate.py stamp <revision>")
        sys.exit(1)
    revision = args[0]
    config = get_alembic_config()
    print(f"Stamping database at revision: {revision}")
    command.stamp(config, revision)
    print(f"Database stamped at: {get_current_revision()}")


def cmd_check(args):
    """Check if there are pending migrations."""
    config = get_alembic_config()
    script = ScriptDirectory.from_config(config)
    head = script.get_current_head()
    current = get_current_revision()

    if current == head:
        print(f"Database is up to date at revision: {current}")
        return True
    else:
        print(f"Pending migrations detected!")
        print(f"  Current: {current}")
        print(f"  Head:    {head}")
        # List pending revisions
        revs = list(script.walk_revisions(head, current))
        print(f"  Pending: {len(revs)} migration(s)")
        for rev in reversed(revs):
            print(f"    - {rev.revision}: {rev.doc}")
        return False


COMMANDS = {
    "upgrade": cmd_upgrade,
    "downgrade": cmd_downgrade,
    "current": cmd_current,
    "history": cmd_history,
    "heads": cmd_heads,
    "generate": cmd_generate,
    "stamp": cmd_stamp,
    "check": cmd_check,
}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    if cmd not in COMMANDS:
        print(f"Unknown command: {cmd}")
        print(f"Available commands: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    COMMANDS[cmd](sys.argv[2:])


if __name__ == "__main__":
    main()
