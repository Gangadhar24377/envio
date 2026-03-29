# Security Policy

## Supported Versions

The following versions of Envio are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within Envio, please send an email to gangadharkambhamettu@gmail.com. All security vulnerabilities will be promptly addressed.

Please include the following information:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Best Practices

When using Envio, follow these security best practices:

### 1. API Key Management

- **Never commit API keys** to version control
- Use environment variables or `.env` files (already in `.gitignore`)
- Rotate API keys periodically
- Use minimal permissions when possible

```bash
# Recommended: Set API key via environment variable
export OPENAI_API_KEY="sk-..."

# Or use envio's config command (stores in ~/.envio/config.json)
envio config api <your-key>
```

### 2. Package Validation

Envio validates package names against PyPI to prevent:
- Typosquatting attacks
- Invalid package names
- Version conflicts

Always verify packages before installation:
```bash
envio install <package> --dry-run
```

### 3. Script Execution Safety

Envio generates installation scripts that are:
- Written to temporary files with restricted permissions
- Executed in isolated virtual environments
- Cross-platform safe (PowerShell on Windows, Bash on Unix)

### 4. Dependency Scanning

Use the built-in security audit:
```bash
envio audit -n <environment>
```

This uses `pip-audit` to check for known vulnerabilities.

## Security Features Implemented

| Feature | Description |
|---------|-------------|
| Package Name Validation | PEP 503 compliant validation |
| Shell Escaping | Prevents command injection |
| Path Traversal Protection | Validates file paths in resurrect command |
| Secure Config Storage | File permissions set to 0o600 |
| API Key Masking | Keys masked in console output |
| Retry Logic | Network calls have exponential backoff |

## Known Security Considerations

### 1. LLM-Generated Commands

When using AI to generate package installation commands:
- Always review suggested commands before execution
- Use `--dry-run` to preview changes
- The AI may suggest incorrect package names (always validate)

### 2. Third-Party Package Sources

- Default: PyPI (pypi.org) - trusted
- Conda: Anaconda cloud - verify sources
- Always verify package authenticity

### 3. Network Security

- All HTTP calls use HTTPS
- API keys are never logged
- Retry logic prevents information leakage through error messages

## Update Policy

Security updates will be released as patch versions. We follow semantic versioning for releases.

- Critical security fixes: Released immediately
- Major security changes: Released in next minor version

## Attribution

This security policy is adapted from best practices for open-source projects.
