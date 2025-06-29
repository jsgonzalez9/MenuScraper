#!/usr/bin/env python3
"""
Dual OCR Testing Script
Tests both EasyOCR and Tesseract functionality
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from yelp_optimized_chicago_scraper import (
    get_easyocr_reader,
    check_tesseract_availability,
    extract_text_with_easyocr,
    extract_text_with_tesseract,
    extract_text_from_image
)

def create_sample_menu_image():
    """Create a sample menu image for testing"""
    # Create a white background image
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic if not available
    try:
        font = ImageFont.truetype("arial.ttf", 16)
        title_font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Draw menu content
    draw.text((50, 30), "RESTAURANT MENU", fill='black', font=title_font)
    draw.text((50, 70), "Chicken Caesar Salad - $12.99", fill='black', font=font)
    draw.text((50, 100), "Fresh romaine lettuce with grilled chicken", fill='black', font=font)
    draw.text((50, 130), "Margherita Pizza - $15.50", fill='black', font=font)
    draw.text((50, 160), "Fresh mozzarella, basil, tomato sauce", fill='black', font=font)
    draw.text((50, 190), "Beef Burger - $11.75", fill='black', font=font)
    draw.text((50, 220), "Angus beef patty with lettuce and tomato", fill='black', font=font)
    
    return img

def test_easyocr():
    """Test EasyOCR functionality"""
    print("\n=== Testing EasyOCR ===")
    try:
        reader = get_easyocr_reader()
        if reader:
            print("✅ EasyOCR initialized successfully")
            return True
        else:
            print("❌ EasyOCR initialization failed")
            return False
    except Exception as e:
        print(f"❌ EasyOCR error: {e}")
        return False

def test_tesseract():
    """Test Tesseract functionality"""
    print("\n=== Testing Tesseract ===")
    try:
        available = check_tesseract_availability()
        if available:
            print("✅ Tesseract is available and working")
            return True
        else:
            print("❌ Tesseract is not available")
            return False
    except Exception as e:
        print(f"❌ Tesseract error: {e}")
        return False

def test_dual_ocr_extraction():
    """Test dual OCR extraction on sample image"""
    print("\n=== Testing Dual OCR Extraction ===")
    
    # Create sample menu image
    print("Creating sample menu image...")
    img = create_sample_menu_image()
    
    # Convert PIL image to numpy array for OCR
    img_array = np.array(img)
    
    try:
        # Test EasyOCR extraction
        print("\nTesting EasyOCR extraction...")
        easyocr_text = extract_text_with_easyocr(img_array)
        print(f"EasyOCR Result: {easyocr_text[:100]}..." if len(easyocr_text) > 100 else f"EasyOCR Result: {easyocr_text}")
        
        # Test Tesseract extraction
        print("\nTesting Tesseract extraction...")
        tesseract_text = extract_text_with_tesseract(img_array)
        print(f"Tesseract Result: {tesseract_text[:100]}..." if len(tesseract_text) > 100 else f"Tesseract Result: {tesseract_text}")
        
        # Test combined extraction
        print("\nTesting combined dual OCR extraction...")
        combined_text = extract_text_from_image(img_array)
        print(f"Combined Result: {combined_text[:100]}..." if len(combined_text) > 100 else f"Combined Result: {combined_text}")
        
        # Analyze results
        print("\n=== Analysis ===")
        print(f"EasyOCR length: {len(easyocr_text)} characters")
        print(f"Tesseract length: {len(tesseract_text)} characters")
        print(f"Combined length: {len(combined_text)} characters")
        
        # Check for menu keywords
        keywords = ['menu', 'chicken', 'pizza', 'burger', '$']
        for keyword in keywords:
            easyocr_has = keyword.lower() in easyocr_text.lower()
            tesseract_has = keyword.lower() in tesseract_text.lower()
            combined_has = keyword.lower() in combined_text.lower()
            print(f"Keyword '{keyword}': EasyOCR={easyocr_has}, Tesseract={tesseract_has}, Combined={combined_has}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dual OCR extraction failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🔍 Dual OCR Testing Script")
    print("=" * 50)
    
    # Test individual components
    easyocr_ok = test_easyocr()
    tesseract_ok = test_tesseract()
    
    # Test combined functionality
    if easyocr_ok or tesseract_ok:
        dual_ocr_ok = test_dual_ocr_extraction()
    else:
        print("\n❌ Cannot test dual OCR - no OCR engines available")
        dual_ocr_ok = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"EasyOCR: {'✅ Working' if easyocr_ok else '❌ Failed'}")
    print(f"Tesseract: {'✅ Working' if tesseract_ok else '❌ Failed'}")
    print(f"Dual OCR: {'✅ Working' if dual_ocr_ok else '❌ Failed'}")
    
    if easyocr_ok and tesseract_ok:
        print("\n🎉 Both OCR engines are working! Dual OCR is ready for menu extraction.")
    elif easyocr_ok or tesseract_ok:
        print("\n⚠️ One OCR engine is working. Partial OCR functionality available.")
    else:
        print("\n❌ No OCR engines are working. Check your installation.")
    
    print("\n💡 Next steps:")
    print("1. Run the main scraper to test OCR on real restaurant pages")
    print("2. Look for restaurants with image-based menus")
    print("3. Check the OCR usage in the output JSON files")

if __name__ == "__main__":
    main()