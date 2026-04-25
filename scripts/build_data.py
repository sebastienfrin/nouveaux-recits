"""
Nouveaux Recits d'Entreprise - Import SBTi + ADEME
"""
import json, os, re, sys, hashlib, csv, io
from datetime import datetime

try:
    import openpyxl
except ImportError:
    os.system(f"{sys.executable} -m pip install openpyxl -q")
    import openpyxl
try:
    import requests
except ImportError:
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

SBTI_LOCAL = "data/companies-excel.xlsx"
SBTI_URL = "https://files.sciencebasedtargets.org/production/files/companies-excel.xlsx"
ADEME_CSV_URL = "https://github.com/lou-dupont/BEGES/raw/main/output/assessments.csv"
OUTPUT_FILE = "data/projects.json"
EDITORIAL_FILE = "data/editorial.json"

SECTOR_MAP = {
    "food and beverage": "Agroalimentaire", "food and staples": "Agroalimentaire",
    "agricultural": "Agroalimentaire", "retailing": "Distribution",
    "textile": "Mode & Textile", "apparel": "Mode & Textile",
    "footwear": "Mode & Textile", "luxury": "Mode & Textile",
    "construction": "BTP & Immobilier", "real estate": "BTP & Immobilier",
    "building products": "BTP & Immobilier", "homebuilding": "BTP & Immobilier",
    "electrical equipment": "Industrie manufacturière", "machinery": "Industrie manufacturière",
    "consumer durables": "Industrie manufacturière", "household": "Industrie manufacturière",
    "containers": "Industrie manufacturière", "packaging": "Industrie manufacturière",
    "forest and paper": "Industrie manufacturière", "paper": "Industrie manufacturière",
    "automobiles": "Transport", "transportation": "Transport",
    "air freight": "Transport", "marine": "Transport", "airlines": "Transport",
    "software": "Tech & Numérique", "technology hardware": "Tech & Numérique",
    "telecommunication": "Tech & Numérique", "media": "Tech & Numérique",
    "semiconductor": "Tech & Numérique", "it services": "Tech & Numérique",
    "banks": "Finance", "financials": "Finance", "insurance": "Finance",
    "capital markets": "Finance", "consumer finance": "Finance",
    "chemicals": "Industrie chimique", "metals": "Industrie lourde",
    "mining": "Industrie lourde", "steel": "Industrie lourde",
    "pharma": "Santé & Pharma", "biotech": "Santé & Pharma",
    "healthcare": "Santé & Pharma", "life sciences": "Santé & Pharma",
    "hotels": "Tourisme & Loisirs", "restaurants": "Tourisme & Loisirs",
    "leisure": "Tourisme & Loisirs",
    "professional services": "Services", "commercial services": "Services",
    "trading companies": "Services", "distributors": "Services",
    "utilities": "Énergie", "energy": "Énergie", "oil and gas": "Énergie",
    "electric": "Énergie", "renewable": "Énergie", "power": "Énergie",
}

REGION_MAP = {
    "europe": "Europe", "northern america": "Amérique du Nord",
    "asia": "Asie", "latin america": "Amérique latine",
    "africa": "Afrique", "oceania": "Océanie", "mena": "Moyen-Orient",
}

