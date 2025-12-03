#!/usr/bin/env python3
"""
Working markdown to PDF converter using markdown-pdf.
"""

import markdown_pdf
from pathlib import Path
import sys


def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF."""

    try:
        print(f"Converting {markdown_file} to PDF...")

        # Read markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Create PDF converter
        converter = markdown_pdf.MarkdownPdf(toc_level=6, mode="commonmark")

        # Add CSS styling
        custom_css = """
        @page {
            size: A4;
            margin: 2cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            font-size: 11px;
            line-height: 1.6;
            color: #333;
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
        """

        # Create a section with the markdown content
        section = markdown_pdf.Section(markdown_content)

        # Add section to PDF
        converter.add_section(section, user_css=custom_css)

        # Save PDF
        converter.save(pdf_file)

        print(f"PDF successfully created: {pdf_file}")
        return True

    except Exception as e:
        print(f"Error converting to PDF: {e}")
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
