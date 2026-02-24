import sqlite3
import os

# Points directly to your existing data folder
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'thunderz_data.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── IPAM / Network Mapper ─────────────────────────────────────────────────
    # Multiple services can share an IP (e.g. Docker containers) so the
    # unique constraint is on (ip_address, port) rather than ip_address alone.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_allocations (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address  TEXT NOT NULL,
            hostname    TEXT,
            vlan        TEXT,
            device_type TEXT,
            port        TEXT DEFAULT '',
            notes       TEXT,
            UNIQUE(ip_address, port)
        )
    ''')

    # Safe migration: if the old table has UNIQUE on ip_address alone,
    # recreate it with the composite UNIQUE(ip_address, port) instead.
    try:
        # Check for the old schema — try inserting a duplicate IP with a
        # different port.  If it fails with UNIQUE constraint, migrate.
        cursor.execute(
            "INSERT INTO ip_allocations (ip_address, hostname, port) "
            "VALUES ('__migration_test__', '__test__', '99999')")
        cursor.execute(
            "INSERT INTO ip_allocations (ip_address, hostname, port) "
            "VALUES ('__migration_test__', '__test2__', '99998')")
        # If both inserts succeeded, the composite unique is already in place
        cursor.execute(
            "DELETE FROM ip_allocations WHERE ip_address='__migration_test__'")
        conn.commit()
    except Exception:
        # The second insert failed — old UNIQUE(ip_address) is active.  Migrate.
        conn.rollback()
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS _ip_alloc_new (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address  TEXT NOT NULL,
                    hostname    TEXT,
                    vlan        TEXT,
                    device_type TEXT,
                    port        TEXT DEFAULT '',
                    notes       TEXT,
                    UNIQUE(ip_address, port)
                )
            ''')
            cursor.execute(
                "INSERT OR IGNORE INTO _ip_alloc_new "
                "(id, ip_address, hostname, vlan, device_type, port, notes) "
                "SELECT id, ip_address, hostname, vlan, device_type, port, notes "
                "FROM ip_allocations")
            cursor.execute("DROP TABLE ip_allocations")
            cursor.execute("ALTER TABLE _ip_alloc_new RENAME TO ip_allocations")
            conn.commit()
        except Exception:
            pass

    # Safe migration for DBs created before port column existed
    try:
        cursor.execute("ALTER TABLE ip_allocations ADD COLUMN port TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # ── Docker Compose stacks ─────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS docker_stacks (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            compose    TEXT,
            status     TEXT DEFAULT 'Not Deployed',
            notes      TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Script Vault ──────────────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scripts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            content    TEXT,
            category   TEXT DEFAULT 'General',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Settings / UniFi credentials ─────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # ── Lab Notes / Runbook ───────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            content    TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Credentials Vault ─────────────────────────────────────────────────────
    # vault_pin stores a bcrypt/sha256 hash of the user's chosen PIN.
    # credentials stores label/username/password/notes — password is stored
    # as plaintext in SQLite (local-only tool); the PIN just gates UI access.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credentials (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            label      TEXT NOT NULL,
            username   TEXT DEFAULT '',
            password   TEXT DEFAULT '',
            url        TEXT DEFAULT '',
            notes      TEXT DEFAULT '',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Service Health Log ──────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_health_log (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ip_address TEXT NOT NULL,
            hostname   TEXT,
            port       TEXT DEFAULT '',
            online     INTEGER NOT NULL DEFAULT 0,
            latency_ms INTEGER DEFAULT 0,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_health_log_ip_time
        ON service_health_log (ip_address, checked_at DESC)
    ''')

    # ── Phase 2 migrations ────────────────────────────────────────────────────
    # run_on: which IPAM host to SSH into when running a script
    try:
        cursor.execute("ALTER TABLE scripts ADD COLUMN run_on TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # deploy_target: which IPAM host to deploy a Docker stack to
    try:
        cursor.execute(
            "ALTER TABLE docker_stacks ADD COLUMN deploy_target TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass  # Column already exists

    # ── Script Execution Log ──────────────────────────────────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS script_execution_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            script_id    INTEGER,
            script_title TEXT,
            hostname     TEXT,
            exit_code    INTEGER,
            output       TEXT,
            started_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def execute_query(query, params=()):
    """Execute a query and return results (SELECT) or lastrowid (writes).
    Returns None on error."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if query.strip().upper().startswith("SELECT"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid
    except Exception as e:
        print(f"Database Error: {e}")
        result = None
    finally:
        conn.close()
    return result