FLAG_MAP = {
    "France": "🇫🇷", "Germany": "🇩🇪", "United Kingdom": "🇬🇧",
    "United States": "🇺🇸", "Japan": "🇯🇵", "China": "🇨🇳",
    "Denmark": "🇩🇰", "Sweden": "🇸🇪", "Netherlands": "🇳🇱",
    "Switzerland": "🇨🇭", "Belgium": "🇧🇪", "Italy": "🇮🇹",
    "Spain": "🇪🇸", "Norway": "🇳🇴", "Finland": "🇫🇮",
    "Canada": "🇨🇦", "Australia": "🇦🇺", "Brazil": "🇧🇷",
    "India": "🇮🇳", "South Korea": "🇰🇷", "Korea, Republic of": "🇰🇷",
    "Ireland": "🇮🇪", "Austria": "🇦🇹", "Portugal": "🇵🇹",
    "Luxembourg": "🇱🇺", "Mexico": "🇲🇽", "Singapore": "🇸🇬",
    "Taiwan": "🇹🇼", "Taiwan, Province of China": "🇹🇼",
    "Thailand": "🇹🇭", "South Africa": "🇿🇦", "New Zealand": "🇳🇿",
    "Poland": "🇵🇱", "Turkey": "🇹🇷", "Israel": "🇮🇱",
    "Colombia": "🇨🇴", "Chile": "🇨🇱", "Argentina": "🇦🇷",
    "Malaysia": "🇲🇾", "Indonesia": "🇮🇩", "Vietnam": "🇻🇳",
    "Philippines": "🇵🇭", "Greece": "🇬🇷", "Romania": "🇷🇴",
    "Hungary": "🇭🇺", "Czech Republic": "🇨🇿", "Czechia": "🇨🇿",
    "United Arab Emirates": "🇦🇪", "Saudi Arabia": "🇸🇦",
    "Egypt": "🇪🇬", "Kenya": "🇰🇪", "Nigeria": "🇳🇬",
    "Morocco": "🇲🇦", "Peru": "🇵🇪", "Costa Rica": "🇨🇷",
    "Armenia": "🇦🇲", "Kazakhstan": "🇰🇿",
}

SECTOR_EMOJI = {
    "Agroalimentaire": "🌾", "Distribution": "🛒", "Mode & Textile": "👗",
    "BTP & Immobilier": "🏗️", "Énergie": "⚡", "Transport": "🚛",
    "Tech & Numérique": "💻", "Finance": "🏦", "Industrie chimique": "🧪",
    "Industrie lourde": "⛏️", "Industrie manufacturière": "🏭",
    "Santé & Pharma": "💊", "Tourisme & Loisirs": "🏨", "Services": "📋",
    "Mobilité": "🚗", "Services environnementaux": "♻️",
}


def map_sector(raw):
    if not raw: return "Autre"
    low = raw.lower()
    for key, val in SECTOR_MAP.items():
        if key in low:
            return val
    return "Autre"


def map_region(raw):
    if not raw: return "Autre"
    low = str(raw).lower()
    for key, val in REGION_MAP.items():
        if key in low:
            return val
    return "Autre"


def extract_reduction(text):
    if not text: return None, None, None
    # Scope 1&2 reduction
    m12 = re.search(r'scope\s*1\s*(?:and|&)\s*(?:scope\s*)?2.*?(\d+(?:\.\d+)?)\s*%', text, re.I)
    # Scope 1 only
    m1 = re.search(r'scope\s*1\s+(?:GHG\s+)?emissions?\s+(\d+(?:\.\d+)?)\s*%', text, re.I)
    # Scope 3
    m3 = re.search(r'scope\s*3.*?(\d+(?:\.\d+)?)\s*%', text, re.I)
    # Generic reduce X%
    mg = re.search(r'reduce\s+.*?(\d+(?:\.\d+)?)\s*%', text, re.I)

    r12 = float(m12.group(1)) if m12 else (float(mg.group(1)) if mg else None)
    r3 = float(m3.group(1)) if m3 else None
    return r12, r3, None


def parse_year(val):
    if not val: return None
    try: return int(float(str(val).replace("FY", "").strip()))
    except: return None


def gen_id(name):
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16) % 100000 + 1000


