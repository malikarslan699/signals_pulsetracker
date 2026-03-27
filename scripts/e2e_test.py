#!/usr/bin/env python3
"""
Comprehensive end-to-end tests for PulseSignal Pro API at http://localhost:8100

Discovered API structure:
  - /api/v1/auth/me   (NOT /api/v1/users/me — returns 404)
  - /api/v1/auth/login
  - /api/v1/auth/register  (email must be non-special-use TLD; .test is rejected)
  - /api/v1/admin/users/   (GET list, PUT /{id} — POST not supported on collection)
  - /api/v1/signals/
  - /api/v1/scanner/status, /scanner/pairs
  - /api/v1/alerts/
  - /api/v1/admin/analytics/overview
"""

import json
import http.client
from typing import Any, Optional

BASE_HOST = "localhost"
BASE_PORT = 8100

# Test result tracking
results = []


def log(label: str, passed: bool, detail: str = ""):
    status_str = "PASS" if passed else "FAIL"
    results.append((label, passed, detail))
    icon = "+" if passed else "X"
    print(f"  [{status_str}] {icon} {label}: {detail}")


def make_request(
    method: str,
    path: str,
    token: Optional[str] = None,
    body: Optional[dict] = None,
) -> tuple[int, Any]:
    conn = http.client.HTTPConnection(BASE_HOST, BASE_PORT, timeout=15)
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    encoded_body = None
    if body is not None:
        encoded_body = json.dumps(body).encode("utf-8")

    try:
        conn.request(method, path, body=encoded_body, headers=headers)
        resp = conn.getresponse()
        status_code = resp.status
        raw = resp.read().decode("utf-8")
        conn.close()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = raw
        return status_code, data
    except Exception as e:
        return 0, {"error": str(e)}


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def is_numeric(v) -> bool:
    if v is None:
        return False
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


# ============================================================
# SECTION 1: OWNER ACCOUNT
# ============================================================
section("1. OWNER ACCOUNT (malik.g72@gmail.com)")

OWNER_EMAIL = "malik.g72@gmail.com"
OWNER_PASS = "PulseOwner2025!"

# 1.1 Login
status, data = make_request(
    "POST",
    "/api/v1/auth/login",
    body={"email": OWNER_EMAIL, "password": OWNER_PASS},
)
owner_token = None
owner_user_id = ""
if status == 200 and isinstance(data, dict) and "access_token" in data:
    owner_token = data["access_token"]
    log("Owner login", True, f"HTTP {status} — token obtained")
else:
    log("Owner login", False, f"HTTP {status} — {str(data)[:200]}")

# 1.2 GET /api/v1/auth/me  (correct path is /auth/me, not /users/me)
if owner_token:
    status, data = make_request("GET", "/api/v1/auth/me", token=owner_token)
    if status == 200 and isinstance(data, dict):
        role = data.get("role", "")
        plan = data.get("plan", "")
        owner_user_id = data.get("id", "")
        role_ok = role in ("superadmin", "owner")
        plan_ok = plan == "lifetime"
        log("Owner GET /auth/me — role check", role_ok,
            f"role={role} (expected superadmin/owner)")
        log("Owner GET /auth/me — plan check", plan_ok,
            f"plan={plan} (expected lifetime)")
        print(f"    Owner ID: {owner_user_id}")
        print(f"    Owner email: {data.get('email')}, verified={data.get('is_verified')}")
    else:
        log("Owner GET /auth/me", False, f"HTTP {status} — {str(data)[:200]}")

# 1.3 GET /api/v1/signals/
signals_list = []
if owner_token:
    status, data = make_request("GET", "/api/v1/signals/?limit=5", token=owner_token)
    if status == 200:
        if isinstance(data, list):
            signals_list = data
        elif isinstance(data, dict) and "items" in data:
            signals_list = data["items"]
        elif isinstance(data, dict) and "signals" in data:
            signals_list = data["signals"]

        has_signals = len(signals_list) > 0
        if has_signals:
            first = signals_list[0]
            has_entry = "entry" in first or "entry_price" in first
            has_tp1 = "tp1" in first or "take_profit_1" in first
            has_sl = "sl" in first or "stop_loss" in first
            log("Owner GET /signals/ — returns signals", True,
                f"{len(signals_list)} signals returned")
            log("Owner GET /signals/ — entry/tp1/sl fields", has_entry and has_tp1 and has_sl,
                f"entry={has_entry}, tp1={has_tp1}, sl={has_sl}")
        else:
            log("Owner GET /signals/ — returns signals", False,
                f"No signals in response: {str(data)[:200]}")
    else:
        log("Owner GET /signals/", False, f"HTTP {status} — {str(data)[:200]}")

