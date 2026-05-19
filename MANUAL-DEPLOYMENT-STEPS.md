# Manual Deployment Steps for Boomi Integration

## Status: Code Pushed to GitHub ✅

The Boomi integration code has been successfully committed and pushed to GitHub.

**Commit:** `b47318b` - "Add Boomi integration endpoints"

---

## What You Need to Do

### Step 1: SSH into the Server

Open your terminal and run:

```bash
ssh -i aws-lightsail.pem ubuntu@3.11.229.68
```

Or if you have the key in a different location:

```bash
ssh -i /path/to/aws-lightsail.pem ubuntu@3.11.229.68
```

---

### Step 2: Navigate to Project Directory

```bash
cd /opt/tbn-protocol
```

---

### Step 3: Pull Latest Code

```bash
git pull origin main
```

You should see:
```
Updating a61b391..b47318b
Fast-forward
 api/routes.py | 790 insertions(+)
 1 file changed, 790 insertions(+)
```

---

### Step 4: Restart the TBN Service

```bash
sudo systemctl restart tbn
```

Wait a few seconds for the service to restart.

---

### Step 5: Verify Deployment

Test the health check endpoint:

```bash
curl -X GET https://tbn.hardinai.co.uk/api/boomi/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "TBN Protocol",
  "version": "1.0.0",
  "boomi_integration": "enabled",
  "timestamp": "2026-05-12T10:30:00Z"
}
```

If you see this, the deployment is successful! ✅

---

### Step 6: Check Logs (Optional)

If something goes wrong, check the logs:

```bash
sudo journalctl -u tbn -f
```

Look for any errors related to Boomi.

---

## What Was Deployed

- **File:** `api/routes.py`
- **Changes:** Added 790 lines of code
- **New Endpoints:**
  - `GET /api/boomi/health` — Health check
  - `POST /api/boomi/process` — Process handler
- **Process Types:**
  - `bot_registration` — Register bots
  - `certification_check` — Check certifications
  - `governance_query` — Query bot status

---

## Next Steps After Deployment

1. **Get API Key**
   - Go to: https://tbn.hardinai.co.uk/api/access/request
   - Choose TRIAL or paid plan
   - Save your API key

2. **Configure Boomi**
   - Add HTTP connector
   - URL: `https://tbn.hardinai.co.uk/api/boomi/process`
   - Header: `Authorization: Bearer tbn_live_YOUR_KEY`

3. **Test**
   - Test health check
   - Test bot registration

4. **Deploy Boomi Process**
   - Activate your process

---

## Troubleshooting

### Error: "Permission denied (publickey)"
- Check your SSH key path
- Make sure the key has correct permissions: `chmod 600 aws-lightsail.pem`

### Error: "Connection refused"
- Check the server IP: `3.11.229.68`
- Check your internet connection

### Error: "git pull" fails
- Check you're in the right directory: `/opt/tbn-protocol`
- Check your git credentials

### Error: "systemctl restart tbn" fails
- You might need to use `sudo`
- Check the service name: `sudo systemctl list-units --type=service | grep tbn`

---

## Server Information

- **IP:** 3.11.229.68
- **User:** ubuntu
- **SSH Key:** aws-lightsail.pem
- **Project Root:** /opt/tbn-protocol
- **Service Name:** tbn
- **Service Restart:** `sudo systemctl restart tbn`
- **Service Status:** `sudo systemctl status tbn`
- **Service Logs:** `sudo journalctl -u tbn -f`

---

## Support

Email: info@hardinai.co.uk

Tell them:
- You're deploying Boomi integration
- Commit: b47318b
- Any errors you see