def build_sbti_entry(row):
    status = str(row.get("near_term_status") or "").strip()
    if status != "Targets set":
        return None

    name = str(row.get("company_name") or "").strip()
    if not name: return None

    country = str(row.get("location") or "").strip()
    region = map_region(row.get("region"))
    sector = map_sector(str(row.get("sector") or ""))
    org_type = str(row.get("organization_type") or "").strip()
    classification = str(row.get("near_term_target_classification") or "").strip()
    target_lang = str(row.get("full_target_language") or "").strip()
    nz_status = str(row.get("net_zero_status") or "").strip()
    target_year = parse_year(row.get("near_term_target_year"))
    nz_year = parse_year(row.get("net_zero_year"))

    r12, r3, _ = extract_reduction(target_lang)
    size = "PME" if org_type == "SME" else "Grande entreprise"
    flag = FLAG_MAP.get(country, "🏳️")
    logo = SECTOR_EMOJI.get(sector, "🏢")

    # Title
    parts = []
    if r12: parts.append(f"-{r12:.0f}% d'émissions")
    if classification: parts.append(f"aligné {classification}")
    title = " — ".join(parts) if parts else "Objectifs SBTi validés"

    # Summary - clean up target language
    summary = ""
    if target_lang and len(target_lang) > 30:
        s = re.sub(r'https?://\S+\s*', '', target_lang)
        s = re.sub(r'This target was approved.*?(?:SMEs|enterprises)\.\s*', '', s, flags=re.DOTALL|re.I)
        s = re.sub(r'^Near-[Tt]erm [Tt]argets?:?\s*', '', s.strip())
        s = re.sub(r'^Overall [Nn]et-[Zz]ero [Tt]arget:?\s*', '', s.strip())
        summary = (s[:300] + "...") if len(s) > 300 else s
    if not summary:
        summary = f"{name} a fait valider ses objectifs SBTi ({classification or 'Accord de Paris'}). Secteur : {sector}."

    # Stats
    stats = []
    if r12: stats.append({"value": f"-{r12:.0f}%", "label": "réduction Scope 1&2", "color": "#059669"})
    if r3: stats.append({"value": f"-{r3:.0f}%", "label": "réduction Scope 3", "color": "#D97706"})
    if classification: stats.append({"value": classification, "label": "alignement", "color": "#0284C7"})
    if nz_status == "Targets set" and nz_year:
        stats.append({"value": str(nz_year), "label": "objectif net zero", "color": "#7C3AED"})
    elif target_year:
        stats.append({"value": str(target_year), "label": "horizon cible", "color": "#7C3AED"})
    if not stats:
        stats.append({"value": "SBTi", "label": "validé", "color": "#0284C7"})

    # Scope
    scope = "Net Zero" if nz_status == "Targets set" else ("Scope 3" if r3 else "Scope 1 & 2")

    # Target text
    tt = f"SBTi validé — {classification or 'Accord de Paris'}"
    if target_year: tt += f" (horizon {target_year})"
    if nz_status == "Targets set" and nz_year: tt += f" — Net Zero {nz_year}"

    # Actions
    actions = []
    if r12: actions.append(f"Réduction de {r12:.0f}% des émissions Scope 1&2 d'ici {target_year or '?'}")
    if r3: actions.append(f"Réduction de {r3:.0f}% des émissions Scope 3")
    actions.append(f"Trajectoire alignée {classification or 'Accord de Paris'}")
    if nz_status == "Targets set": actions.append(f"Engagement Net Zero d'ici {nz_year or '?'}")

    return {
        "id": gen_id(name), "company": name, "title": title,
        "sector": sector, "region": region, "scope": scope,
        "source": "SBTi", "country": country or "?",
        "countryFlag": flag, "year": 2025, "logo": logo, "size": size,
        "summary": summary, "actions": actions, "stats": stats,
        "target": tt, "difficulty": "", "roi": "",
        "sourceUrl": "https://sciencebasedtargets.org/target-dashboard",
        "lastUpdated": datetime.now().strftime("%Y-%m-%d"),
        "contributors": ["Import automatique SBTi"],
        "verified": True, "autoImport": True,
    }


