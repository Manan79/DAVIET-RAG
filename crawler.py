import asyncio
import json
import re
import sys
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, urldefrag
from pathlib import Path
from typing import Set, List, Dict, Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from config import START_URL, ALLOWED_DOMAIN, MAX_PAGES_DEFAULT, RAW_DIR

# Skip these file types - they are not HTML pages
IGNORE_EXTENSIONS = {
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".mp4", ".mp3", ".avi", ".mov", ".zip", ".tar", ".gz",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".exe"
}


def normalize_url(url: str, base_url: str = START_URL) -> str:
    """Clean and normalize a URL. Returns the normalized URL or empty string if invalid."""
    if not url:
        return ""
    full_url = urljoin(base_url, url.strip())
    full_url, _ = urldefrag(full_url)  # remove #fragment part
    parsed = urlparse(full_url)
    if parsed.scheme not in ("http", "https"):
        return ""
    if ALLOWED_DOMAIN not in parsed.netloc.lower():
        return ""
    path_lower = parsed.path.lower()
    for ext in IGNORE_EXTENSIONS:
        if path_lower.endswith(ext):
            return ""
    return full_url


def clean_text(md_text: str) -> str:
    """
    Clean up extracted webpage text into plain readable text format.
    Removes markdown links, image references, HTML tags, special symbols,
    buzz words, and formatting noise, leaving clean readable text.
    """
    if not md_text:
        return ""

    text = md_text

    # 1. Remove image references: ![alt](url) -> alt
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # 2. Remove markdown links: [text](url) -> text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)

    # 3. Remove raw URLs
    text = re.sub(r"https?://[^\s\)\]]+", "", text)

    # 4. Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # 5. Remove HTML entities & special symbols
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = re.sub(r"&[a-zA-Z]+;", " ", text)
    text = text.replace("", "").replace("“", "\"").replace("”", "\"").replace("‘", "'").replace("’", "'")

    # 6. Remove markdown formatting symbols (*, _, #, >, etc.)
    text = re.sub(r"[\#\*\_\`\~\-\=]{1,}", " ", text)

    # 7. Remove zero-width spaces / non-printable chars
    text = text.replace("​", "")

    # 8. Collapse whitespace and newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 9. Clean up lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and len(line) > 1]  # filter out single stray characters/symbols

    return "\n".join(lines)


def get_url_hash(url: str) -> str:
    """Generate a short hash for safe file naming."""
    return hashlib.md5(url.encode("utf-8")).hexdigest()[:12]


async def crawl_website(
    start_url: str = START_URL,
    max_pages: int = MAX_PAGES_DEFAULT,
    headless: bool = True
) -> List[Dict[str, Any]]:
    """
    Crawl the website starting from start_url up to max_pages.
    Saves extracted pages to RAW_DIR.
    """
    visited_urls: Set[str] = set()
    to_visit: List[str] = [normalize_url(start_url) or start_url]
    crawled_data: List[Dict[str, Any]] = []

    browser_config = BrowserConfig(headless=headless, verbose=False)
    run_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, stream=False)

    print(f"[*] Starting crawl on: {start_url}")
    print(f"[*] Maximum pages target: {max_pages}")
    print(f"[*] Saving raw files to: {RAW_DIR}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while to_visit and len(visited_urls) < max_pages:
            current_url = to_visit.pop(0)
            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            page_num = len(visited_urls)
            print(f"[{page_num}/{max_pages}] Crawling: {current_url}")

            try:
                result = await crawler.arun(url=current_url, config=run_config)
                if not result.success:
                    print(f"  [!] Failed: {result.error_message}")
                    continue

                raw_md = result.markdown or ""
                cleaned_text = clean_text(raw_md)

                # Skip pages with virtually no text content
                if len(cleaned_text) < 50:
                    print(f"  [i] Skipping short/empty content ({len(cleaned_text)} chars)")
                    continue

                page_title = (
                    result.metadata.get("title") if result.metadata else ""
                ) or current_url

                # Save individual page as plain text file (.txt)
                url_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", urlparse(current_url).path.strip("/"))
                if not url_slug:
                    url_slug = "home"
                file_name = f"{page_num:03d}_{url_slug[:30]}_{get_url_hash(current_url)}.txt"
                file_path = RAW_DIR / file_name

                file_content = (
                    f"URL: {current_url}\n"
                    f"TITLE: {page_title}\n"
                    f"CRAWLED_AT: {datetime.now(timezone.utc).isoformat()}\n"
                    f"{'='*50}\n\n"
                    f"{cleaned_text}\n"
                )

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                crawled_data.append({"url": current_url, "title": page_title})
                print(f"  [+] Saved {len(cleaned_text)} chars -> {file_name}")

                # Discover new links to crawl
                internal_links = result.links.get("internal", []) if result.links else []
                for link_obj in internal_links:
                    href = link_obj.get("href")
                    normalized = normalize_url(href, base_url=current_url)
                    if normalized and normalized not in visited_urls and normalized not in to_visit:
                        to_visit.append(normalized)

            except Exception as e:
                print(f"  [!] Exception: {e}")

    print(f"\n[+] Crawl complete! Saved {len(crawled_data)} pages to {RAW_DIR}")
    return crawled_data


if __name__ == "__main__":
    max_p = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    asyncio.run(crawl_website(max_pages=max_p))