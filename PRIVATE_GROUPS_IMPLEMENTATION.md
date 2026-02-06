# Private Groups & Access Control - Implementation Guide

## Backend Status ✅ COMPLETE

The backend is fully implemented with:
- **Models**: Group, GroupAccessRequest, GroupMarket
- **API Endpoints**: Full CRUD for groups and access management  
- **Admin Interface**: Complete group management dashboard
- **Migrations**: Applied and ready
- **Pushed to GitHub**: Ready for deployment

---

## Frontend Implementation Checklist

### Phase 1: Mobile Responsive Text Arrangement

**Files to modify**: `src/components/PrivateMarkets.tsx`, `src/components/MarketCard.tsx`

**Changes needed**:

1. **Grid Layout** (PrivateMarkets.tsx around L390-404)
   ```
   OLD: grid-cols-1 md:grid-cols-2 lg:grid-cols-3
   NEW: grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
   ```

2. **Category Text Wrapping**
   ```
   OLD: truncate max-w-[80px]
   NEW: max-w-full md:max-w-[120px] line-clamp-2 md:line-clamp-1
   ```

3. **Market Titles**
   ```
   OLD: line-clamp-3
   NEW: line-clamp-2 sm:line-clamp-2 md:line-clamp-3
   ```

4. **Spacing**
   ```
   OLD: gap-4
   NEW: gap-3 md:gap-4 lg:gap-6 px-2 sm:px-4 lg:px-8
   ```

### Phase 2: API Integration

**Base endpoint**: `https://kastia-backend.onrender.com/api/groups/`

**Key endpoints to integrate**:

| Action | Endpoint | Method | Body |
|--------|----------|--------|------|
| List groups | `/api/groups/` | GET | - |
| Discover public groups | `/api/groups/discover/` | GET | - |
| Get group details | `/api/groups/{id}/` | GET | - |
| Create group | `/api/groups/` | POST | `{name, description, category, privacy}` |
| Request access | `/api/groups/{id}/request-access/` | POST | `{message}` |
| Approve request | `/api/groups/{id}/approve-access/` | POST | `{request_id}` |
| Deny request | `/api/groups/{id}/deny-access/` | POST | `{request_id}` |
| List pending requests | `/api/groups/{id}/access-requests/` | GET | - |
| Add market to group | `/api/groups/{id}/add-market/` | POST | `{market_id}` |
| Remove market from group | `/api/groups/{id}/remove-market/` | POST | `{market_id}` |

### Phase 3: Toast Notifications

**Existing Toast System in App.tsx**:

```typescript
// Pattern: showToast(type, title, message)
showToast('info', 'Request Sent', 'Your access request has been sent to group admins')
showToast('success', 'Market Added', 'Market added to group successfully')
showToast('error', 'Already Requested', 'You have already requested access')
```

**Use cases**:

| Event | Code |
|-------|------|
| Access requested | `showToast('info', 'Request Sent', 'Your request has been sent')` |
| Access approved | `showToast('success', 'Access Granted', 'You can now join {groupName}')` |
| Access denied | `showToast('error', 'Request Denied', 'Your access request was denied')` |
| Market added | `showToast('success', 'Market Added', 'Market added to group')` |
| Market removed | `showToast('success', 'Market Removed', 'Market removed from group')` |
| Group created | `showToast('success', 'Group Created', 'New group created successfully')` |

### Phase 4: UI Component Updates

**Discover Tab** (PrivateMarkets.tsx L443-454):
- Update "Request Access" button to call: `POST /api/groups/{id}/request-access/`
- Show loading state while request submits
- Display success toast on completion
- Change button to "Request Pending" while pending

**Group Settings Modal** (PrivateMarkets.tsx L487-498):
- Add "Add to Group" dropdown/select
- Call: `POST /api/groups/{id}/add-market/` with selected markets
- Show success toast on completion
- Update market list after adding

**Access Requests Tab** (for group admins):
- Display pending requests with user info
- Show "Approve" and "Deny" buttons
- Call: `POST /api/groups/{id}/approve-access/` or `deny-access/`
- Update UI after action with success toast

**Members Tab**:
- Fetch and display group members from `GET /api/groups/{id}/`
- Show member roles (owner, admin, member)
- Poll or use Supabase real-time for member list updates

