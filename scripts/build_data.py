"""
Nouveaux Recits d'Entreprise - Script d'import SBTi
Lit les donnees ouvertes SBTi, les transforme en projects.json
"""

import json
import os
import re
import sys
import hashlib
from datetime import datetime

try:
    import openpyxl
except ImportError:
    os.system(f"{sys.executable} -m pip install openpyxl --quiet")
    import openpyxl

try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests --quiet")
    import requests

SBTI_URL = "https://files.sciencebasedtargets.org/production/files/companies-excel.xlsx"
SBTI_LOCAL = "data/companies-excel.xlsx"
OUTPUT_FILE = "data/projects.json"
EDITORIAL_FILE = "data/editorial.json"
CACHE_DIR = "scripts/.cache"

SECTOR_MAP = {
    "food and beverage": "Agroalimentaire",
    "retailing": "Distribution",
    "textile": "Mode & Textile",
    "apparel": "Mode & Textile",
    "footwear": "Mode & Textile",
    "luxury": "Mode & Textile",
    "construction": "BTP & Immobilier",
    "real estate": "BTP & Immobilier",
    "building products": "BTP & Immobilier",
    "electrical equipment": "Industrie manufacturiere",
    "consumer durables": "Industrie manufacturiere",
    "containers": "Industrie manufacturiere",
    "packaging": "Industrie manufacturiere",
    "forest and paper": "Industrie manufacturiere",
    "automobiles": "Transport",
    "transportation": "Transport",
    "air freight": "Transport",
    "marine": "Transport",
    "software": "Tech & Numerique",
    "technology hardware": "Tech & Numerique",
    "telecommunication": "Tech & Numerique",
    "media": "Tech & Numerique",
    "banks": "Finance",
    "financials": "Finance",
    "insurance": "Finance",
    "chemicals": "Industrie chimique",
    "metals": "Industrie lourde",
    "mining": "Industrie lourde",
    "steel": "Industrie lourde",
    "pharma": "Sante & Pharma",
    "biotech": "Sante & Pharma",
    "healthcare": "Sante & Pharma",
    "hotels": "Tourisme & Loisirs",
    "restaurants": "Tourisme & Loisirs",
    "leisure": "Tourisme & Loisirs",
    "professional services": "Services",
    "commercial services": "Services",
    "trading companies": "Services",
    "utilities": "Energie",
    "energy": "Energie",
    "oil and gas": "Energie",
}

REGION_MAP = {
    "europe": "Europe",
    "northern america": "Amerique du Nord",
    "asia": "Asie",
    "latin america": "Amerique latine",
    "africa": "Afrique",
    "oceania": "Oceanie",
    "mena": "Moyen-Orient",
}

FLAG_MAP = {
    "France": "\U0001f1eb\U0001f1f7", "Germany": "\U0001f1e9\U0001f1ea",
    "United Kingdom": "\U0001f1ec\U0001f1e7", "United States": "\U0001f1fa\U0001f1f8",
    "Japan": "\U0001f1ef\U0001f1f5", "China": "\U0001f1e8\U0001f1f3",
    "Denmark": "\U0001f1e9\U0001f1f0", "Sweden": "\U0001f1f8\U0001f1ea",
    "Netherlands": "\U0001f1f3\U0001f1f1", "Switzerland": "\U0001f1e8\U0001f1ed",
    "Belgium": "\U0001f1e7\U0001f1ea", "Italy": "\U0001f1ee\U0001f1f9",
    "Spain": "\U0001f1ea\U0001f1f8", "Norway": "\U0001f1f3\U0001f1f4",
    "Finland": "\U0001f1eb\U0001f1ee", "Canada": "\U0001f1e8\U0001f1e6",
    "Australia": "\U0001f1e6\U0001f1fa", "Brazil": "\U0001f1e7\U0001f1f7",
    "India": "\U0001f1ee\U0001f1f3", "South Korea": "\U0001f1f0\U0001f1f7",
    "Ireland": "\U0001f1ee\U0001f1ea", "Austria": "\U0001f1e6\U0001f1f9",
    "Portugal": "\U0001f1f5\U0001f1f9", "Luxembourg": "\U0001f1f1\U0001f1fa",
    "Mexico": "\U0001f1f2\U0001f1fd", "Singapore": "\U0001f1f8\U0001f1ec",
    "Taiwan": "\U0001f1f9\U0001f1fc", "Thailand": "\U0001f1f9\U0001f1ed",
    "South Africa": "\U0001f1ff\U0001f1e6", "New Zealand": "\U0001f1f3\U0001f1ff",
    "Poland": "\U0001f1f5\U0001f1f1", "Turkey": "\U0001f1f9\U0001f1f7",
    "Israel": "\U0001f1ee\U0001f1f1", "Colombia": "\U0001f1e8\U0001f1f4",
    "Chile": "\U0001f1e8\U0001f1f1", "Argentina": "\U0001f1e6\U0001f1f7",
    "Malaysia": "\U0001f1f2\U0001f1fe", "Indonesia": "\U0001f1ee\U0001f1e9",
    "Vietnam": "\U0001f1fb\U0001f1f3", "Philippines": "\U0001f1f5\U0001f1ed",
}

