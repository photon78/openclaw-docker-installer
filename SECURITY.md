# Security Policy

## Our commitment

This project takes security seriously — it would be embarrassing not to, given that it installs security controls for AI agents with shell access.

We follow responsible disclosure and will respond to security reports promptly.

---

## Supported versions

| Version | Supported |
|---------|-----------|
| latest `main` | ✅ |
| older releases | on a case-by-case basis |

---

## Reporting a vulnerability

**Please do not open a public GitHub issue for security vulnerabilities.**

Report privately via one of these channels:

1. **GitHub Private Advisory:** [Security Advisories](https://github.com/photon78/openclaw-docker-installer/security/advisories/new)
2. **Email:** contact via OpenClaw Discord (DM to maintainer)

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Your suggested fix (optional but appreciated)

---

## What to expect

- **Acknowledgement:** within 48 hours
- **Status update:** within 7 days
- **Fix timeline:** depends on severity — critical issues within 14 days, others within 30 days
- **Credit:** we'll credit you in the CHANGELOG unless you prefer to remain anonymous

---

## Scope

In scope:
- Installer code generating insecure configurations
- Privilege escalation in generated scripts
- Secret leakage (API keys, tokens) in generated files
- Allowlist bypass vulnerabilities

Out of scope:
- Vulnerabilities in OpenClaw itself (report to [OpenClaw](https://github.com/openclaw/openclaw))
- Vulnerabilities in dependencies (report upstream)
- Social engineering of the user

---

## Known limitations

This installer generates security configurations for OpenClaw. We document known limitations honestly in [SECURITY-ARCHITECTURE.md](SECURITY-ARCHITECTURE.md). If you find something we missed there, that's in scope.