### Phase 5: Real-time Notifications  

**Option A: Polling** (Simpler)
```typescript
// In PrivateMarkets.tsx, check for access request status change
useEffect(() => {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/groups/${groupId}/`)
    // Check if user.isMember changed
  }, 5000); // Check every 5 seconds
  
  return () => clearInterval(interval);
}, [groupId])
```

**Option B: Supabase Real-time** (Better)
```typescript
// Use Supabase subscription on groups table
const subscription = supabase
  .from('api_groupaccessrequest')
  .on('*', payload => {
    if (payload.new.user_id === userId) {
      showToast('success', 'Access Granted', 'You can now join ' + payload.new.group.name)
    }
  })
  .subscribe()
```

---

## Testing Checklist

### Backend Testing ✅
- [x] Models created and migrated
- [x] Serializers working
- [x] ViewSets functional
- [x] Admin interface operational
- [x] Audit logging tracking actions
- [x] Pushed to GitHub

### Frontend Testing (TODO)
- [ ] Mobile responsive layout working
- [ ] "Request Access" button functional
- [ ] Toast notifications display correctly
- [ ] Access request shows in admin panel
- [ ] Approve/deny buttons work
- [ ] "Add to Group" Settings work
- [ ] Members list updates in real-time
- [ ] Pending requests display correctly
- [ ] Search/filter groups functional

---

## API Response Examples

### Get Group Details
```json
{
  "id": "group-123",
  "name": "DeFi Traders",
  "description": "Private group for DeFi trading strategies",
  "category": "Finance",
  "privacy": "INVITE",
  "owner": 5,
  "owner_info": {
    "id": 5,
    "username": "admin",
    "email": "admin@example.com"
  },
  "members_info": [
    {"id": 10, "username": "trader1", "email": "trader1@example.com"}
  ],
  "member_count": 2,
  "is_member": true,
  "is_owner": false,
  "is_admin": false,
  "markets": [
    {"id": 1, "market": 42, "market_title": "Bitcoin to $100k", "created_at": "2026-02-06T..."}
  ],
  "access_requests": [
    {"id": 1, "user": 20, "user_info": {...}, "status": "PENDING", "message": "I trade crypto", "requested_at": "2026-02-06T..."}
  ]
}
```

### Request Access Response
```json
{
  "id": 2,
  "group": "group-123",
  "user": 15,
  "user_info": {"id": 15, "username": "newtrader", "email": "new@example.com"},
  "status": "PENDING",
  "message": "Interested in learning DeFi",
  "requested_at": "2026-02-06T10:30:00Z",
  "responded_at": null,
  "responded_by": null
}
```

---

## Error Handling

Common error responses and how to handle:

| Status | Error Message | Action |
|--------|-----------|--------|
| 400 | "You are already a member" | Hide request button, show "Already member" |
| 400 | "You have already requested access" | Show "Request pending", disable button |
| 403 | "Only group owner/admins can..." | Hide admin buttons for non-admins |
| 404 | "Group not found" | Show error toast, redirect to discover |
| 403 | "You do not have permission" | Redirect to login |

---

## Deployment

**When ready to deploy frontend**:
1. Test all endpoints against `https://kastia-backend.onrender.com/api/groups/`
2. Ensure CORS headers are correct (backend already configured for xastia.vercel.app)
3. Deploy frontend changes
4. TestNotifications from admin console

On Render backend:
- Migrations already applied
- Admin interface live at `/admin/`
- API endpoints live at `/api/groups/`

---

## GitHub Commits

✅ Backend implementation pushed to https://github.com/Marshallmay28/Kastia-Backend
- Commit: `feat: implement private group management system with access requests`
- Includes all models, views, serializers, migrations

🔄 Frontend changes need to be pushed to https://github.com/Marshallmay28/Kastia

---

## Support

For questions on:
- **Backend API**: Check [backend/api/group_views.py](backend/api/group_views.py)
- **Models**: Check [backend/api/models.py](backend/api/models.py) (Group, GroupAccessRequest, GroupMarket)
- **Serializers**: Check [backend/api/group_serializers.py](backend/api/group_serializers.py)
- **Admin**: Check [backend/api/admin.py](backend/api/admin.py) (GroupAdmin, GroupAccessRequestAdmin)