SECTOR_EMOJI = {
    "Agroalimentaire": "\U0001f33e", "Distribution": "\U0001f6d2",
    "Mode & Textile": "\U0001f457", "BTP & Immobilier": "\U0001f3d7\ufe0f",
    "Energie": "\u26a1", "Transport": "\U0001f69b",
    "Tech & Numerique": "\U0001f4bb", "Finance": "\U0001f3e6",
    "Industrie chimique": "\U0001f9ea", "Industrie lourde": "\u26cf\ufe0f",
    "Industrie manufacturiere": "\U0001f3ed", "Sante & Pharma": "\U0001f48a",
    "Tourisme & Loisirs": "\U0001f3e8", "Services": "\U0001f4cb",
}


def download_file(url, filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    filepath = os.path.join(CACHE_DIR, filename)
    try:
        h = {"User-Agent": "Mozilla/5.0", "Referer": "https://sciencebasedtargets.org"}
        resp = requests.get(url, timeout=120, headers=h)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"  Downloaded {len(resp.content)//1024} KB")
        return filepath
    except Exception as e:
        print(f"  Download failed: {e}")
        return filepath if os.path.exists(filepath) else None


def map_sector(raw):
    if not raw:
        return "Autre"
    low = raw.lower()
    for key, val in SECTOR_MAP.items():
        if key in low:
            return val
    return "Autre"


def map_region(raw):
    if not raw:
        return "Autre"
    low = str(raw).lower()
    for key, val in REGION_MAP.items():
        if key in low:
            return val
    return "Autre"


