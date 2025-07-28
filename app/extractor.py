import os
import re
import json
import fitz  # PyMuPDF

def is_all_caps(text):
    return text.isupper() and len(text) > 3

def is_bold(span):
    return 'Bold' in span.get('font', '')

def extract_headings_by_pattern(pdf_path):
    doc = fitz.open(pdf_path)
    outline = []
    title = None
    font_sizes = []
    font_size_counts = {}

    # First pass: collect all font sizes and their counts
    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")['blocks']
        for b in blocks:
            if 'lines' in b:
                for l in b['lines']:
                    for s in l['spans']:
                        sz = s['size']
                        font_sizes.append(sz)
                        font_size_counts[sz] = font_size_counts.get(sz, 0) + 1
    if font_sizes:
        # Only use the single largest font size as heading candidate
        unique_sizes = sorted(list(set(font_sizes)), reverse=True)
        heading_sizes = unique_sizes[:1]
    else:
        heading_sizes = []

    # Second pass: extract headings by number, font size, bold, or all-caps
    for page_num, page in enumerate(doc, start=1):
        lines = page.get_text().split('\n')
        i = 0
        # For font-based heading detection
        blocks = page.get_text("dict")['blocks']
        font_headings = set()
        for b in blocks:
            if 'lines' in b:
                for l in b['lines']:
                    for s in l['spans']:
                        txt = s['text'].strip()
                        if not txt or len(txt) < 5:
                            continue
                        if s['size'] in heading_sizes:
                            # Only treat as heading if also bold or all-caps, or just largest font
                            if is_bold(s) or is_all_caps(txt) or s['size'] == heading_sizes[0]:
                                font_headings.add(txt)
        while i < len(lines):
            line = lines[i].strip()
            if len(line) < 5:
                i += 1
                continue
            # Numbered heading: number only on this line, title on next
            m = re.match(r"^((?:\d+\.){1,3})$", line)
            if m and i + 1 < len(lines):
                heading_text = f"{line} {lines[i+1].strip()}"
                num = line
                if num.count('.') == 2:
                    level = "H3"
                elif num.count('.') == 1:
                    level = "H2"
                elif num.count('.') == 0:
                    level = "H1"
                else:
                    level = None
                if level:
                    if not title and level == "H1":
                        title = heading_text.strip()
                    outline.append({
                        "level": level,
                        "text": heading_text.strip(),
                        "page": page_num
                    })
                i += 2
                continue
            # Numbered heading: number and title on same line
            m2 = re.match(r"^((?:\d+\.){1,3})\s+(.+)", line)
            if m2:
                num = m2.group(1).strip()
                heading_title = m2.group(2).strip()
                heading_text = f"{num} {heading_title}"
                if num.count('.') == 2:
                    level = "H3"
                elif num.count('.') == 1:
                    level = "H2"
                elif num.count('.') == 0:
                    level = "H1"
                else:
                    level = None
                if level:
                    if not title and level == "H1":
                        title = heading_text.strip()
                    outline.append({
                        "level": level,
                        "text": heading_text.strip(),
                        "page": page_num
                    })
            # Font-based heading (unnumbered)
            elif line in font_headings:
                if not any(h['text'] == line and h['page'] == page_num for h in outline):
                    if not title:
                        title = line.strip()
                    outline.append({
                        "level": "H1",
                        "text": line.strip(),
                        "page": page_num
                    })
            i += 1

    if not title:
        title = os.path.splitext(os.path.basename(pdf_path))[0]

    return {
        "title": title.strip() if title else "",
        "outline": outline
    }

def classify_heading(text):
    m = re.match(r"^((?:\d+\.){1,3})\s*(.+)", text)
    if m:
        num = m.group(1).strip()
        title = m.group(2).strip()
        if num.count('.') == 2:
            return "H3", f"{num} {title}"
        elif num.count('.') == 1:
            return "H2", f"{num} {title}"
        elif num.count('.') == 0:
            return "H1", f"{num} {title}"
    return None, None

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    outline = []
    title = None
    if toc:
        for item in toc:
            level, text, page = item
            outline.append({
                "level": f"H{level}",
                "text": text.strip(),
                "page": page
            })
        title = doc.metadata.get("title") or os.path.splitext(os.path.basename(pdf_path))[0]
        return {"title": title.strip(), "outline": outline}
    else:
        return extract_headings_by_pattern(pdf_path)

def main():
    input_dir = "/app/input" if os.path.exists("/app/input") else "app/input"
    output_dir = "/app/output" if os.path.exists("/app/output") else "app/output"
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    print(f"Found {len(pdf_files)} PDF(s)")

    for pdf in pdf_files:
        path = os.path.join(input_dir, pdf)
        output = extract_outline(path)
        output_path = os.path.join(output_dir, os.path.splitext(pdf)[0] + ".json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"[✓] Processed: {pdf} → {len(output['outline'])} headings")

if __name__ == "__main__":
    main()
