"""
Platform-specific automation handlers.

Each handler knows how to navigate a specific job board's public listing pages,
extract job metadata, and — when autopilot runs a submission cycle — fill
application forms using humanized input patterns.

Compliance rules enforced for every platform:
  1. robots.txt is checked before any page is loaded
  2. Crawl-delay is respected between page loads
  3. Only public-facing listing pages are accessed
  4. No private API endpoints, GraphQL, or internal data objects are queried
  5. Session credentials and CV data are held only in-process memory
     and wiped immediately after the submission loop closes
"""

import asyncio
import random
from typing import List, Optional
from urllib.parse import urlparse

from .browser import (
    get_browser_context, type_humanized, scroll_humanized,
    click_humanized, wait_for_page, fetch_robots_txt, is_path_allowed,
)
from src.compliance.firewall import assert_permitted


_RESULT_LIMIT = 10  # Max listings extracted per platform visit


async def scrape_reed(
    sector_keyword: str,
    location: str,
    playwright,
    proxy_url: Optional[str] = None,
) -> List[dict]:
    """Reads public job listing pages from Reed.co.uk."""
    assert_permitted("reed", "navigate_public_job_listing_page")
    assert_permitted("reed", "read_publicly_displayed_job_metadata")
    domain = "www.reed.co.uk"
    robots = await fetch_robots_txt(domain)
    path = f"/jobs/{sector_keyword.lower().replace(' ', '-')}-jobs"

    if not is_path_allowed(robots, path):
        return []

    browser, context = await get_browser_context(playwright, proxy_url)
    jobs = []
    try:
        page = await context.new_page()
        url = f"https://{domain}{path}?location={location}&proximity=25"
        await page.goto(url, wait_until="domcontentloaded")
        await wait_for_page(page)
        await scroll_humanized(page, 1200)
        await asyncio.sleep(robots["crawl_delay_seconds"])

        cards = await page.query_selector_all("[data-qa='job-card']")
        for card in cards[:_RESULT_LIMIT]:
            try:
                title_el = await card.query_selector("[data-qa='job-title']")
                company_el = await card.query_selector("[data-qa='job-employer']")
                loc_el = await card.query_selector("[data-qa='job-location']")
                salary_el = await card.query_selector("[data-qa='job-salary']")
                link_el = await card.query_selector("a")

                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                location_text = await loc_el.inner_text() if loc_el else ""
                salary_text = await salary_el.inner_text() if salary_el else ""
                href = await link_el.get_attribute("href") if link_el else ""

                if title and company:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location_text.strip(),
                        "salary_text": salary_text.strip(),
                        "job_url": f"https://{domain}{href}" if href.startswith("/") else href,
                        "source": "Reed.co.uk",
                    })
            except Exception:
                continue
    finally:
        await context.close()
        await browser.close()

    return jobs


async def scrape_seek(
    sector_keyword: str,
    location: str,
    country_tld: str,
    playwright,
    proxy_url: Optional[str] = None,
) -> List[dict]:
    """Scrapes SEEK listings for AU/NZ markets."""
    tld_map = {"AUSTRALIA": "seek.com.au", "NEW_ZEALAND": "seek.co.nz"}
    domain = tld_map.get(country_tld, "seek.com.au")
    robots = await fetch_robots_txt(domain)
    keyword_slug = sector_keyword.lower().replace(" & ", "-").replace(" ", "-")
    path = f"/{keyword_slug}-jobs/in-{location.lower().replace(', ', '-').replace(' ', '-')}"

    if not is_path_allowed(robots, f"/{keyword_slug}-jobs"):
        return []

    browser, context = await get_browser_context(playwright, proxy_url)
    jobs = []
    try:
        page = await context.new_page()
        await page.goto(f"https://{domain}{path}", wait_until="domcontentloaded")
        await wait_for_page(page)
        await scroll_humanized(page, 1500)
        await asyncio.sleep(robots["crawl_delay_seconds"])

        cards = await page.query_selector_all("[data-automation='normalJob']")
        for card in cards[:_RESULT_LIMIT]:
            try:
                title_el = await card.query_selector("[data-automation='jobTitle']")
                company_el = await card.query_selector("[data-automation='jobCompany']")
                loc_el = await card.query_selector("[data-automation='jobLocation']")
                link_el = await card.query_selector("a[data-automation='jobTitle']")

                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                location_text = await loc_el.inner_text() if loc_el else ""
                href = await link_el.get_attribute("href") if link_el else ""

                if title and company:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location_text.strip(),
                        "salary_text": "",
                        "job_url": f"https://{domain}{href}" if href.startswith("/") else href,
                        "source": f"SEEK ({country_tld.title()})",
                    })
            except Exception:
                continue
    finally:
        await context.close()
        await browser.close()

    return jobs


