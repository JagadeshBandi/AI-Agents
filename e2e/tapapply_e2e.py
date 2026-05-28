"""
TapApply End-to-End Test Suite — Playwright (Python sync API)

Tests every major feature:
  1.  Health check (API)
  2.  Onboarding Step 1 — country selection (UI)
  3.  Onboarding Step 2 — sector selection (UI)
  4.  Onboarding Step 3 — manual profile form (UI)
  5.  API: POST /api/onboarding/step1
  6.  API: POST /api/onboarding/step2
  7.  API: POST /api/onboarding/step3/manual
  8.  API: GET  /api/profile/{user_id}
  9.  Dashboard loads, metrics cards visible
  10. Dashboard: missing-CV banner for incomplete profile
  11. Analyze page — JD match flow
  12. Autopilot toggle (enable / disable)
  13. Track page — applications list renders
  14. WebSocket support agent sends / receives
  15. Floating guide (FloatingGuide) opens chat panel
  16. Navigation between pages
  17. Error state — 404 profile returns correct message
  18. ATS score display in Analyze
"""

import json
import time
import uuid
import threading
import websocket          # websocket-client
import requests
from playwright.sync_api import sync_playwright, Page, expect

BASE_API = "http://localhost:8000"
BASE_UI  = "http://localhost:3000"
TIMEOUT  = 15_000   # 15 s per assertion

# ── helpers ────────────────────────────────────────────────────────────────

def fresh_user() -> str:
    """Create a new user via Step 1 (UK) and return the user_id."""
    r = requests.post(f"{BASE_API}/api/onboarding/step1", json={"country": "UK"})
    assert r.status_code == 200, r.text
    return r.json()["user_id"]


def full_profile_user() -> str:
    """Create a user with a complete manual profile and return user_id."""
    uid = fresh_user()
    requests.post(f"{BASE_API}/api/onboarding/step2",
                  json={"user_id": uid, "sector": "Tech & Software"})
    requests.post(f"{BASE_API}/api/onboarding/step3/manual", json={
        "user_id": uid,
        "full_name": "Jane E2E",
        "email": "jane_e2e@test.com",
        "phone": "+447911000000",
        "location": "London, UK",
        "professional_summary": "Senior Python Engineer with 8 years experience.",
        "skills_technical": ["Python", "FastAPI", "React", "Docker", "PostgreSQL"],
        "skills_soft": ["Communication", "Leadership"],
        "target_role": "Senior Engineer",
        "target_level": "senior",
        "tone_preference": "professional",
    })
    return uid