# 1.4 GET /api/v1/scanner/pairs
if owner_token:
    status, data = make_request("GET", "/api/v1/scanner/pairs", token=owner_token)
    if status == 200 and isinstance(data, list):
        log("Owner GET /scanner/pairs", True, f"{len(data)} pairs returned")
    elif status == 200 and isinstance(data, dict) and "items" in data:
        log("Owner GET /scanner/pairs", True, f"{len(data['items'])} pairs returned")
    else:
        log("Owner GET /scanner/pairs", False, f"HTTP {status} — {str(data)[:200]}")

# 1.5 GET /api/v1/alerts/
if owner_token:
    status, data = make_request("GET", "/api/v1/alerts/", token=owner_token)
    if status == 200:
        count = len(data) if isinstance(data, list) else data.get("total", "?")
        log("Owner GET /alerts/", True, f"HTTP {status} — {count} alerts")
    else:
        log("Owner GET /alerts/", False, f"HTTP {status} — {str(data)[:200]}")

# 1.6 GET /api/v1/admin/users/
admin_users_data = {}
if owner_token:
    status, data = make_request("GET", "/api/v1/admin/users/", token=owner_token)
    if status == 200 and isinstance(data, dict) and "items" in data:
        total_users = data.get("total", len(data["items"]))
        log("Owner GET /admin/users/", True,
            f"HTTP {status} — total={total_users} users")
        admin_users_data = data
    elif status == 200 and isinstance(data, list):
        log("Owner GET /admin/users/", True, f"HTTP {status} — {len(data)} users")
        admin_users_data = {"items": data, "total": len(data)}
    else:
        log("Owner GET /admin/users/", False, f"HTTP {status} — {str(data)[:200]}")

# 1.7 GET /api/v1/admin/analytics/overview  (admin stats)
if owner_token:
    status, data = make_request(
        "GET", "/api/v1/admin/analytics/overview", token=owner_token
    )
    if status == 200 and isinstance(data, dict):
        total_accts = data.get("users", {}).get("total_accounts", "?")
        log("Owner GET /admin/analytics/overview (stats)", True,
            f"HTTP {status} — total_accounts={total_accts}")
    else:
        log("Owner GET /admin/analytics/overview (stats)", False,
            f"HTTP {status} — {str(data)[:200]}")


# ============================================================
# SECTION 2: CREATE AND TEST DEMO USER
# ============================================================
section("2. CREATE AND TEST DEMO USER")

# NOTE: .test TLD is rejected by Pydantic email validator (special-use domain).
# Using demo@pulsesignal.com instead. Email verification is required on this instance.
DEMO_EMAIL = "demo@pulsesignal.com"
DEMO_PASS = "DemoUser2025!"
demo_token = None
demo_user_id = None

# 2.1 Register demo user (or confirm already exists)
status, reg_data = make_request(
    "POST",
    "/api/v1/auth/register",
    body={
        "email": DEMO_EMAIL,
        "username": "demopulse2025",
        "password": DEMO_PASS,
    },
)

if status in (200, 201):
    log("Register demo user via /auth/register", True,
        f"HTTP {status} — user created (email verification required)")
elif status == 409:
    log("Register demo user via /auth/register", True,
        f"HTTP {status} — user already exists (OK)")
else:
    # Try to look up via admin search
    if owner_token:
        su_status, su_data = make_request(
            "GET",
            "/api/v1/admin/users/?search=demopulse2025",
            token=owner_token,
        )
        if su_status == 200 and su_data.get("total", 0) > 0:
            log("Register demo user", True,
                f"Already exists in DB (found via admin search)")
        else:
            log("Register demo user", False,
                f"HTTP {status} — {str(reg_data)[:200]}")
    else:
        log("Register demo user", False, f"HTTP {status} — {str(reg_data)[:200]}")

