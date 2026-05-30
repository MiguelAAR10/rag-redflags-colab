"""
RAG Core Loaders — PDF parsing for Red Flags guide (REWORK v2).

Extracts LOGICAL documentary units from OCP Red Flags PDF.
Corrections from Fase 1.1 review:
- indicator_name: extracted from page title (largest font spans), not Definition text
- family: mapped from inferred Stage (Planning/Tender/Award/Contract) → 4 families, 0 unknown
- Logical units: split by section headers (core/formula/example), not char count
- block_type for linked sub-units
- Clean text: no page numbers or layout labels
"""

import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter

import fitz


PDF_PATH = Path("data/raw/OCP2024-RedFlagProcurement-1.pdf")
OUTPUT_PATH = Path("data/processed/redflags_units.jsonl")

# Known section headers (exclude from title extraction)
KNOWN_HEADERS = {
    "definition", "why is this a red flag?", "unit of analysis",
    "type of red flag", "stage", "source", "required data fields",
    "methodology", "example", "data fields needed", "ocds fields",
    "why is this a red flag", "collusion risks", "bid-rigging",
    "fraud", "low competition", "low transparency",
}


def clean_text(text: str) -> str:
    """Clean text: normalize whitespace, remove standalone page numbers."""
    # Remove standalone page numbers at start or as lines
    text = re.sub(r'^(\d{1,3})\s*\n', '\n', text)
    text = re.sub(r'\n\s*\d{1,3}\s*\n', '\n', text)
    # Normalize whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    return text


def extract_page_info(page: fitz.Page) -> Dict:
    """Extract structured info from a page."""
    blocks = page.get_text("dict")["blocks"]
    full_text = page.get_text()
    
    # Extract lines with font sizes
    lines = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = ""
            line_size = 0
            for span in line["spans"]:
                line_text += span["text"]
                line_size = max(line_size, span["size"])
            lines.append({
                "text": line_text.strip(),
                "size": line_size,
            })
    
    return {
        "lines": lines,
        "full_text": full_text,
    }


def extract_indicator_title(page_info: Dict) -> Optional[str]:
    """Extract indicator title from largest non-header spans."""
    candidates = []
    for line in page_info["lines"]:
        text = line["text"]
        size = line["size"]
        if size >= 16 and len(text) > 3 and not text.isdigit():
            text_lower = text.lower()
            is_header = any(header in text_lower for header in KNOWN_HEADERS)
            if not is_header:
                candidates.append((size, text))
    
    if not candidates:
        return None
    
    # Sort by size descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_size = candidates[0][0]
    
    # Get all lines with size >= best_size - 2
    best_lines = [t for s, t in candidates if s >= best_size - 2]
    
    if best_lines:
        title = " ".join(best_lines)
        title = re.sub(r'\s+', ' ', title)
        # Remove Rxxx code
        title = re.sub(r'\s*R\d{3}\s*$', '', title)
        title = re.sub(r'^\s*R\d{3}\s*', '', title)
        title = title.strip()
        return title if len(title) > 3 else None
    
    return None


def extract_indicator_code(page_info: Dict) -> Optional[str]:
    """Extract Rxxx code from page text."""
    text = page_info["full_text"]
    codes = re.findall(r'R\d{3}', text)
    return codes[0] if codes else None


