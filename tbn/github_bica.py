"""
GitHub-backed BICA Registry
Stores bot certificates in a GitHub repository for persistence and transparency.
Replaces local JSON storage with distributed, version-controlled registry.
"""

import json
import base64
import os
from datetime import datetime, timezone
from typing import Optional, Dict, List
import requests

from .identity import BotIdentity


class GitHubBICA:
    """
    Bot Identity & Certification Authority backed by GitHub.
    
    Stores bot certificates in a GitHub repository:
    - registry/bots/{bot_id}.json - Individual bot certificates
    - registry/certifications/{bot_id}.json - Certification records
    - registry/audit/{date}.json - Daily audit logs
    - registry/stats.json - Network statistics
    """
    
    def __init__(self, repo: str, token: str = None, branch: str = "main"):
        self.repo = repo  # e.g., "burhanyanbolu-design/tbn-bica-registry"
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo}"
        
        # Local cache for performance
        self._cache: Dict[str, dict] = {}
        self._cache_timestamp = 0
        self._cache_ttl = 300  # 5 minutes
        
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            })
    
    def initialize_registry(self) -> bool:
        """
        Initialize the GitHub repository structure.
        Creates necessary directories and files.
        """
        try:
            # Check if repo exists and is accessible
            response = self.session.get(self.base_url)
            if response.status_code != 200:
                print(f"❌ Cannot access repository: {self.repo}")
                return False
            
            # Create initial structure
            initial_files = {
                "registry/README.md": self._create_readme(),
                "registry/stats.json": json.dumps({
                    "total_bots": 0,
                    "certified_bots": 0,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "network_version": "0.1.0"
                }, indent=2),
                "registry/bots/.gitkeep": "",
                "registry/certifications/.gitkeep": "",
                "registry/audit/.gitkeep": ""
            }
            
            for path, content in initial_files.items():
                self._create_or_update_file(path, content, f"Initialize {path}")
            
            print(f"✅ GitHub BICA registry initialized: {self.repo}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize GitHub registry: {e}")
            return False
    
    def register(self, identity: BotIdentity, cert_level: str = "STANDARD") -> bool:
        """
        Register a bot certificate in the GitHub registry.
        """
        try:
            cert = identity.to_certificate()
            cert["cert_level"] = cert_level
            cert["registered_at"] = datetime.now(timezone.utc).isoformat()
            
            # Store bot certificate
            bot_path = f"registry/bots/{cert['bot_id']}.json"
            self._create_or_update_file(
                bot_path,
                json.dumps(cert, indent=2),
                f"Register bot: {cert['name']} ({cert['bot_id']})"
            )
            
            # Update cache
            self._cache[cert["bot_id"]] = cert
            
            # Update stats
            self._update_stats()
            
            # Log audit event
            self._log_audit_event("REGISTER", cert["bot_id"], {
                "name": cert["name"],
                "cert_level": cert_level
            })
            
            print(f"[GitHub-BICA] ✅ Registered: {cert['bot_id']} ({cert['name']})")
            return True
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Registration failed: {e}")
            return False
    
    def verify_certificate(self, cert: dict) -> bool:
        """
        Verify if a certificate exists in the GitHub registry.
        """
        bot_id = cert.get("bot_id")
        if not bot_id:
            return False
        
        try:
            # Check cache first
            if self._is_cache_valid() and bot_id in self._cache:
                print(f"[GitHub-BICA] ✅ Verified (cached): {bot_id}")
                return True
            
            # Fetch from GitHub
            bot_path = f"registry/bots/{bot_id}.json"
            stored_cert = self._get_file_content(bot_path)
            
            if stored_cert:
                stored_data = json.loads(stored_cert)
                self._cache[bot_id] = stored_data
                print(f"[GitHub-BICA] ✅ Verified: {bot_id}")
                return True
            else:
                print(f"[GitHub-BICA] ❌ Unknown bot: {bot_id}")
                return False
                
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Verification error: {e}")
            return False
    
    def get_bot_certificate(self, bot_id: str) -> Optional[dict]:
        """
        Retrieve a specific bot certificate.
        """
        try:
            # Check cache first
            if self._is_cache_valid() and bot_id in self._cache:
                return self._cache[bot_id]
            
            # Fetch from GitHub
            bot_path = f"registry/bots/{bot_id}.json"
            content = self._get_file_content(bot_path)
            
            if content:
                cert = json.loads(content)
                self._cache[bot_id] = cert
                return cert
            
            return None
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Error fetching certificate: {e}")
            return None
    
    def list_bots(self) -> List[dict]:
        """
        List all registered bot certificates.
        """
        try:
            # Get list of bot files
            response = self.session.get(
                f"{self.base_url}/contents/registry/bots",
                params={"ref": self.branch}
            )
            
            if response.status_code != 200:
                return []
            
            files = response.json()
            bots = []
            
            for file_info in files:
                if file_info["name"].endswith(".json"):
                    bot_id = file_info["name"][:-5]  # Remove .json
                    cert = self.get_bot_certificate(bot_id)
                    if cert:
                        bots.append(cert)
            
            return bots
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Error listing bots: {e}")
            return []
    
    def certify_bot(self, bot_id: str, level: str, purpose: str = "", ethical_declaration: bool = False) -> bool:
        """
        Update a bot's certification level.
        """
        try:
            # Get existing certificate
            cert = self.get_bot_certificate(bot_id)
            if not cert:
                print(f"[GitHub-BICA] ❌ Bot not found: {bot_id}")
                return False
            
            # Update certification
            cert["cert_level"] = level
            cert["certified_at"] = datetime.now(timezone.utc).isoformat()
            
            if level == "COMMUNITY":
                cert["purpose"] = purpose
                cert["ethical_declaration"] = ethical_declaration
            
            # Store updated certificate
            bot_path = f"registry/bots/{bot_id}.json"
            self._create_or_update_file(
                bot_path,
                json.dumps(cert, indent=2),
                f"Certify bot: {level} - {cert['name']}"
            )
            
            # Store certification record
            cert_record = {
                "bot_id": bot_id,
                "level": level,
                "purpose": purpose,
                "ethical_declaration": ethical_declaration,
                "certified_at": cert["certified_at"],
                "certified_by": "system"
            }
            
            cert_path = f"registry/certifications/{bot_id}.json"
            self._create_or_update_file(
                cert_path,
                json.dumps(cert_record, indent=2),
                f"Certification record: {bot_id} -> {level}"
            )
            
            # Update cache
            self._cache[bot_id] = cert
            
            # Log audit event
            self._log_audit_event("CERTIFY", bot_id, {
                "level": level,
                "purpose": purpose
            })
            
            print(f"[GitHub-BICA] ✅ Certified: {bot_id} -> {level}")
            return True
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Certification failed: {e}")
            return False
    
    def revoke(self, bot_id: str, reason: str = "") -> bool:
        """
        Revoke a bot's certificate.
        """
        try:
            # Move certificate to revoked directory
            bot_path = f"registry/bots/{bot_id}.json"
            revoked_path = f"registry/revoked/{bot_id}.json"
            
            # Get existing certificate
            cert_content = self._get_file_content(bot_path)
            if not cert_content:
                print(f"[GitHub-BICA] ❌ Bot not found: {bot_id}")
                return False
            
            # Add revocation info
            cert = json.loads(cert_content)
            cert["revoked_at"] = datetime.now(timezone.utc).isoformat()
            cert["revocation_reason"] = reason
            
            # Store in revoked directory
            self._create_or_update_file(
                revoked_path,
                json.dumps(cert, indent=2),
                f"Revoke bot: {bot_id} - {reason}"
            )
            
            # Delete from active registry
            self._delete_file(bot_path, f"Remove revoked bot: {bot_id}")
            
            # Remove from cache
            if bot_id in self._cache:
                del self._cache[bot_id]
            
            # Log audit event
            self._log_audit_event("REVOKE", bot_id, {"reason": reason})
            
            print(f"[GitHub-BICA] ✅ Revoked: {bot_id}")
            return True
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Revocation failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get network statistics from GitHub registry.
        """
        try:
            stats_content = self._get_file_content("registry/stats.json")
            if stats_content:
                return json.loads(stats_content)
            
            # Generate stats if file doesn't exist
            bots = self.list_bots()
            stats = {
                "total_bots": len(bots),
                "certified_bots": len([b for b in bots if b.get("cert_level") != "RESTRICTED"]),
                "by_level": {
                    "COMMUNITY": len([b for b in bots if b.get("cert_level") == "COMMUNITY"]),
                    "STANDARD": len([b for b in bots if b.get("cert_level") == "STANDARD"]),
                    "RESTRICTED": len([b for b in bots if b.get("cert_level") == "RESTRICTED"])
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "network_version": "0.1.0"
            }
            
            # Store updated stats
            self._create_or_update_file(
                "registry/stats.json",
                json.dumps(stats, indent=2),
                "Update network statistics"
            )
            
            return stats
            
        except Exception as e:
            print(f"[GitHub-BICA] ❌ Error getting stats: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _create_readme(self) -> str:
        """Create README content for the registry."""
        return """# TBN Protocol - BICA Registry

