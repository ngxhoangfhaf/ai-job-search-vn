#!/usr/bin/env python3
"""
TopCV Search CLI - Python version
"""

import asyncio
import argparse
import json
import re
import sys

BASE_URL = "https://www.topcv.vn"

async def htmlFetch(url: str) -> str:
    import aiohttp
    maxRetries = 6
    delay = 500
    for attempt in range(7):
        try:
            async with aiohttp.ClientSession() as session:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers={
                        "User-Agent": "Mozilla/5.0 (compatible; topcv-search/1.0)",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "vi,en;q=0.9",
                    }, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 429 or response.status >= 500:
                            if attempt == 6:
                                raise Exception(f"API request failed: {response.status}")
                            await asyncio.sleep(delay / 1000)
                            delay = min(delay * 2, 5000)
                            continue
                        if response.status == 404:
                            raise Exception("Job not found")
                        if response.status >= 400:
                            raise Exception(f"API request failed: {response.status}")
                        return await response.text()
        except Exception as e:
            if attempt == 6:
                raise Exception(f"Request failed after max retries: {e}")
            await asyncio.sleep(delay / 1000)
            delay = min(delay * 2, 5000)
            continue

def decodeHtmlEntities(text: str) -> str:
    import html, re
    text = html.unescape(text)
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text

def stripTags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()

