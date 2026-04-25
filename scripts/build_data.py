"""
Nouveaux Récits d'Entreprise — Script d'import SBTi + ADEME
Télécharge les données ouvertes, les transforme en projects.json

Usage:
    python scripts/build_data.py

Sources:
    - SBTi Target Dashboard (XLS, mis à jour chaque jeudi)
    - ADEME Bilans GES (CSV via data.gouv.fr)
"""

import json
import os
import sys
import hashlib
from datetime import datetime

try:
    import openpyxl
except ImportError:
    print("Installing openpyxl...")
    os.system(f"{sys.executable} -m pip install openpyxl --quiet")
    import openpyxl

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests --quiet")
    import requests

# ─── CONFIG ─────────────────────────────────────────
SBTI_URL = "https://files.sciencebasedtargets.org/production/files/companies-excel.xlsx"
SBTI_LOCAL = "data/companies-excel.xlsx"  # Manual upload fallback
ADEME_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/bilan-ges/lines?size=10000&format=json"
OUTPUT_FILE = "data/projects.json"
EDITORIAL_FILE = "data/editorial.json"
CACHE_DIR = "scripts/.cache"

SECTOR_MAP = {
    "Food & Beverage Processing": "Agroalimentaire",
    "Food & Staples Retailing": "Distribution",
    "Agricultural Products": "Agroalimentaire",
    "Textiles, Apparel & Luxury Goods": "Mode & Textile",
    "Apparel, Accessories & Luxury Goods": "Mode & Textile",
    "Construction Materials": "BTP & Immobilier",
    "Real Estate": "BTP & Immobilier",
    "Homebuilding": "BTP & Immobilier",
    "Electric Utilities": "Énergie",
    "Oil, Gas & Consumable Fuels": "Énergie",
    "Renewable Electricity": "Énergie",
    "Independent Power Producers & Energy Traders": "Énergie",
    "Multi-Utilities": "Énergie",
    "Gas Utilities": "Énergie",
    "Automobiles": "Transport",
    "Airlines": "Transport",
    "Marine Transportation": "Transport",
    "Trucking": "Transport",
    "Air Freight & Logistics": "Transport",
    "Railroads": "Transport",
    "Software": "Tech & Numérique",
    "IT Services": "Tech & Numérique",
    "Technology Hardware, Storage & Peripherals": "Tech & Numérique",
    "Semiconductors": "Tech & Numérique",
    "Internet & Direct Marketing Retail": "Tech & Numérique",
    "Banks": "Finance",
    "Insurance": "Finance",
    "Capital Markets": "Finance",
    "Diversified Financial Services": "Finance",
    "Consumer Finance": "Finance",
    "Chemicals": "Industrie chimique",
    "Steel": "Industrie lourde",
    "Metals & Mining": "Industrie lourde",
    "Industrial Machinery & Supplies & Components": "Industrie manufacturière",
    "Electrical Equipment": "Industrie manufacturière",
    "Building Products": "Industrie manufacturière",
    "Containers & Packaging": "Industrie manufacturière",
    "Paper & Forest Products": "Industrie manufacturière",
    "Pharmaceuticals": "Santé & Pharma",
    "Health Care Equipment & Supplies": "Santé & Pharma",
    "Biotechnology": "Santé & Pharma",
    "Hotels, Restaurants & Leisure": "Tourisme & Loisirs",
    "Professional Services": "Services",
    "Commercial Services & Supplies": "Services",
    "Media": "Services",
}

REGION_MAP = {
    "Europe": "Europe",
    "North America": "Amérique du Nord",
    "South America": "Amérique latine",
    "Latin America & the Caribbean": "Amérique latine",
    "Africa": "Afrique",
    "Asia": "Asie",
    "Oceania": "Océanie",
    "Middle East": "Moyen-Orient",
}

FLAG_MAP = {
    "France": "🇫🇷", "Germany": "🇩🇪", "United Kingdom": "🇬🇧",
    "United States": "🇺🇸", "Japan": "🇯🇵", "China": "🇨🇳",
    "Denmark": "🇩🇰", "Sweden": "🇸🇪", "Netherlands": "🇳🇱",
    "Switzerland": "🇨🇭", "Belgium": "🇧🇪", "Italy": "🇮🇹",
    "Spain": "🇪🇸", "Norway": "🇳🇴", "Finland": "🇫🇮",
    "Canada": "🇨🇦", "Australia": "🇦🇺", "Brazil": "🇧🇷",
    "India": "🇮🇳", "South Korea": "🇰🇷", "Ireland": "🇮🇪",
    "Austria": "🇦🇹", "Portugal": "🇵🇹", "Luxembourg": "🇱🇺",
    "Mexico": "🇲🇽", "Singapore": "🇸🇬", "Taiwan": "🇹🇼",
    "Thailand": "🇹🇭", "South Africa": "🇿🇦", "New Zealand": "🇳🇿",
    "Poland": "🇵🇱", "Czech Republic": "🇨🇿", "Turkey": "🇹🇷",
    "Israel": "🇮🇱", "Colombia": "🇨🇴", "Chile": "🇨🇱",
    "Argentina": "🇦🇷", "Philippines": "🇵🇭", "Malaysia": "🇲🇾",
    "Indonesia": "🇮🇩", "Vietnam": "🇻🇳", "Peru": "🇵🇪",
    "Greece": "🇬🇷", "Romania": "🇷🇴", "Hungary": "🇭🇺",
    "United Arab Emirates": "🇦🇪", "Saudi Arabia": "🇸🇦",
}

