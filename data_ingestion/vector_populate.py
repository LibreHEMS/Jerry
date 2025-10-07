"""
Knowledge base population script for Jerry AI assistant.

This script populates the vector database with knowledge chunks from
various document sources (PDFs, text files, etc.).
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Add src to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data.models import KnowledgeChunk
from src.rag.embeddings import get_embeddings_service
from src.rag.vector_store import ChromaVectorStore
from src.utils.config import get_config
from src.utils.logging import setup_logging
from data_ingestion.pdf_processor import PDFProcessor, TextProcessor

logger = logging.getLogger(__name__)


class KnowledgeBasePopulator:
    """Knowledge base population service."""
    
    def __init__(
        self,
        vector_store: ChromaVectorStore,
        pdf_processor: PDFProcessor,
        text_processor: TextProcessor,
        batch_size: int = 50
    ):
        """Initialize the knowledge base populator.
        
        Args:
            vector_store: Vector store for storing embeddings
            pdf_processor: PDF processor for extracting text
            text_processor: Text processor for text files
            batch_size: Batch size for embedding generation
        """
        self.vector_store = vector_store
        self.pdf_processor = pdf_processor
        self.text_processor = text_processor
        self.batch_size = batch_size
        
        # Get embeddings service
        self.embeddings_service = get_embeddings_service()
        
        logger.info(f"Initialized knowledge base populator with batch_size={batch_size}")
    
    def process_chunks_with_embeddings(self, chunks: List[KnowledgeChunk]) -> List[KnowledgeChunk]:
        """Generate embeddings for knowledge chunks.
        
        Args:
            chunks: List of knowledge chunks without embeddings
            
        Returns:
            List of knowledge chunks with embeddings
        """
        if not chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract text content for embedding
        texts = [chunk.content for chunk in chunks]
        
        # Generate embeddings in batches
        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self.embeddings_service.encode_batch(batch_texts, self.batch_size)
            all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated embeddings for batch {i//self.batch_size + 1}/{(len(texts) + self.batch_size - 1)//self.batch_size}")
        
        # Update chunks with embeddings
        for chunk, embedding in zip(chunks, all_embeddings):
            chunk.update_embedding(embedding)
        
        logger.info(f"Generated embeddings for all {len(chunks)} chunks")
        return chunks
    
    def populate_from_pdf(self, pdf_path: str, document_id: Optional[str] = None) -> int:
        """Populate knowledge base from a single PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            document_id: Optional document ID
            
        Returns:
            Number of chunks added
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        try:
            # Process PDF into chunks
            chunks = self.pdf_processor.process_pdf(pdf_path, document_id)
            
            if not chunks:
                logger.warning(f"No chunks generated from {pdf_path}")
                return 0
            
            # Generate embeddings
            chunks_with_embeddings = self.process_chunks_with_embeddings(chunks)
            
            # Add to vector store
            self.vector_store.add_chunks(chunks_with_embeddings)
            
            logger.info(f"Added {len(chunks_with_embeddings)} chunks from {pdf_path}")
            return len(chunks_with_embeddings)
            
        except Exception as e:
            logger.error(f"Failed to process PDF {pdf_path}: {e}")
            return 0
    
    def populate_from_text_file(self, file_path: str, document_id: Optional[str] = None) -> int:
        """Populate knowledge base from a text file.
        
        Args:
            file_path: Path to the text file
            document_id: Optional document ID
            
        Returns:
            Number of chunks added
        """
        logger.info(f"Processing text file: {file_path}")
        
        try:
            # Process text file into chunks
            chunks = self.text_processor.process_text_file(file_path, document_id)
            
            if not chunks:
                logger.warning(f"No chunks generated from {file_path}")
                return 0
            
            # Generate embeddings
            chunks_with_embeddings = self.process_chunks_with_embeddings(chunks)
            
            # Add to vector store
            self.vector_store.add_chunks(chunks_with_embeddings)
            
            logger.info(f"Added {len(chunks_with_embeddings)} chunks from {file_path}")
            return len(chunks_with_embeddings)
            
        except Exception as e:
            logger.error(f"Failed to process text file {file_path}: {e}")
            return 0
    
    def populate_from_directory(self, directory_path: str, recursive: bool = True) -> int:
        """Populate knowledge base from a directory of documents.
        
        Args:
            directory_path: Path to directory containing documents
            recursive: Whether to search subdirectories
            
        Returns:
            Total number of chunks added
        """
        logger.info(f"Processing directory: {directory_path}")
        
        if not os.path.exists(directory_path):
            logger.error(f"Directory not found: {directory_path}")
            return 0
        
        total_chunks = 0
        
        # Process PDF files
        try:
            for chunks in self.pdf_processor.process_directory(directory_path, recursive):
                if chunks:
                    chunks_with_embeddings = self.process_chunks_with_embeddings(chunks)
                    self.vector_store.add_chunks(chunks_with_embeddings)
                    total_chunks += len(chunks_with_embeddings)
        except Exception as e:
            logger.error(f"Error processing PDFs from directory: {e}")
        
        # Process text files
        import glob
        text_patterns = ["*.txt", "*.md"]
        
        for pattern in text_patterns:
            if recursive:
                search_pattern = os.path.join(directory_path, "**", pattern)
                text_files = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(directory_path, pattern)
                text_files = glob.glob(search_pattern)
            
            for text_file in text_files:
                try:
                    chunks_added = self.populate_from_text_file(text_file)
                    total_chunks += chunks_added
                except Exception as e:
                    logger.error(f"Failed to process text file {text_file}: {e}")
        
        logger.info(f"Added {total_chunks} total chunks from directory {directory_path}")
        return total_chunks
    
    def populate_from_resources(self) -> int:
        """Populate knowledge base from the Resources directory.
        
        Returns:
            Number of chunks added
        """
        # Look for Resources directory
        resources_path = Path(__file__).parent.parent / "Resources"
        
        if not resources_path.exists():
            logger.warning("Resources directory not found")
            return 0
        
        logger.info(f"Populating from Resources directory: {resources_path}")
        return self.populate_from_directory(str(resources_path), recursive=True)
    
    def clear_knowledge_base(self) -> None:
        """Clear all data from the knowledge base.
        
        Warning: This will delete all stored knowledge!
        """
        logger.warning("Clearing knowledge base...")
        self.vector_store.reset_collection()
        logger.warning("Knowledge base cleared")
    
    def get_stats(self) -> dict:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = self.vector_store.get_collection_stats()
        model_info = self.embeddings_service.get_model_info()
        
        return {
            "vector_store": stats,
            "embeddings_model": model_info,
            "batch_size": self.batch_size
        }