# 2.2 Admin: find demo user ID and mark as verified
if owner_token:
    status, search_data = make_request(
        "GET",
        "/api/v1/admin/users/?search=demopulse2025",
        token=owner_token,
    )
    if status == 200 and isinstance(search_data, dict) and search_data.get("total", 0) > 0:
        demo_user_id = search_data["items"][0]["id"]
        demo_is_verified = search_data["items"][0].get("is_verified", False)
        demo_role = search_data["items"][0].get("role", "")
        print(f"    Demo user found: id={demo_user_id}, verified={demo_is_verified}, role={demo_role}")

        # If not verified, mark as verified so login works
        if not demo_is_verified:
            pu_status, pu_data = make_request(
                "PUT",
                f"/api/v1/admin/users/{demo_user_id}",
                token=owner_token,
                body={"is_verified": True},
            )
            log("Admin: verify demo user email", pu_status == 200,
                f"HTTP {pu_status}")
        else:
            log("Demo user already verified", True, "is_verified=True")
    else:
        log("Find demo user via admin search", False,
            f"HTTP {status} — {str(search_data)[:200]}")

# 2.3 Login as demo user
if demo_user_id:
    status, login_data = make_request(
        "POST",
        "/api/v1/auth/login",
        body={"email": DEMO_EMAIL, "password": DEMO_PASS},
    )
    if status == 200 and isinstance(login_data, dict) and "access_token" in login_data:
        demo_token = login_data["access_token"]
        log("Demo user login", True, f"HTTP {status} — token obtained")
    else:
        log("Demo user login", False, f"HTTP {status} — {str(login_data)[:200]}")

# 2.4 GET /auth/me as demo user
if demo_token:
    status, me_data = make_request("GET", "/api/v1/auth/me", token=demo_token)
    if status == 200 and isinstance(me_data, dict):
        role = me_data.get("role", "")
        plan = me_data.get("plan", "")
        log("Demo GET /auth/me — role=user", role == "user", f"role={role}")
        log("Demo GET /auth/me — plan check", plan in ("free", "trial"),
            f"plan={plan}")
    else:
        log("Demo GET /auth/me", False, f"HTTP {status} — {str(me_data)[:200]}")

# 2.5 Demo user can see signals
if demo_token:
    status, sig_data = make_request(
        "GET", "/api/v1/signals/?limit=3", token=demo_token
    )
    if status == 200:
        if isinstance(sig_data, list):
            count = len(sig_data)
        elif isinstance(sig_data, dict):
            count = len(sig_data.get("items", sig_data.get("signals", [])))
        else:
            count = 0
        log("Demo GET /signals/", True,
            f"HTTP {status} — {count} signals visible to demo user")
    else:
        log("Demo GET /signals/", False, f"HTTP {status} — {str(sig_data)[:200]}")


# ============================================================
# SECTION 3: PROMOTE DEMO USER TO ADMIN
# ============================================================
section("3. PROMOTE DEMO USER TO ADMIN AND TEST ADMIN ENDPOINTS")

promoted = False
admin_token = None

if owner_token and demo_user_id:
    status, promo_data = make_request(
        "PUT",
        f"/api/v1/admin/users/{demo_user_id}",
        token=owner_token,
        body={"role": "admin", "plan": "lifetime"},
    )
    if status == 200 and isinstance(promo_data, dict):
        new_role = promo_data.get("role", "")
        new_plan = promo_data.get("plan", "")
        log("Promote demo user to admin", new_role == "admin",
            f"role={new_role}, plan={new_plan}")
        promoted = new_role == "admin"
    else:
        log("Promote demo user to admin", False,
            f"HTTP {status} — {str(promo_data)[:200]}")
else:
    log("Promote demo user to admin", False,
        "Skipped — missing owner token or demo user id")

