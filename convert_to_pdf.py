#!/usr/bin/env python3
"""
Convert UATP Capsule Engine markdown documentation to PDF.
"""

import markdown
import weasyprint
from pathlib import Path


def convert_markdown_to_pdf(markdown_file, pdf_file):
    """Convert markdown file to PDF with professional styling."""

    # Read markdown content
    with open(markdown_file, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=["codehilite", "toc", "tables", "fenced_code"])
    html_content = md.convert(markdown_content)

    # CSS styling for professional PDF
    css_style = """
    <style>
    @page {
        size: A4;
        margin: 2cm;
        @bottom-center {
            content: "UATP Capsule Engine System Guide - Page " counter(page);
            font-size: 10px;
            color: #666;
        }
    }
    
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 11px;
        line-height: 1.6;
        color: #333;
        max-width: 100%;
    }
    
    h1 {
        color: #2c3e50;
        font-size: 24px;
        margin-top: 30px;
        margin-bottom: 20px;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        page-break-before: always;
    }
    
    h1:first-child {
        page-break-before: avoid;
        text-align: center;
        font-size: 32px;
        color: #2c3e50;
        margin-bottom: 30px;
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
    
    h4 {
        color: #34495e;
        font-size: 14px;
        margin-top: 15px;
        margin-bottom: 8px;
    }
    
    p {
        margin-bottom: 12px;
        text-align: justify;
    }
    
    ul, ol {
        margin-bottom: 15px;
        padding-left: 20px;
    }
    
    li {
        margin-bottom: 5px;
    }
    
    code {
        background-color: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 10px;
        color: #e74c3c;
    }
    
    pre {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 15px;
        margin: 15px 0;
        overflow-x: auto;
        font-size: 10px;
        line-height: 1.4;
    }
    
    pre code {
        background-color: transparent;
        padding: 0;
        color: #333;
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
        color: #2c3e50;
    }
    
    tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    blockquote {
        border-left: 4px solid #3498db;
        padding-left: 15px;
        margin: 15px 0;
        color: #666;
        font-style: italic;
    }
    
    .toc {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 20px;
        margin: 20px 0;
    }
    
    .toc h2 {
        margin-top: 0;
        color: #2c3e50;
    }
    
    .toc ul {
        list-style-type: none;
        padding-left: 0;
    }
    
    .toc li {
        margin-bottom: 3px;
    }
    
    .toc a {
        color: #3498db;
        text-decoration: none;
    }
    
    .toc a:hover {
        text-decoration: underline;
    }
    
    .page-break {
        page-break-before: always;
    }
    
    /* API endpoint styling */
    .api-endpoint {
        background-color: #e8f5e8;
        border-left: 4px solid #27ae60;
        padding: 10px;
        margin: 10px 0;
        border-radius: 3px;
    }
    
    /* Warning boxes */
    .warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
        border-radius: 3px;
    }
    
    /* Info boxes */
    .info {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 10px;
        margin: 10px 0;
        border-radius: 3px;
    }
    
    /* Print-specific styles */
    @media print {
        body {
            font-size: 10px;
        }
        
        h1 {
            font-size: 22px;
        }
        
        h2 {
            font-size: 16px;
        }
        
        h3 {
            font-size: 14px;
        }
        
        pre {
            font-size: 9px;
        }
        
        table {
            font-size: 9px;
        }
    }
    </style>
    """

    # Create full HTML document
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UATP Capsule Engine System Guide</title>
        {css_style}
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Convert HTML to PDF
    try:
        print(f"Converting {markdown_file} to PDF...")
        html_doc = weasyprint.HTML(string=full_html)
        html_doc.write_pdf(pdf_file)
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
        print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n❌ PDF conversion failed!")