def create_populator() -> KnowledgeBasePopulator:
    """Create and configure the knowledge base populator.
    
    Returns:
        Configured KnowledgeBasePopulator instance
    """
    # Load configuration
    config = get_config()
    
    # Initialize vector store
    vector_store_config = config.get("vector_store", {})
    persist_directory = vector_store_config.get("persist_directory", "./data/chroma")
    collection_name = vector_store_config.get("collection_name", "jerry_knowledge_base")
    
    vector_store = ChromaVectorStore(
        persist_directory=persist_directory,
        collection_name=collection_name
    )
    
    # Initialize processors
    processing_config = config.get("document_processing", {})
    chunk_size = processing_config.get("chunk_size", 1000)
    chunk_overlap = processing_config.get("chunk_overlap", 200)
    min_chunk_size = processing_config.get("min_chunk_size", 100)
    
    pdf_processor = PDFProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size
    )
    
    text_processor = TextProcessor(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        min_chunk_size=min_chunk_size
    )
    
    # Get batch size for embeddings
    embeddings_config = config.get("embeddings", {})
    batch_size = embeddings_config.get("batch_size", 50)
    
    return KnowledgeBasePopulator(
        vector_store=vector_store,
        pdf_processor=pdf_processor,
        text_processor=text_processor,
        batch_size=batch_size
    )


def main():
    """Main entry point for the knowledge base population script."""
    parser = argparse.ArgumentParser(description="Populate Jerry's knowledge base")
    
    # Command selection
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add file command
    add_file_parser = subparsers.add_parser("add-file", help="Add a single file to knowledge base")
    add_file_parser.add_argument("file_path", help="Path to the file to add")
    add_file_parser.add_argument("--document-id", help="Optional document ID")
    
    # Add directory command
    add_dir_parser = subparsers.add_parser("add-directory", help="Add all files from a directory")
    add_dir_parser.add_argument("directory_path", help="Path to the directory")
    add_dir_parser.add_argument("--no-recursive", action="store_true", help="Don't search subdirectories")
    
    # Add resources command
    subparsers.add_parser("add-resources", help="Add files from Resources directory")
    
    # Clear command
    subparsers.add_parser("clear", help="Clear all knowledge base data")
    
    # Stats command
    subparsers.add_parser("stats", help="Show knowledge base statistics")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging()
    
    try:
        # Create populator
        populator = create_populator()
        
        # Execute command
        if args.command == "add-file":
            chunks_added = 0
            file_path = args.file_path
            
            if file_path.lower().endswith(".pdf"):
                chunks_added = populator.populate_from_pdf(file_path, args.document_id)
            else:
                chunks_added = populator.populate_from_text_file(file_path, args.document_id)
            
            print(f"Added {chunks_added} chunks from {file_path}")
        
        elif args.command == "add-directory":
            recursive = not args.no_recursive
            chunks_added = populator.populate_from_directory(args.directory_path, recursive)
            print(f"Added {chunks_added} chunks from directory {args.directory_path}")
        
        elif args.command == "add-resources":
            chunks_added = populator.populate_from_resources()
            print(f"Added {chunks_added} chunks from Resources directory")
        
        elif args.command == "clear":
            response = input("Are you sure you want to clear the knowledge base? (yes/no): ")
            if response.lower() == "yes":
                populator.clear_knowledge_base()
                print("Knowledge base cleared")
            else:
                print("Operation cancelled")
        
        elif args.command == "stats":
            stats = populator.get_stats()
            print("Knowledge Base Statistics:")
            print(f"  Total chunks: {stats['vector_store']['total_chunks']}")
            print(f"  Collection: {stats['vector_store']['collection_name']}")
            print(f"  Embeddings model: {stats['embeddings_model']['model_name']}")
            print(f"  Embedding dimension: {stats['embeddings_model']['embedding_dimension']}")
            print(f"  Batch size: {stats['batch_size']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())