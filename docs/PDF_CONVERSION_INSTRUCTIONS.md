
# Converting UATP Manual to PDF

## Method 1: Using Browser (Recommended)
1. Open the HTML manual: docs/UATP_Capsule_Engine_Manual.html
2. Press Ctrl+P (or Cmd+P on Mac)
3. Select "Save as PDF" as destination
4. Choose "More settings" and select:
   - Paper size: A4 or Letter
   - Margins: Normal
   - Options: Headers and footers (unchecked)
5. Click "Save"

## Method 2: Install Pandoc (Best Quality)
```bash
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt-get install pandoc

# Windows
choco install pandoc

# Then generate PDF
pandoc docs/COMPREHENSIVE_SYSTEM_MANUAL.md -o docs/UATP_Manual.pdf --pdf-engine=xelatex --toc
```

## Method 3: Online Converters
1. Go to https://pandoc.org/try/
2. Upload docs/COMPREHENSIVE_SYSTEM_MANUAL.md
3. Select "from: markdown" and "to: pdf"
4. Click "Convert"

## Method 4: Python Libraries
```bash
pip install markdown2 weasyprint
python3 generate_simple_pdf.py
```

The HTML version is already optimized for printing and PDF conversion.