def infer_stage_from_title(title: str) -> str:
    """Infer OCDS stage from indicator title using keyword matching."""
    title_lower = title.lower()
    
    # Contract/Implementation - very specific keywords first
    contract_keywords = [
        'contract', 'delivery', 'subcontract', 'amendment', 'modification', 
        'signature', 'transaction', 'price increase', 'reduce line', 'increase line',
        'work completed', 'specifications', 'losing bidders hired', 'contractor subcontracts',
        'prevalence of subcontracts', 'decision period', 'contract is not published',
        'contract has modifications', 'contract amount', 'value and final contract amount',
        'contract signature date', 'supplier followed by', 'heterogeneous supplier',
        'supplier is not traceable', 'small initial purchase'
    ]
    for kw in contract_keywords:
        if kw in title_lower:
            return 'contract'
    
    # Award - specific keywords
    award_keywords = [
        'award', 'winning', 'disqualified', 'identical bid', 'late bid won',
        'bid rotation', 'heavily discounted', 'award value', 'direct award',
        'below threshold', 'change orders', 'award criteria', 'all except winning',
        'lowest bid disqualified', 'poorly supported disqualifications',
        'excessive disqualified', 'high share of buyer', 'high market share',
        'high market concentration', 'losing bidder', 'buyer\'s contracts',
        'excessive unsuccessful bids', 'missing bidders', 'prevalence of consortia',
        'co-bidding pairs', 'recurrent winner', 'multiple direct awards'
    ]
    for kw in award_keywords:
        if kw in title_lower:
            return 'award'
    
    # Tender - specific keywords
    tender_keywords = [
        'tender', 'bid', 'bidding', 'submission', 'prequalification', 'participation',
        'complaint', 'consortia', 'missing bidders', 'unsuccessful bids',
        'time between', 'advertising', 'opening', 'evaluation', 'single bid',
        'low number of bidders', 'fixed-multiple', 'disparity', 'close to winning',
        'short time between', 'long time between', 'the submission period',
        'unreasonable technical specifications', 'unreasonable participation fees',
        'cost of the bidding documents', 'non competitive procedure',
        'unreasonably low or high line item', 'line item'
    ]
    for kw in tender_keywords:
        if kw in title_lower:
            return 'tender'
    
    # Planning - specific keywords
    planning_keywords = [
        'planning', 'documents', 'advertise', 'request for bids',
        'non-competitive methods', 'procurement plan', 'procurement thresholds',
        'manipulation of procurement'
    ]
    for kw in planning_keywords:
        if kw in title_lower:
            return 'planning'
    
    return 'unknown'


def stage_to_family(stage: str) -> str:
    """Map OCDS stage to family."""
    mapping = {
        'planning': 'planeacion',
        'tender': 'competencia/licitacion',
        'award': 'adjudicacion',
        'contract': 'ejecucion/contrato',
    }
    return mapping.get(stage, 'unknown')


def is_indicator_page(page_info: Dict) -> bool:
    """Check if page is an indicator definition page."""
    text = page_info["full_text"]
    return "Definition" in text and "Why is this a red flag" in text and bool(re.search(r'R\d{3}', text))


def split_indicator_blocks(text: str) -> List[Tuple[str, str]]:
    """Split indicator text into logical blocks by section headers."""
    text = clean_text(text)
    
    # Define headers and their block types
    header_to_type = {
        'definition': 'core',
        'why is this a red flag': 'core',
        'unit of analysis': 'core',
        'type of red flag': 'core',
        'stage': 'core',
        'source': 'core',
        'example': 'example',
        'methodology': 'formula',
        'required data fields': 'formula',
        'data fields needed': 'formula',
        'ocds fields': 'formula',
    }
    
    # Find all header positions
    header_positions = []
    for header, btype in header_to_type.items():
        # Match header at start of line or after newline
        pattern = r'(?:^|\n)\s*' + re.escape(header) + r'\s*(?:\?|:)?\s*(?=\n|$)'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            header_positions.append((match.start(), header, btype))
    
    header_positions.sort()
    
    if not header_positions:
        return [('core', text)]
    
    # Group consecutive positions by block type
    blocks = []
    current_type = None
    current_start = None
    
    for pos, header, btype in header_positions:
        if btype != current_type:
            # Save previous block
            if current_type is not None and current_start is not None:
                end_pos = pos
                block_text = text[current_start:end_pos].strip()
                if block_text and len(block_text) > 30:
                    blocks.append((current_type, block_text))
            current_type = btype
            current_start = pos
    
    # Save last block
    if current_type is not None and current_start is not None:
        block_text = text[current_start:].strip()
        if block_text and len(block_text) > 30:
            blocks.append((current_type, block_text))
    
    if not blocks:
        return [('core', text)]
    
    return blocks


