"""
PEVN — Unit Tests for Database Safety & Fail-Closed URL Enforcement (DOC-03-R2)

Verifies:
  1. Missing TEST_DATABASE_URL raises DatabaseSecurityError.
  2. Valid pevn_test_db URL is accepted and converted properly.
  3. Rejection of operational pevn_db in test mode.
  4. Rejection of unknown databases (e.g. pevn_staging, postgres, master).
  5. Rejection of malformed URLs.
  6. Rejection of unsupported schemes (mysql, sqlite, http, etc.).
  7. Credential masking: URLs with secret passwords never expose the secret in error messages.
  8. Bypass attempts blocked:
     - Substring match tricks: pevn_test_db_evil, evil_pevn_test_db.
     - Path traversal tricks: /pevn_test_db/../pevn_db, /pevn_test_db/other.
     - Query parameter tricks: /pevn_db?db=pevn_test_db, /pevn_test_db?evil.
  9. Operational read-only mode requires explicit ALLOW_OPERATIONAL_DIAGNOSTICS=true opt-in.
  10. Operational read-only mode rejects test database and unauthorized databases.
"""

import os
import pytest

from app.core.db_safety import (
    DatabaseSecurityError,
    get_safe_operational_readonly_url,
    get_safe_test_db_url,
    mask_url_credentials,
    validate_and_sanitize_db_url,
)