This repository contains the Bot Identity & Certification Authority (BICA) registry for the TBN Protocol network.

## Structure

- `registry/bots/` - Active bot certificates
- `registry/certifications/` - Certification records
- `registry/audit/` - Audit logs
- `registry/revoked/` - Revoked certificates
- `registry/stats.json` - Network statistics

## About TBN Protocol

TBN Protocol provides trust infrastructure for AI agents. Every bot gets a cryptographic identity and certificate stored in this registry.

- **Website:** https://tbn.hardinai.co.uk
- **GitHub:** https://github.com/burhanyanbolu-design/tbn-protocol
- **PyPI:** https://pypi.org/project/tbn-protocol/

## License

AGPL-3.0 - See main repository for details.
"""
    
    def _is_cache_valid(self) -> bool:
        """Check if local cache is still valid."""
        import time
        return (time.time() - self._cache_timestamp) < self._cache_ttl
    
    def _get_file_content(self, path: str) -> Optional[str]:
        """Get file content from GitHub."""
        try:
            response = self.session.get(
                f"{self.base_url}/contents/{path}",
                params={"ref": self.branch}
            )
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            
            return None
            
        except Exception:
            return None
    
    def _create_or_update_file(self, path: str, content: str, message: str) -> bool:
        """Create or update a file in GitHub."""
        try:
            # Check if file exists to get SHA
            existing_response = self.session.get(
                f"{self.base_url}/contents/{path}",
                params={"ref": self.branch}
            )
            
            data = {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "branch": self.branch
            }
            
            if existing_response.status_code == 200:
                # File exists, need SHA for update
                data["sha"] = existing_response.json()["sha"]
            
            response = self.session.put(f"{self.base_url}/contents/{path}", json=data)
            return response.status_code in [200, 201]
            
        except Exception as e:
            print(f"❌ Error creating/updating file {path}: {e}")
            return False
    
    def _delete_file(self, path: str, message: str) -> bool:
        """Delete a file from GitHub."""
        try:
            # Get file SHA
            response = self.session.get(
                f"{self.base_url}/contents/{path}",
                params={"ref": self.branch}
            )
            
            if response.status_code != 200:
                return False
            
            sha = response.json()["sha"]
            
            # Delete file
            delete_response = self.session.delete(
                f"{self.base_url}/contents/{path}",
                json={
                    "message": message,
                    "sha": sha,
                    "branch": self.branch
                }
            )
            
            return delete_response.status_code == 200
            
        except Exception as e:
            print(f"❌ Error deleting file {path}: {e}")
            return False
    
    def _update_stats(self) -> None:
        """Update network statistics."""
        try:
            stats = self.get_stats()
            # Stats are updated in get_stats() method
        except Exception as e:
            print(f"❌ Error updating stats: {e}")
    
    def _log_audit_event(self, event_type: str, bot_id: str, details: dict) -> None:
        """Log an audit event."""
        try:
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            audit_path = f"registry/audit/{today}.json"
            
            # Get existing audit log
            existing_content = self._get_file_content(audit_path)
            if existing_content:
                audit_log = json.loads(existing_content)
            else:
                audit_log = {"date": today, "events": []}
            
            # Add new event
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": event_type,
                "bot_id": bot_id,
                "details": details
            }
            
            audit_log["events"].append(event)
            
            # Store updated audit log
            self._create_or_update_file(
                audit_path,
                json.dumps(audit_log, indent=2),
                f"Audit log: {event_type} {bot_id}"
            )
            
        except Exception as e:
            print(f"❌ Error logging audit event: {e}")