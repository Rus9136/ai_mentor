# Migration 012: RLS Policies - Implementation Notes

## Critical Findings and Fixes

### Issue 1: SUPERUSER Role Bypasses RLS
**Problem:** The `ai_mentor_user` role created by Docker Compose has SUPERUSER privilege, which bypasses ALL RLS policies regardless of `FORCE ROW LEVEL SECURITY` setting.

**Solution:**
- Created `ai_mentor_app` role without SUPERUSER privilege for application runtime
- Use `ai_mentor_user` only for migrations and database administration
- Updated `.env` to use `ai_mentor_app` for application connections

**Database Setup:**
```sql
-- Created in production database
CREATE ROLE ai_mentor_app WITH LOGIN PASSWORD 'ai_mentor_pass';
GRANT CONNECT ON DATABASE ai_mentor_db TO ai_mentor_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ai_mentor_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ai_mentor_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ai_mentor_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ai_mentor_app;
```

### Issue 2: NULL Session Variables Cause Cast Errors
**Problem:** When session variables are not set, `current_setting()` returns empty string `''`.
Casting empty string to boolean or integer causes errors:
```sql
-- This fails:
current_setting('app.is_super_admin', true)::boolean = true
-- Error: invalid input syntax for type boolean: ""

current_setting('app.current_tenant_id', true)::int
-- Error: invalid input syntax for type integer: ""
```

**Solution:** Use COALESCE to handle NULL/empty values:
```sql
-- For boolean check:
COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'

-- For integer check:
COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
```

This ensures:
- Empty string → 'false' (for boolean) or '0' (for integer)
- No cast errors
- Secure default: when no tenant is set, school_id = 0 matches no rows

### Issue 3: FORCE ROW LEVEL SECURITY Not Applied
**Problem:** Even with `ENABLE ROW LEVEL SECURITY`, table owners bypass RLS policies by default.

**Solution:** Add `FORCE ROW LEVEL SECURITY` for all tables:
```sql
ALTER TABLE tablename ENABLE ROW LEVEL SECURITY;
ALTER TABLE tablename FORCE ROW LEVEL SECURITY;  -- Critical!
```

## Migration File Updates

The migration file `401bffeccd70_enable_rls_policies.py` has been updated with:

1. **Comprehensive documentation** in STEP 1 explaining:
   - SUPERUSER bypass issue
   - Session variable NULL handling
   - Proper role usage (ai_mentor_user vs ai_mentor_app)

2. **FORCE ROW LEVEL SECURITY** added to all table creation sections

3. **COALESCE pattern** applied to all policy USING and WITH CHECK clauses

## Testing Results

After fixes applied:
✅ No tenant context: 0 rows visible (secure default)
✅ school_id=3: 3 students visible (correct isolation)
✅ school_id=1: 0 students visible (no data for that tenant)
✅ is_super_admin=true: All rows visible (bypass works)
✅ Global content (school_id=NULL): Visible to all tenants
✅ NO DATA OVERLAP between tenants

## Files Modified

1. `backend/alembic/versions/401bffeccd70_enable_rls_policies.py` - Migration with fixes
2. `backend/fix_rls_policies.sql` - SQL script to fix existing database
3. `backend/.env` - Updated to use ai_mentor_app role
4. `backend/app/core/tenancy.py` - Session variable management
5. `backend/app/middleware/tenancy.py` - Automatic tenant context setup
6. `backend/app/main.py` - TenancyMiddleware integration

## Production Deployment Checklist

Before deploying to production:

- [ ] Create `ai_mentor_app` non-superuser role
- [ ] Grant necessary permissions to `ai_mentor_app`
- [ ] Update connection string to use `ai_mentor_app`
- [ ] Apply migration with FORCE RLS and COALESCE fixes
- [ ] Test RLS isolation with non-superuser role
- [ ] Verify SUPER_ADMIN bypass works via session variable
- [ ] Test global content visibility across tenants
- [ ] Performance test: Check if policy EXISTS clauses need indexes

## Performance Considerations

1. **Denormalized school_id** in progress tables (already done in migration 008) helps RLS filtering
2. **Indexes** on school_id columns are critical for RLS performance
3. **EXISTS clauses** in policies for inherited tables (chapters, questions, etc.) may need monitoring
4. Consider **materialized views** for complex joins if performance issues arise

## Next Steps

- Update `init_db.sql` to create `ai_mentor_app` role automatically
- Add integration tests for RLS with different user roles
- Document role switching for migrations vs runtime
- Monitor query performance with RLS enabled in production