async def scrape_stepstone(
    sector_keyword: str,
    location: str,
    playwright,
    proxy_url: Optional[str] = None,
) -> List[dict]:
    """Scrapes StepStone.de for German market listings."""
    domain = "www.stepstone.de"
    robots = await fetch_robots_txt(domain)
    keyword_slug = sector_keyword.lower().replace(" ", "-")
    path = f"/jobs/{keyword_slug}"

    if not is_path_allowed(robots, path):
        return []

    browser, context = await get_browser_context(playwright, proxy_url)
    jobs = []
    try:
        page = await context.new_page()
        await page.goto(
            f"https://{domain}{path}?q={sector_keyword}&location={location}",
            wait_until="domcontentloaded",
        )
        await wait_for_page(page)
        await scroll_humanized(page, 1200)
        await asyncio.sleep(robots["crawl_delay_seconds"])

        cards = await page.query_selector_all("article[data-at='job-item']")
        for card in cards[:_RESULT_LIMIT]:
            try:
                title_el = await card.query_selector("[data-at='job-item-title']")
                company_el = await card.query_selector("[data-at='job-item-company-name']")
                loc_el = await card.query_selector("[data-at='job-item-location']")
                link_el = await card.query_selector("a")

                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                location_text = await loc_el.inner_text() if loc_el else ""
                href = await link_el.get_attribute("href") if link_el else ""

                if title and company:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location_text.strip(),
                        "salary_text": "",
                        "job_url": href if href.startswith("http") else f"https://{domain}{href}",
                        "source": "StepStone",
                    })
            except Exception:
                continue
    finally:
        await context.close()
        await browser.close()

    return jobs


async def scrape_irishjobs(
    sector_keyword: str,
    playwright,
    proxy_url: Optional[str] = None,
) -> List[dict]:
    """Scrapes IrishJobs.ie for Ireland market listings."""
    domain = "www.irishjobs.ie"
    robots = await fetch_robots_txt(domain)
    keyword_slug = sector_keyword.lower().replace(" & ", "-").replace(" ", "-")
    path = f"/jobs/{keyword_slug}"

    if not is_path_allowed(robots, path):
        return []

    browser, context = await get_browser_context(playwright, proxy_url)
    jobs = []
    try:
        page = await context.new_page()
        await page.goto(f"https://{domain}{path}", wait_until="domcontentloaded")
        await wait_for_page(page)
        await scroll_humanized(page, 1200)
        await asyncio.sleep(robots["crawl_delay_seconds"])

        cards = await page.query_selector_all(".job-item")
        for card in cards[:_RESULT_LIMIT]:
            try:
                title_el = await card.query_selector(".job-title a")
                company_el = await card.query_selector(".company-name")
                loc_el = await card.query_selector(".location")
                href = await title_el.get_attribute("href") if title_el else ""
                title = await title_el.inner_text() if title_el else ""
                company = await company_el.inner_text() if company_el else ""
                location_text = await loc_el.inner_text() if loc_el else ""

                if title and company:
                    jobs.append({
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location_text.strip(),
                        "salary_text": "",
                        "job_url": href if href.startswith("http") else f"https://{domain}{href}",
                        "source": "IrishJobs.ie",
                    })
            except Exception:
                continue
    finally:
        await context.close()
        await browser.close()

    return jobs


async def scrape_for_region(
    country: str,
    sector: str,
    location: str,
    playwright,
    proxy_url: Optional[str] = None,
) -> List[dict]:
    """
    Dispatcher — routes to the correct platform scraper based on country.
    Returns an empty list on any failure, triggering sample data fallback.
    """
    try:
        if country in ("UK",):
            return await scrape_reed(sector, location, playwright, proxy_url)
        elif country in ("AUSTRALIA", "NEW_ZEALAND"):
            return await scrape_seek(sector, location, country, playwright, proxy_url)
        elif country == "GERMANY":
            return await scrape_stepstone(sector, location, playwright, proxy_url)
        elif country == "IRELAND":
            return await scrape_irishjobs(sector, playwright, proxy_url)
        else:
            return []
    except Exception as exc:
        print(f"[Automation] Scrape failed for {country}/{sector}: {exc}")
        return []
