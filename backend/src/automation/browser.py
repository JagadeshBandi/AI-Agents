"""
Playwright stealth browser configuration.

Implements humanized interaction patterns to simulate native browser behaviour:
variable typing speed, non-linear scroll velocity, randomized click delays,
and robots.txt compliance. Proxy routing is applied when credentials are set.

IMPORTANT: All automation strictly observes robots.txt Disallow directives and
Crawl-delay values. No private API endpoints or internal data objects are accessed.
Only public-facing job listing pages are navigated.
"""

import asyncio
import random
import httpx
from typing import Optional
from urllib.parse import urlparse


HUMANIZED = {
    "typing_min_ms": 50,
    "typing_max_ms": 180,
    "scroll_pause_min_ms": 300,
    "scroll_pause_max_ms": 1200,
    "click_delay_min_ms": 80,
    "click_delay_max_ms": 350,
    "page_load_wait_ms": 2000,
    "post_submit_wait_ms": 3000,
}

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

_ROBOTS_CACHE: dict = {}


async def fetch_robots_txt(domain: str) -> dict:
    """
    Fetches and parses the robots.txt for a domain.
    Returns a dict with 'disallowed_paths' and 'crawl_delay_seconds'.
    Cached in-process for the lifetime of the server.
    """
    if domain in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[domain]

    result = {"disallowed_paths": [], "crawl_delay_seconds": 2}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://{domain}/robots.txt")
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            result["disallowed_paths"].append(path)
                    elif line.lower().startswith("crawl-delay:"):
                        try:
                            result["crawl_delay_seconds"] = float(line.split(":", 1)[1].strip())
                        except ValueError:
                            pass
    except Exception:
        pass

    _ROBOTS_CACHE[domain] = result
    return result


def is_path_allowed(robots: dict, path: str) -> bool:
    for disallowed in robots["disallowed_paths"]:
        if disallowed and path.startswith(disallowed):
            return False
    return True


async def get_browser_context(playwright, proxy_url: Optional[str] = None):
    """
    Returns a Playwright browser context configured with:
    - Randomized user agent
    - Realistic viewport dimensions
    - Geolocation, timezone, and locale matching the target region
    - Optional residential proxy routing
    - navigator.webdriver = false (via init script)
    """
    launch_kwargs = {"headless": True}
    if proxy_url:
        launch_kwargs["proxy"] = {"server": proxy_url}

    browser = await playwright.chromium.launch(**launch_kwargs)

    viewport = random.choice([
        {"width": 1920, "height": 1080},
        {"width": 1440, "height": 900},
        {"width": 1366, "height": 768},
        {"width": 2560, "height": 1440},
    ])

    context = await browser.new_context(
        user_agent=random.choice(_USER_AGENTS),
        viewport=viewport,
        locale="en-GB",
        timezone_id="Europe/London",
        java_script_enabled=True,
        accept_downloads=False,
    )

    # Mask automation signals
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-GB', 'en'] });
        window.chrome = { runtime: {} };
    """)

    return browser, context


async def type_humanized(page, selector: str, text: str) -> None:
    """Types into an element with random per-character delays."""
    await page.click(selector)
    await asyncio.sleep(random.uniform(0.1, 0.3))
    for char in text:
        await page.keyboard.type(char)
        delay = random.randint(HUMANIZED["typing_min_ms"], HUMANIZED["typing_max_ms"])
        await asyncio.sleep(delay / 1000)


async def scroll_humanized(page, target_y: int = 800) -> None:
    """Scrolls in non-linear increments to simulate human reading behaviour."""
    current_y = 0
    while current_y < target_y:
        step = random.randint(80, 250)
        current_y = min(current_y + step, target_y)
        await page.evaluate(f"window.scrollTo(0, {current_y})")
        pause = random.randint(HUMANIZED["scroll_pause_min_ms"], HUMANIZED["scroll_pause_max_ms"])
        await asyncio.sleep(pause / 1000)


async def click_humanized(page, selector: str) -> None:
    """Waits a natural delay before clicking to avoid instant-click bot signatures."""
    delay = random.randint(HUMANIZED["click_delay_min_ms"], HUMANIZED["click_delay_max_ms"])
    await asyncio.sleep(delay / 1000)
    await page.click(selector)


async def wait_for_page(page, delay_ms: Optional[int] = None) -> None:
    ms = delay_ms or HUMANIZED["page_load_wait_ms"]
    jitter = random.randint(-200, 400)
    await asyncio.sleep(max(500, ms + jitter) / 1000)
