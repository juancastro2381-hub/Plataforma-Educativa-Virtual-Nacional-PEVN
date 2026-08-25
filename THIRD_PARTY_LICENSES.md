# PEVN — Third-Party Dependency License Inventory

**Plataforma Educativa Virtual Nacional**  
**Last Updated:** 2026-08-21

This document inventories all third-party dependencies and their licenses.
The PEVN platform is licensed under Apache-2.0.

> [!IMPORTANT]
> This inventory must be updated whenever a new dependency is added.
> Each dependency's original license must be preserved and respected.
> Apache-2.0 is compatible with the licenses listed below.

---

## Backend Dependencies (Python)

### Core Dependencies (`requirements/base.txt`)

| Package | Version | License | License URL |
|---------|---------|---------|------------|
| fastapi | ~0.115 | MIT | https://github.com/fastapi/fastapi/blob/master/LICENSE |
| uvicorn | ~0.34 | BSD-3-Clause | https://github.com/encode/uvicorn/blob/master/LICENSE.md |
| pydantic | ~2.10 | MIT | https://github.com/pydantic/pydantic/blob/main/LICENSE |
| pydantic-settings | ~2.7 | MIT | https://github.com/pydantic/pydantic-settings/blob/main/LICENSE |
| sqlalchemy | ~2.0 | MIT | https://github.com/sqlalchemy/sqlalchemy/blob/main/LICENSE |
| asyncpg | ~0.30 | Apache-2.0 | https://github.com/MagicStack/asyncpg/blob/master/LICENSE |
| alembic | ~1.14 | MIT | https://github.com/sqlalchemy/alembic/blob/main/LICENSE |
| redis | ~5.2 | MIT | https://github.com/redis/redis-py/blob/master/LICENSE |
| httpx | ~0.28 | BSD-3-Clause | https://github.com/encode/httpx/blob/master/LICENSE.md |
| structlog | ~24.4 | Apache-2.0 OR MIT | https://github.com/hynek/structlog/blob/main/LICENSE |
| slowapi | ~0.1 | MIT | https://github.com/laurents/slowapi/blob/master/LICENSE |
| python-multipart | ~0.0 | Apache-2.0 | https://github.com/Kludex/python-multipart/blob/master/LICENSE.txt |
| argon2-cffi | ~25.1 | MIT OR Apache-2.0 | https://github.com/hynek/argon2-cffi/blob/main/LICENSE |
| pyjwt | ~2.10 | Apache-2.0 | https://github.com/jpadilla/pyjwt/blob/master/LICENSE |


### Development Dependencies (`requirements/development.txt`)

| Package | Version | License | Notes |
|---------|---------|---------|-------|
| pytest | ~8.3 | MIT | Test framework |
| pytest-asyncio | ~0.24 | Apache-2.0 | Async test support |
| aiosqlite | ~0.22 | MIT | In-memory async SQLite driver for tests |
| pytest-cov | ~6.0 | MIT | Coverage |
| httpx | ~0.28 | BSD-3-Clause | Test HTTP client |
| anyio | ~4.7 | MIT | Async test backend |
| black | ~24.12 | MIT | Code formatter |
| ruff | ~0.9 | MIT | Linter |
| isort | ~5.13 | MIT | Import sorter |
| mypy | ~1.14 | MIT | Type checker |
| pip-audit | ~2.8 | Apache-2.0 | Dependency security scanner |

### Production Dependencies (`requirements/production.txt`)

| Package | Version | License | Notes |
|---------|---------|---------|-------|
| gunicorn | ~23.0 | MIT | WSGI server for production |

---

## Infrastructure Dependencies (Docker Images)

| Image | Version | License |
|-------|---------|---------|
| python | 3.12.8-slim | Python PSF License |
| postgres | 16.4-alpine | PostgreSQL License |
| redis | 7.4-alpine | BSD-3-Clause |
| node | 20.18-alpine | MIT |

---

## Frontend Dependencies (Node.js)

### Production Dependencies (`package.json` - `dependencies`)

| Package | Version | License | License URL |
|---------|---------|---------|------------|
| react | ^18.3 | MIT | https://github.com/facebook/react/blob/main/LICENSE |
| react-dom | ^18.3 | MIT | https://github.com/facebook/react/blob/main/LICENSE |
| react-router-dom | ^6.28 | MIT | https://github.com/remix-run/react-router/blob/main/LICENSE.md |
| axios | ^1.7 | MIT | https://github.com/axios/axios/blob/v1.x/LICENSE |

### Development Dependencies (`package.json` - `devDependencies`)

| Package | Version | License | Notes |
|---------|---------|---------|-------|
| vite | ^6.0 | MIT | Build tool |
| @vitejs/plugin-react | ^4.3 | MIT | React Vite plugin |
| vite-plugin-pwa | ^0.21 | MIT | PWA support |
| typescript | ^5.7 | Apache-2.0 | Type checker |
| tailwindcss | ^3.4 | MIT | CSS framework |
| autoprefixer | ^10.4 | MIT | CSS post-processing |
| postcss | ^8.5 | MIT | CSS pipeline |
| eslint | ^9.17 | MIT | Linter |
| @eslint/js | ^9.17 | MIT | ESLint core rules |
| typescript-eslint | ^8.20 | MIT | TypeScript ESLint |
| eslint-plugin-react | ^7.37 | MIT | React ESLint rules |
| eslint-plugin-react-hooks | ^5.1 | MIT | React hooks rules |
| eslint-plugin-react-refresh | ^0.4 | MIT | React Refresh rules |
| prettier | ^3.4 | MIT | Code formatter |
| vitest | ^2.1 | MIT | Test framework |
| @vitest/coverage-v8 | ^2.1 | MIT | Coverage provider |
| @testing-library/react | ^16.1 | MIT | React test utilities |
| @testing-library/jest-dom | ^6.6 | MIT | DOM matchers |
| @testing-library/user-event | ^14.5 | MIT | User event simulation |
| jsdom | ^25.0 | MIT | DOM implementation for tests |
| globals | ^15.14 | MIT | Global variable definitions |

---

## Third-Party Services

| Service | License | Notes |
|---------|---------|-------|
| Inter (Google Fonts) | SIL Open Font License 1.1 | Typography |
| BigBlueButton (Phase 3+) | LGPL-3.0 | Virtual classroom (not yet integrated) |

---

## License Compatibility Summary

All listed dependencies use licenses that are compatible with Apache-2.0:

| License | Compatible with Apache-2.0? | Notes |
|---------|---------------------------|-------|
| MIT | ✅ Yes | Permissive, compatible |
| Apache-2.0 | ✅ Yes | Same license |
| BSD-3-Clause | ✅ Yes | Permissive, compatible |
| PostgreSQL License | ✅ Yes | Permissive, similar to BSD |
| Python PSF License | ✅ Yes | Permissive, compatible |
| SIL OFL 1.1 | ✅ Yes (font use only) | Font-specific license |
| LGPL-3.0 | ⚠️ Yes (dynamic linking) | BigBlueButton — Phase 3, review required |

---

## Maintenance Notes

When adding a new dependency:

1. Add it to the appropriate requirements file
2. Add an entry to this inventory
3. Verify license compatibility with Apache-2.0
4. If the license is not MIT/Apache/BSD, escalate for legal review before adding

This file must be reviewed and updated at the start of each development phase.
