# Vulnerable Flask application

> **Intentionally insecure. Run only on `127.0.0.1` for learning purposes.**

See the [main README](../README.md) for setup, findings and context.

Deliberate vulnerabilities, each marked in the code with a `VULNERABILIDAD DELIBERADA` comment:

| Vulnerability | Where |
|---|---|
| SQL injection | `login()` in `app.py`, where the query is built by string concatenation |
| Reflected XSS | `search()` in `app.py`, where `q` is interpolated into raw HTML |
| Broken access control | `admin()` in `app.py`, which has no session or role check |
| Missing security headers | Application-wide, because no security headers are set |

Other insecure choices that are part of the test environment: plain-text passwords, a hardcoded `secret_key` and `debug=True`.

The code, comments and user interface are in Spanish, as submitted with the thesis.
