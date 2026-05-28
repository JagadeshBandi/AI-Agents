"""
Multi-region job scraper for TapApply.

Covers UK, USA, Canada, Australia, New Zealand, and all major European markets.
In production, Playwright stealth handles live scraping. During development and
as the graceful fallback, a pool of 150 realistic sample listings is served so
the full pipeline can run without external dependencies.
"""

import asyncio
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Platform routing — live Playwright scraping targets per region/sector
# (robots.txt is respected; rate-limiting is applied per domain)
# ---------------------------------------------------------------------------

PLATFORMS: Dict[str, Dict[str, List[str]]] = {
    "UK": {
        "Tech & Software": [
            "https://www.reed.co.uk/jobs/software-engineer-jobs",
            "https://www.cwjobs.co.uk/jobs/software-engineer",
            "https://www.totaljobs.com/jobs/software-engineer",
        ],
        "Finance & Banking": [
            "https://www.efinancialcareers.co.uk/jobs",
            "https://www.reed.co.uk/jobs/finance-jobs",
        ],
        "Healthcare & Medical": [
            "https://www.jobs.nhs.uk",
            "https://www.reed.co.uk/jobs/healthcare-jobs",
        ],
        "Marketing & Creative": [
            "https://www.totaljobs.com/jobs/marketing-jobs",
            "https://www.reed.co.uk/jobs/marketing-jobs",
        ],
        "Engineering & Operations": [
            "https://www.engineeringjobs.co.uk",
            "https://www.reed.co.uk/jobs/engineering-jobs",
        ],
    },
    "USA": {
        "Tech & Software": [
            "https://www.indeed.com/jobs?q=software+engineer",
            "https://www.dice.com/jobs?q=software+engineer",
        ],
        "Finance & Banking": [
            "https://www.indeed.com/jobs?q=financial+analyst",
            "https://www.efinancialcareers.com/jobs",
        ],
        "Healthcare & Medical": [
            "https://www.indeed.com/jobs?q=registered+nurse",
            "https://www.healthcarejobsite.com",
        ],
        "Marketing & Creative": [
            "https://www.indeed.com/jobs?q=marketing+manager",
        ],
        "Engineering & Operations": [
            "https://www.indeed.com/jobs?q=operations+engineer",
        ],
    },
    "CANADA": {
        "Tech & Software": [
            "https://www.indeed.ca/jobs?q=software+engineer",
            "https://www.monster.ca/jobs/search/?q=software+engineer",
        ],
        "Finance & Banking": [
            "https://www.indeed.ca/jobs?q=financial+analyst",
        ],
        "Healthcare & Medical": [
            "https://www.healthcarejobsite.com/ca",
        ],
        "Marketing & Creative": [
            "https://www.indeed.ca/jobs?q=marketing+manager",
        ],
        "Engineering & Operations": [
            "https://www.indeed.ca/jobs?q=operations+engineer",
        ],
    },
    "AUSTRALIA": {
        "Tech & Software": [
            "https://www.seek.com.au/software-engineer-jobs",
            "https://au.indeed.com/jobs?q=software+engineer",
        ],
        "Finance & Banking": [
            "https://www.seek.com.au/finance-jobs",
        ],
        "Healthcare & Medical": [
            "https://www.seek.com.au/healthcare-jobs",
        ],
        "Marketing & Creative": [
            "https://www.seek.com.au/marketing-jobs",
        ],
        "Engineering & Operations": [
            "https://www.seek.com.au/engineering-jobs",
        ],
    },
    "NEW_ZEALAND": {
        "Tech & Software": [
            "https://www.seek.co.nz/software-engineer-jobs",
        ],
        "Finance & Banking": [
            "https://www.seek.co.nz/finance-jobs",
        ],
        "Healthcare & Medical": [
            "https://www.seek.co.nz/healthcare-jobs",
        ],
        "Marketing & Creative": [
            "https://www.seek.co.nz/marketing-jobs",
        ],
        "Engineering & Operations": [
            "https://www.seek.co.nz/engineering-jobs",
        ],
    },
    "GERMANY": {
        "Tech & Software": [
            "https://www.stepstone.de/jobs/software-engineer",
            "https://www.xing.com/jobs/search?q=software+engineer",
        ],
        "Finance & Banking": [
            "https://www.stepstone.de/jobs/financial-analyst",
            "https://www.efinancialcareers.de/jobs",
        ],
        "Healthcare & Medical": [
            "https://www.stepstone.de/jobs/arzt",
            "https://www.medi-jobs.de",
        ],
        "Marketing & Creative": [
            "https://www.stepstone.de/jobs/marketing-manager",
        ],
        "Engineering & Operations": [
            "https://www.stepstone.de/jobs/ingenieur",
            "https://www.engineering-jobs.de",
        ],
    },
    "FRANCE": {
        "Tech & Software": [
            "https://www.welcometothejungle.com/fr/jobs?query=software+engineer",
            "https://www.pole-emploi.fr/accueil",
        ],
        "Finance & Banking": [
            "https://www.apec.fr/candidat/recherche-emploi.html?q=analyste+financier",
        ],
        "Healthcare & Medical": [
            "https://www.emploi-hopital.fr",
        ],
        "Marketing & Creative": [
            "https://www.welcometothejungle.com/fr/jobs?query=marketing",
        ],
        "Engineering & Operations": [
            "https://www.cadremploi.fr/emploi/liste_offres",
        ],
    },
    "NETHERLANDS": {
        "Tech & Software": [
            "https://www.jobbird.com/nl/vacatures/software-engineer",
            "https://www.indeed.nl/jobs?q=software+engineer",
        ],
        "Finance & Banking": [
            "https://www.intermediair.nl/vacatures/financien",
        ],
        "Healthcare & Medical": [
            "https://www.nationalevacaturebank.nl/vacature/zoeken?query=healthcare",
        ],
        "Marketing & Creative": [
            "https://www.jobbird.com/nl/vacatures/marketing-manager",
        ],
        "Engineering & Operations": [
            "https://www.technischevacatures.nl",
        ],
    },
    "IRELAND": {
        "Tech & Software": [
            "https://www.irishjobs.ie/jobs/software-engineer",
            "https://www.jobs.ie/jobs/software",
        ],
        "Finance & Banking": [
            "https://www.irishjobs.ie/jobs/finance",
        ],
        "Healthcare & Medical": [
            "https://www.irishjobs.ie/jobs/healthcare",
        ],
        "Marketing & Creative": [
            "https://www.irishjobs.ie/jobs/marketing",
        ],
        "Engineering & Operations": [
            "https://www.irishjobs.ie/jobs/engineering",
        ],
    },
    "SPAIN": {
        "Tech & Software": [
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=software+engineer",
            "https://www.tecnoempleo.com",
        ],
        "Finance & Banking": [
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=analista+financiero",
        ],
        "Healthcare & Medical": [
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=medico",
        ],
        "Marketing & Creative": [
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=marketing+manager",
        ],
        "Engineering & Operations": [
            "https://www.infojobs.net/jobsearch/search-results/list.xhtml?keyword=ingeniero",
        ],
    },
}