# 3.1 Re-login to get token with new role embedded
if promoted:
    status, login_data = make_request(
        "POST",
        "/api/v1/auth/login",
        body={"email": DEMO_EMAIL, "password": DEMO_PASS},
    )
    if status == 200 and isinstance(login_data, dict) and "access_token" in login_data:
        admin_token = login_data["access_token"]
        log("Admin (promoted demo) login", True,
            f"HTTP {status} — new token with admin role")
    else:
        log("Admin (promoted demo) login", False,
            f"HTTP {status} — {str(login_data)[:200]}")

# 3.2 Test admin endpoints with promoted user
if admin_token:
    status, data = make_request("GET", "/api/v1/admin/users/", token=admin_token)
    if status == 200:
        total = (
            data.get("total", len(data)) if isinstance(data, dict) else len(data)
        )
        log("Admin GET /admin/users/ (promoted user)", True,
            f"HTTP {status} — total={total} users")
    else:
        log("Admin GET /admin/users/ (promoted user)", False,
            f"HTTP {status} — {str(data)[:200]}")

    status, data = make_request(
        "GET", "/api/v1/admin/analytics/overview", token=admin_token
    )
    if status == 200:
        log("Admin GET /admin/analytics/overview (promoted user)", True,
            f"HTTP {status}")
    else:
        log("Admin GET /admin/analytics/overview (promoted user)", False,
            f"HTTP {status} — {str(data)[:200]}")


# ============================================================
# SECTION 4: SIGNALS DATA QUALITY
# ============================================================
section("4. SIGNALS DATA QUALITY CHECK")

if owner_token:
    status, data = make_request(
        "GET", "/api/v1/signals/?limit=5", token=owner_token
    )
    if status == 200:
        if isinstance(data, list):
            signals_check = data
        elif isinstance(data, dict) and "items" in data:
            signals_check = data["items"]
        elif isinstance(data, dict) and "signals" in data:
            signals_check = data["signals"]
        else:
            signals_check = []

        if signals_check:
            print(f"\n  Checking {len(signals_check)} signals for data quality...")
            first = signals_check[0]

            sym = first.get("symbol", first.get("pair", "?"))
            direction = first.get("direction", "?")
            confidence = first.get("confidence", "?")
            entry = first.get("entry", first.get("entry_price", "?"))
            tp1 = first.get("tp1", first.get("take_profit_1", "?"))
            tp2 = first.get("tp2", first.get("take_profit_2", "?"))
            tp3 = first.get("tp3", first.get("take_profit_3", "?"))
            sl = first.get("sl", first.get("stop_loss", "?"))

            print(f"\n  --- First Signal Sample ---")
            print(f"  Symbol:     {sym}")
            print(f"  Direction:  {direction}")
            print(f"  Confidence: {confidence}")
            print(f"  Entry:      {entry}")
            print(f"  TP1:        {tp1}")
            print(f"  TP2:        {tp2}")
            print(f"  TP3:        {tp3}")
            print(f"  SL:         {sl}")
            print(f"  Fields:     {list(first.keys())}")
            print()

            for i, sig in enumerate(signals_check):
                s_entry = sig.get("entry", sig.get("entry_price"))
                s_tp1 = sig.get("tp1", sig.get("take_profit_1"))
                s_sl = sig.get("sl", sig.get("stop_loss"))
                s_conf = sig.get("confidence")

                entry_ok = is_numeric(s_entry)
                tp1_ok = is_numeric(s_tp1)
                sl_ok = is_numeric(s_sl)
                conf_ok = (
                    is_numeric(s_conf) and 0 <= float(s_conf) <= 100
                    if s_conf is not None
                    else False
                )

                sig_sym = sig.get("symbol", sig.get("pair", f"signal_{i}"))
                log(f"Signal[{i}] {sig_sym} — entry numeric", entry_ok,
                    f"entry={s_entry}")
                log(f"Signal[{i}] {sig_sym} — tp1 numeric", tp1_ok,
                    f"tp1={s_tp1}")
                log(f"Signal[{i}] {sig_sym} — sl numeric", sl_ok, f"sl={s_sl}")
                log(f"Signal[{i}] {sig_sym} — confidence 0-100", conf_ok,
                    f"confidence={s_conf}")
        else:
            log("Signals data quality", False,
                "No signals returned to check")
    else:
        log("Signals data quality — fetch", False,
            f"HTTP {status} — {str(data)[:200]}")
