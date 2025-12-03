#!/usr/bin/env python3
"""
Simple script to convert Markdown to PDF using Python libraries
"""

import os
import sys
from pathlib import Path

import markdown


def md_to_html(md_file_path):
    """Convert markdown file to HTML string"""
    with open(md_file_path) as f:
        md_content = f.read()

    # Convert Markdown to HTML
    html_content = markdown.markdown(
        md_content, extensions=["extra", "codehilite", "tables", "toc"]
    )

    # Add HTML header, CSS styling for better appearance
    full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>UATP Capsule Engine Master Guide</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #3498db;
                margin-top: 30px;
            }}
            h3 {{
                color: #2980b9;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 3px;
                padding: 15px;
                overflow: auto;
            }}
            code {{
                background-color: #f8f8f8;
                border-radius: 3px;
                padding: 2px 5px;
                font-family: Consolas, Monaco, 'Andale Mono', monospace;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px 12px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            blockquote {{
                background-color: #f9f9f9;
                border-left: 4px solid #ccc;
                padding: 10px 20px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    return full_html


def save_html(html_content, output_path):
    """Save HTML content to file"""
    with open(output_path, "w") as f:
        f.write(html_content)
    print(f"HTML saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python md_to_pdf.py <path_to_markdown_file>")
        sys.exit(1)

    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found")
        sys.exit(1)

    # Generate output file paths
    md_path = Path(md_file)
    output_dir = Path("docs/pdf")
    output_dir.mkdir(exist_ok=True, parents=True)

    html_output = output_dir / f"{md_path.stem}.html"

    # Convert to HTML
    html_content = md_to_html(md_file)
    save_html(html_content, html_output)

    print("\nConversion complete!")
    print(f"\nHTML file: {html_output}")
    print(
        "\nTo create a PDF, open the HTML file in a web browser and use Print > Save as PDF"
    )
