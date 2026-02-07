# Security Policy

## Overview

ARIA (Adaptive Reasoning & Intelligent Automation) is a production-grade agentic AI system that handles sensitive operations including browser automation, credential management, and system interactions. Security is a fundamental design principle, not an afterthought.

This document outlines our security policies, vulnerability reporting process, and best practices for secure deployment and usage.

---

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 1.x.x   | :white_check_mark: | Active development |
| < 1.0   | :x:                | Development/Beta - Not recommended for production |

**Note:** We follow semantic versioning. Security patches are released as PATCH versions (x.x.X).

---

## Security Principles

ARIA is designed with the following security principles:

### 1. **Human-in-the-Loop (HITL) Safety**
- Sensitive actions (login, payment, CAPTCHA) require explicit human approval
- No autonomous execution of irreversible or high-risk operations
- Configurable safety gates per operation type

### 2. **Event Sourcing & Auditability**
- Complete audit trail of all agent actions via Kafka/Redpanda
- Immutable event log enables forensic analysis
- Replay capability for security incident investigation

### 3. **Credential Isolation**
- Credentials never logged or stored in event streams
- Environment-based secret management
- Support for external secret stores (future: HashiCorp Vault, AWS Secrets Manager)

### 4. **Least Privilege Execution**
- Plugins run with minimal required permissions
- Browser automation sandboxed via Playwright
- Desktop automation requires explicit user consent

### 5. **Privacy-First Design**
- Local LLM support eliminates data exfiltration to third-party APIs
- Sensitive screenshots can be masked or excluded from logging
- PII detection and redaction capabilities

---

## Reporting a Vulnerability

### Scope

We take all security bugs seriously. Please report any vulnerability in:

- **Core ARIA components** (Brain, Eye, Hand, Memory)
- **API endpoints** (FastAPI, WebSocket)
- **Authentication & authorization mechanisms**
- **Credential handling & storage**
- **Plugin security boundaries**
- **Event sourcing & replay security**
- **Dependency vulnerabilities** (if exploitable in ARIA context)

### Out of Scope

The following are generally **not** considered security vulnerabilities:

- Bugs in third-party services (LinkedIn, Indeed, etc.) - report to the service provider
- Social engineering attacks targeting end users
- Vulnerabilities requiring physical access to the host machine
- Known limitations documented in README or architecture docs
- Issues in example code or test fixtures (unless they expose production code vulnerabilities)

### How to Report

**⚠️ DO NOT create a public GitHub issue for security vulnerabilities.**

Instead, please email security reports to:

📧 **mahdinavaei1367@gmail.com**

**Subject:** `[SECURITY] Brief description of vulnerability`

### What to Include

Please provide:

1. **Description** of the vulnerability
2. **Steps to reproduce** (ideally with a minimal example)
3. **Impact assessment** (what can an attacker do?)
4. **Affected versions** (if known)
5. **Suggested fix** (if you have one)
6. **Your name/handle** (for attribution, if desired)

### Response Timeline

| Stage | Timeline |
|-------|----------|
| **Initial response** | Within 48 hours |
| **Triage & assessment** | Within 5 business days |
| **Fix development** | Depends on severity (1-30 days) |
| **Patch release** | After thorough testing |
| **Public disclosure** | 90 days after fix, or sooner if agreed |

### Recognition

We maintain a **Security Hall of Fame** below. Researchers who responsibly disclose vulnerabilities will be credited (unless they prefer to remain anonymous).

---

## Security Best Practices

### For Users

#### 1. Environment Configuration

**Never commit `.env` files to version control:**

```bash
# Already in .gitignore, but verify:
git ls-files | grep .env  # Should return nothing
```

**Use strong, unique credentials:**

```bash
# Generate secure API keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Rotate credentials regularly:**
- API keys every 90 days
- Service passwords every 180 days
- Review access logs monthly

#### 2. Network Security

**Restrict API access:**

```yaml
# config/api.yaml
api:
  host: "127.0.0.1"  # Only localhost, not 0.0.0.0
  allowed_origins:
    - "http://localhost:8501"  # Streamlit only
