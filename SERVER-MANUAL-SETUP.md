# Manual Server Setup — Add Boomi Integration Code

## Problem
The server doesn't have git initialized, so we need to manually add the Boomi code to `routes.py`.

## Solution
Add the Boomi integration code to the end of `/opt/tbn-protocol/api/routes.py` before the last line.

---

## Step 1: SSH into Server

You're already connected. Good!

```
ubuntu@ip-172-26-0-177:/opt/tbn-protocol$
```

---

## Step 2: Backup the Current File

```bash
cp api/routes.py api/routes.py.backup
```

---

## Step 3: Open the File in Nano Editor

```bash
nano api/routes.py
```

---

## Step 4: Go to the End of the File

Press: `Ctrl + End` (or `Ctrl + V` then `Ctrl + V` to go to end)

---

## Step 5: Find the Last Line

Look for the last route definition. It should be something like:

```python
@api.route("/...")
def some_function():
    ...
```

---

## Step 6: Add the Boomi Code

Add this code BEFORE the very last line of the file:

```python
# ── Boomi Integration Endpoints ──────────────────────────────────────

@api.route("/boomi/process", methods=["POST"])
@require_api_key
def boomi_process():
    """
    Boomi Integration Endpoint
    
    Receives documents from Boomi processes and routes them to appropriate TBN handlers.
    
    Body: {
        "process_type": "bot_registration" | "certification_check" | "governance_query",
        "data": { ... process-specific data ... },
        "metadata": {
            "boomi_process_id": "...",
            "timestamp": "2026-05-12T10:30:00Z",
            "source": "boomi"
        }
    }
    
    Returns: {
        "success": true,
        "process_id": "...",
        "result": { ... },
        "status": "completed" | "pending" | "error"
    }
    """
    try:
        body = request.get_json() or {}
        process_type = body.get("process_type", "").strip()
        data = body.get("data", {})
        metadata = body.get("metadata", {})
        
        if not process_type:
            return jsonify({"error": "process_type is required"}), 400
        
        # Route to appropriate handler
        if process_type == "bot_registration":
            result = _boomi_register_bot(data, metadata)
        elif process_type == "certification_check":
            result = _boomi_check_certification(data, metadata)
        elif process_type == "governance_query":
            result = _boomi_governance_query(data, metadata)
        else:
            return jsonify({"error": f"Unknown process_type: {process_type}"}), 400
        
        # Log the Boomi interaction
        state.log_activity(
            "boomi_integration",
            f"Boomi process: {process_type}",
            {"boomi_process_id": metadata.get("boomi_process_id"), "result": result}
        )
        
        return jsonify({
            "success": True,
            "process_id": metadata.get("boomi_process_id"),
            "result": result,
            "status": "completed"
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "error"
        }), 500


def _boomi_register_bot(data: dict, metadata: dict) -> dict:
    """
    Handle bot registration from Boomi.
    
    Expected data: {
        "bot_name": "...",
        "bot_type": "SEARCH" | "VALIDATOR" | "CONNECTOR" | "MESSENGER",
        "company": "...",
        "email": "...",
        "description": "..."
    }
    """
    bot_name = data.get("bot_name", "").strip()
    bot_type = data.get("bot_type", "SEARCH").upper()
    company = data.get("company", "").strip()
    email = data.get("email", "").strip()
    description = data.get("description", "").strip()
    
    if not bot_name or not company or not email:
        raise ValueError("bot_name, company, and email are required")
    
    if bot_type not in BOT_CLASSES:
        raise ValueError(f"Invalid bot_type: {bot_type}")
    
    # Create bot instance
    bot_class = BOT_CLASSES[bot_type]
    bot = bot_class(name=bot_name, company=company)
    
    return {
        "bot_id": bot.bot_id,
        "bot_name": bot_name,
        "bot_type": bot_type,
        "company": company,
        "status": "registered",
        "created_at": datetime.now(timezone.utc).isoformat()
    }


def _boomi_check_certification(data: dict, metadata: dict) -> dict:
    """
    Check certification status of a bot.
    
    Expected data: {
        "bot_id": "...",
        "cert_level": "BRONZE" | "SILVER" | "GOLD" (optional)
    }
    """
    bot_id = data.get("bot_id", "").strip()
    cert_level = data.get("cert_level", "").strip()
    
    if not bot_id:
        raise ValueError("bot_id is required")
    
    # Get bot from registry
    bots = state.get_bots()
    bot = next((b for b in bots if b.get("bot_id") == bot_id), None)
    
    if not bot:
        raise ValueError(f"Bot not found: {bot_id}")
    
    # Check certification
    ca = CertificationAuthority()
    cert_info = ca.verify_certificate(bot_id)
    
    return {
        "bot_id": bot_id,
        "certified": cert_info.get("valid", False),
        "cert_level": cert_info.get("level", "NONE"),
        "expires": cert_info.get("expires"),
        "verified_at": datetime.now(timezone.utc).isoformat()
    }


def _boomi_governance_query(data: dict, metadata: dict) -> dict:
    """
    Query governance status and decisions.
    
    Expected data: {
        "query_type": "bot_status" | "violations" | "access_requests",
        "bot_id": "..." (optional),
        "limit": 10 (optional)
    }
    """
    query_type = data.get("query_type", "bot_status").strip()
    bot_id = data.get("bot_id", "").strip()
    limit = data.get("limit", 10)
    
    if query_type == "bot_status":
        bots = state.get_bots()
        if bot_id:
            bots = [b for b in bots if b.get("bot_id") == bot_id]
        return {
            "query_type": query_type,
            "count": len(bots),
            "bots": bots[:limit]
        }
    
    elif query_type == "violations":
        # Get violations from governance engine
        violations = state.get_violations()
        if bot_id:
            violations = [v for v in violations if v.get("bot_id") == bot_id]
        return {
            "query_type": query_type,
            "count": len(violations),
            "violations": violations[:limit]
        }
    
    elif query_type == "access_requests":
        # Get pending access requests
        requests = state.get_access_requests()
        return {
            "query_type": query_type,
            "count": len(requests),
            "requests": requests[:limit]
        }
    
    else:
        raise ValueError(f"Unknown query_type: {query_type}")


@api.route("/boomi/health", methods=["GET"])
def boomi_health():
    """
    Health check endpoint for Boomi integration.
    No authentication required — used for monitoring.
    """
    return jsonify({
        "status": "healthy",
        "service": "TBN Protocol",
        "version": "1.0.0",
        "boomi_integration": "enabled",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


# ── End of Boomi Integration ─────────────────────────────────────────
```

---

## Step 7: Save the File

Press: `Ctrl + X`
Then: `Y` (for yes)
Then: `Enter` (to confirm filename)

---

## Step 8: Restart the Service

```bash
sudo systemctl restart tbn
```

Wait 3 seconds for it to restart.

---

## Step 9: Test It

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

If you see this, it's working! ✅

---

## If Something Goes Wrong

Restore the backup:
```bash
cp api/routes.py.backup api/routes.py
sudo systemctl restart tbn
```

---

## Next Steps

Once the health check works:

1. Get API key: https://tbn.hardinai.co.uk/api/access/request
2. Configure Boomi with the endpoint
3. Test bot registration
4. Deploy your Boomi process

---

## Support

Email: info@hardinai.co.uk