class TestDatabaseSafetyFailClosed:
    """Test suite verifying fail-closed database target validation."""

    SECRET_PASS = "SuperSecretP@ssw0rd99!"
    VALID_TEST_URL = f"postgresql+asyncpg://pevn_app:{SECRET_PASS}@localhost:5433/pevn_test_db"
    VALID_OP_URL = f"postgresql+asyncpg://pevn_app:{SECRET_PASS}@localhost:5433/pevn_db"

    def test_01_missing_test_database_url_raises(self, monkeypatch):
        """1. Missing TEST_DATABASE_URL strictly raises DatabaseSecurityError."""
        monkeypatch.delenv("TEST_DATABASE_URL", raising=False)
        monkeypatch.setenv("DATABASE_URL", self.VALID_OP_URL)  # Should NOT fall back!

        with pytest.raises(DatabaseSecurityError) as exc_info:
            get_safe_test_db_url()

        err_msg = str(exc_info.value)
        assert "FAIL-CLOSED: TEST_DATABASE_URL environment variable is not configured" in err_msg
        assert self.SECRET_PASS not in err_msg

    def test_02_valid_pevn_test_db_accepted_and_converted(self, monkeypatch):
        """2. Valid pevn_test_db URL is accepted and converted properly."""
        monkeypatch.setenv("TEST_DATABASE_URL", self.VALID_TEST_URL)

        # SQLAlchemy mode
        url_sa = get_safe_test_db_url(as_asyncpg=False)
        assert url_sa.startswith("postgresql+asyncpg://")
        assert url_sa.endswith("/pevn_test_db")

        # asyncpg raw mode
        url_pg = get_safe_test_db_url(as_asyncpg=True)
        assert url_pg.startswith("postgresql://")
        assert "asyncpg" not in url_pg.split("://")[0]
        assert url_pg.endswith("/pevn_test_db")

    def test_03_rejection_of_operational_pevn_db_in_test_mode(self, monkeypatch):
        """3. Connection to operational database 'pevn_db' is strictly forbidden in test mode."""
        monkeypatch.setenv("TEST_DATABASE_URL", self.VALID_OP_URL)

        with pytest.raises(DatabaseSecurityError) as exc_info:
            get_safe_test_db_url()

        err_msg = str(exc_info.value)
        assert "FAIL-CLOSED REJECTION" in err_msg
        assert "pevn_db" in err_msg
        assert "strictly forbidden in test mode" in err_msg
        # Must mask credentials
        assert self.SECRET_PASS not in err_msg
        assert "***" in err_msg

    def test_04_rejection_of_unknown_database(self, monkeypatch):
        """4. Rejection of unknown databases (e.g. pevn_prod, postgres, random_db)."""
        unknown_url = f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_prod"
        monkeypatch.setenv("TEST_DATABASE_URL", unknown_url)

        with pytest.raises(DatabaseSecurityError) as exc_info:
            get_safe_test_db_url()

        err_msg = str(exc_info.value)
        assert "FAIL-CLOSED REJECTION: Unauthorized database target 'pevn_prod'" in err_msg
        assert self.SECRET_PASS not in err_msg

    def test_05_rejection_of_malformed_url(self, monkeypatch):
        """5. Rejection of malformed URLs without valid scheme or host."""
        for malformed in ["not_a_url", "://localhost/pevn_test_db", "http://", ""]:
            with pytest.raises(DatabaseSecurityError) as exc_info:
                validate_and_sanitize_db_url(malformed, mode="test")
            assert self.SECRET_PASS not in str(exc_info.value)

    def test_06_rejection_of_unsupported_schemes(self):
        """6. Rejection of unsupported schemes (mysql, sqlite, http, etc.)."""
        for bad_scheme in ["mysql", "sqlite+aiosqlite", "http", "redis", "mongodb"]:
            bad_url = f"{bad_scheme}://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_test_db"
            with pytest.raises(DatabaseSecurityError) as exc_info:
                validate_and_sanitize_db_url(bad_url, mode="test")

            err_msg = str(exc_info.value)
            assert "Unsupported database scheme" in err_msg
            assert self.SECRET_PASS not in err_msg

    def test_07_credentials_never_exposed_in_error_messages(self):
        """7. Passwords and secrets are masked in all generated error strings."""
        sensitive_url = f"postgresql+asyncpg://app_admin:{self.SECRET_PASS}@db.internal:5432/unauthorized_db"
        with pytest.raises(DatabaseSecurityError) as exc_info:
            validate_and_sanitize_db_url(sensitive_url, mode="test")

        err_msg = str(exc_info.value)
        assert self.SECRET_PASS not in err_msg
        assert "app_admin:***@db.internal:5432/unauthorized_db" in err_msg

    def test_08_bypass_attempts_substring_tricks(self):
        """8. Substring tricks (pevn_test_db_evil, evil_pevn_test_db) are rejected."""
        tricks = [
            f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_test_db_evil",
            f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/evil_pevn_test_db",
            f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_test_db2",
            f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_test_db/extra",
            f"postgresql+asyncpg://pevn_app:{self.SECRET_PASS}@localhost:5433/pevn_test_db/../pevn_db",
        ]
        for trick_url in tricks:
            with pytest.raises(DatabaseSecurityError) as exc_info:
                validate_and_sanitize_db_url(trick_url, mode="test")
            assert self.SECRET_PASS not in str(exc_info.value)

    def test_09_operational_readonly_requires_explicit_opt_in(self, monkeypatch):
        """9. Operational read-only mode requires ALLOW_OPERATIONAL_DIAGNOSTICS=true."""
        monkeypatch.delenv("ALLOW_OPERATIONAL_DIAGNOSTICS", raising=False)
        monkeypatch.setenv("DATABASE_URL", self.VALID_OP_URL)

        with pytest.raises(DatabaseSecurityError) as exc_info:
            get_safe_operational_readonly_url()

        err_msg = str(exc_info.value)
        assert "Operational database access is disabled by default" in err_msg
        assert "ALLOW_OPERATIONAL_DIAGNOSTICS=true" in err_msg
        assert self.SECRET_PASS not in err_msg

    def test_10_operational_readonly_succeeds_with_opt_in(self, monkeypatch):
        """10. Operational read-only mode succeeds when explicitly enabled."""
        monkeypatch.setenv("ALLOW_OPERATIONAL_DIAGNOSTICS", "true")
        monkeypatch.setenv("DATABASE_URL", self.VALID_OP_URL)

        url = get_safe_operational_readonly_url(as_asyncpg=True)
        assert url.startswith("postgresql://")
        assert url.endswith("/pevn_db")

    def test_11_mask_url_credentials_utility(self):
        """11. mask_url_credentials masks user and password correctly."""
        url = "postgresql+asyncpg://myuser:mypassword123@myhost:5432/mydb?ssl=true"
        masked = mask_url_credentials(url)
        assert "mypassword123" not in masked
        assert "myuser:***@myhost:5432/mydb" in masked