async def parseJobCards(html: str):
    BASE_URL = "https://www.topcv.vn"
    CARD_PATTERN = re.compile(r'<div[^>]+class="[^"]*job-item[^"]*"[^>]*>([\s\S]*?)(?=<div[^>]+class="[^"]*job-item|$)', re.IGNORECASE)
    ID_PATTERNS = [
        re.compile(r'data-job-id="(\d+)"', re.IGNORECASE),
        re.compile(r'data-id="(\d+)"', re.IGNORECASE),
        re.compile(r'job-id="(\d+)"', re.IGNORECASE),
        re.compile(r'href="(?:https?:\/\/)?(?:www\.)?topcv\.vn\/[^"]*\/(\d+)(?:[?#]|")', re.IGNORECASE),
    ]
    TITLE_PATTERNS = [
        re.compile(r'<h3[^>]*class="[^"]*job-title[^"]*"[^>]*>([\s\S]*?)<\/h3>', re.IGNORECASE),
        re.compile(r'<h3[^>]*>([\s\S]*?)<\/h3>', re.IGNORECASE),
        re.compile(r'<a[^>]+class="[^"]*job-title[^"]*"[^>]*>([\s\S]*?)<\/a>', re.IGNORECASE),
        re.compile(r'title="([^"]+)"', re.IGNORECASE),
    ]
    COMPANY_PATTERNS = [
        re.compile(r'class="[^"]*company[^"]*"[^>]*>([\s\S]*?)<\/div>', re.IGNORECASE),
        re.compile(r'class="[^"]*company-name[^"]*"[^>]*>([\s\S]*?)<\/div>', re.IGNORECASE),
        re.compile(r'<a[^>]+class="[^"]*company[^"]*"[^>]*>([\s\S]*?)<\/a>', re.IGNORECASE),
    ]
    LOCATION_PATTERNS = [
        re.compile(r'class="[^"]*location[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
        re.compile(r'class="[^"]*job-location[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
    ]
    DATE_PATTERNS = [
        re.compile(r'<time[^>]+datetime="([^"]+)"', re.IGNORECASE),
        re.compile(r'class="[^"]*date[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
    ]
    URL_PATTERNS = [
        re.compile(r'href="(https?:\/\/[^"]*topcv\.vn\/[^"]+)"', re.IGNORECASE),
        re.compile(r'href="(\/viec-lam\/[^"]+)"', re.IGNORECASE),
    ]
    DESC_PATTERNS = [
        re.compile(r'class="[^"]*description[^"]*"[^>]*>([\s\S]*?)<\/div>', re.IGNORECASE),
        re.compile(r'class="[^"]*job-desc[^"]*"[^>]*>([\s\S]*?)<\/div>', re.IGNORECASE),
        re.compile(r'<p[^>]*>([\s\S]*?)<\/p>', re.IGNORECASE),
    ]
    LOCATION_PATTERNS_2 = [
        re.compile(r'class="[^"]*location[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
        re.compile(r'class="[^"]*job-location[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
    ]
    DATE_PATTERNS_2 = [
        re.compile(r'<time[^>]+datetime="([^"]+)"', re.IGNORECASE),
        re.compile(r'class="[^"]*date[^"]*"[^>]*>([\s\S]*?)<\/span>', re.IGNORECASE),
    ]

    results = []
    for match in CARD_PATTERN.finditer(html):
        cardHtml = match.group(1)
        jobId = ""
        for pattern in ID_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                jobId = m.group(1)
                break
        if not jobId:
            continue

        title = ""
        for pattern in TITLE_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                title = decodeHtmlEntities(stripTags(m.group(1)))
                break
        if not title:
            continue

        company = ""
        companyUrl = ""
        for pattern in COMPANY_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                linkMatch = re.search(r'href="([^"]+)"', m.group(1))
                if linkMatch:
                    companyUrl = linkMatch.group(1)
                company = decodeHtmlEntities(stripTags(m.group(1)))
                break

        jobLocation = ""
        for pattern in LOCATION_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                jobLocation = decodeHtmlEntities(stripTags(m.group(1)))
                break

        jobDate = ""
        for pattern in DATE_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                jobDate = m.group(1)
                break

        url = f"https://www.topcv.vn/viec-lam/{jobId}"
        for pattern in URL_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                urlCandidate = m.group(1)
                if urlCandidate.startswith("/"):
                    url = f"https://www.topcv.vn{urlCandidate}"
                else:
                    url = urlCandidate
                break

        description = ""
        for pattern in DESC_PATTERNS:
            m = pattern.search(cardHtml)
            if m:
                text = decodeHtmlEntities(stripTags(m.group(1)))
                description = text[:300] if len(text) > 300 else text
                break

        jobLoc2 = ""
        for pattern in LOCATION_PATTERNS_2:
            m = pattern.search(cardHtml)
            if m:
                jobLoc2 = decodeHtmlEntities(stripTags(m.group(1)))
                break

        jobDate2 = ""
        for pattern in DATE_PATTERNS_2:
            m = pattern.search(cardHtml)
            if m:
                jobDate2 = m.group(1)
                break

        results.append({
            "id": jobId,
            "title": title,
            "company": company or None,
            "companyUrl": companyUrl or None,
            "location": jobLocation or jobLoc2 or None,
            "date": jobDate or jobDate2 or None,
            "url": url,
            "description": description or None,
        })
    return results

def parseHitCount(html: str) -> int:
    match = (re.search(r'tìm thấy\s+<strong>([\d.,]+)<\/strong>', html, re.IGNORECASE) or
             re.search(r'tìm được\s+<strong>([\d.,]+)<\/strong>', html, re.IGNORECASE) or
             re.search(r'tổng cộng\s+<strong>([\d.,]+)<\/strong>', html, re.IGNORECASE))
    if not match:
        return 0
    numStr = match.group(1).replace(".", "").replace(",", "")
    return int(numStr) or 0

def decodeHtmlEntities(text: str) -> str:
    import html, re
    text = html.unescape(text)
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text

def stripTags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()

async def search(args):
    params = {"q": args.query}
    if args.jobage:
        params["age"] = args.jobage
    if args.sort:
        params["sort"] = args.sort
    if args.page:
        params["page"] = str(args.page)

    try:
        html = await htmlFetch(f"{BASE_URL}/tim-viec-lam/tat-ca-viec-lam")
        jobs = await parseJobCards(html)
        total = parseHitCount(html)

        filtered = jobs
        if args.limit:
            filtered = filtered[:args.limit]

        fmt = args.format or "json"
        if fmt == "json":
            print(json.dumps({"meta": {"total": total, "page": args.page or 1}, "data": filtered}, ensure_ascii=False, indent=2))
        elif fmt == "table":
            print("ID\tTitle\tCompany\tLocation\tDate\tURL")
            for job in filtered:
                print(f"{job['id']}\t{job['title']}\t{job['company'] or 'N/A'}\t{job['location'] or 'N/A'}\t{job['date'] or 'N/A'}\t{job['url']}")
        elif fmt == "plain":
            for job in filtered:
                print("---")
                print(f"Title: {job['title']}")
                print(f"Company: {job['company'] or 'N/A'}")
                print(f"Location: {job['location'] or 'N/A'}")
                print(f"Date: {job['date'] or 'N/A'}")
                print(f"URL: {job['url']}")
                if job['description']:
                    print(f"Description: {job['description']}")
    except Exception as e:
        print(json.dumps({"error": str(e), "code": "SEARCH_FAILED"}), file=sys.stderr)
        sys.exit(1)

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="TopCV Search CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search job listings")
    search_parser.add_argument("--query", "-q", required=True, help="Keyword search")
    search_parser.add_argument("--jobage", choices=["1", "7", "14", "30", "9999"])
    search_parser.add_argument("--sort", choices=["relevance", "date"])
    search_parser.add_argument("--page", type=int)
    search_parser.add_argument("--limit", type=int)
    search_parser.add_argument("--format", choices=["json", "table", "plain"], default="json")

    args = parser.parse_args()

    if args.command == "search":
        await search(args)
    else:
        print(json.dumps({"error": "Unknown command"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())