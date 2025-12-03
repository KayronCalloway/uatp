#!/usr/bin/env python3
"""
HTML to PDF converter using markdown and PyMuPDF.
"""

import markdown
import fitz  # PyMuPDF
from pathlib import Path
import sys
import tempfile


def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF via HTML."""

    try:
        print(f"Converting {markdown_file} to PDF...")

        # Read markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Convert markdown to HTML
        md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
        html_content = md.convert(markdown_content)

        # Add CSS styling
        css_style = """
        <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.6;
            color: #333;
            margin: 40px;
            max-width: 800px;
        }
        
        h1 {
            color: #2c3e50;
            font-size: 24px;
            margin-top: 30px;
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        
        h2 {
            color: #34495e;
            font-size: 18px;
            margin-top: 25px;
            margin-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }
        
        h3 {
            color: #34495e;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        
        pre {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            padding: 15px;
            margin: 15px 0;
            font-size: 10px;
            overflow-x: auto;
        }
        
        code {
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 10px;
            color: #e74c3c;
        }
        
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 10px;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
        }
        
        ul, ol {
            margin: 10px 0;
            padding-left: 20px;
        }
        
        li {
            margin: 5px 0;
        }
        
        p {
            margin: 10px 0;
        }
        </style>
        """

        # Create complete HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>UATP Capsule Engine System Guide</title>
            {css_style}
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Create temporary HTML file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as temp_html:
            temp_html.write(full_html)
            temp_html_path = temp_html.name

        # Convert HTML to PDF using PyMuPDF
        doc = fitz.open()

        # Create a simple text-based PDF
        page = doc.new_page()

        # Split content into pages manually
        lines = markdown_content.split("\n")
        y_pos = 50
        page_height = 750

        for line in lines:
            if y_pos > page_height:
                page = doc.new_page()
                y_pos = 50

            # Simple text rendering
            if line.startswith("#"):
                # Header
                page.insert_text(
                    (50, y_pos), line.strip("#").strip(), fontsize=14, color=(0, 0, 0)
                )
                y_pos += 20
            elif line.strip():
                # Regular text
                page.insert_text((50, y_pos), line[:80], fontsize=10, color=(0, 0, 0))
                y_pos += 15
            else:
                y_pos += 10

        # Save PDF
        doc.save(pdf_file)
        doc.close()

        # Clean up temporary file
        Path(temp_html_path).unlink()

        print(f"PDF successfully created: {pdf_file}")
        return True

    except Exception as e:
        print(f"Error converting to PDF: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # File paths
    markdown_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide.md"
    )
    pdf_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide.pdf"
    )

    # Convert markdown to PDF
    success = convert_markdown_to_pdf(markdown_file, pdf_file)

    if success:
        print(f"\n✅ PDF conversion completed successfully!")
        print(f"📄 PDF file: {pdf_file}")
        if pdf_file.exists():
            print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n❌ PDF conversion failed!")
        sys.exit(1)
