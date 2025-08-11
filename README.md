# AI pptx Auditor

A small tool to extract slide text and images from `.pptx` files, send each slide to Gemini for transcription and cleanup, cross-check slides for inconsistencies, and generate a report. The GUI uses `tkinter` to pick a PPTX file. Output files (`extracted_slides.json` and `reports.txt`) are saved in the same folder as the selected PPTX.

---

## Features
- Direct `.pptx` extraction (no `python-pptx`) into slide-wise chunks (texts, tables, images).
- Per-slide processing with Gemini to get cleaned/transcribed slide text.
- Cross-slide consistency/fact-check using Gemini (returns structured JSON of issues & suggestions).
- `reports.txt` saved next to the PPTX; terminal prints the number of issues and the report path.
- Simple `tkinter` file picker UI (no CLI path required).

---

## Quick Start

### 1. Clone the repo
```bash
git clone [https://github.com]/muvva-krishna/AI_PPT_Inspector.git
cd AI_PPT_Inspector
```

### 2. Create a virtual environment and install dependencies
```bash
# Create a virtual environment
python -m venv .venv

# Activate the environment
# On macOS / Linux:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

### 3. Set your Gemini API key
You can set your API key in one of two ways.

**Option A: Create a `.env` file**

Create a file named `.env` in the project root and add your key:
```ini
GEMINI_API_KEY="your_api_key_here"
```

**Option B: Set an environment variable**

Set the key directly in your terminal session.

```bash
# On macOS / Linux:
export GEMINI_API_KEY="your_api_key_here"

# On Windows (Command Prompt - for current session):
set GEMINI_API_KEY="your_api_key_here"

# On Windows (PowerShell - for current session):
$env:GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the app
```bash
python checkdeck.py
```
A file-picker window will open. Choose your `.pptx` file. After processing:

- `extracted_slides.json` and `reports.txt` will be saved in the same directory as your PPTX file.
- The terminal will show how many issues were found and the full path to the `reports.txt` file.

###File Overview
checkdeck.py
Entry point that:

Opens tkinter file dialog

Extracts slides via extractor.py

Sends each slide to Gemini for processing

Saves JSON + runs cross-check

Writes reports.txt in PPTX folder

extractor.py
Reads .pptx as a ZIP archive

Extracts:

Texts (<a:t> tags)

Tables

Images (base64-encoded)

Outputs per-slide structured data

gemini_client.py
Communicates with Gemini API

extract_slide_with_gemini() → cleans/transcribes a slide

compare_slides_with_gemini() → finds inconsistencies between slides

reporter.py
Writes reports.txt listing:

Detected issues (with slide numbers)

Suggestions

utils.py
Helper function: image_to_base64() for encoding images.

###Pipeline
Select .pptx file via GUI

Extract text/images per slide

Process each slide with Gemini

Save results to extracted_slides.json

Cross-check all slides with Gemini

Save report to reports.txt in PPTX folder

Print summary in terminal