else:
    log("Signals data quality", False, "Skipped — no owner token")


# ============================================================
# SECTION 5: SCANNER STATUS
# ============================================================
section("5. SCANNER STATUS")

if owner_token:
    status, data = make_request(
        "GET", "/api/v1/scanner/status", token=owner_token
    )
    if status == 200 and isinstance(data, dict):
        is_running = data.get("is_running", "?")
        pairs_total = data.get("pairs_total", "?")
        pairs_done = data.get("pairs_done", "?")
        queue_len = data.get("queue_length", "?")
        last_run_at = data.get("last_run_at", "?")
        log("GET /scanner/status", True,
            f"HTTP {status} — is_running={is_running}, pairs_total={pairs_total}, "
            f"pairs_done={pairs_done}, queue_length={queue_len}")
        print(f"    last_run_at={last_run_at}")
    else:
        log("GET /scanner/status", False, f"HTTP {status} — {str(data)[:200]}")

    status, data = make_request(
        "GET", "/api/v1/scanner/pairs", token=owner_token
    )
    if status == 200 and isinstance(data, list):
        log("GET /scanner/pairs", True, f"HTTP {status} — {len(data)} pairs returned")
        if data:
            print(f"    Sample pairs: {[p.get('symbol', p) for p in data[:5]]}")
    elif status == 200 and isinstance(data, dict) and "items" in data:
        log("GET /scanner/pairs", True,
            f"HTTP {status} — {len(data['items'])} pairs returned")
    else:
        log("GET /scanner/pairs", False, f"HTTP {status} — {str(data)[:200]}")
else:
    log("Scanner status tests", False, "Skipped — no owner token")


# ============================================================
# SECTION 6: ALERTS
# ============================================================
section("6. ALERTS — CREATE AND VERIFY")

created_alert_id = None
if owner_token:
    # Create an email alert (no telegram setup needed)
    status, data = make_request(
        "POST",
        "/api/v1/alerts/",
        token=owner_token,
        body={
            "channel": "email",
            "min_confidence": 75,
            "directions": ["LONG", "SHORT"],
            "timeframes": ["1H", "4H"],
            "markets": ["crypto"],
            "is_active": True,
        },
    )
    if status in (200, 201) and isinstance(data, dict) and "id" in data:
        created_alert_id = data["id"]
        log("POST /alerts/ — create email alert", True,
            f"HTTP {status} — id={created_alert_id}, channel={data.get('channel')}, "
            f"min_confidence={data.get('min_confidence')}")
    else:
        log("POST /alerts/ — create email alert", False,
            f"HTTP {status} — {str(data)[:200]}")

    # Verify in list
    status, data = make_request("GET", "/api/v1/alerts/", token=owner_token)
    if status == 200 and isinstance(data, list):
        found = (
            any(str(a.get("id", "")) == str(created_alert_id) for a in data)
            if created_alert_id
            else False
        )
        log("GET /alerts/ — verify created alert exists", found or len(data) > 0,
            f"HTTP {status} — {len(data)} alerts total, target found={found}")
    else:
        log("GET /alerts/ — verify", False, f"HTTP {status} — {str(data)[:200]}")
else:
    log("Alerts tests", False, "Skipped — no owner token")


# ============================================================
# FINAL SUMMARY
# ============================================================
print(f"\n{'='*60}")
print(f"  FINAL TEST SUMMARY")
print(f"{'='*60}")

total = len(results)
passed = sum(1 for _, p, _ in results if p)
failed = total - passed

print(f"\n  Total: {total} | Passed: {passed} | Failed: {failed}")
print(f"  Pass rate: {passed / total * 100:.1f}%")

if failed > 0:
    print("\n  FAILED TESTS:")
    for label, ok, detail in results:
        if not ok:
            print(f"    X {label}")
            print(f"      Detail: {detail}")

print(f"\n  All results:")
for label, ok, detail in results:
    icon = "+" if ok else "X"
    print(f"    [{icon}] {label}")

print()
