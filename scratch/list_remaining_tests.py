import glob

all_files = set(glob.glob('backend/tests/test_*.py'))
already_run = {
    'backend/tests\\test_tokens.py',
    'backend/tests\\test_password_hasher.py',
    'backend/tests\\test_config.py',
    'backend/tests\\test_authorization.py',
    'backend/tests\\test_health.py',
    'backend/tests\\test_ready.py',
    'backend/tests\\test_academic_models.py',
    'backend/tests\\test_auth_service.py',
    'backend/tests\\test_domain_services.py',
    'backend/tests\\test_enrollments_and_assignments.py',
    'backend/tests\\test_groups_and_actors_models.py',
    'backend/tests\\test_national_catalog_active_campus_accounting.py',
    'backend/tests\\test_national_catalog_completion_audit.py',
    'backend/tests\\test_promotion_authorization_gate.py',
    'backend/tests\\test_promotion_graduation_semantics.py',
    'backend/tests\\test_siee_and_evaluations_domain_services.py',
    'backend/tests\\test_virtual_classroom_models.py',
    'backend/tests\\test_virtual_classroom_services.py',
    'backend/tests\\test_auth_endpoints.py',
    'backend/tests\\test_auth_security_hardening.py',
}

remaining = sorted(all_files - already_run)
print(f'Remaining test files: {len(remaining)}')
for r in remaining:
    print(' ', r)
