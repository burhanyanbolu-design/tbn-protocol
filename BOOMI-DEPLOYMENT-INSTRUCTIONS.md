# Boomi Integration — Deployment Instructions

## Status: Code Ready, Needs Deployment

The Boomi integration code is complete and tested locally, but it needs to be deployed to the production server.

---

## What Needs to Be Deployed

### Files Modified:
1. **`api/routes.py`** — Added Boomi endpoints
   - `GET /api/boomi/health`
   - `POST /api/boomi/process`
   - Three process handlers

2. **`api/access_control.py`** — Already has API key system (no changes needed)

### What's New:
- Lines 1025-1229 in `api/routes.py` contain all Boomi integration code

---

## Deployment Steps

### Option 1: Git Push (Recommended)

1. **Stage the changes:**
   ```bash
   git add api/routes.py
   ```

2. **Commit:**
   ```bash
   git commit -m "Add Boomi integration endpoints"
   ```

3. **Push to main:**
   ```bash
   git push origin main
   ```

4. **On the server, pull and restart:**
   ```bash
   cd /opt/tbn-protocol
   git pull origin main
   sudo systemctl restart tbn
   ```

### Option 2: Manual Copy

1. **Copy the file to the server:**
   ```bash
   scp -i aws-lightsail.pem api/routes.py ubuntu@3.11.229.68:/opt/tbn-protocol/api/
   ```

2. **SSH into the server:**
   ```bash
   ssh -i aws-lightsail.pem ubuntu@3.11.229.68
   ```

3. **Restart the service:**
   ```bash
   sudo systemctl restart tbn
   ```

### Option 3: Direct Edit on Server

1. **SSH into the server:**
   ```bash
   ssh -i aws-lightsail.pem ubuntu@3.11.229.68
   ```

2. **Edit the file:**
   ```bash
   nano /opt/tbn-protocol/api/routes.py
   ```

3. **Add the Boomi code** (lines 1025-1229 from local file)

4. **Save and exit** (Ctrl+X, then Y, then Enter)

5. **Restart:**
   ```bash
   sudo systemctl restart tbn
   ```

---

## Verification After Deployment

### Test 1: Health Check
```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "TBN Protocol",
  "version": "1.0.0",
  "boomi_integration": "enabled",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

### Test 2: Check Logs
```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
sudo journalctl -u tbn -f
```

Look for any errors related to the Boomi endpoints.

### Test 3: Full Test
```bash
curl -X POST https://tbn.hardinai.co.uk/api/boomi/process \
  -H "Authorization: Bearer tbn_live_test" \
  -H "Content-Type: application/json" \
  -d '{"process_type": "bot_registration", "data": {"bot_name": "Test", "bot_type": "SEARCH", "company": "Test", "email": "test@test.com", "description": "Test"}, "metadata": {"boomi_process_id": "test-001", "timestamp": "2026-05-12T10:30:00Z", "source": "boomi"}}'
```

---

## Server Information

- **IP:** 3.11.229.68
- **User:** ubuntu
- **SSH Key:** aws-lightsail.pem
- **Project Root:** /opt/tbn-protocol
- **Service:** tbn
- **Restart Command:** `sudo systemctl restart tbn`

---

## Rollback (If Something Goes Wrong)

If the deployment breaks something:

```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
cd /opt/tbn-protocol
git revert HEAD
sudo systemctl restart tbn
```

---

## Next Steps

1. **Deploy the code** using one of the three options above
2. **Verify** using the test commands
3. **Get API key** from https://tbn.hardinai.co.uk/api/access/request
4. **Configure Boomi** with the endpoint
5. **Test** the integration
6. **Deploy** your Boomi process

---

## Support

Email: info@hardinai.co.uk