def process_indicator_page(page_num: int, page_info: Dict) -> List[Dict]:
    """Process an indicator page into logical units."""
    title = extract_indicator_title(page_info)
    code = extract_indicator_code(page_info)
    stage = infer_stage_from_title(title) if title else 'unknown'
    family = stage_to_family(stage)
    
    blocks = split_indicator_blocks(page_info["full_text"])
    
    units = []
    parent_id = None
    
    for block_type, block_text in blocks:
        # Clean block text more aggressively
        block_text = clean_text(block_text)
        if len(block_text) < 30:
            continue
            
        text_hash = hashlib.md5(block_text.encode()).hexdigest()[:12]
        doc_id = f"ocp_{code or 'unk'}_{block_type}_{text_hash}"
        
        unit = {
            "doc_id": doc_id,
            "parent_doc_id": parent_id if parent_id else None,
            "source_file": "OCP2024-RedFlagProcurement-1.pdf",
            "page_start": page_num,
            "page_end": page_num,
            "section": "indicator",
            "block_type": block_type,
            "family": family,
            "stage": stage,
            "indicator_code": code,
            "indicator_name": title,
            "hash": text_hash,
            "text": block_text,
        }
        
        units.append(unit)
        
        if parent_id is None:
            parent_id = doc_id
    
    return units


def extract_methodology_sections(page_info: Dict) -> List[Tuple[str, str]]:
    """Split methodology page into sections by headers."""
    text = page_info["full_text"]
    text = clean_text(text)
    
    if len(text) < 100:
        return []
    
    # Find headers: lines with font size >= 14
    headers = []
    for line in page_info["lines"]:
        if line["size"] >= 14 and len(line["text"].strip()) > 3:
            t = line["text"].strip()
            if not t.isdigit():
                headers.append(t)
    
    if len(headers) < 2:
        # Not enough headers, use page as one section
        title = headers[0] if headers else "General"
        return [(title, text)]
    
    # Find header positions in text
    header_positions = []
    for title in headers:
        # Escape special regex chars
        escaped = re.escape(title)
        for match in re.finditer(escaped, text):
            header_positions.append((match.start(), title))
    
    header_positions.sort()
    
    # Deduplicate by position
    seen_pos = set()
    unique_positions = []
    for pos, title in header_positions:
        # Check if within 10 chars of existing
        if not any(abs(pos - p) < 10 for p in seen_pos):
            seen_pos.add(pos)
            unique_positions.append((pos, title))
    
    sections = []
    for i, (pos, title) in enumerate(unique_positions):
        start = pos + len(title)
        end = unique_positions[i + 1][0] if i + 1 < len(unique_positions) else len(text)
        section_text = text[start:end].strip()
        if section_text and len(section_text) > 50:
            sections.append((title, section_text))
    
    if not sections:
        # Fallback: treat whole text as one section
        return [(headers[0] if headers else "General", text)]
    
    return sections


def process_methodology_page(page_num: int, page_info: Dict) -> List[Dict]:
    """Process a methodology page into section units."""
    sections = extract_methodology_sections(page_info)
    
    units = []
    for title, section_text in sections:
        text_hash = hashlib.md5(section_text.encode()).hexdigest()[:12]
        doc_id = f"ocp_meta_p{page_num:03d}_{text_hash}"
        
        unit = {
            "doc_id": doc_id,
            "parent_doc_id": None,
            "source_file": "OCP2024-RedFlagProcurement-1.pdf",
            "page_start": page_num,
            "page_end": page_num,
            "section": "metodologia",
            "block_type": "section",
            "family": "metodologia",
            "stage": None,
            "indicator_code": None,
            "indicator_name": title,
            "hash": text_hash,
            "text": section_text,
        }
        units.append(unit)
    
    return units


