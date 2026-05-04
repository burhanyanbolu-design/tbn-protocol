# TBN Protocol — License Guide

## AGPL-3.0 License Overview

TBN Protocol is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

---

## What Does AGPL Mean?

AGPL is like GPL (General Public License) but **stronger for network services**.

### Key Requirement:
**If you run TBN as a web service, you MUST open-source your modifications.**

This is different from MIT license, which allows companies to keep modifications private.

---

## Use Cases

### ✅ Allowed WITHOUT Open-Sourcing:

1. **Personal Use**
   - Running TBN on your laptop
   - Testing and development
   - Learning and education

2. **Internal Company Use**
   - Running TBN internally (not exposed to external users)
   - Private bot networks within your organization

### ⚠️ Requires Open-Sourcing:

1. **Public Web Service**
   - Running TBN as a public API
   - Offering bot certification as a service
   - Any network service accessible to external users

2. **Modified Versions**
   - If you modify TBN and run it as a service
   - You MUST publish your source code
   - Under AGPL-3.0 license

---

## Commercial Licensing

### Don't Want to Open-Source?

We offer **commercial licenses** that allow you to:
- Run modified TBN as a proprietary service
- Keep your modifications private
- Get priority support
- Custom features and integrations

**Contact:** burhan@hardinai.co.uk

---

## Trademark Protection

Even with AGPL, these are **protected trademarks**:
- ✅ "TBN Protocol"
- ✅ "Trusted Bot Network"
- ✅ "BICA" (Bot Identity & Certification Authority)

You cannot use these names for your fork without permission.

---

## Why AGPL?

### Protects the Network
- Prevents companies from taking TBN, improving it, and keeping improvements private
- Ensures the community benefits from all improvements
- Creates a level playing field

### Encourages Contribution
- Companies that improve TBN must share improvements
- Everyone benefits from better code
- Builds a stronger ecosystem

### Enables Dual Licensing
- Open source for community
- Commercial licenses for enterprises
- Sustainable business model

---

## Comparison with Other Licenses

| License | Can Use Freely? | Must Open-Source Modifications? | Network Service Clause? |
|---------|----------------|--------------------------------|------------------------|
| **MIT** | ✅ Yes | ❌ No | ❌ No |
| **GPL** | ✅ Yes | ✅ Yes (if distributed) | ❌ No |
| **AGPL** | ✅ Yes | ✅ Yes (even for services) | ✅ **Yes** |

---

## FAQ

### Q: Can I use TBN in my startup?
**A:** Yes! If you're running it as a public service, you must open-source your modifications. Or get a commercial license.

### Q: Can I fork TBN and create my own network?
**A:** Yes, but you must use AGPL-3.0 and cannot use our trademarks.

### Q: What if I just want to test TBN?
**A:** Go ahead! Testing and personal use don't require open-sourcing.

### Q: Can I sell TBN-based services?
**A:** Yes, but your code must be AGPL. Or get a commercial license.

### Q: What happens if I violate AGPL?
**A:** Your license terminates immediately. We may pursue legal action.

---

## How to Comply with AGPL

If you run a modified TBN service:

1. **Publish your source code**
   - On GitHub, GitLab, or similar
   - Include all modifications
   - Use AGPL-3.0 license

2. **Provide a link**
   - In your API responses
   - On your website
   - In your documentation

3. **Include copyright notices**
   - Keep original copyright headers
   - Add your own copyright for your changes

4. **Include LICENSE file**
   - Full AGPL-3.0 text
   - In your repository

---

## Example Compliance

```python
# In your API response:
{
  "version": "1.0.0",
  "license": "AGPL-3.0",
  "source_code": "https://github.com/yourcompany/tbn-fork",
  "original": "https://github.com/burhanyanbolu-design/tbn-protocol"
}
```

---

## Get Help

Questions about licensing?

**Email:** burhan@hardinai.co.uk  
**Website:** https://hardinai.co.uk

---

*This guide is for informational purposes only and does not constitute legal advice.*
