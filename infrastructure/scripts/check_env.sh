#!/bin/bash
# ============================================================
# PEVN — Environment Configuration Validator
# ============================================================
# Run this script before starting the application to verify
# that all required environment variables are set.
#
# Usage:
#   chmod +x infrastructure/scripts/check_env.sh
#   ./infrastructure/scripts/check_env.sh
#
# Exit codes:
#   0 — All required variables are set
#   1 — One or more required variables are missing
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "=============================================="
echo "  PEVN Environment Configuration Check"
echo "=============================================="
echo ""

ERRORS=0

check_var() {
    local var_name="$1"
    local description="$2"
    local value="${!var_name}"

    if [ -z "$value" ]; then
        echo -e "${RED}✗ MISSING${NC}  ${var_name}"
        echo "           ${description}"
        ERRORS=$((ERRORS + 1))
    elif [[ "$value" == *"REPLACE_ME"* ]]; then
        echo -e "${YELLOW}⚠ PLACEHOLDER${NC}  ${var_name}"
        echo "              ${description}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ SET${NC}  ${var_name}"
    fi
}

echo "--- Required Variables ---"
check_var "ENVIRONMENT"            "Runtime environment (development|staging|production)"
check_var "SECRET_KEY"             "Cryptographic secret key (min 128 chars)"
check_var "DATABASE_URL"           "PostgreSQL connection string"
check_var "POSTGRES_DB"            "PostgreSQL database name"
check_var "POSTGRES_USER"          "PostgreSQL admin user"
check_var "POSTGRES_PASSWORD"      "PostgreSQL admin password"
check_var "POSTGRES_APP_USER"      "PostgreSQL application user (least privilege)"
check_var "POSTGRES_APP_PASSWORD"  "PostgreSQL application user password"
check_var "REDIS_URL"              "Redis connection URL"
check_var "CORS_ORIGINS"           "Allowed CORS origins (comma-separated)"
check_var "ALLOWED_HOSTS"          "Allowed Host header values (comma-separated)"

echo ""
echo "--- Security Checks ---"

# Check SECRET_KEY length
if [ -n "$SECRET_KEY" ] && [ ${#SECRET_KEY} -lt 64 ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}  SECRET_KEY is shorter than 64 characters"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ OK${NC}  SECRET_KEY length"
fi

# Check CORS wildcard in production
if [ "$ENVIRONMENT" = "production" ] && [[ "$CORS_ORIGINS" == *"*"* ]]; then
    echo -e "${RED}✗ CRITICAL${NC}  CORS_ORIGINS contains wildcard (*) in production!"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ OK${NC}  CORS configuration"
fi

# Check DEBUG in production
if [ "$ENVIRONMENT" = "production" ] && [ "$DEBUG" = "true" ]; then
    echo -e "${RED}✗ CRITICAL${NC}  DEBUG is 'true' in production!"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✓ OK${NC}  DEBUG configuration"
fi

echo ""
echo "=============================================="

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed. Environment is configured correctly.${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}✗ ${ERRORS} check(s) failed. Fix the above issues before starting.${NC}"
    echo ""
    exit 1
fi
