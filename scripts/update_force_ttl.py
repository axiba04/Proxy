#!/usr/bin/env python3

import re
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DNS_SERVER = "180.184.1.1:53"
SOURCE_V2FLY = "https://raw.githubusercontent.com/v2fly/domain-list-community/refs/heads/master/data/bytedance"
SOURCE_DOUYIN = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/DouYin/DouYin.list"
OUTPUT_FILE = Path("force_ttl_rules.txt")

DOMAIN_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,63}$"
)


def download(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "PaoPaoDNS-ForceTTL-GitHubAction/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse_v2fly(text: str) -> set[str]:
    domains: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        line = line.split("#", 1)[0].strip()
        if not line:
            continue

        if line.startswith(("include:", "full:", "regexp:", "keyword:")):
            continue

        domain = line.split()[0].strip().lower().rstrip(".")
        if DOMAIN_RE.match(domain):
            domains.add(domain)

    return domains


def parse_douyin(text: str) -> set[str]:
    domains: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2:
            continue

        rule_type = parts[0].upper()
        domain = parts[1].lower().rstrip(".")

        if rule_type not in ("DOMAIN", "DOMAIN-SUFFIX"):
            continue

        if DOMAIN_RE.match(domain):
            domains.add(domain)

    return domains


def read_existing_domains() -> set[str]:
    if not OUTPUT_FILE.exists():
        return set()

    domains: set[str] = set()
    for raw_line in OUTPUT_FILE.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        domain = line.split("@", 1)[0].strip().lower()
        if DOMAIN_RE.match(domain):
            domains.add(domain)

    return domains


def write_rules(domains: set[str]) -> None:
    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")
    sorted_domains = sorted(domains)

    header = f"""# ==========================================
# PaoPaoDNS Force TTL Rules (Bytedance)
# Updated: {now} (北京时间)
# Count:   {len(sorted_domains)} domains
# DNS:     {DNS_SERVER}
# Source 1:  {SOURCE_V2FLY}
# Source 2:  {SOURCE_DOUYIN}
# Author:  GitHub Action Bot
# ==========================================

"""

    rules = "\n".join(f"{domain}@{DNS_SERVER}" for domain in sorted_domains)
    OUTPUT_FILE.write_text(header + rules + "\n", encoding="utf-8")


def main() -> None:
    print("Downloading V2Fly Bytedance rules...")
    v2fly_domains = parse_v2fly(download(SOURCE_V2FLY))

    print("Downloading Blackmatrix7 DouYin rules...")
    douyin_domains = parse_douyin(download(SOURCE_DOUYIN))

    domains = v2fly_domains | douyin_domains
    existing_domains = read_existing_domains()

    print(f"V2Fly domains: {len(v2fly_domains)}")
    print(f"DouYin domains: {len(douyin_domains)}")
    print(f"Merged domains: {len(domains)}")

    if domains == existing_domains:
        print("No domain changes; keeping existing file unchanged.")
        return

    write_rules(domains)
    print(f"Updated {OUTPUT_FILE} with {len(domains)} domains.")


if __name__ == "__main__":
    main()