def load_pdf() -> List[Dict]:
    """Main loader: parse PDF into documentary units."""
    print(f"Loading PDF: {PDF_PATH}")
    doc = fitz.open(str(PDF_PATH))
    
    all_units = []
    indicator_pages = 0
    methodology_pages = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_info = extract_page_info(page)
        
        if is_indicator_page(page_info):
            units = process_indicator_page(page_num + 1, page_info)
            all_units.extend(units)
            indicator_pages += 1
        elif len(page_info["full_text"].strip()) > 100:
            units = process_methodology_page(page_num + 1, page_info)
            all_units.extend(units)
            methodology_pages += 1
    
    page_count = len(doc)
    doc.close()
    
    print(f"Pages: {page_count}, Indicator pages: {indicator_pages}, Methodology pages: {methodology_pages}")
    print(f"Total units: {len(all_units)}")
    
    return all_units


def save_units(units: List[Dict], output_path: Path) -> None:
    """Save units to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for unit in units:
            f.write(json.dumps(unit, ensure_ascii=False) + "\n")
    print(f"Saved {len(units)} units to {output_path}")


def generate_report(units: List[Dict]) -> Dict:
    """Generate exploration report with verification metrics."""
    total = len(units)
    indicator_units = [u for u in units if u["section"] == "indicator"]
    methodology_units = [u for u in units if u["section"] == "metodologia"]
    
    # Family distribution
    family_dist = dict(Counter(u.get("family", "unknown") for u in units))
    
    # Stage distribution
    stage_dist = dict(Counter(u.get("stage") or "null" for u in indicator_units))
    
    # Block type distribution
    block_dist = dict(Counter(u.get("block_type", "unknown") for u in units))
    
    # Indicator name coverage
    ind_with_name = sum(1 for u in indicator_units if u.get("indicator_name"))
    ind_total = len(indicator_units)
    name_coverage = (ind_with_name / ind_total * 100) if ind_total > 0 else 0
    
    # Verification
    unknown_family = family_dist.get("unknown", 0)
    required_families = {"planeacion", "competencia/licitacion", "adjudicacion", "ejecucion/contrato"}
    present_families = set(family_dist.keys()) - {"metodologia", "unknown"}
    missing_families = list(required_families - present_families)
    
    criteria_passed = (
        total >= 100 and
        name_coverage >= 95 and
        unknown_family == 0 and
        len(missing_families) == 0
    )
    
    report = {
        "total_units": total,
        "indicator_pages": len(set(u["page_start"] for u in indicator_units)),
        "indicator_units": len(indicator_units),
        "methodology_units": len(methodology_units),
        "family_distribution": family_dist,
        "stage_distribution": stage_dist,
        "block_type_distribution": block_dist,
        "indicator_name_coverage_pct": round(name_coverage, 1),
        "indicator_name_coverage_count": f"{ind_with_name}/{ind_total}",
        "unknown_family_count": unknown_family,
        "missing_families": missing_families,
        "all_families_present": len(missing_families) == 0,
        "target_met": total >= 100,
        "criteria_passed": criteria_passed,
        "sample_units": units[:2] if units else [],
    }
    
    return report


if __name__ == "__main__":
    units = load_pdf()
    save_units(units, OUTPUT_PATH)
    
    report = generate_report(units)
    print("\n=== EXPLORATION REPORT ===")
    for key, value in report.items():
        if key not in ["sample_units"]:
            print(f"  {key}: {value}")
    
    report_path = Path("progress/evidence/fase1-exploration-report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nReport saved to {report_path}")
    
    if report["criteria_passed"]:
        print("\n✅ ALL CRITERIA PASSED")
    else:
        print("\n❌ SOME CRITERIA FAILED")