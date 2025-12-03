#!/usr/bin/env python3
"""
Final PDF converter with proper font handling.
"""

import fitz  # PyMuPDF
from pathlib import Path
import sys
import re
import textwrap


def create_final_pdf(markdown_file, pdf_file):
    """Create a well-formatted PDF from markdown."""

    try:
        print(f"Creating PDF from {markdown_file}...")

        # Read markdown content
        with open(markdown_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Create PDF document
        doc = fitz.open()

        # Document settings
        page_width = 595  # A4 width
        page_height = 842  # A4 height
        margin = 50

        # Current page and position
        page = doc.new_page()
        y_pos = margin

        # Colors
        title_color = (0.17, 0.24, 0.31)  # Dark blue
        header_color = (0.20, 0.29, 0.37)  # Blue-gray
        body_color = (0.2, 0.2, 0.2)  # Dark gray

        def add_new_page():
            nonlocal page, y_pos
            page = doc.new_page()
            y_pos = margin

        def check_page_space(needed_space):
            nonlocal y_pos
            if y_pos + needed_space > page_height - margin:
                add_new_page()

        def add_title(text, font_size=24):
            nonlocal y_pos
            check_page_space(font_size + 20)
            page.insert_text(
                (margin, y_pos), text, fontsize=font_size, color=title_color
            )
            y_pos += font_size + 20

        def add_header(text, level=1):
            nonlocal y_pos
            font_sizes = {1: 18, 2: 16, 3: 14, 4: 12}
            font_size = font_sizes.get(level, 12)

            check_page_space(font_size + 15)

            # Add some space before headers (except level 1)
            if level > 1:
                y_pos += 10

            page.insert_text(
                (margin, y_pos), text, fontsize=font_size, color=header_color
            )
            y_pos += font_size + 15

        def add_text(text, font_size=11):
            nonlocal y_pos
            if not text.strip():
                y_pos += 10
                return

            # Wrap text to fit page width
            wrapped_lines = textwrap.wrap(text, width=75)

            for line in wrapped_lines:
                check_page_space(font_size + 5)
                page.insert_text(
                    (margin, y_pos), line, fontsize=font_size, color=body_color
                )
                y_pos += font_size + 5

            y_pos += 5  # Extra space after paragraph

        def add_code_block(text):
            nonlocal y_pos
            lines = text.split("\n")

            # Add background rectangle
            rect_height = len(lines) * 12 + 20
            check_page_space(rect_height)

            rect = fitz.Rect(
                margin - 5, y_pos - 5, page_width - margin + 5, y_pos + rect_height - 5
            )
            page.draw_rect(rect, color=(0.95, 0.95, 0.95), fill=(0.95, 0.95, 0.95))

            for line in lines:
                if line.strip():
                    # Truncate long lines
                    display_line = line[:90] + "..." if len(line) > 90 else line
                    page.insert_text(
                        (margin, y_pos), display_line, fontsize=9, color=body_color
                    )
                y_pos += 12

            y_pos += 10

        def add_list_item(text, level=0):
            nonlocal y_pos
            indent = margin + (level * 20)
            bullet = "•" if level == 0 else "◦"

            check_page_space(15)
            # Wrap long list items
            wrapped_text = textwrap.wrap(text, width=65)
            for i, line in enumerate(wrapped_text):
                if i == 0:
                    page.insert_text(
                        (indent, y_pos),
                        f"{bullet} {line}",
                        fontsize=11,
                        color=body_color,
                    )
                else:
                    page.insert_text(
                        (indent + 15, y_pos), line, fontsize=11, color=body_color
                    )
                y_pos += 15

        # Parse markdown content
        lines = content.split("\n")
        in_code_block = False
        code_content = []

        # Add title page
        add_title("UATP Capsule Engine", 32)
        add_title("System Guide", 24)
        y_pos += 50
        add_text("Comprehensive AI reasoning trace management system")
        add_text("with federated model registry capabilities")
        y_pos += 100
        add_text("Generated from comprehensive system documentation")

        add_new_page()

        for line in lines:
            # Handle code blocks
            if line.startswith("```"):
                if in_code_block:
                    add_code_block("\n".join(code_content))
                    code_content = []
                    in_code_block = False
                else:
                    in_code_block = True
                continue

            if in_code_block:
                code_content.append(line)
                continue

            # Handle headers
            if line.startswith("#"):
                header_level = len(line) - len(line.lstrip("#"))
                header_text = line.strip("#").strip()

                if header_level == 1:
                    if header_text.lower() != "uatp capsule engine system guide":
                        add_new_page()

                add_header(header_text, header_level)

            # Handle list items
            elif line.startswith("- ") or line.startswith("* "):
                item_text = line[2:].strip()
                add_list_item(item_text)

            # Handle numbered lists
            elif re.match(r"^\d+\.", line):
                item_text = re.sub(r"^\d+\.\s*", "", line)
                add_list_item(item_text)

            # Handle regular text
            elif line.strip():
                # Skip markdown table syntax and other formatting
                if (
                    not line.startswith("|")
                    and not line.startswith("---")
                    and not line.startswith("```")
                ):
                    # Clean up markdown formatting
                    clean_line = re.sub(r"\*\*(.*?)\*\*", r"\1", line)  # Remove bold
                    clean_line = re.sub(
                        r"\*(.*?)\*", r"\1", clean_line
                    )  # Remove italic
                    clean_line = re.sub(r"`(.*?)`", r"\1", clean_line)  # Remove code
                    clean_line = re.sub(
                        r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_line
                    )  # Remove links
                    add_text(clean_line)

            # Empty line
            else:
                y_pos += 10

        # Add page numbers
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page.insert_text(
                (page_width - 100, page_height - 30),
                f"Page {page_num + 1} of {doc.page_count}",
                fontsize=10,
                color=(0.5, 0.5, 0.5),
            )

        # Save PDF
        doc.save(pdf_file)
        doc.close()

        print(f"PDF successfully created: {pdf_file}")
        return True

    except Exception as e:
        print(f"Error creating PDF: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    # File paths
    markdown_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide.md"
    )
    pdf_file = Path(
        "/Users/kay/uatp-capsule-engine/UATP_Capsule_Engine_System_Guide_Final.pdf"
    )

    # Create final PDF
    success = create_final_pdf(markdown_file, pdf_file)

    if success:
        print(f"\n✅ PDF creation completed successfully!")
        print(f"📄 PDF file: {pdf_file}")
        if pdf_file.exists():
            print(f"📊 File size: {pdf_file.stat().st_size / 1024:.1f} KB")
    else:
        print("\n❌ PDF creation failed!")
        sys.exit(1)