def load_ademe():
    """Try to load ADEME bilans GES data."""
    print("\n  Tentative ADEME...")
    try:
        h = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(ADEME_CSV_URL, timeout=60, headers=h)
        resp.raise_for_status()
        reader = csv.DictReader(io.StringIO(resp.text))
        ademe = {}
        for row in reader:
            name = (row.get("organization_name") or "").strip()
            if not name: continue
            s1 = row.get("total_scope_1") or ""
            s2 = row.get("total_scope_2") or ""
            s3 = row.get("total_scope_3") or ""
            try:
                total = float(s1 or 0) + float(s2 or 0)
            except:
                total = 0
            if total > 0:
                ademe[name.lower()] = {
                    "scope1": s1, "scope2": s2, "scope3": s3,
                    "total_s12": total,
                    "year": row.get("reporting_year", ""),
                    "sector_ademe": row.get("collectivity_type", ""),
                }
        print(f"  ADEME: {len(ademe)} bilans chargés")
        return ademe
    except Exception as e:
        print(f"  ADEME non disponible: {e}")
        return {}


def enrich_with_ademe(entries, ademe):
    """Add ADEME data to matching entries."""
    if not ademe: return 0
    count = 0
    for entry in entries:
        key = entry["company"].lower().strip()
        if key in ademe:
            d = ademe[key]
            total = d["total_s12"]
            if total > 1000:
                label = f"{total/1000:.0f} ktCO₂" if total > 1000 else f"{total:.0f} tCO₂"
            else:
                label = f"{total:.0f} tCO₂"
            entry["stats"].append({
                "value": label,
                "label": f"émissions Scope 1&2 ({d['year']})",
                "color": "#DC2626"
            })
            entry["source"] = "SBTi + ADEME"
            count += 1
    return count


def main():
    print("=" * 50)
    print("Nouveaux Récits — Build Data")
    print("=" * 50)

    # 1. SBTi
    print("\n1. SBTi...")
    f = SBTI_LOCAL if os.path.exists(SBTI_LOCAL) else None
    if not f:
        try:
            os.makedirs("scripts/.cache", exist_ok=True)
            h = {"User-Agent": "Mozilla/5.0", "Referer": "https://sciencebasedtargets.org"}
            r = requests.get(SBTI_URL, timeout=120, headers=h)
            r.raise_for_status()
            f = "scripts/.cache/sbti.xlsx"
            with open(f, "wb") as fh: fh.write(r.content)
        except: pass

    entries = []
    if f:
        print(f"  Fichier: {f}")
        wb = openpyxl.load_workbook(f, read_only=True, data_only=True)
        ws = wb.active
        headers = None
        total = 0
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 0:
                headers = list(row)
                continue
            e = build_sbti_entry(dict(zip(headers, row)))
            if e: entries.append(e)
            total += 1
        wb.close()
        print(f"  {total} lignes → {len(entries)} avec objectifs validés")

    # 2. ADEME
    print("\n2. ADEME...")
    ademe = load_ademe()
    if ademe:
        enriched = enrich_with_ademe(entries, ademe)
        print(f"  {enriched} fiches enrichies avec données ADEME")

    # 3. Editorial
    print("\n3. Fiches éditoriales...")
    editorial = []
    if os.path.exists(EDITORIAL_FILE):
        with open(EDITORIAL_FILE, "r", encoding="utf-8") as fh:
            editorial = json.load(fh)
        print(f"  {len(editorial)} fiches")

    # 4. Merge
    print("\n4. Fusion...")
    names = {e["company"].lower().strip() for e in editorial}
    added = [e for e in entries if e["company"].lower().strip() not in names]
    merged = editorial + added
    print(f"  {len(editorial)} éditoriales + {len(added)} SBTi = {len(merged)} total")

    # 5. Write
    print("\n5. Écriture...")
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        json.dump(merged, fh, ensure_ascii=False, indent=2)

    # Stats
    pme = len([e for e in merged if e.get("size") == "PME"])
    nz = len([e for e in merged if e.get("scope") == "Net Zero"])
    fr = len([e for e in merged if e.get("country") == "France"])
    with_red = len([e for e in merged if any("réduction" in s.get("label","") for s in e.get("stats",[]))])
    print(f"\n✅ {len(merged)} projets")
    print(f"   {pme} PME | {nz} Net Zero | {fr} France | {with_red} avec % réduction")


if __name__ == "__main__":
    main()