```

**Use HTTPS in production:**

```bash
# Behind reverse proxy (nginx/Caddy)
uvicorn aria.api.main:app --host 127.0.0.1 --port 8000
```

**Firewall configuration:**

```bash
# Example: Allow only localhost connections
sudo ufw deny 8000/tcp
sudo ufw allow from 127.0.0.1 to any port 8000
```

#### 3. Dependency Management

**Keep dependencies updated:**

```bash
# Check for security updates
pip list --outdated

# Update with caution (test first)
pip install --upgrade package-name
```

**Audit dependencies regularly:**

```bash
# Use pip-audit or safety
pip install pip-audit
pip-audit

# Or use safety
pip install safety
safety check
```

**Pin critical dependencies:**

```txt
# requirements.txt
langchain==0.1.0  # Pin exact version for reproducibility
playwright>=1.40.0,<2.0.0  # Allow patches, not majors
```

#### 4. Secrets Management

**Never hardcode secrets:**

```python
# ❌ BAD
OPENAI_API_KEY = "sk-..."

# ✅ GOOD
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")
```

**Use `.env` for local development:**

```bash
# .env (never commit!)
OPENAI_API_KEY=sk-...
REDIS_PASSWORD=...
```

**Use secret stores in production:**

```bash
# Example: AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id aria/prod/openai-key
```

#### 5. Docker Security

**Run containers as non-root:**

```dockerfile
# Dockerfile
USER aria:aria  # Not root
```

**Limit container capabilities:**

```yaml
# docker-compose.yml
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only if needed
```

**Use read-only filesystems where possible:**

```yaml
read_only: true
tmpfs:
  - /tmp
```

**Scan images regularly:**

```bash
docker scan mahdinavaei/aria:latest
```

#### 6. Data Protection

**Sanitize logs:**

```python
# Logs should never contain credentials
logger.info(f"Logged in as {username}")  # ✅ OK
logger.info(f"Password: {password}")     # ❌ NEVER
```

**Encrypt sensitive data at rest:**

```python
# Example: Encrypt profile data
from cryptography.fernet import Fernet

key = os.getenv("ENCRYPTION_KEY")
cipher = Fernet(key)
encrypted = cipher.encrypt(profile_data.encode())
```

**Use HTTPS for all external API calls:**

```python
# Verify SSL certificates
import requests
response = requests.get(url, verify=True)  # Default, but be explicit
```

#### 7. Browser Automation Security

**Disable unnecessary permissions:**

```python
# playwright launch args
browser = await playwright.chromium.launch(
    args=[
        "--disable-dev-shm-usage",
        "--no-sandbox",  # Only in Docker
        "--disable-geolocation",
        "--disable-notifications",
    ]
)
```

**Clear browser state after runs:**

```python
# Clean up cookies/storage
await context.clear_cookies()
await context.clear_permissions()
```

**Validate URLs before navigation:**

```python
from urllib.parse import urlparse

def is_safe_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.netloc
```

### For Contributors

#### 1. Code Review Checklist

Before submitting PRs, verify:

- [ ] No hardcoded credentials or API keys
- [ ] Input validation on all user-provided data
- [ ] No SQL/Command injection vulnerabilities
- [ ] Proper error handling (no stack traces to users)
- [ ] Logging doesn't expose sensitive data
- [ ] Dependencies are up-to-date and audited

#### 2. Secure Coding Practices

**Validate all inputs:**

```python
from pydantic import BaseModel, validator

