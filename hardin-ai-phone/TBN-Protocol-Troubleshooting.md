# TBN Protocol — Troubleshooting Guide

**Product:** TBN Protocol Boomi Integration  
**Version:** 1.0.0  
**Date:** May 2026

---

## Common Issues and Solutions

### 1. Authentication Error (401 Unauthorized)

**Symptom:** API returns `401 Unauthorized`

**Cause:** Invalid or missing API key

**Solution:**
- Verify the `X-API-Key` header is included in the request
- Check the API key is correct (no extra spaces or characters)
- Confirm the API key has not expired
- Contact info@hardinai.co.uk if you need a new key

---

### 2. Bad Request (400)

**Symptom:** API returns `400 Bad Request`

**Cause:** Missing required fields in the request body

**Solution:**
- Check all required fields are included in the JSON body
- For bot_registration: `bot_name`, `bot_type`, `capabilities`, `owner` are required
- For certification_check: `bot_id` is required
- For governance_query: `query_type` and `bot_id` are required
- Ensure Content-Type header is set to `application/json`

---

### 3. Connection Timeout

**Symptom:** Boomi connector times out when calling TBN API

**Cause:** Network connectivity or server issue

**Solution:**
- Verify the URL is correct: `https://tbn.hardinai.co.uk/api/boomi`
- Check your Boomi Atom has outbound internet access on port 443
- Test connectivity: `curl https://tbn.hardinai.co.uk/health`
- If server is down, contact burhan@hardinai.co.uk

---

### 4. Rate Limit Exceeded (429)

**Symptom:** API returns `429 Too Many Requests`

**Cause:** Exceeded daily API call limit

**Solution:**
- Trial tier: 100 calls/day
- Standard tier: 1,000 calls/day
- Enterprise tier: Unlimited
- Contact info@hardinai.co.uk to upgrade your tier

---

### 5. Bot Not Found (404)

**Symptom:** Certification check returns `404 Not Found`

**Cause:** The bot_id does not exist in the registry

**Solution:**
- Verify the bot_id is correct
- Register the bot first using `/bot_registration` endpoint
- Check for typos in the bot_id value

---

### 6. SSL/TLS Certificate Error

**Symptom:** SSL handshake failure

**Cause:** TLS version mismatch or certificate validation issue

**Solution:**
- TBN Protocol requires TLS 1.2 or higher
- Ensure your Boomi Atom's Java runtime trusts Let's Encrypt certificates
- Update your Atom's CA certificate store if needed

---

### 7. JSON Parse Error

**Symptom:** API returns `400` with "Invalid JSON" message

**Cause:** Malformed JSON in request body

**Solution:**
- Validate your JSON using a tool like jsonlint.com
- Ensure proper quoting of strings
- Check for trailing commas
- Verify the Boomi Map step is producing valid JSON output

---

## Health Check

Test the API is running:

```
GET https://tbn.hardinai.co.uk/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "tbn-protocol"
}
```

---

## HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Request completed |
| 400 | Bad Request | Check request body fields |
| 401 | Unauthorized | Check API key |
| 404 | Not Found | Check bot_id or endpoint URL |
| 429 | Rate Limited | Wait or upgrade tier |
| 500 | Server Error | Contact support |

---

## Support Contact

**Email:** burhan@hardinai.co.uk  
**Phone:** +442045772353  
**Hours:** 09:00–18:00 GMT, Monday–Friday  
**Response SLA:** 24 hours

---

*Document Version 1.0 — May 2026*
