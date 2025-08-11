import zipfile
import os
import xml.etree.ElementTree as ET
from utils import image_to_base64

def extract_slides_text_and_images(path):
    """
    Extracts slide-wise text, table data, and base64 images from a PPTX file without python-pptx.

    Returns:
    [
        {
            "slide_number": int,
            "slide_text": "concatenated text",
            "texts": [lines],
            "tables": [[[cell1, cell2, ...], ...]],
            "images_b64": [b64str]
        },
        ...
    ]
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"PPTX file not found: {path}")

    slides_data = []

    with zipfile.ZipFile(path, 'r') as z:
        # Collect slide files and sort by numeric index
        slide_files = sorted(
            [f for f in z.namelist() if f.startswith("ppt/slides/slide") and f.endswith(".xml")],
            key=lambda x: int(''.join(filter(str.isdigit, os.path.basename(x))) or 0)
        )

        # Namespaces commonly used in pptx slide XMLs
        ns = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        }

        for slide_file in slide_files:
            # derive slide number from filename (e.g., slide1.xml)
            base = os.path.basename(slide_file)
            slide_num = int(''.join(filter(str.isdigit, base)) or 0)

            texts = []
            tables = []
            images_b64 = []

            try:
                raw = z.read(slide_file)
                root = ET.fromstring(raw)
            except Exception:
                root = None

            if root is not None:
                # extract all text nodes <a:t>
                for t in root.findall(".//a:t", ns):
                    if t.text and t.text.strip():
                        texts.append(t.text.strip())

                # extract tables (<a:tbl>)
                for tbl in root.findall(".//a:tbl", ns):
                    table_data = []
                    for row in tbl.findall(".//a:tr", ns):
                        row_data = []
                        for cell in row.findall(".//a:tc", ns):
                            cell_texts = [tx.text.strip() for tx in cell.findall(".//a:t", ns) if tx.text]
                            row_data.append(" ".join(cell_texts))
                        table_data.append(row_data)
                    if table_data:
                        tables.append(table_data)

                # find images referenced in slide rels
                rels_path = f"ppt/slides/_rels/{base}.rels"
                if rels_path in z.namelist():
                    try:
                        rels_raw = z.read(rels_path)
                        rels_root = ET.fromstring(rels_raw)
                        # relationships use the Target attribute with r namespace
                        for rel in rels_root.findall(".//"):
                            target = rel.attrib.get(f"{{{ns['r']}}}Target") or rel.attrib.get("Target")
                            if target and target.startswith("../media/"):
                                media_name = os.path.basename(target)
                                img_zip_path = f"ppt/media/{media_name}"
                                if img_zip_path in z.namelist():
                                    try:
                                        img_bytes = z.read(img_zip_path)
                                        images_b64.append(image_to_base64(img_bytes))
                                    except Exception:
                                        # skip unreadable media
                                        pass
                    except Exception:
                        # If rels are malformed, skip images for this slide
                        pass

            slide_text_combined = " ".join(texts).strip()
            slides_data.append({
                "slide_number": slide_num,
                "slide_text": slide_text_combined,
                "texts": texts,
                "tables": tables,
                "images_b64": images_b64
            })

    # Ensure slides ordered by slide_number ascending
    slides_data = sorted(slides_data, key=lambda s: s["slide_number"])
    return slides_data