SECTOR_EMOJI = {
    "Agroalimentaire": "🌾", "Distribution": "🛒", "Mode & Textile": "👗",
    "BTP & Immobilier": "🏗️", "Énergie": "⚡", "Transport": "🚛",
    "Tech & Numérique": "💻", "Finance": "🏦", "Industrie chimique": "🧪",
    "Industrie lourde": "⛏️", "Industrie manufacturière": "🏭",
    "Santé & Pharma": "💊", "Tourisme & Loisirs": "🏨", "Services": "📋",
    "Mobilité": "🚗", "Services environnementaux": "♻️",
}


def download_file(url, filename):
    """Download a file with caching."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    filepath = os.path.join(CACHE_DIR, filename)
    print(f"  Downloading {url}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*",
            "Referer": "https://sciencebasedtargets.org/target-dashboard",
        }
        resp = requests.get(url, timeout=120, headers=headers)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"  ✓ Downloaded {len(resp.content) / 1024:.0f} KB")
        return filepath
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        if os.path.exists(filepath):
            print(f"  → Using cached version")
            return filepath
        return None


def parse_sbti(filepath):
    """Parse SBTi companies Excel into structured data."""
    print("  Parsing SBTi data...")
    wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
    ws = wb.active

    headers = []
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i == 0:
            headers = [str(h).strip().lower().replace(" ", "_") if h else f"col_{j}" for j, h in enumerate(row)]
            continue
        if any(cell is not None for cell in row):
            rows.append(dict(zip(headers, row)))

    wb.close()
    print(f"  ✓ Parsed {len(rows)} companies")
    return rows


def map_sector(raw_sector):
    """Map SBTi sector to our categories."""
    if not raw_sector:
        return "Autre"
    raw = str(raw_sector).strip()
    if raw in SECTOR_MAP:
        return SECTOR_MAP[raw]
    for key, val in SECTOR_MAP.items():
        if key.lower() in raw.lower() or raw.lower() in key.lower():
            return val
    return "Autre"


def map_region(raw_region):
    """Map SBTi region to our categories."""
    if not raw_region:
        return "Autre"
    raw = str(raw_region).strip()
    for key, val in REGION_MAP.items():
        if key.lower() in raw.lower():
            return val
    return "Autre"


def determine_scope(row):
    """Determine scope from target data."""
    # Check various column names that might contain scope info
    for key in row:
        val = str(row.get(key, "")).lower()
        if "net-zero" in val or "net zero" in val:
            return "Net Zero"
        if "scope 3" in val or "scope3" in val:
            return "Scope 3"
    return "Scope 1 & 2"


def determine_alignment(row):
    """Get temperature alignment."""
    for key in row:
        if "temperature" in key or "alignment" in key:
            val = str(row.get(key, ""))
            if "1.5" in val:
                return "1.5°C"
            if "2" in val and "well" in val.lower():
                return "Well-below 2°C"
            if "2" in val:
                return "2°C"
    return None


def get_target_year(row):
    """Extract target year."""
    for key in row:
        if "year" in key and "target" in key:
            val = row.get(key)
            if val and str(val).isdigit():
                return int(val)
    return None


def get_status(row):
    """Get target status."""
    for key in row:
        if "status" in key or "near_term" in key:
            val = str(row.get(key, "")).strip()
            if val and val.lower() not in ("none", "nan", ""):
                return val
    return None


def generate_id(company_name):
    """Generate a stable numeric ID from company name."""
    return int(hashlib.md5(company_name.encode()).hexdigest()[:8], 16) % 100000 + 1000


def build_sbti_entry(row):
    """Convert a SBTi row to a project entry."""
    # Try to find company name
    name = None
    for key in ["company_name", "organization", "company", "name"]:
        if key in row and row[key]:
            name = str(row[key]).strip()
            break
    if not name:
        return None

    # Try to find country
    country = None
    for key in ["country", "location", "hq_country"]:
        if key in row and row[key]:
            country = str(row[key]).strip()
            break

    # Try to find sector
    raw_sector = None
    for key in ["sector", "industry", "sub_industry", "isic", "cdp_acs"]:
        if key in row and row[key]:
            raw_sector = str(row[key]).strip()
            break

    sector = map_sector(raw_sector)
    region = "Europe"  # Default
    for key in ["region", "continent"]:
        if key in row and row[key]:
            region = map_region(str(row[key]))
            break

    status = get_status(row)
    if not status or "Targets Set" not in status:
        return None  # Only keep companies with validated targets

    alignment = determine_alignment(row)
    scope = determine_scope(row)
    target_year = get_target_year(row)

    flag = FLAG_MAP.get(country, "🏳️") if country else "🏳️"
    logo = SECTOR_EMOJI.get(sector, "🏢")

    alignment_text = f" — Aligné {alignment}" if alignment else ""
    target_text = f"Objectif SBTi validé{alignment_text}"
    if target_year:
        target_text += f" (horizon {target_year})"

    default_alignment = "conforme a l'Accord de Paris"
    summary = f"{name} a fait valider ses objectifs de décarbonation par le SBTi, "
    summary += f"alignés sur une trajectoire {alignment or default_alignment}. "
    summary += f"Secteur : {sector}."

    entry = {
        "id": generate_id(name),
        "company": name,
        "title": f"Objectifs SBTi validés — {sector}",
        "sector": sector,
        "region": region,
        "scope": scope,
        "source": "SBTi",
        "country": country or "Non renseigné",
        "countryFlag": flag,
        "year": 2025,
        "logo": logo,
        "size": "Non renseigné",
        "summary": summary,
        "actions": [
            f"Objectifs de réduction SBTi validés ({scope})",
            f"Alignement sur trajectoire {alignment or 'Accord de Paris'}",
        ],
        "stats": [],
        "target": target_text,
        "difficulty": "",
        "roi": "",
        "sourceUrl": "https://sciencebasedtargets.org/target-dashboard",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "contributors": ["Import automatique SBTi"],
        "verified": True,
        "autoImport": True,
    }

    if alignment:
        entry["stats"].append({
            "value": alignment,
            "label": "alignement température",
            "color": "#059669"
        })

    entry["stats"].append({
        "value": "SBTi",
        "label": "objectifs validés",
        "color": "#0284C7"
    })

    if scope != "Scope 1 & 2":
        entry["stats"].append({
            "value": scope,
            "label": "périmètre couvert",
            "color": "#7C3AED"
        })

    return entry


def load_editorial():
    """Load hand-curated editorial entries."""
    if os.path.exists(EDITORIAL_FILE):
        with open(EDITORIAL_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
        print(f"  ✓ Loaded {len(entries)} editorial entries")
        return entries
    return []


def merge_entries(editorial, sbti_entries):
    """Merge editorial (priority) with auto-imported entries."""
    # Editorial entries take priority — matched by company name
    editorial_names = {e["company"].lower().strip() for e in editorial}

    merged = list(editorial)
    added = 0
    for entry in sbti_entries:
        if entry["company"].lower().strip() not in editorial_names:
            merged.append(entry)
            added += 1

    print(f"  ✓ Merged: {len(editorial)} éditorialisées + {added} auto-importées = {len(merged)} total")
    return merged


def main():
    print("=" * 60)
    print("🌱 Nouveaux Récits d'Entreprise — Build Data")
    print("=" * 60)

    # 1. Get SBTi data (local file first, then try download)
    print("\n📥 Étape 1 : Récupération SBTi...")
    sbti_file = None
    if os.path.exists(SBTI_LOCAL):
        sbti_file = SBTI_LOCAL
        print(f"  ✓ Fichier local trouvé : {SBTI_LOCAL}")
    else:
        sbti_file = download_file(SBTI_URL, "sbti-companies.xlsx")
        if not sbti_file:
            print("  ⚠ Pas de fichier SBTi disponible — seules les fiches éditoriales seront utilisées")

    sbti_entries = []
    if sbti_file:
        # 2. Parse SBTi
        print("\n🔄 Étape 2 : Parsing SBTi...")
        rows = parse_sbti(sbti_file)

        # 3. Transform
        print("\n🔧 Étape 3 : Transformation...")
        for row in rows:
            entry = build_sbti_entry(row)
            if entry:
                sbti_entries.append(entry)
        print(f"  ✓ {len(sbti_entries)} entreprises avec objectifs validés")

    # 4. Load editorial entries
    print("\n📝 Étape 4 : Chargement des fiches éditorialisées...")
    editorial = load_editorial()

    # 5. Merge
    print("\n🔀 Étape 5 : Fusion...")
    all_entries = merge_entries(editorial, sbti_entries)

    # 6. Write output
    print("\n💾 Étape 6 : Écriture...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {OUTPUT_FILE} — {len(all_entries)} entrées")

    print(f"\n✅ Terminé ! {len(all_entries)} projets dans la base.")
    print(f"   → {len(editorial)} fiches éditorialisées (enrichies)")
    print(f"   → {len(sbti_entries)} fiches auto-importées SBTi")


if __name__ == "__main__":
    main()
