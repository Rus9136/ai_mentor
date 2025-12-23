#!/usr/bin/env python3
"""
PDF to Text converter using Tesseract OCR
Converts scanned PDF pages to text with improved quality
"""
import os
import sys
import re
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import subprocess
from pathlib import Path

def preprocess_image(image):
    """
    Preprocess image for better OCR quality
    - Convert to grayscale
    - Increase contrast
    - Sharpen
    - Reduce noise
    """
    # Convert to grayscale
    image = image.convert('L')

    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)

    # Sharpen
    image = image.filter(ImageFilter.SHARPEN)

    # Remove noise with median filter
    image = image.filter(ImageFilter.MedianFilter(size=3))

    return image

def clean_text(text):
    """
    Clean up OCR text:
    - Remove excessive whitespace
    - Fix common OCR errors
    - Remove artifacts
    """
    if not text:
        return ""

    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove lines with only special characters or dots
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines with just spaces
        if not stripped:
            cleaned_lines.append('')
            continue

        # Skip lines that are mostly special characters or dots
        if len(stripped) > 0:
            special_chars = sum(1 for c in stripped if not c.isalnum() and c not in ' -—–')
            if special_chars / len(stripped) > 0.7:
                continue

        # Skip lines with repetitive patterns like "....." or "----"
        if re.match(r'^[.\-_=•*]{4,}$', stripped):
            continue

        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)

    # Remove trailing spaces from each line
    text = '\n'.join(line.rstrip() for line in text.split('\n'))

    # Fix common OCR mistakes (expand as needed)
    text = text.replace('—', '—')  # Normalize dashes
    text = text.replace('–', '–')  # Normalize en-dashes

    return text

def pdf_to_text(pdf_path, output_txt_path, languages='rus+kaz'):
    """
    Convert PDF with scanned images to text using Tesseract OCR

    Args:
        pdf_path: Path to input PDF file
        output_txt_path: Path to output text file
        languages: Tesseract language codes (e.g., 'rus+kaz' for Russian and Kazakh)
    """
    print(f"Converting PDF: {pdf_path}")
    print(f"Using languages: {languages}")

    # Create temporary directory for images
    temp_dir = Path("temp_images")
    temp_dir.mkdir(exist_ok=True)

    # Convert PDF to images with higher DPI for better quality
    print("Converting PDF pages to images...")
    try:
        images = convert_from_path(pdf_path, dpi=400)  # Increased DPI
        total_pages = len(images)
        print(f"Total pages: {total_pages}")
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return False

    # Process each page with OCR
    all_text = []

    for i, image in enumerate(images, start=1):
        print(f"Processing page {i}/{total_pages}...")

        # Preprocess image for better OCR
        processed_image = preprocess_image(image)

        # Save preprocessed image temporarily
        image_path = temp_dir / f"page_{i}.png"
        processed_image.save(image_path, "PNG")

        # Run Tesseract OCR with PSM mode 3 (fully automatic page segmentation)
        try:
            result = subprocess.run(
                ["tesseract", str(image_path), "stdout", "-l", languages, "--psm", "3"],
                capture_output=True,
                text=True,
                check=True
            )
            page_text = result.stdout

            # Clean up the text
            page_text = clean_text(page_text)

            # Only add page separator if there's actual content
            if page_text.strip():
                all_text.append(f"\n\n{'─' * 60}\n")
                all_text.append(f"[Страница {i}]\n")
                all_text.append(f"{'─' * 60}\n\n")
                all_text.append(page_text)

        except subprocess.CalledProcessError as e:
            print(f"Error processing page {i}: {e}")
            all_text.append(f"\n[Ошибка обработки страницы {i}]\n")

        # Clean up temporary image
        image_path.unlink()

    # Write all text to output file
    print(f"\nWriting text to: {output_txt_path}")
    with open(output_txt_path, 'w', encoding='utf-8') as f:
        full_text = ''.join(all_text)
        # Final cleanup of excessive blank lines
        full_text = re.sub(r'\n{4,}', '\n\n\n', full_text)
        f.write(full_text)

    # Clean up temporary directory
    temp_dir.rmdir()

    print(f"\n✓ Conversion complete!")
    print(f"Output saved to: {output_txt_path}")
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Convert scanned PDF to text using OCR')
    parser.add_argument('input_pdf', nargs='?', help='Path to input PDF file')
    parser.add_argument('-o', '--output', help='Path to output text file')
    parser.add_argument('-l', '--lang', default='rus+kaz', help='Tesseract language codes (default: rus+kaz)')

    args = parser.parse_args()

    # Default paths
    if args.input_pdf is None:
        pdf_file = "../books/input/История Казахстана Каз.pdf"
    else:
        pdf_file = args.input_pdf

    if args.output is None:
        # Extract filename without extension
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        output_file = f"../books/output/{base_name}_improved.txt"
    else:
        output_file = args.output

    langs = args.lang

    if not os.path.exists(pdf_file):
        print(f"❌ Error: PDF file not found: {pdf_file}")
        print(f"   Place your PDF files in: books/input/")
        sys.exit(1)

    success = pdf_to_text(pdf_file, output_file, langs)
    sys.exit(0 if success else 1)
