"""
PDF Processor Module
Handles extraction of text from PDF resume files
"""
import os
import logging
from typing import Optional
from pypdf import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text(pdf_path: str) -> Optional[str]:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a string, or None if extraction fails
    """
    try:
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF file not found at {pdf_path}")
            return None
        
        # Check if file is readable
        if not os.access(pdf_path, os.R_OK):
            logger.error(f"PDF file is not readable at {pdf_path}")
            return None
        
        # Read the PDF
        reader = PdfReader(pdf_path)
        
        # Check if PDF has pages
        if len(reader.pages) == 0:
            logger.error("PDF has no pages")
            return None
        
        # Extract text from all pages
        text_content = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {str(e)}")
                continue
        
        # Combine all text
        full_text = "\n".join(text_content)
        
        # Return None if no text was extracted
        if not full_text.strip():
            logger.error("No text could be extracted from PDF")
            return None
        
        return full_text
        
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None


def validate_pdf(pdf_path: str) -> bool:
    """
    Validate that a file is a readable PDF.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if not os.path.exists(pdf_path):
            return False
        
        # Try to read the PDF
        reader = PdfReader(pdf_path)
        
        # Check if it has at least one page
        if len(reader.pages) == 0:
            return False
        
        return True
        
    except Exception:
        return False
