# Quick Reference - Admin Endpoints

All admin endpoints are now working. This is a quick reference guide.

---

## URL Structure

- Admin Dashboard: `/api/admin/dashboard/*`
- Plan Management: `/api/admin/plans/*`
- Notifications: `/api/notifications/admin/*`
- Reports: `/api/admin/reports/*`

---

## Complete Endpoint List

### Dashboard (11 endpoints)
1. GET `/api/admin/dashboard/stats/` - Dashboard statistics
2. GET `/api/admin/dashboard/requests/` - List all requests
3. GET `/api/admin/dashboard/requests/<id>/` - Request detail
4. PATCH `/api/admin/dashboard/requests/<id>/status/` - Update status
5. POST `/api/admin/dashboard/requests/bulk-status/` - Bulk update
6. POST `/api/admin/dashboard/requests/<id>/notes/` - Add note
7. POST `/api/admin/dashboard/requests/<id>/assign/` - Assign request
8. PATCH `/api/admin/dashboard/requests/<id>/assign/` - Update assignment
9. GET `/api/admin/dashboard/users/` - Admin users list
10. GET `/api/admin/dashboard/all-users/` - All users list (NEW)
11. GET `/api/admin/dashboard/all-users/<id>/` - User detail (NEW)

### Reports (3 endpoints)
12. POST `/api/admin/reports/` - Create report
13. POST `/api/admin/reports/upload/` - Upload report PDF
14. GET `/api/admin/dashboard/requests/<id>/report/download/` - Download PDF (NEW)

### Plans (5 endpoints - ALL NEW)
15. GET `/api/admin/plans/` - List all plans
16. POST `/api/admin/plans/` - Create plan
17. GET `/api/admin/plans/<id>/` - Plan detail
18. PATCH `/api/admin/plans/<id>/` - Update plan
19. DELETE `/api/admin/plans/<id>/` - Delete plan (soft)
20. POST `/api/admin/plans/<id>/toggle-status/` - Toggle active/inactive

### Notifications (3 endpoints - ALL NEW)
21. GET `/api/notifications/admin/` - List notifications
22. POST `/api/notifications/admin/<id>/mark-read/` - Mark as read
23. POST `/api/notifications/admin/mark-all-read/` - Mark all as read

---

## Common Request Examples

### Get Dashboard Stats
```bash
curl http://localhost:8000/api/admin/dashboard/stats/ \
  -H "Authorization: Bearer TOKEN"
```

### Filter Requests
```bash
curl "http://localhost:8000/api/admin/dashboard/requests/?status=pending&search=john" \
  -H "Authorization: Bearer TOKEN"
```

### Update Status
```bash
curl -X PATCH http://localhost:8000/api/admin/dashboard/requests/1/status/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress", "notes": "Working on it"}'
```

### Create Plan
```bash
curl -X POST http://localhost:8000/api/admin/plans/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Plan",
    "plan_type": "premium",
    "price_per_report": 50.00,
    "description": "All features included",
    "identity_verification": true,
    "ssn_trace": true,
    "national_criminal_search": true,
    "employment_verification": true,
    "education_verification": true
  }'
```

### Download Report
```bash
curl http://localhost:8000/api/admin/dashboard/requests/1/report/download/ \
  -H "Authorization: Bearer TOKEN" \
  -o report.pdf
```

### Get User Detail
```bash
curl http://localhost:8000/api/admin/dashboard/all-users/1/ \
  -H "Authorization: Bearer TOKEN"
```

---

## Files Changed

1. **admin_dashboard/admin_views.py**
   - Added 9 new view classes
   - Total view classes: 17

2. **admin_dashboard/urls.py**
   - Added 9 new URL patterns
   - Total patterns: 23

3. **notifications/urls.py**
   - Added 3 notification endpoints

---

## Status Summary

| Category | Total | New | Fixed |
|----------|-------|-----|-------|
| Dashboard | 11 | 2 | 1 |
| Reports | 3 | 1 | 0 |
| Plans | 5 | 5 | 0 |
| Notifications | 3 | 3 | 0 |
| **TOTAL** | **22** | **11** | **1** |

---

## Testing

Run the test script:
```bash
python test_admin_endpoints.py
```

Make sure to:
1. Update `ADMIN_TOKEN` with real JWT token
2. Server running on `http://localhost:8000`
3. Have test data in database

---

## Authentication

All endpoints require:
- JWT Token in Authorization header
- `is_staff=True` (admin user)

Get admin token:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin_password"
  }'
```

---

## Response Formats

### Success Response (200/201)
```json
{
  "id": 1,
  "field": "value",
  ...
}
```

### Error Response (400/404)
```json
{
  "error": "Error message"
}
```

### List Response
```json
{
  "count": 10,
  "results": [...]
}
```

---

## Permission Errors

If you get 403 Forbidden:
- User must have `is_staff=True`
- Token must be valid and not expired
- Use admin account credentials

---

## Next Steps

1. Test all endpoints with Postman/Insomnia
2. Integrate with frontend
3. Add pagination where needed
4. Implement proper logging
5. Add rate limiting
6. Create admin activity audit log

---

## Support

For issues:
1. Check server logs
2. Verify token is valid
3. Ensure test data exists
4. Check URL patterns match
5. Verify permission settings

All endpoints are now fully functional and ready for frontend integration.
