import zipfile
import re
from pathlib import Path

docx_path = Path(r"c:\Users\Narahari\Downloads\ORCA_AI_Website_Maintenance_Agent_Research.docx")
out_path = Path(r"c:\Users\Narahari\Projects\Ai website Agent\AI-Website-Reliability-Engineer\_extracted_orca.txt")

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

with zipfile.ZipFile(docx_path, "r") as z:
    xml = z.read("word/document.xml").decode("utf-8")

body_match = re.search(r"<w:body>(.*)</w:body>", xml, re.DOTALL)
body = body_match.group(1) if body_match else xml

def paragraph_style(p_xml):
    m = re.search(r"<w:pStyle w:val=\"([^\"]+)\"", p_xml)
    return m.group(1) if m else None

def text_from_xml(fragment):
    parts = []
    for m in re.finditer(r"<w:tab\s*/>", fragment):
        pass
    # sequential parse for t, tab, br
    pos = 0
    for m in re.finditer(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:tab\s*/>|<w:br\s*/>", fragment):
        if m.group(1) is not None:
            parts.append(m.group(1))
        elif "<w:tab" in m.group(0):
            parts.append("\t")
        else:
            parts.append("\n")
    return "".join(parts)

lines = []
# split top-level body children roughly
for block in re.finditer(r"<w:p\b.*?</w:p>|<w:tbl\b.*?</w:tbl>", body, re.DOTALL):
    block_xml = block.group(0)
    if block_xml.startswith("<w:p"):
        text = text_from_xml(block_xml).strip()
        style = paragraph_style(block_xml)
        if not text:
            lines.append("")
            continue
        if style and ("Heading" in style or style == "Title"):
            lvl = 1
            for i in range(1, 10):
                if str(i) in style:
                    lvl = i
                    break
            lines.append("#" * lvl + " " + text)
        else:
            lines.append(text)
    else:
        for row in re.finditer(r"<w:tr\b.*?</w:tr>", block_xml, re.DOTALL):
            cells = []
            for cell in re.finditer(r"<w:tc\b.*?</w:tc>", row.group(0), re.DOTALL):
                cells.append(text_from_xml(cell.group(0)).strip())
            if any(cells):
                lines.append(" | ".join(cells))
        lines.append("")

full = "\n".join(lines)
out_path.write_text(full, encoding="utf-8")
print(full)
print("---END---")