def extract_reduction(text):
    if not text:
        return None
    m = re.search(r'reduce\s+.*?(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE)
    return float(m.group(1)) if m else None


def gen_id(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16) % 100000 + 1000


def build_entry(row):
    status = str(row.get("near_term_status") or "").strip()
    if status != "Targets set":
        return None

    name = str(row.get("company_name") or "").strip()
    if not name:
        return None

    country = str(row.get("location") or "").strip()
    region = map_region(row.get("region"))
    sector = map_sector(str(row.get("sector") or ""))
    org_type = str(row.get("organization_type") or "").strip()
    classification = str(row.get("near_term_target_classification") or "").strip()
    target_lang = str(row.get("full_target_language") or "").strip()
    nz_status = str(row.get("net_zero_status") or "").strip()

    # Parse years
    def parse_year(val):
        if not val:
            return None
        try:
            return int(float(str(val).replace("FY", "").strip()))
        except (ValueError, TypeError):
            return None

    target_year = parse_year(row.get("near_term_target_year"))
    nz_year = parse_year(row.get("net_zero_year"))

    reduction = extract_reduction(target_lang)
    size = "PME" if org_type == "SME" else "Grande entreprise"
    flag = FLAG_MAP.get(country, "\U0001f3f3\ufe0f")
    logo = SECTOR_EMOJI.get(sector, "\U0001f3e2")

    # Title
    parts = []
    if reduction:
        parts.append(f"-{reduction:.0f}% d'emissions")
    if classification:
        parts.append(f"aligne {classification}")
    title = " - ".join(parts) if parts else "Objectifs SBTi valides"

    # Summary
    summary = ""
    if target_lang and len(target_lang) > 30:
        s = re.sub(r'https?://\S+\s*', '', target_lang)
        s = re.sub(r'This target was approved.*?SMEs\.\s*', '', s, flags=re.DOTALL)
        s = re.sub(r'Near-[Tt]erm [Tt]argets?:?\s*', '', s).strip()
        s = re.sub(r'Overall [Nn]et-[Zz]ero [Tt]arget:?\s*', '', s).strip()
        summary = s[:300] + "..." if len(s) > 300 else s
    if not summary:
        summary = f"{name} a fait valider ses objectifs SBTi ({classification or 'Accord de Paris'}). Secteur : {sector}."

    # Stats
    stats = []
    if reduction:
        stats.append({"value": f"-{reduction:.0f}%", "label": "reduction emissions", "color": "#059669"})
    if classification:
        stats.append({"value": classification, "label": "alignement", "color": "#0284C7"})
    if nz_status == "Targets set" and nz_year:
        stats.append({"value": str(nz_year), "label": "objectif net zero", "color": "#7C3AED"})
    elif target_year:
        stats.append({"value": str(target_year), "label": "horizon cible", "color": "#7C3AED"})
    if not stats:
        stats.append({"value": "SBTi", "label": "valide", "color": "#0284C7"})

    # Scope
    scope = "Net Zero" if nz_status == "Targets set" else ("Scope 3" if target_lang and "scope 3" in target_lang.lower() else "Scope 1 & 2")

    # Target text
    tt = f"SBTi valide - {classification or 'Accord de Paris'}"
    if target_year:
        tt += f" (horizon {target_year})"
    if nz_status == "Targets set" and nz_year:
        tt += f" - Net Zero {nz_year}"

    return {
        "id": gen_id(name), "company": name, "title": title,
        "sector": sector, "region": region, "scope": scope,
        "source": "SBTi", "country": country or "?",
        "countryFlag": flag, "year": 2025, "logo": logo, "size": size,
        "summary": summary,
        "actions": [
            f"Objectifs SBTi valides ({scope})",
            f"Trajectoire {classification or 'Accord de Paris'}",
        ],
        "stats": stats, "target": tt,
        "difficulty": "", "roi": "",
        "sourceUrl": "https://sciencebasedtargets.org/target-dashboard",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "contributors": ["Import automatique SBTi"],
        "verified": True, "autoImport": True,
    }


def main():
    print("=" * 50)
    print("Nouveaux Recits - Build Data")
    print("=" * 50)

    # 1. Get file
    print("\n1. Recuperation SBTi...")
    f = None
    if os.path.exists(SBTI_LOCAL):
        f = SBTI_LOCAL
        print(f"  Fichier local: {f}")
    else:
        f = download_file(SBTI_URL, "sbti.xlsx")

    entries = []
    if f:
        print("\n2. Parsing...")
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        ws = wb.active
        headers = None
        total = 0
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = list(row)
                continue
            data = dict(zip(headers, row))
            e = build_entry(data)
            if e:
                entries.append(e)
            total += 1
        wb.close()
        print(f"  {total} lignes -> {len(entries)} avec objectifs valides")

    # Editorial
    print("\n3. Fiches editoriales...")
    editorial = []
    if os.path.exists(EDITORIAL_FILE):
        with open(EDITORIAL_FILE, "r", encoding="utf-8") as fh:
            editorial = json.load(fh)
        print(f"  {len(editorial)} fiches")

    # Merge
    print("\n4. Fusion...")
    names = {e["company"].lower().strip() for e in editorial}
    added = [e for e in entries if e["company"].lower().strip() not in names]
    merged = editorial + added
    print(f"  {len(editorial)} editoriales + {len(added)} SBTi = {len(merged)} total")

    # Write
    print("\n5. Ecriture...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)
    print(f"  {OUTPUT_FILE} - {len(merged)} entrees")
    print(f"\nTermine! {len(merged)} projets.")


if __name__ == "__main__":
    main()