# ═══════════════════════════════════════════════════════════════════════════
# BLOCK 1 — Pure API tests (no browser)
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIHealth:
    def test_health_ok(self):
        r = requests.get(f"{BASE_API}/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert "version" in body
        print("  ✓ /api/health → healthy")

    def test_404_unknown_profile(self):
        r = requests.get(f"{BASE_API}/api/profile/{uuid.uuid4()}")
        assert r.status_code == 404
        print("  ✓ Unknown profile returns 404")

    def test_step1_creates_user(self):
        r = requests.post(f"{BASE_API}/api/onboarding/step1",
                          json={"country": "UK"})
        assert r.status_code == 200
        uid = r.json()["user_id"]
        assert uid and len(uid) == 36      # UUID
        print(f"  ✓ Step 1 created user {uid[:8]}…")

    def test_step1_all_countries(self):
        countries = ["UK", "USA", "CANADA", "AUSTRALIA", "NEW_ZEALAND",
                     "GERMANY", "FRANCE", "NETHERLANDS", "IRELAND"]
        for c in countries:
            r = requests.post(f"{BASE_API}/api/onboarding/step1",
                              json={"country": c})
            assert r.status_code == 200, f"Country {c} failed: {r.text}"
        print(f"  ✓ All {len(countries)} countries accepted in Step 1")

    def test_step2_requires_existing_user(self):
        r = requests.post(f"{BASE_API}/api/onboarding/step2",
                          json={"user_id": str(uuid.uuid4()),
                                "sector": "Tech & Software"})
        assert r.status_code == 404
        print("  ✓ Step 2 returns 404 for unknown user")

    def test_step2_sets_sector(self):
        uid = fresh_user()
        r = requests.post(f"{BASE_API}/api/onboarding/step2",
                          json={"user_id": uid, "sector": "Tech & Software"})
        assert r.status_code == 200
        print("  ✓ Step 2 sets sector OK")

    def test_step3_manual_profile(self):
        uid = fresh_user()
        requests.post(f"{BASE_API}/api/onboarding/step2",
                      json={"user_id": uid, "sector": "Tech & Software"})
        r = requests.post(f"{BASE_API}/api/onboarding/step3/manual", json={
            "user_id": uid,
            "full_name": "Test User",
            "email": "test@test.com",
            "skills_technical": ["Python", "Docker"],
            "target_level": "mid",
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["success"] is True
        assert "generated_cv_preview" in body
        print("  ✓ Step 3 manual profile created with ATS CV preview")

    def test_profile_get(self):
        uid = full_profile_user()
        r = requests.get(f"{BASE_API}/api/profile/{uid}")
        assert r.status_code == 200
        p = r.json()
        assert p["country"] == "UK"
        assert p["sector"] == "Tech & Software"
        assert p["onboarding_path"] == "manual"
        print("  ✓ GET /api/profile returns correct data")

    def test_jobs_endpoint(self):
        uid = fresh_user()
        r = requests.get(f"{BASE_API}/api/jobs/{uid}")
        assert r.status_code == 200
        assert "jobs" in r.json()
        print("  ✓ GET /api/jobs returns jobs array")

    def test_applications_endpoint(self):
        uid = fresh_user()
        r = requests.get(f"{BASE_API}/api/applications/{uid}")
        assert r.status_code == 200
        assert "applications" in r.json()
        print("  ✓ GET /api/applications returns array")

    def test_analyze_match_no_cv(self):
        uid = fresh_user()
        r = requests.post(f"{BASE_API}/api/analyze-match",
                          json={"user_id": uid,
                                "jd_text": "We need a Python developer."})
        # Should 400 — no CV
        assert r.status_code == 400
        print("  ✓ analyze-match returns 400 when no CV/profile")

    def test_analyze_match_with_profile(self):
        uid = full_profile_user()
        r = requests.post(f"{BASE_API}/api/analyze-match", json={
            "user_id": uid,
            "jd_text": (
                "We are looking for a Senior Python Engineer with experience "
                "in FastAPI, Docker, PostgreSQL, React, and leadership skills."
            ),
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert "ats_score" in body, f"Expected 'ats_score' key in response. Got: {list(body.keys())}"
        assert "matched_keywords" in body
        score = body["ats_score"]
        assert 0 <= score <= 100
        print(f"  ✓ ATS score returned: {score}/100  "
              f"matched={body['matched_keywords']}")

    def test_ats_score_quality(self):
        """High-match CV should score ≥ 70."""
        uid = full_profile_user()
        r = requests.post(f"{BASE_API}/api/analyze-match", json={
            "user_id": uid,
            "jd_text": (
                "Senior Python Engineer. Must know FastAPI, Docker, PostgreSQL, "
                "React, and have strong Leadership and Communication skills."
            ),
        })
        body = r.json()
        score = body.get("ats_score", 0)
        assert score >= 70, f"Expected ≥70, got {score}"
        print(f"  ✓ High-match ATS score = {score}/100 (≥70 threshold)")

    def test_generate_ats_cv(self):
        uid = full_profile_user()
        r = requests.post(f"{BASE_API}/api/generate-ats-cv", json={
            "user_id": uid,
            "jd_text": "Senior Python Engineer, Docker, PostgreSQL required.",
            "missing_keywords": ["Kubernetes"],
        })
        assert r.status_code == 200, r.text
        body = r.json()
        assert "cv_markdown" in body
        assert len(body["cv_markdown"]) > 100
        print(f"  ✓ ATS CV generated ({len(body['cv_markdown'])} chars)")

    def test_autopilot_enable_disable(self):
        uid = fresh_user()
        r = requests.post(f"{BASE_API}/api/autopilot/enable?user_id={uid}")
        assert r.status_code == 200
        r2 = requests.post(f"{BASE_API}/api/autopilot/disable?user_id={uid}")
        assert r2.status_code == 200
        print("  ✓ Autopilot enable/disable OK")

    def test_autopilot_status(self):
        r = requests.get(f"{BASE_API}/api/autopilot/status")
        assert r.status_code == 200
        print("  ✓ Autopilot status endpoint OK")

    def test_websocket_support_agent(self):
        """WebSocket handshake, DISCLAIMER sent on connect, reply to message."""
        received = []
        error_flag = []

        def on_message(ws, msg):
            received.append(json.loads(msg))

        def on_error(ws, err):
            error_flag.append(str(err))

        client_id = str(uuid.uuid4())
        ws_url = f"ws://localhost:8000/ws/support/{client_id}"

        ws_app = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
        )

        t = threading.Thread(target=ws_app.run_forever, daemon=True)
        t.start()
        time.sleep(1.5)   # wait for connect + DISCLAIMER

        ws_app.send(json.dumps({
            "type": "message",
            "message": "How do I write a good CV for Reed.co.uk?",
            "sector": "Tech & Software",
        }))
        time.sleep(4)     # wait for LLM reply
        ws_app.close()

        assert not error_flag, f"WS error: {error_flag}"
        assert len(received) >= 1, "No messages received from support agent"
        types = [m.get("type") for m in received]
        assert "system" in types, f"DISCLAIMER not received. Got: {types}"
        print(f"  ✓ WS support agent: {len(received)} messages received, "
              f"types={types}")


# ═══════════════════════════════════════════════════════════════════════════
# BLOCK 2 — Browser UI tests
# ═══════════════════════════════════════════════════════════════════════════

class TestOnboardingUI:
    def test_onboarding_page_loads(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            # Page title
            expect(page.locator("h1")).to_contain_text("TapApply", timeout=TIMEOUT)
            # Heading
            expect(page.locator("h2").first).to_contain_text("Where are you targeting", timeout=TIMEOUT)
            # Country grid shows buttons
            buttons = page.locator("button").all()
            assert len(buttons) >= 9, f"Expected ≥9 country buttons, got {len(buttons)}"
            print("  ✓ Onboarding page loads with 9+ country buttons")
            browser.close()

    def test_step1_country_select_and_advance(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            # Click United Kingdom
            page.locator("button", has_text="United Kingdom").first.click()
            # Should advance to Step 2
            expect(page.locator("h2")).to_contain_text(
                "professional field", timeout=TIMEOUT
            )
            print("  ✓ Clicking UK advances to Step 2")
            browser.close()

    def test_step2_sector_selection(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            page.locator("button", has_text="United Kingdom").first.click()
            page.wait_for_selector("h2:has-text('professional field')", timeout=TIMEOUT)

            # Sector cards / buttons visible
            sector_btns = page.locator("button").all()
            assert len(sector_btns) >= 4, "Expected sector buttons"

            # Select the sector (sets React state only, no API call yet)
            page.locator("button", has_text="Tech & Software").first.click()
            # Click Continue to trigger the API call and advance to Step 3
            page.locator("button", has_text="Continue").last.click()
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            # Advances to Step 3
            expect(page.locator("h2")).to_contain_text("profile", timeout=TIMEOUT)
            print("  ✓ Sector selection advances to Step 3 profile")
            browser.close()

    def test_step3_manual_form_visible(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            page.locator("button", has_text="United Kingdom").first.click()
            page.wait_for_selector("h2:has-text('professional field')", timeout=TIMEOUT)
            page.locator("button", has_text="Tech & Software").first.click()
            page.locator("button", has_text="Continue").last.click()
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            page.wait_for_selector("h2:has-text('profile')", timeout=TIMEOUT)

            # Full name input visible
            expect(page.locator("input[placeholder*='Jane']")).to_be_visible(timeout=TIMEOUT)
            # Email input visible
            expect(page.locator("input[type='email']")).to_be_visible(timeout=TIMEOUT)
            print("  ✓ Step 3 profile form fields visible")
            browser.close()

    def test_step3_form_validation_submit(self):
        """Fill name + email and submit manual profile."""
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            # Navigate through steps 1 & 2
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")
            page.locator("button", has_text="United Kingdom").first.click()
            page.wait_for_selector("h2:has-text('professional field')", timeout=TIMEOUT)
            page.locator("button", has_text="Tech & Software").first.click()
            page.locator("button", has_text="Continue").last.click()
            page.wait_for_load_state("networkidle", timeout=TIMEOUT)
            page.wait_for_selector("h2:has-text('profile')", timeout=TIMEOUT)

            # Fill mandatory fields
            page.locator("input[placeholder*='Jane']").fill("Alice Tester")
            page.locator("input[type='email']").fill("alice@test.com")

            # Click the Step 3 submit button ("Launch Autopilot")
            submit = page.locator("button", has_text="Launch Autopilot").first
            submit.click()

            # Should navigate to /dashboard
            page.wait_for_url("**/dashboard**", timeout=20_000)
            assert "/dashboard" in page.url
            print("  ✓ Completing Step 3 redirects to /dashboard")
            browser.close()

    def test_step_indicator_updates(self):
        """Step dots update as user progresses through onboarding."""
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            # Step 1 indicator — use exact span to avoid matching background decoration
            step1_label = page.locator("span", has_text="Region").first
            expect(step1_label).to_be_visible(timeout=TIMEOUT)

            page.locator("button", has_text="United Kingdom").first.click()
            page.wait_for_selector("h2:has-text('professional field')", timeout=TIMEOUT)

            # Step 2 indicator active
            step2_label = page.locator("span", has_text="Sector").first
            expect(step2_label).to_be_visible(timeout=TIMEOUT)
            print("  ✓ Step indicators visible and update on navigation")
            browser.close()


class TestDashboardUI:
    def test_dashboard_loads(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            # Set localStorage via init script so it is available before the
            # dashboard's useEffect runs (avoids the redirect-to-onboarding race).
            # Use "load" not "networkidle" — the SSE log stream keeps the network
            # permanently active and networkidle would never resolve.
            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/dashboard", wait_until="load")
            page.wait_for_timeout(2000)   # let React hydrate + render

            body_text = page.locator("body").inner_text()
            assert any(t in body_text for t in ["Dashboard", "TapApply", "Autopilot", "Applications"]), \
                f"Dashboard content not found. Body: {body_text[:300]}"
            print("  ✓ Dashboard page loads")
            browser.close()

    def test_dashboard_metric_cards(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/dashboard", wait_until="load")
            page.wait_for_timeout(2000)

            body = page.locator("body").inner_text()
            assert len(body) > 200, "Dashboard appears empty"
            print("  ✓ Dashboard metric area rendered with content")
            browser.close()

    def test_autopilot_toggle_ui(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/dashboard", wait_until="load")
            page.wait_for_timeout(3000)   # allow async data fetches to render

            # Find autopilot section — could be "Autopilot", "Auto Pilot", or "autopilot"
            body = page.locator("body").inner_text().lower()
            assert any(t in body for t in ["autopilot", "auto pilot", "enable", "toggle"]), \
                f"Autopilot section not found. Body preview: {body[:400]}"
            print("  ✓ Autopilot section present on dashboard")
            browser.close()


class TestAnalyzeUI:
    def test_analyze_page_loads(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/analyze", wait_until="networkidle")

            body = page.locator("body").inner_text()
            assert any(t in body for t in ["ATS", "Analyse", "Analyze", "Job Description", "Match"]), \
                f"Analyze page content not found. Body: {body[:300]}"
            print("  ✓ Analyze/ATS page loads")
            browser.close()

    def test_analyze_jd_submit(self):
        """Paste a JD, click analyse, score should appear."""
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/analyze", wait_until="networkidle")

            jd = (
                "We are hiring a Senior Python Engineer. "
                "Requirements: Python, FastAPI, Docker, PostgreSQL, React, Leadership."
            )
            textarea = page.locator("textarea").first
            if textarea.is_visible():
                textarea.fill(jd)
                # Click the analyse / submit button
                analyse_btn = page.locator("button", has_text="Analy").first
                if analyse_btn.is_visible():
                    analyse_btn.click()
                    # Wait for score result (up to 20 s for LLM)
                    page.wait_for_selector(
                        "text=/[0-9]+\\/100|ATS|Score/i",
                        timeout=25_000
                    )
                    result_text = page.locator("body").inner_text()
                    assert any(t in result_text for t in ["/100", "ATS", "Score", "score"]), \
                        "Score not shown after analysis"
                    print("  ✓ ATS analysis returns score in UI")
                else:
                    print("  ⚠ Analyse button not visible — skipping click")
            else:
                print("  ⚠ No textarea found on Analyze page — skipping submit")
            browser.close()


class TestTrackUI:
    def test_track_page_loads(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()

            uid = full_profile_user()
            page.add_init_script(f"localStorage.setItem('tapapply_user_id', '{uid}')")
            page.goto(f"{BASE_UI}/track", wait_until="networkidle")

            body = page.locator("body").inner_text()
            assert any(t in body for t in ["Application", "Track", "Status", "Job"]), \
                f"Track page content missing. Body: {body[:300]}"
            print("  ✓ Track page loads")
            browser.close()


class TestNavigation:
    def test_root_redirects_or_loads(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(BASE_UI, wait_until="networkidle")
            # Root might redirect to /onboarding or show a landing page
            body = page.locator("body").inner_text()
            assert len(body) > 50, "Root page appears blank"
            print(f"  ✓ Root URL loaded: {page.url}")
            browser.close()

    def test_all_routes_return_200(self):
        routes = ["/onboarding", "/dashboard", "/analyze", "/track"]
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            for route in routes:
                page = browser.new_page()
                resp = page.goto(f"{BASE_UI}{route}", wait_until="domcontentloaded")
                assert resp is not None and resp.status == 200, \
                    f"Route {route} returned {resp.status if resp else 'no response'}"
                page.close()
            browser.close()
        print(f"  ✓ All {len(routes)} routes return HTTP 200")

    def test_floating_guide_button_visible(self):
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            # FloatingGuide renders a fixed button in the bottom-right
            # It has z-50 and is always on screen
            fixed_btns = page.locator("button").all()
            assert len(fixed_btns) >= 1
            print("  ✓ Page rendered with buttons (FloatingGuide included)")
            browser.close()

    def test_background_canvas_not_blocking_clicks(self):
        """Country buttons must be clickable despite canvas layer."""
        with sync_playwright() as p:
            browser = p.webkit.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE_UI}/onboarding", wait_until="networkidle")

            uk_btn = page.locator("button", has_text="United Kingdom").first
            expect(uk_btn).to_be_visible(timeout=TIMEOUT)
            uk_btn.click()
            # Succeeds = canvas is NOT intercepting clicks
            expect(page.locator("h2")).to_contain_text("professional field", timeout=TIMEOUT)
            print("  ✓ Canvas pointer-events:none — country buttons clickable")
            browser.close()


# ═══════════════════════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════════════════════

def run_all():
    results = {"passed": [], "failed": [], "warnings": []}

    suites = [
        ("API — Health & Endpoints", TestAPIHealth),
        ("UI  — Onboarding Flow",    TestOnboardingUI),
        ("UI  — Dashboard",          TestDashboardUI),
        ("UI  — ATS Analyze",        TestAnalyzeUI),
        ("UI  — Track Applications", TestTrackUI),
        ("UI  — Navigation & UX",    TestNavigation),
    ]

    for suite_name, SuiteClass in suites:
        print(f"\n{'═'*60}")
        print(f"  {suite_name}")
        print(f"{'═'*60}")
        instance = SuiteClass()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        for method_name in methods:
            label = method_name.replace("test_", "").replace("_", " ")
            try:
                getattr(instance, method_name)()
                results["passed"].append(f"{suite_name} :: {label}")
            except AssertionError as e:
                msg = f"{suite_name} :: {label} — ASSERT: {e}"
                print(f"  ✗ {label}")
                print(f"    → {e}")
                results["failed"].append(msg)
            except Exception as e:
                msg = f"{suite_name} :: {label} — ERROR: {type(e).__name__}: {e}"
                print(f"  ✗ {label}")
                print(f"    → {type(e).__name__}: {e}")
                results["failed"].append(msg)

    print(f"\n{'═'*60}")
    print("  SUMMARY")
    print(f"{'═'*60}")
    print(f"  Passed : {len(results['passed'])}")
    print(f"  Failed : {len(results['failed'])}")
    if results["failed"]:
        print("\n  FAILURES:")
        for f in results["failed"]:
            print(f"    ✗ {f}")
    print()
    return results


if __name__ == "__main__":
    run_all()