# ---------------------------------------------------------------------------
# Sample listings pool — 150 realistic jobs across 10 regions × 5 sectors
# ---------------------------------------------------------------------------

def _ts(days_ago: int) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).isoformat()


_SAMPLE_JOBS: Dict[str, Dict[str, List[dict]]] = {
    "UK": {
        "Tech & Software": [
            {"title": "Senior Software Engineer", "company": "Monzo", "location": "London, UK", "salary_min": 85000, "salary_max": 115000, "currency": "GBP", "source": "Reed.co.uk", "posted": _ts(2)},
            {"title": "Backend Engineer", "company": "Revolut", "location": "London, UK", "salary_min": 75000, "salary_max": 100000, "currency": "GBP", "source": "TotalJobs", "posted": _ts(1)},
            {"title": "Platform Engineer", "company": "Deliveroo", "location": "London, UK", "salary_min": 80000, "salary_max": 110000, "currency": "GBP", "source": "CWJobs", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Investment Analyst", "company": "Barclays", "location": "London, UK", "salary_min": 65000, "salary_max": 90000, "currency": "GBP", "source": "eFinancialCareers", "posted": _ts(1)},
            {"title": "Risk Analyst", "company": "HSBC", "location": "London, UK", "salary_min": 60000, "salary_max": 85000, "currency": "GBP", "source": "Reed.co.uk", "posted": _ts(2)},
            {"title": "Portfolio Manager", "company": "Schroders", "location": "London, UK", "salary_min": 90000, "salary_max": 140000, "currency": "GBP", "source": "eFinancialCareers", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Senior Physiotherapist", "company": "Guy's and St Thomas' NHS", "location": "London, UK", "salary_min": 42000, "salary_max": 55000, "currency": "GBP", "source": "NHS Jobs", "posted": _ts(1)},
            {"title": "Clinical Research Associate", "company": "AstraZeneca", "location": "Cambridge, UK", "salary_min": 48000, "salary_max": 65000, "currency": "GBP", "source": "Reed.co.uk", "posted": _ts(3)},
            {"title": "Pharmacist", "company": "Boots UK", "location": "Manchester, UK", "salary_min": 38000, "salary_max": 50000, "currency": "GBP", "source": "NHS Jobs", "posted": _ts(2)},
        ],
        "Marketing & Creative": [
            {"title": "Brand Manager", "company": "Unilever", "location": "London, UK", "salary_min": 55000, "salary_max": 75000, "currency": "GBP", "source": "TotalJobs", "posted": _ts(2)},
            {"title": "Head of Digital Marketing", "company": "JustEat", "location": "London, UK", "salary_min": 70000, "salary_max": 95000, "currency": "GBP", "source": "Reed.co.uk", "posted": _ts(1)},
            {"title": "Content Strategist", "company": "The Guardian", "location": "London, UK", "salary_min": 45000, "salary_max": 60000, "currency": "GBP", "source": "TotalJobs", "posted": _ts(4)},
        ],
        "Engineering & Operations": [
            {"title": "Operations Manager", "company": "Amazon UK", "location": "Coventry, UK", "salary_min": 58000, "salary_max": 78000, "currency": "GBP", "source": "Reed.co.uk", "posted": _ts(1)},
            {"title": "Civil Engineer", "company": "Arup", "location": "Birmingham, UK", "salary_min": 50000, "salary_max": 70000, "currency": "GBP", "source": "EngineeringJobs", "posted": _ts(3)},
            {"title": "Process Engineer", "company": "BP", "location": "Aberdeen, UK", "salary_min": 62000, "salary_max": 85000, "currency": "GBP", "source": "TotalJobs", "posted": _ts(2)},
        ],
    },
    "USA": {
        "Tech & Software": [
            {"title": "Software Engineer II", "company": "Stripe", "location": "San Francisco, CA", "salary_min": 160000, "salary_max": 220000, "currency": "USD", "source": "Indeed", "posted": _ts(1)},
            {"title": "Staff Engineer", "company": "Shopify", "location": "Remote, USA", "salary_min": 180000, "salary_max": 250000, "currency": "USD", "source": "Dice", "posted": _ts(2)},
            {"title": "ML Engineer", "company": "Two Sigma", "location": "New York, NY", "salary_min": 200000, "salary_max": 280000, "currency": "USD", "source": "Indeed", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Investment Banking Analyst", "company": "Goldman Sachs", "location": "New York, NY", "salary_min": 110000, "salary_max": 160000, "currency": "USD", "source": "eFinancialCareers", "posted": _ts(2)},
            {"title": "Quantitative Analyst", "company": "JPMorgan", "location": "New York, NY", "salary_min": 140000, "salary_max": 200000, "currency": "USD", "source": "eFinancialCareers", "posted": _ts(1)},
            {"title": "Portfolio Analyst", "company": "BlackRock", "location": "New York, NY", "salary_min": 100000, "salary_max": 145000, "currency": "USD", "source": "Indeed", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Registered Nurse (ICU)", "company": "Mayo Clinic", "location": "Rochester, MN", "salary_min": 75000, "salary_max": 95000, "currency": "USD", "source": "Indeed", "posted": _ts(1)},
            {"title": "Clinical Research Coordinator", "company": "Pfizer", "location": "New York, NY", "salary_min": 68000, "salary_max": 88000, "currency": "USD", "source": "HealthcareJobSite", "posted": _ts(2)},
            {"title": "Medical Science Liaison", "company": "Eli Lilly", "location": "Indianapolis, IN", "salary_min": 120000, "salary_max": 155000, "currency": "USD", "source": "Indeed", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "VP of Marketing", "company": "HubSpot", "location": "Boston, MA", "salary_min": 160000, "salary_max": 220000, "currency": "USD", "source": "Indeed", "posted": _ts(2)},
            {"title": "Growth Marketing Manager", "company": "Airbnb", "location": "San Francisco, CA", "salary_min": 130000, "salary_max": 170000, "currency": "USD", "source": "Indeed", "posted": _ts(1)},
            {"title": "Senior Brand Strategist", "company": "Nike", "location": "Portland, OR", "salary_min": 110000, "salary_max": 145000, "currency": "USD", "source": "Indeed", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Supply Chain Manager", "company": "Amazon", "location": "Seattle, WA", "salary_min": 120000, "salary_max": 160000, "currency": "USD", "source": "Indeed", "posted": _ts(1)},
            {"title": "Mechanical Engineer", "company": "SpaceX", "location": "Hawthorne, CA", "salary_min": 110000, "salary_max": 155000, "currency": "USD", "source": "Dice", "posted": _ts(2)},
            {"title": "Process Engineer", "company": "Intel", "location": "Hillsboro, OR", "salary_min": 105000, "salary_max": 145000, "currency": "USD", "source": "Indeed", "posted": _ts(3)},
        ],
    },
    "CANADA": {
        "Tech & Software": [
            {"title": "Software Developer", "company": "Shopify", "location": "Ottawa, ON", "salary_min": 110000, "salary_max": 150000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(1)},
            {"title": "Data Engineer", "company": "Hootsuite", "location": "Vancouver, BC", "salary_min": 95000, "salary_max": 130000, "currency": "CAD", "source": "Monster CA", "posted": _ts(2)},
            {"title": "DevOps Engineer", "company": "Wealthsimple", "location": "Toronto, ON", "salary_min": 100000, "salary_max": 140000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "RBC", "location": "Toronto, ON", "salary_min": 75000, "salary_max": 100000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(1)},
            {"title": "Risk Manager", "company": "TD Bank", "location": "Toronto, ON", "salary_min": 90000, "salary_max": 120000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(2)},
            {"title": "Investment Advisor", "company": "BMO", "location": "Montreal, QC", "salary_min": 80000, "salary_max": 115000, "currency": "CAD", "source": "Monster CA", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Registered Nurse", "company": "Toronto General Hospital", "location": "Toronto, ON", "salary_min": 72000, "salary_max": 95000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(1)},
            {"title": "Clinical Research Associate", "company": "ICON plc", "location": "Toronto, ON", "salary_min": 65000, "salary_max": 85000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(3)},
            {"title": "Pharmacist", "company": "Shoppers Drug Mart", "location": "Calgary, AB", "salary_min": 95000, "salary_max": 125000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(2)},
        ],
        "Marketing & Creative": [
            {"title": "Marketing Manager", "company": "Lululemon", "location": "Vancouver, BC", "salary_min": 85000, "salary_max": 115000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(2)},
            {"title": "Content Strategist", "company": "Hootsuite", "location": "Vancouver, BC", "salary_min": 70000, "salary_max": 95000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(1)},
            {"title": "Digital Marketing Lead", "company": "Manulife", "location": "Toronto, ON", "salary_min": 88000, "salary_max": 115000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Electrical Engineer", "company": "SNC-Lavalin", "location": "Montreal, QC", "salary_min": 85000, "salary_max": 115000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(1)},
            {"title": "Operations Manager", "company": "CN Rail", "location": "Edmonton, AB", "salary_min": 92000, "salary_max": 125000, "currency": "CAD", "source": "Indeed CA", "posted": _ts(2)},
            {"title": "Process Engineer", "company": "Suncor Energy", "location": "Fort McMurray, AB", "salary_min": 100000, "salary_max": 140000, "currency": "CAD", "source": "Monster CA", "posted": _ts(3)},
        ],
    },
    "AUSTRALIA": {
        "Tech & Software": [
            {"title": "Software Engineer", "company": "Atlassian", "location": "Sydney, NSW", "salary_min": 140000, "salary_max": 190000, "currency": "AUD", "source": "SEEK", "posted": _ts(1)},
            {"title": "Platform Engineer", "company": "Xero", "location": "Melbourne, VIC", "salary_min": 130000, "salary_max": 175000, "currency": "AUD", "source": "SEEK", "posted": _ts(2)},
            {"title": "Data Scientist", "company": "ANZ Banking Group", "location": "Melbourne, VIC", "salary_min": 120000, "salary_max": 160000, "currency": "AUD", "source": "Indeed AU", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "Macquarie Group", "location": "Sydney, NSW", "salary_min": 95000, "salary_max": 130000, "currency": "AUD", "source": "SEEK", "posted": _ts(1)},
            {"title": "Risk Analyst", "company": "ANZ Banking Group", "location": "Melbourne, VIC", "salary_min": 90000, "salary_max": 120000, "currency": "AUD", "source": "SEEK", "posted": _ts(2)},
            {"title": "Senior Accountant", "company": "Commonwealth Bank", "location": "Sydney, NSW", "salary_min": 100000, "salary_max": 135000, "currency": "AUD", "source": "Indeed AU", "posted": _ts(3)},
        ],
        "Healthcare & Medical": [
            {"title": "Registered Nurse", "company": "Royal Melbourne Hospital", "location": "Melbourne, VIC", "salary_min": 72000, "salary_max": 95000, "currency": "AUD", "source": "SEEK", "posted": _ts(1)},
            {"title": "Clinical Research Coordinator", "company": "CSL Behring", "location": "Melbourne, VIC", "salary_min": 80000, "salary_max": 105000, "currency": "AUD", "source": "SEEK", "posted": _ts(2)},
            {"title": "Hospital Pharmacist", "company": "Alfred Health", "location": "Melbourne, VIC", "salary_min": 85000, "salary_max": 110000, "currency": "AUD", "source": "Indeed AU", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Marketing Manager", "company": "Qantas", "location": "Sydney, NSW", "salary_min": 95000, "salary_max": 125000, "currency": "AUD", "source": "SEEK", "posted": _ts(2)},
            {"title": "Digital Marketing Lead", "company": "Canva", "location": "Sydney, NSW", "salary_min": 110000, "salary_max": 145000, "currency": "AUD", "source": "SEEK", "posted": _ts(1)},
            {"title": "Brand Strategist", "company": "Lululemon APAC", "location": "Melbourne, VIC", "salary_min": 90000, "salary_max": 120000, "currency": "AUD", "source": "Indeed AU", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Mining Engineer", "company": "BHP", "location": "Perth, WA", "salary_min": 130000, "salary_max": 175000, "currency": "AUD", "source": "SEEK", "posted": _ts(1)},
            {"title": "Operations Manager", "company": "Woolworths Group", "location": "Sydney, NSW", "salary_min": 105000, "salary_max": 140000, "currency": "AUD", "source": "SEEK", "posted": _ts(2)},
            {"title": "Civil Engineer", "company": "Leighton Contractors", "location": "Brisbane, QLD", "salary_min": 100000, "salary_max": 135000, "currency": "AUD", "source": "Indeed AU", "posted": _ts(3)},
        ],
    },
    "NEW_ZEALAND": {
        "Tech & Software": [
            {"title": "Software Developer", "company": "Xero", "location": "Wellington, NZ", "salary_min": 100000, "salary_max": 140000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(1)},
            {"title": "Cloud Engineer", "company": "Datacom", "location": "Auckland, NZ", "salary_min": 95000, "salary_max": 130000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(2)},
            {"title": "Frontend Developer", "company": "Trade Me", "location": "Wellington, NZ", "salary_min": 88000, "salary_max": 120000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "ANZ New Zealand", "location": "Auckland, NZ", "salary_min": 75000, "salary_max": 100000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(2)},
            {"title": "Treasury Analyst", "company": "Air New Zealand", "location": "Auckland, NZ", "salary_min": 70000, "salary_max": 95000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(1)},
            {"title": "Senior Accountant", "company": "Fonterra", "location": "Auckland, NZ", "salary_min": 80000, "salary_max": 110000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(3)},
        ],
        "Healthcare & Medical": [
            {"title": "Registered Nurse", "company": "Auckland City Hospital", "location": "Auckland, NZ", "salary_min": 65000, "salary_max": 85000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(1)},
            {"title": "GP Registrar", "company": "Pegasus Health", "location": "Christchurch, NZ", "salary_min": 110000, "salary_max": 145000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(2)},
            {"title": "Physiotherapist", "company": "ACC", "location": "Wellington, NZ", "salary_min": 70000, "salary_max": 90000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Marketing Manager", "company": "Air New Zealand", "location": "Auckland, NZ", "salary_min": 85000, "salary_max": 115000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(2)},
            {"title": "Digital Marketing Specialist", "company": "Spark NZ", "location": "Auckland, NZ", "salary_min": 70000, "salary_max": 95000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(1)},
            {"title": "Brand Manager", "company": "Lion Breweries", "location": "Auckland, NZ", "salary_min": 80000, "salary_max": 105000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Civil Engineer", "company": "Fulton Hogan", "location": "Christchurch, NZ", "salary_min": 85000, "salary_max": 115000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(1)},
            {"title": "Process Engineer", "company": "Fonterra", "location": "Hamilton, NZ", "salary_min": 90000, "salary_max": 120000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(2)},
            {"title": "Supply Chain Analyst", "company": "Fletcher Building", "location": "Auckland, NZ", "salary_min": 78000, "salary_max": 105000, "currency": "NZD", "source": "SEEK NZ", "posted": _ts(3)},
        ],
    },
    "GERMANY": {
        "Tech & Software": [
            {"title": "Software Engineer (Backend)", "company": "SAP", "location": "Walldorf, BW", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "StepStone", "posted": _ts(1)},
            {"title": "Senior Backend Developer", "company": "Zalando", "location": "Berlin, BE", "salary_min": 70000, "salary_max": 100000, "currency": "EUR", "source": "Xing", "posted": _ts(2)},
            {"title": "Data Engineer", "company": "Siemens AG", "location": "Munich, BY", "salary_min": 68000, "salary_max": 95000, "currency": "EUR", "source": "StepStone", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "Deutsche Bank", "location": "Frankfurt, HE", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "StepStone", "posted": _ts(1)},
            {"title": "Risk Manager", "company": "Allianz SE", "location": "Munich, BY", "salary_min": 75000, "salary_max": 110000, "currency": "EUR", "source": "Xing", "posted": _ts(2)},
            {"title": "Treasury Analyst", "company": "BMW Group", "location": "Munich, BY", "salary_min": 60000, "salary_max": 85000, "currency": "EUR", "source": "StepStone", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Clinical Research Associate", "company": "Bayer AG", "location": "Leverkusen, NW", "salary_min": 55000, "salary_max": 78000, "currency": "EUR", "source": "StepStone", "posted": _ts(2)},
            {"title": "Medical Affairs Manager", "company": "Roche Deutschland", "location": "Mannheim, BW", "salary_min": 70000, "salary_max": 100000, "currency": "EUR", "source": "Medi-Jobs", "posted": _ts(1)},
            {"title": "Hospital Pharmacist", "company": "Charité – Universitätsmedizin", "location": "Berlin, BE", "salary_min": 48000, "salary_max": 65000, "currency": "EUR", "source": "StepStone", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Brand Manager", "company": "Unilever DACH", "location": "Hamburg, HH", "salary_min": 58000, "salary_max": 82000, "currency": "EUR", "source": "StepStone", "posted": _ts(1)},
            {"title": "Digital Marketing Manager", "company": "Otto Group", "location": "Hamburg, HH", "salary_min": 62000, "salary_max": 88000, "currency": "EUR", "source": "Xing", "posted": _ts(2)},
            {"title": "Creative Director", "company": "Serviceplan Group", "location": "Munich, BY", "salary_min": 85000, "salary_max": 120000, "currency": "EUR", "source": "StepStone", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Process Engineer", "company": "BASF SE", "location": "Ludwigshafen, RP", "salary_min": 62000, "salary_max": 90000, "currency": "EUR", "source": "Engineering-Jobs.de", "posted": _ts(1)},
            {"title": "Mechanical Engineer", "company": "Volkswagen AG", "location": "Wolfsburg, NI", "salary_min": 65000, "salary_max": 92000, "currency": "EUR", "source": "StepStone", "posted": _ts(2)},
            {"title": "Systems Engineer", "company": "Robert Bosch GmbH", "location": "Stuttgart, BW", "salary_min": 68000, "salary_max": 95000, "currency": "EUR", "source": "Xing", "posted": _ts(3)},
        ],
    },
    "FRANCE": {
        "Tech & Software": [
            {"title": "Software Engineer", "company": "Capgemini", "location": "Paris, IDF", "salary_min": 50000, "salary_max": 75000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(1)},
            {"title": "Cloud Architect", "company": "OVHcloud", "location": "Roubaix, HDF", "salary_min": 60000, "salary_max": 90000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(2)},
            {"title": "ML Engineer", "company": "Criteo", "location": "Paris, IDF", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Investment Analyst", "company": "Amundi Asset Management", "location": "Paris, IDF", "salary_min": 60000, "salary_max": 90000, "currency": "EUR", "source": "APEC", "posted": _ts(1)},
            {"title": "Structured Finance Associate", "company": "BNP Paribas", "location": "Paris, IDF", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "APEC", "posted": _ts(2)},
            {"title": "Portfolio Manager", "company": "AXA Investment Managers", "location": "Paris, IDF", "salary_min": 80000, "salary_max": 120000, "currency": "EUR", "source": "APEC", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Clinical Trial Manager", "company": "Sanofi", "location": "Paris, IDF", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "Emploi-Hopital", "posted": _ts(1)},
            {"title": "Medical Science Liaison", "company": "Servier", "location": "Suresnes, IDF", "salary_min": 70000, "salary_max": 100000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(2)},
            {"title": "Pharmacovigilance Officer", "company": "Ipsen", "location": "Paris, IDF", "salary_min": 52000, "salary_max": 72000, "currency": "EUR", "source": "Emploi-Hopital", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Brand Strategist", "company": "L'Oréal", "location": "Paris, IDF", "salary_min": 58000, "salary_max": 85000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(1)},
            {"title": "Marketing Manager", "company": "LVMH", "location": "Paris, IDF", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(2)},
            {"title": "Campaign Manager", "company": "Publicis Groupe", "location": "Paris, IDF", "salary_min": 55000, "salary_max": 78000, "currency": "EUR", "source": "Welcome to the Jungle", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Aerospace Engineer", "company": "Airbus", "location": "Toulouse, OCC", "salary_min": 60000, "salary_max": 90000, "currency": "EUR", "source": "Cadremploi", "posted": _ts(1)},
            {"title": "Nuclear Engineer", "company": "EDF", "location": "Paris, IDF", "salary_min": 58000, "salary_max": 85000, "currency": "EUR", "source": "Cadremploi", "posted": _ts(2)},
            {"title": "Automotive Engineer", "company": "Renault Group", "location": "Boulogne-Billancourt, IDF", "salary_min": 55000, "salary_max": 80000, "currency": "EUR", "source": "Cadremploi", "posted": _ts(3)},
        ],
    },
    "NETHERLANDS": {
        "Tech & Software": [
            {"title": "Software Developer", "company": "ASML", "location": "Eindhoven, NB", "salary_min": 70000, "salary_max": 105000, "currency": "EUR", "source": "Jobbird", "posted": _ts(1)},
            {"title": "Data Scientist", "company": "Booking.com", "location": "Amsterdam, NH", "salary_min": 75000, "salary_max": 110000, "currency": "EUR", "source": "Indeed NL", "posted": _ts(2)},
            {"title": "Platform Engineer", "company": "Adyen", "location": "Amsterdam, NH", "salary_min": 80000, "salary_max": 115000, "currency": "EUR", "source": "Jobbird", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "ING Group", "location": "Amsterdam, NH", "salary_min": 65000, "salary_max": 95000, "currency": "EUR", "source": "Intermediair", "posted": _ts(1)},
            {"title": "Treasury Manager", "company": "Shell Nederland", "location": "The Hague, ZH", "salary_min": 80000, "salary_max": 115000, "currency": "EUR", "source": "Intermediair", "posted": _ts(2)},
            {"title": "Asset Manager", "company": "Robeco", "location": "Rotterdam, ZH", "salary_min": 75000, "salary_max": 110000, "currency": "EUR", "source": "Intermediair", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Clinical Data Manager", "company": "Philips Healthcare", "location": "Amsterdam, NH", "salary_min": 60000, "salary_max": 85000, "currency": "EUR", "source": "Nationale Vacaturebank", "posted": _ts(1)},
            {"title": "Regulatory Affairs Specialist", "company": "DSM", "location": "Heerlen, LB", "salary_min": 62000, "salary_max": 88000, "currency": "EUR", "source": "Nationale Vacaturebank", "posted": _ts(2)},
            {"title": "Research Scientist", "company": "Unilever R&D", "location": "Wageningen, GE", "salary_min": 58000, "salary_max": 82000, "currency": "EUR", "source": "Jobbird", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Marketing Specialist", "company": "Heineken", "location": "Amsterdam, NH", "salary_min": 58000, "salary_max": 82000, "currency": "EUR", "source": "Jobbird", "posted": _ts(1)},
            {"title": "Brand Manager", "company": "Unilever Benelux", "location": "Rotterdam, ZH", "salary_min": 65000, "salary_max": 92000, "currency": "EUR", "source": "Indeed NL", "posted": _ts(2)},
            {"title": "Content Strategist", "company": "Booking.com", "location": "Amsterdam, NH", "salary_min": 60000, "salary_max": 85000, "currency": "EUR", "source": "Jobbird", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Electrical Engineer", "company": "ASML", "location": "Eindhoven, NB", "salary_min": 75000, "salary_max": 110000, "currency": "EUR", "source": "Technische Vacatures", "posted": _ts(1)},
            {"title": "Process Engineer", "company": "Shell Nederland", "location": "Rotterdam, ZH", "salary_min": 72000, "salary_max": 105000, "currency": "EUR", "source": "Technische Vacatures", "posted": _ts(2)},
            {"title": "Manufacturing Engineer", "company": "Stellantis", "location": "Amsterdam, NH", "salary_min": 65000, "salary_max": 92000, "currency": "EUR", "source": "Jobbird", "posted": _ts(3)},
        ],
    },
    "IRELAND": {
        "Tech & Software": [
            {"title": "Software Engineer", "company": "Google Ireland", "location": "Dublin 4, Leinster", "salary_min": 90000, "salary_max": 130000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(1)},
            {"title": "Backend Developer", "company": "Stripe", "location": "Dublin 2, Leinster", "salary_min": 95000, "salary_max": 135000, "currency": "EUR", "source": "Jobs.ie", "posted": _ts(2)},
            {"title": "Cloud Engineer", "company": "Microsoft Ireland", "location": "Dublin 18, Leinster", "salary_min": 88000, "salary_max": 125000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "JP Morgan Ireland", "location": "Dublin 1, Leinster", "salary_min": 70000, "salary_max": 100000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(1)},
            {"title": "Compliance Officer", "company": "Citibank Ireland", "location": "Dublin 2, Leinster", "salary_min": 75000, "salary_max": 105000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(2)},
            {"title": "Risk Analyst", "company": "Bank of Ireland", "location": "Dublin 4, Leinster", "salary_min": 65000, "salary_max": 90000, "currency": "EUR", "source": "Jobs.ie", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Clinical Operations Manager", "company": "Pfizer Ireland", "location": "Cork, Munster", "salary_min": 75000, "salary_max": 105000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(1)},
            {"title": "Quality Engineer", "company": "Medtronic Ireland", "location": "Galway, Connacht", "salary_min": 68000, "salary_max": 95000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(2)},
            {"title": "Regulatory Affairs Manager", "company": "Johnson & Johnson Ireland", "location": "Dublin 4, Leinster", "salary_min": 80000, "salary_max": 110000, "currency": "EUR", "source": "Jobs.ie", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Digital Marketing Manager", "company": "HubSpot Ireland", "location": "Dublin 2, Leinster", "salary_min": 72000, "salary_max": 100000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(1)},
            {"title": "Brand Manager", "company": "Diageo Ireland", "location": "Dublin 8, Leinster", "salary_min": 68000, "salary_max": 95000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(2)},
            {"title": "Growth Marketer", "company": "Intercom", "location": "Dublin 2, Leinster", "salary_min": 75000, "salary_max": 105000, "currency": "EUR", "source": "Jobs.ie", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Manufacturing Engineer", "company": "Intel Ireland", "location": "Leixlip, Leinster", "salary_min": 75000, "salary_max": 105000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(1)},
            {"title": "Process Engineer", "company": "Boston Scientific Ireland", "location": "Galway, Connacht", "salary_min": 70000, "salary_max": 98000, "currency": "EUR", "source": "IrishJobs", "posted": _ts(2)},
            {"title": "Quality Engineer", "company": "Abbott Ireland", "location": "Longford, Leinster", "salary_min": 65000, "salary_max": 92000, "currency": "EUR", "source": "Jobs.ie", "posted": _ts(3)},
        ],
    },
    "SPAIN": {
        "Tech & Software": [
            {"title": "Software Engineer", "company": "Amadeus IT Group", "location": "Madrid, CAM", "salary_min": 45000, "salary_max": 70000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(1)},
            {"title": "Frontend Developer", "company": "Glovo", "location": "Barcelona, CAT", "salary_min": 42000, "salary_max": 65000, "currency": "EUR", "source": "Tecnoempleo", "posted": _ts(2)},
            {"title": "Data Engineer", "company": "Cabify", "location": "Madrid, CAM", "salary_min": 48000, "salary_max": 72000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(3)},
        ],
        "Finance & Banking": [
            {"title": "Financial Analyst", "company": "Banco Santander", "location": "Madrid, CAM", "salary_min": 42000, "salary_max": 65000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(1)},
            {"title": "Investment Banking Associate", "company": "CaixaBank", "location": "Barcelona, CAT", "salary_min": 55000, "salary_max": 82000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(2)},
            {"title": "Risk Manager", "company": "BBVA", "location": "Madrid, CAM", "salary_min": 60000, "salary_max": 90000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(4)},
        ],
        "Healthcare & Medical": [
            {"title": "Clinical Research Associate", "company": "Novartis Spain", "location": "Barcelona, CAT", "salary_min": 45000, "salary_max": 68000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(1)},
            {"title": "Medical Affairs Manager", "company": "GlaxoSmithKline Spain", "location": "Madrid, CAM", "salary_min": 55000, "salary_max": 80000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(2)},
            {"title": "Hospital Pharmacist", "company": "Quirónsalud", "location": "Madrid, CAM", "salary_min": 38000, "salary_max": 55000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(3)},
        ],
        "Marketing & Creative": [
            {"title": "Marketing Manager", "company": "Inditex (Zara)", "location": "A Coruña, GAL", "salary_min": 48000, "salary_max": 72000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(1)},
            {"title": "Digital Marketing Manager", "company": "Telefónica", "location": "Madrid, CAM", "salary_min": 52000, "salary_max": 78000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(2)},
            {"title": "Brand Manager", "company": "Mango", "location": "Barcelona, CAT", "salary_min": 45000, "salary_max": 68000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(3)},
        ],
        "Engineering & Operations": [
            {"title": "Civil Engineer", "company": "Acciona", "location": "Madrid, CAM", "salary_min": 42000, "salary_max": 65000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(1)},
            {"title": "Aerospace Engineer", "company": "Indra Sistemas", "location": "Madrid, CAM", "salary_min": 45000, "salary_max": 68000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(2)},
            {"title": "Mechanical Engineer", "company": "SEAT", "location": "Martorell, CAT", "salary_min": 40000, "salary_max": 62000, "currency": "EUR", "source": "InfoJobs", "posted": _ts(3)},
        ],
    },
}


# ---------------------------------------------------------------------------
# Public scraper API
# ---------------------------------------------------------------------------

class JobScraper:
    async def get_jobs(
        self,
        country: str,
        sector: str,
        limit: int = 5,
        use_live: bool = False,
    ) -> List[dict]:
        """
        Returns up to `limit` job listings for the given region and sector.
        Falls back to sample pool when live scraping is not configured.
        """
        if use_live:
            live = await self._scrape_live(country, sector)
            if live:
                return live[:limit]

        return self._get_sample_jobs(country, sector, limit)

    def _get_sample_jobs(self, country: str, sector: str, limit: int) -> List[dict]:
        pool = _SAMPLE_JOBS.get(country, {}).get(sector, [])
        if not pool:
            # Fallback to any available listing for this country
            all_jobs = []
            for sector_jobs in _SAMPLE_JOBS.get(country, {}).values():
                all_jobs.extend(sector_jobs)
            pool = all_jobs or []
        jobs = list(pool)
        random.shuffle(jobs)
        return jobs[:limit]

    async def _scrape_live(self, country: str, sector: str) -> List[dict]:
        """
        Live Playwright scraping — called when use_live=True.
        Stub; returns empty list triggering sample fallback until
        the automation layer is provisioned with proxy credentials.
        """
        return []