class TaskRequest(BaseModel):
    url: str
    
    @validator("url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("Invalid URL scheme")
        return v
```

**Avoid command injection:**

```python
# ❌ DANGEROUS
os.system(f"echo {user_input}")

# ✅ SAFE
subprocess.run(["echo", user_input], check=True)
```

**Prevent path traversal:**

```python
from pathlib import Path

def safe_file_access(user_path: str, base_dir: Path) -> Path:
    full_path = (base_dir / user_path).resolve()
    if not full_path.is_relative_to(base_dir):
        raise ValueError("Path traversal attempt detected")
    return full_path
```

#### 3. Testing Security Features

**Write security-focused tests:**

```python
def test_api_requires_authentication():
    """Unauthenticated requests should fail"""
    response = client.get("/api/tasks")
    assert response.status_code == 401

def test_sql_injection_prevented():
    """SQL injection attempts should be sanitized"""
    malicious = "'; DROP TABLE users; --"
    response = client.post("/api/search", json={"query": malicious})
    assert response.status_code == 400  # Rejected
```

---

## Known Security Considerations

### 1. Local LLM Models

**Risk:** LLM models may generate malicious code or commands.

**Mitigation:**
- Human-in-the-loop approval for all system commands
- Sandboxed execution environments
- Output validation and sanitization

### 2. Browser Automation

**Risk:** Automated browser could be hijacked to visit malicious sites.

**Mitigation:**
- URL allowlist/blocklist configuration
- Human approval for navigation outside approved domains
- Browser isolation via Playwright contexts

### 3. Credential Storage

**Risk:** Credentials stored in Redis could be exposed if Redis is compromised.

**Mitigation:**
- Encrypt credentials at rest (planned for v2.0)
- Use Redis authentication (`requirepass`)
- Network isolation (Redis only accessible from ARIA containers)

### 4. Event Log Sensitivity

**Risk:** Event logs may contain sensitive UI screenshots or form data.

**Mitigation:**
- Configurable PII redaction
- Screenshot masking for sensitive fields
- Event retention policies (auto-delete after N days)

### 5. API Exposure

**Risk:** Unauthenticated API access could allow unauthorized task execution.

**Mitigation:**
- API authentication required (API key or OAuth)
- Rate limiting per client
- IP allowlisting for production deployments

---

## Incident Response Plan

If a security incident occurs:

### 1. Detection
- Monitor logs for suspicious activity
- Set up alerts for failed authentication attempts
- Review event streams for anomalies

### 2. Containment
- Immediately rotate compromised credentials
- Disable affected API endpoints if necessary
- Isolate affected containers/services

### 3. Eradication
- Apply security patches
- Remove malicious code/data
- Audit all related systems

### 4. Recovery
- Restore services from clean backups
- Verify system integrity before bringing back online
- Monitor closely for 48 hours post-incident

### 5. Post-Incident
- Conduct root cause analysis
- Update security policies and controls
- Communicate with affected users (if applicable)
- Document lessons learned

---

## Security Roadmap

We are actively working on:

- [ ] **API Authentication** (OAuth 2.0, JWT)
- [ ] **Credential Encryption** (at rest in Redis)
- [ ] **Role-Based Access Control (RBAC)** for multi-user deployments
- [ ] **Audit Log Export** (SIEM integration)
- [ ] **PII Detection & Redaction** (automatic)
- [ ] **Secret Store Integration** (Vault, AWS Secrets Manager)
- [ ] **Container Security Scanning** (CI/CD pipeline)
- [ ] **Penetration Testing** (third-party audit)

---

## Compliance & Standards

ARIA aims to align with:

- **OWASP Top 10** (Web Application Security Risks)
- **CWE Top 25** (Most Dangerous Software Weaknesses)
- **NIST Cybersecurity Framework** (Identify, Protect, Detect, Respond, Recover)
- **GDPR** (for European users - data minimization, right to erasure)

---

## Security Hall of Fame

We thank the following researchers for responsibly disclosing vulnerabilities:

| Researcher | Date | Vulnerability |
|------------|------|---------------|
| *No reports yet* | - | - |

---

## Additional Resources

- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [Python Security Best Practices](https://python.readthedocs.io/en/latest/library/security_warnings.html)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

---

## Questions?

For security-related questions (non-vulnerabilities), please email:

📧 **mahdinavaei1367@gmail.com**

For general questions, use GitHub Discussions or Issues.

---

<div align="center">

**Security is everyone's responsibility. Thank you for helping keep ARIA safe.**

*Last updated: February 7, 2026*

</div>
