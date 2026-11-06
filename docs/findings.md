# Findings

Target: vulnerable Flask application at `http://127.0.0.1:5000`, local only.
Tools: OWASP ZAP 2.16.1 in standard mode (traditional spider and active scan; passive scan enabled by default) and manual testing in the browser.
Environment: macOS on Apple Silicon, Python 3.13, Flask development server.

Full detail is in Chapter 6 (testing) and Chapter 7 (remediation) of the [thesis](TFG_Alberto_Moreno_Alcacer.pdf).

## Summary

| ID | Finding | Endpoint | ZAP risk | Detection | Status |
|---|---|---|---|---|---|
| F-01 | SQL injection in login | `POST /login` (`username`, `password`) | High | ZAP active scan and manual | Confirmed |
| F-02 | Reflected XSS | `GET /search?q=` | n/a | Manual only | Confirmed |
| F-03 | Broken access control on admin panel | `GET /admin` | n/a | Manual only | Confirmed |
| F-04 | Missing HTTP security headers | All routes | Medium / Low | ZAP passive scan | Confirmed |

## ZAP alert overview

| Risk | Alert (number of instances) |
|---|---|
| High | SQL Injection - SQLite (2) |
| Medium | Absence of Anti-CSRF Tokens (3) |
| Medium | Content Security Policy (CSP) Header Not Set (3) |
| Medium | Missing Anti-clickjacking Header (8) |
| Low | Cookie without SameSite Attribute (4) |
| Low | Server Leaks Version Information via "Server" HTTP Response Header Field |
| Low | X-Content-Type-Options Header Missing (9) |
| Informational | User Controllable HTML Element Attribute (Potential XSS) |
| Informational | Authentication Request Identified |
| Informational | Session Management Response Identified (4) |

The anti-CSRF and SameSite alerts are valid weaknesses as well, but they were outside the scope of the four vulnerabilities this project set out to study.

## F-01 SQL injection in login

**Cause.** The authentication query is built by string concatenation:

```python
query = ("SELECT * FROM users WHERE username = '" + username
         + "' AND password = '" + password + "'")
```

**Evidence.** ZAP's active scan triggered a `sqlite3.OperationalError` (HTTP 500) on `/login` and raised *SQL Injection - SQLite*, with High risk and Medium confidence (CWE-89). Manually, a crafted value in the username field logged in as `admin` without valid credentials.

**Impact.** Full authentication bypass, including access as the administrator.

**Fix.** Use parameterised queries:

```python
conn.execute("SELECT * FROM users WHERE username = ? AND password = ?",
             (username, password))
```

Passwords should also be stored as salted hashes, not in plain text.

**Mapping.** OWASP Top 10:2025 A05 Injection · ASVS: input validation and injection prevention.

## F-02 Reflected XSS in search

**Cause.** The `q` parameter is interpolated into an f-string HTML response without escaping, both in the page body and in the input's `value` attribute.

**Evidence.** A `<script>` payload in `q` executed a JavaScript alert in the browser. The automated scan did not raise an XSS alert for this parameter.

**Impact.** Arbitrary script execution in the victim's session through a crafted link.

**Fix.** Render through a template so that Jinja2 escapes the value automatically:

```python
return render_template("search.html", query=q)
```

```html
<p>Has buscado: {{ query }}</p>
```

Limiting the parameter length is an additional measure on top of output encoding, not a substitute for it.

**Mapping.** OWASP Top 10:2025 A05 Injection · ASVS: output encoding and handling of untrusted data.

## F-03 Broken access control on `/admin`

**Cause.** The route checks neither that a session exists nor the user's role.

**Evidence.** Opening `/admin` from a private window with no session displayed the list of every user and their role. ZAP did not flag this, because detecting it requires knowing that the route is meant to be restricted.

**Impact.** Disclosure of user accounts and roles to unauthenticated visitors.

**Fix.** Enforce authentication and authorisation on the server:

```python
if "user_id" not in session:
    return redirect("/login")
if session.get("role") != "admin":
    return "Access denied", 403
```

In a larger application this check would live in a decorator. Hiding the navigation link alone would not fix the issue.

**Mapping.** OWASP Top 10:2025 A01 Broken Access Control · ASVS: access control and authorisation.

## F-04 Missing HTTP security headers

**Cause.** Flask does not add security headers by default, and the application does not set them.

**Evidence.** ZAP's passive scan flagged a missing `Content-Security-Policy` header, a missing `X-Content-Type-Options` header and a missing anti-clickjacking header. Inspecting the raw responses in ZAP confirmed that the only headers returned were `Server`, `Date`, `Content-Type`, `Content-Length` and `Connection`.

**Impact.** No defence in depth against XSS, MIME sniffing or clickjacking.

**Fix.** Set the headers centrally:

```python
@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
```

**Mapping.** OWASP Top 10:2025 A02 Security Misconfiguration · ASVS: secure configuration of HTTP responses.

## Lessons learned

- DAST is effective for injection flaws that produce observable errors and for configuration issues visible in responses.
- Logic flaws such as missing authorisation, and some reflected XSS, need a human tester who understands what the application is supposed to do.
- An alert is a lead, not a conclusion. Every ZAP finding here was reproduced manually before it was reported.
- All four issues could have been prevented by basic secure coding controls, which is the basis of the secure development methodology proposed in Chapter 7 (NIST SSDF, OWASP ASVS, ENS).
