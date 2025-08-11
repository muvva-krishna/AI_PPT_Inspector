import sys
import os
import json
import tkinter as tk
from tkinter import filedialog
from extractor import extract_slides_text_and_images
from gemini_client import extract_slide_with_gemini, compare_slides_with_gemini
from reporter import write_report

def select_pptx_file():
    """Open a file picker to select a PPTX file."""
    root = tk.Tk()
    root.withdraw()  # Hide tkinter root window
    file_path = filedialog.askopenfilename(
        title="Select PPTX file",
        filetypes=[("PowerPoint files", "*.pptx")]
    )
    return file_path

def main():
    # 1) File selection
    pptx_path = select_pptx_file()
    if not pptx_path:
        print("No file selected. Exiting...")
        sys.exit(1)

    print(f"Extracting slides from {pptx_path}...")

    # 2) Extract raw content
    raw_slides = extract_slides_text_and_images(pptx_path)

    # 3) Gemini per-slide extraction
    processed_slides = []
    for slide in raw_slides:
        print(f"Processing slide {slide['slide_number']} with Gemini...")
        raw_text = slide.get("slide_text", "") or " ".join(slide.get("texts", []))
        gemini_out = extract_slide_with_gemini(raw_text, slide.get("images_b64", []))
        slide_text = gemini_out.get("slide_text") if isinstance(gemini_out, dict) else str(gemini_out)
        processed_slides.append({
            "slide_number": slide["slide_number"],
            "slide_text": slide_text
        })

    # 4) Save extracted JSON in same folder as PPTX
    pptx_dir = os.path.dirname(pptx_path)
    json_filename = os.path.join(pptx_dir, "extracted_slides.json")
    with open(json_filename, "w", encoding="utf-8") as jf:
        json.dump({"slides": processed_slides}, jf, ensure_ascii=False, indent=2)
    print(f"Saved extracted slide texts to {json_filename}")

    # 5) Cross-check slides
    print("Comparing slides with Gemini for inconsistencies...")
    results = compare_slides_with_gemini(processed_slides)

    # 6) Save report in same folder as PPTX
    report_path = os.path.join(pptx_dir, "reports.txt")
    write_report(results, len(processed_slides), output_path=report_path)

    # 7) Print summary in terminal
    num_issues = len(results.get("issues", [])) if results else 0
    print(f"\nAnalysis complete: {num_issues} issue(s) found.")
    print(f"Report saved at: {report_path}")

if __name__ == "__main__":
    main()
