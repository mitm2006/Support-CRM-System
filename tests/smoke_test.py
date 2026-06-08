"""
tests/smoke_test.py
-------------------
Basic smoke tests against the running local server.
Run with: python tests/smoke_test.py
(Server must be running on http://127.0.0.1:8000)
"""

import json
import sys
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"
PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
errors = []


def req(method, path, body=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(url, data=data,
                                headers={"Content-Type": "application/json"} if data else {},
                                method=method)
    with urllib.request.urlopen(r) as resp:
        return resp.status, json.loads(resp.read())


def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}" + (f" — {detail}" if detail else ""))
        errors.append(label)


print("\n=== Datastraw CRM — Smoke Tests ===\n")

# ── 1. Create Ticket ───────────────────────────────────────────────────────
print("1. POST /api/tickets — Create ticket")
status, data = req("POST", "/api/tickets", {
    "customer_name": "Rahul Sharma",
    "customer_email": "rahul@example.com",
    "subject": "Order not received",
    "description": "Placed order #1234 five days ago."
})
check("Status 201", status == 201, f"got {status}")
check("Has id field", "id" in data, str(data))
check("ticket_id format TKT-NNN", data.get("ticket_id", "").startswith("TKT-"), data.get("ticket_id"))
check("has created_at", "created_at" in data)
TID = data["id"]
print(f"     → Created {data.get('ticket_id')} (id={TID})")

# ── 2. Create second ticket ────────────────────────────────────────────────
print("\n2. POST /api/tickets — Create second ticket")
status2, data2 = req("POST", "/api/tickets", {
    "customer_name": "Priya Mehta",
    "customer_email": "priya@example.com",
    "subject": "Billing issue"
})
check("Status 201", status2 == 201)
check("ticket_id increments", data2.get("id", 0) > TID, f"id={data2.get('id')}")

# ── 3. List All Tickets ────────────────────────────────────────────────────
print("\n3. GET /api/tickets — List all")
status, tickets = req("GET", "/api/tickets")
check("Status 200", status == 200)
check("Returns a list", isinstance(tickets, list))
check("At least 2 tickets", len(tickets) >= 2, f"got {len(tickets)}")
check("ticket_id present in list items", all("ticket_id" in t for t in tickets))

# ── 4. Search ─────────────────────────────────────────────────────────────
print("\n4. GET /api/tickets?search=Rahul — Search")
status, searched = req("GET", "/api/tickets?search=Rahul")
check("Status 200", status == 200)
check("Search returns match", len(searched) >= 1, f"got {len(searched)}")
check("Result matches search term", any("Rahul" in t["customer_name"] for t in searched))

# ── 5. Search by TKT-NNN ──────────────────────────────────────────────────
print("\n5. GET /api/tickets?search=TKT-001 — Search by ticket ID")
status, by_id = req("GET", f"/api/tickets?search=TKT-{TID:03d}")
check("Status 200", status == 200)
check("Returns 1 result by TKT-ID", len(by_id) >= 1)

# ── 6. Status Filter ──────────────────────────────────────────────────────
print("\n6. GET /api/tickets?status=Open — Filter by status")
status, open_tickets = req("GET", "/api/tickets?status=Open")
check("Status 200", status == 200)
check("All results are Open", all(t["status"] == "Open" for t in open_tickets), str([t["status"] for t in open_tickets]))

# ── 7. Ticket Detail ──────────────────────────────────────────────────────
print("\n7. GET /api/tickets/{id} — Ticket detail")
status, detail = req("GET", f"/api/tickets/{TID}")
check("Status 200", status == 200)
check("ticket_id matches", detail.get("ticket_id") == f"TKT-{TID:03d}")
check("customer_name correct", detail.get("customer_name") == "Rahul Sharma")
check("notes is a list", isinstance(detail.get("notes"), list))
check("description present", "description" in detail)

# ── 8. Update Status + Note ────────────────────────────────────────────────
print("\n8. PUT /api/tickets/{id} — Update status + add note")
status, updated = req("PUT", f"/api/tickets/{TID}", {
    "status": "In Progress",
    "note_text": "Escalated to warehouse team."
})
check("Status 200", status == 200)
check("success=true", updated.get("success") is True)
check("has updated_at", "updated_at" in updated)

# ── 9. Verify update persisted ────────────────────────────────────────────
print("\n9. GET /api/tickets/{id} — Verify update & note saved")
status, detail2 = req("GET", f"/api/tickets/{TID}")
check("Status 200", status == 200)
check("Status changed to In Progress", detail2.get("status") == "In Progress", detail2.get("status"))
check("Note saved (1 note)", len(detail2.get("notes", [])) == 1, f"got {len(detail2.get('notes', []))}")
check("Note text correct", detail2["notes"][0]["note_text"] == "Escalated to warehouse team.")

# ── 10. Filter In Progress ─────────────────────────────────────────────────
print("\n10. GET /api/tickets?status=In+Progress — Filter updated ticket")
status, in_prog = req("GET", "/api/tickets?status=In+Progress")
check("Status 200", status == 200)
check("Filtered result includes updated ticket", any(t["id"] == TID for t in in_prog))

# ── 11. 404 on unknown id ─────────────────────────────────────────────────
print("\n11. GET /api/tickets/99999 — 404 for missing ticket")
try:
    req("GET", "/api/tickets/99999")
    check("Should have returned 404", False)
except urllib.error.HTTPError as e:
    check("Returns 404 for missing ticket", e.code == 404, f"got {e.code}")

# ── 12. Page routes ───────────────────────────────────────────────────────
print("\n12. Page routes — HTML responses")
for path in ["/", "/create", "/detail"]:
    r = urllib.request.urlopen(BASE + path)
    check(f"GET {path} returns 200", r.status == 200)

# ── Summary ────────────────────────────────────────────────────────────────
print(f"\n{'='*40}")
if errors:
    print(f"\033[91mFAILED — {len(errors)} test(s) failed:\033[0m")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"\033[92mALL TESTS PASSED\033[0m")
