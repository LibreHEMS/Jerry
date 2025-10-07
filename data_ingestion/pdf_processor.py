"""
PDF document processor for knowledge base ingestion.

This module provides functionality to extract and chunk text content from PDF
documents for the Jerry AI assistant's knowledge base.
"""

import logging
import os
import sys
from typing import Dict, Iterator, List, Optional
from uuid import uuid4

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from pdfplumber import PDF
except ImportError:
    PDF = None

from src.data.models import KnowledgeChunk

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF document processor for text extraction and chunking."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """Initialize the PDF processor.
        
        Args:
            chunk_size: Target size for text chunks in characters
            chunk_overlap: Overlap between consecutive chunks in characters
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Check available PDF libraries
        self.has_pypdf2 = PyPDF2 is not None
        self.has_pdfplumber = PDF is not None
        
        if not self.has_pypdf2 and not self.has_pdfplumber:
            raise ImportError(
                "Either PyPDF2 or pdfplumber is required. "
                "Install with: pip install PyPDF2 pdfplumber"
            )
        
        logger.info(f"Initialized PDF processor with chunk_size={chunk_size}")
    
    def extract_text_pypdf2(self, pdf_path: str) -> str:
        """Extract text from PDF using PyPDF2.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        if not self.has_pypdf2:
            raise ImportError("PyPDF2 not available")
        
        text_content = []
        
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                    logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
        
        return "\n".join(text_content)
    
    def extract_text_pdfplumber(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        if not self.has_pdfplumber:
            raise ImportError("pdfplumber not available")
        
        text_content = []
        
        with PDF.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(page_text)
                    logger.debug(f"Extracted text from page {page_num + 1}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
        
        return "\n".join(text_content)
    
    def extract_text(self, pdf_path: str, method: str = "auto") -> str:
        """Extract text from PDF using specified method.
        
        Args:
            pdf_path: Path to the PDF file
            method: Extraction method ("pypdf2", "pdfplumber", or "auto")
            
        Returns:
            Extracted text content
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from {pdf_path} using method: {method}")
        
        if method == "auto":
            # Try pdfplumber first (generally better), then PyPDF2
            if self.has_pdfplumber:
                method = "pdfplumber"
            elif self.has_pypdf2:
                method = "pypdf2"
            else:
                raise ImportError("No PDF processing library available")
        
        try:
            if method == "pdfplumber":
                text = self.extract_text_pdfplumber(pdf_path)
            elif method == "pypdf2":
                text = self.extract_text_pypdf2(pdf_path)
            else:
                raise ValueError(f"Unknown extraction method: {method}")
            
            logger.info(f"Extracted {len(text)} characters from {pdf_path}")
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_path}: {e}")
            
            # Try fallback method if auto mode
            if method == "auto":
                fallback_method = "pypdf2" if method == "pdfplumber" else "pdfplumber"
                if (fallback_method == "pypdf2" and self.has_pypdf2) or \
                   (fallback_method == "pdfplumber" and self.has_pdfplumber):
                    logger.info(f"Trying fallback method: {fallback_method}")
                    return self.extract_text(pdf_path, fallback_method)
            
            raise
    
    def chunk_text(self, text: str, title: str = "") -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text content to chunk
            title: Document title for context
            
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        # Clean up text
        text = text.strip()
        
        # If text is shorter than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            if len(text) >= self.min_chunk_size:
                return [text]
            else:
                return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at a sentence or paragraph
            if end < len(text):
                # Look for sentence endings within the overlap region
                search_start = max(start + self.chunk_size - self.chunk_overlap, start)
                
                # Find the best break point (paragraph > sentence > word boundary)
                break_point = self._find_break_point(text, search_start, end)
                if break_point > start:
                    end = break_point
            
            # Extract chunk
            chunk = text[start:end].strip()
            
            # Only keep chunks that meet minimum size requirement
            if len(chunk) >= self.min_chunk_size:
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            if end >= len(text):
                break
            
            start = end - self.chunk_overlap
            
            # Ensure we make progress
            if start <= chunks and len(chunks) > 0:
                # If we're not making progress, jump forward
                start = end - self.chunk_overlap // 2
        
        logger.debug(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def _find_break_point(self, text: str, start: int, end: int) -> int:
        """Find the best break point for chunking.
        
        Args:
            text: Full text
            start: Start position to search from
            end: End position to search to
            
        Returns:
            Best break point position
        """
        # Look for paragraph breaks first
        for i in range(end - 1, start - 1, -1):
            if text[i:i+2] == '\n\n':
                return i + 2
        
        # Look for sentence endings
        sentence_endings = '.!?'
        for i in range(end - 1, start - 1, -1):
            if text[i] in sentence_endings and i + 1 < len(text):
                # Make sure it's followed by whitespace or newline
                if text[i + 1].isspace():
                    return i + 1
        
        # Look for word boundaries
        for i in range(end - 1, start - 1, -1):
            if text[i].isspace():
                return i + 1
        
        # No good break point found, use original end
        return end
    
    def process_pdf(
        self,
        pdf_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[KnowledgeChunk]:
        """Process a PDF file into knowledge chunks.
        
        Args:
            pdf_path: Path to the PDF file
            document_id: Optional document ID (generated if not provided)
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of knowledge chunks
        """
        if document_id is None:
            document_id = str(uuid4())
        
        # Extract filename as title
        title = os.path.basename(pdf_path)
        if title.lower().endswith('.pdf'):
            title = title[:-4]
        
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Extract text
            text = self.extract_text(pdf_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {pdf_path}")
                return []
            
            # Chunk text
            text_chunks = self.chunk_text(text, title)
            
            if not text_chunks:
                logger.warning(f"No valid chunks created from {pdf_path}")
                return []
            
            # Create knowledge chunks
            knowledge_chunks = []
            base_metadata = {
                "source_file": pdf_path,
                "file_type": "pdf",
                "total_chunks": len(text_chunks),
                **(metadata or {})
            }
            
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = {
                    **base_metadata,
                    "chunk_number": i + 1
                }
                
                chunk = KnowledgeChunk.create_from_document(
                    document_id=document_id,
                    title=title,
                    content=chunk_text,
                    chunk_index=i,
                    metadata=chunk_metadata
                )
                
                knowledge_chunks.append(chunk)
            
            logger.info(f"Created {len(knowledge_chunks)} knowledge chunks from {pdf_path}")
            return knowledge_chunks
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            return []
    
    def process_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_pattern: str = "*.pdf"
    ) -> Iterator[List[KnowledgeChunk]]:
        """Process all PDF files in a directory.
        
        Args:
            directory_path: Path to directory containing PDFs
            recursive: Whether to search subdirectories
            file_pattern: File pattern to match (e.g., "*.pdf")
            
        Yields:
            List of knowledge chunks for each processed file
        """
        import glob
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        # Build search pattern
        if recursive:
            pattern = os.path.join(directory_path, "**", file_pattern)
            pdf_files = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(directory_path, file_pattern)
            pdf_files = glob.glob(pattern)
        
        logger.info(f"Found {len(pdf_files)} PDF files in {directory_path}")
        
        for pdf_path in pdf_files:
            try:
                chunks = self.process_pdf(pdf_path)
                if chunks:
                    yield chunks
                else:
                    logger.warning(f"No chunks generated for {pdf_path}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")
                continue


class TextProcessor:
    """Simple text processor for non-PDF documents."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100
    ):
        """Initialize the text processor.
        
        Args:
            chunk_size: Target size for text chunks in characters
            chunk_overlap: Overlap between consecutive chunks in characters
            min_chunk_size: Minimum chunk size to keep
        """
        self.pdf_processor = PDFProcessor(chunk_size, chunk_overlap, min_chunk_size)
    
    def process_text_file(
        self,
        file_path: str,
        document_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> List[KnowledgeChunk]:
        """Process a text file into knowledge chunks.
        
        Args:
            file_path: Path to the text file
            document_id: Optional document ID (generated if not provided)
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of knowledge chunks
        """
        if document_id is None:
            document_id = str(uuid4())
        
        # Extract filename as title
        title = os.path.basename(file_path)
        
        logger.info(f"Processing text file: {file_path}")
        
        try:
            # Read text content
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text.strip():
                logger.warning(f"No text content in {file_path}")
                return []
            
            # Chunk text using PDF processor's chunking logic
            text_chunks = self.pdf_processor.chunk_text(text, title)
            
            if not text_chunks:
                logger.warning(f"No valid chunks created from {file_path}")
                return []
            
            # Create knowledge chunks
            knowledge_chunks = []
            base_metadata = {
                "source_file": file_path,
                "file_type": "text",
                "total_chunks": len(text_chunks),
                **(metadata or {})
            }
            
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = {
                    **base_metadata,
                    "chunk_number": i + 1
                }
                
                chunk = KnowledgeChunk.create_from_document(
                    document_id=document_id,
                    title=title,
                    content=chunk_text,
                    chunk_index=i,
                    metadata=chunk_metadata
                )
                
                knowledge_chunks.append(chunk)
            
            logger.info(f"Created {len(knowledge_chunks)} knowledge chunks from {file_path}")
            return knowledge_chunks
            
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            return []