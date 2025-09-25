"""
LangChain Document Processing Service.
Implements ft-llm-001-content-extraction.md
"""

import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# LangChain imports
try:
    from langchain_text_splitters import (
        RecursiveCharacterTextSplitter,
        CharacterTextSplitter,
        MarkdownHeaderTextSplitter,
        HTMLHeaderTextSplitter
    )
    from langchain_community.document_loaders import (
        PyPDFLoader,
        UnstructuredPDFLoader,
        GitHubIssuesLoader,
        GithubFileLoader,
        UnstructuredHTMLLoader,
        TextLoader,
        UnstructuredMarkdownLoader
    )
    from langchain.schema import Document
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Create fallback Document class
    class Document:
        def __init__(self, page_content: str, metadata: Dict[str, Any] = None):
            self.page_content = page_content
            self.metadata = metadata or {}

from django.conf import settings
from .enhanced_llm_service import EnhancedLLMService

logger = logging.getLogger(__name__)


class AdvancedDocumentProcessor:
    """Advanced document processing with LangChain and intelligent text splitting"""

    def __init__(self):
        self.llm_service = EnhancedLLMService()
        self.config = getattr(settings, 'LANGCHAIN_SETTINGS', {})

        # Initialize text splitters
        self._init_text_splitters()

    def _init_text_splitters(self):
        """Initialize various text splitting strategies"""
        chunk_size = self.config.get('chunk_size', 1000)
        chunk_overlap = self.config.get('chunk_overlap', 200)

        # Recursive character splitter (default)
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        ) if HAS_LANGCHAIN else None

        # Character splitter for simple cases
        self.character_splitter = CharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        ) if HAS_LANGCHAIN else None

        # Markdown header splitter
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ]
        ) if HAS_LANGCHAIN else None

        # HTML header splitter
        self.html_splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=[
                ("h1", "Header 1"),
                ("h2", "Header 2"),
                ("h3", "Header 3"),
                ("h4", "Header 4"),
            ]
        ) if HAS_LANGCHAIN else None

    async def process_document(self, content: Union[str, bytes, Path],
                             content_type: str,
                             metadata: Optional[Dict[str, Any]] = None,
                             user_id: Optional[int] = None) -> Dict[str, Any]:
        """Process document with appropriate loader and splitting strategy"""

        if not HAS_LANGCHAIN:
            return await self._fallback_processing(content, content_type, metadata)

        start_time = time.time()
        processing_metadata = {
            'content_type': content_type,
            'langchain_used': True,
            'processing_start_time': start_time
        }

        try:
            # Load document using appropriate loader
            documents = await self._load_document(content, content_type, metadata)

            # Apply intelligent text splitting
            chunks = self._apply_adaptive_splitting(documents, content_type)

            # Enhance chunks with LLM processing if requested
            enhanced_chunks = []
            for i, chunk in enumerate(chunks):
                enhanced_chunk = await self._enhance_chunk_with_llm(
                    chunk, i, content_type, user_id
                )
                enhanced_chunks.append(enhanced_chunk)

            processing_time = int((time.time() - start_time) * 1000)

            result = {
                'success': True,
                'total_chunks': len(enhanced_chunks),
                'chunks': enhanced_chunks,
                'processing_metadata': {
                    **processing_metadata,
                    'processing_time_ms': processing_time,
                    'splitting_strategy': self._get_splitting_strategy_name(content_type),
                    'original_document_count': len(documents),
                    'chunks_generated': len(chunks),
                    'llm_enhancement_applied': True
                }
            }

            logger.info(f"Processed {content_type} document into {len(enhanced_chunks)} chunks in {processing_time}ms")
            return result

        except Exception as e:
            logger.error(f"Document processing failed for {content_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_metadata': {
                    **processing_metadata,
                    'processing_time_ms': int((time.time() - start_time) * 1000),
                    'error_occurred': True
                }
            }

    async def _load_document(self, content: Union[str, bytes, Path],
                           content_type: str,
                           metadata: Optional[Dict[str, Any]]) -> List[Document]:
        """Load document using appropriate LangChain loader"""

        base_metadata = metadata or {}
        base_metadata.update({
            'source_type': content_type,
            'processed_at': time.time()
        })

        if content_type == 'pdf':
            if isinstance(content, (str, Path)):
                # File path provided
                loader = UnstructuredPDFLoader(str(content))
                documents = loader.load()
            else:
                # PDF bytes provided - save temporarily
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(content)
                    tmp_file.flush()
                    loader = UnstructuredPDFLoader(tmp_file.name)
                    documents = loader.load()
                # Clean up temp file
                Path(tmp_file.name).unlink()

        elif content_type == 'github':
            # GitHub repository processing
            repo_url = content if isinstance(content, str) else str(content)
            documents = await self._process_github_repository(repo_url, base_metadata)

        elif content_type == 'html' or content_type == 'web_profile':
            if isinstance(content, str) and content.startswith(('http://', 'https://')):
                # URL provided
                loader = UnstructuredHTMLLoader(content)
                documents = loader.load()
            else:
                # HTML content provided
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp_file:
                    tmp_file.write(content if isinstance(content, str) else content.decode('utf-8'))
                    tmp_file.flush()
                    loader = UnstructuredHTMLLoader(tmp_file.name)
                    documents = loader.load()
                Path(tmp_file.name).unlink()

        elif content_type == 'markdown':
            if isinstance(content, (str, Path)) and Path(content).exists():
                # File path
                loader = UnstructuredMarkdownLoader(str(content))
                documents = loader.load()
            else:
                # Markdown content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as tmp_file:
                    tmp_file.write(content if isinstance(content, str) else content.decode('utf-8'))
                    tmp_file.flush()
                    loader = UnstructuredMarkdownLoader(tmp_file.name)
                    documents = loader.load()
                Path(tmp_file.name).unlink()

        elif content_type == 'text':
            # Plain text content
            text_content = content if isinstance(content, str) else content.decode('utf-8')
            documents = [Document(page_content=text_content, metadata=base_metadata)]

        else:
            raise ValueError(f"Unsupported content type: {content_type}")

        # Add metadata to all documents
        for doc in documents:
            doc.metadata.update(base_metadata)

        return documents

    async def _process_github_repository(self, repo_url: str, metadata: Dict[str, Any]) -> List[Document]:
        """Process GitHub repository with specialized handling"""
        documents = []

        try:
            github_token = getattr(settings, 'GITHUB_TOKEN', '')

            # Load README files
            try:
                readme_loader = GithubFileLoader(
                    repo=repo_url,
                    access_token=github_token,
                    file_filter=lambda file_path: file_path.lower().endswith('readme.md') or
                                                file_path.lower() == 'readme'
                )
                readme_docs = readme_loader.load()
                for doc in readme_docs:
                    doc.metadata.update({**metadata, 'file_type': 'readme'})
                documents.extend(readme_docs)
            except Exception as e:
                logger.warning(f"Failed to load README files: {e}")

            # Load key source files (limited to prevent overwhelming)
            try:
                code_loader = GithubFileLoader(
                    repo=repo_url,
                    access_token=github_token,
                    file_filter=lambda path: any(path.endswith(ext) for ext in
                                               ['.py', '.js', '.ts', '.java', '.cpp', '.go', '.rs']) and
                                            'test' not in path.lower() and
                                            len(path.split('/')) <= 3  # Limit depth
                )
                code_docs = code_loader.load()

                # Limit number of code files to process
                max_files = self.config.get('max_code_files', 10)
                for doc in code_docs[:max_files]:
                    doc.metadata.update({**metadata, 'file_type': 'source_code'})
                documents.extend(code_docs[:max_files])

            except Exception as e:
                logger.warning(f"Failed to load source code files: {e}")

            # Load documentation files
            try:
                doc_loader = GithubFileLoader(
                    repo=repo_url,
                    access_token=github_token,
                    file_filter=lambda path: any(path.lower().endswith(ext) for ext in
                                               ['.md', '.rst', '.txt']) and
                                            any(keyword in path.lower() for keyword in
                                               ['doc', 'guide', 'tutorial', 'example'])
                )
                doc_files = doc_loader.load()
                for doc in doc_files[:5]:  # Limit documentation files
                    doc.metadata.update({**metadata, 'file_type': 'documentation'})
                documents.extend(doc_files[:5])

            except Exception as e:
                logger.warning(f"Failed to load documentation files: {e}")

        except Exception as e:
            logger.error(f"GitHub repository processing failed: {e}")
            # Create a fallback document with just the repo URL
            documents = [Document(
                page_content=f"GitHub Repository: {repo_url}",
                metadata={**metadata, 'file_type': 'repository_reference', 'error': str(e)}
            )]

        return documents

    def _apply_adaptive_splitting(self, documents: List[Document], content_type: str) -> List[Document]:
        """Apply intelligent text splitting based on document type and content"""
        if not HAS_LANGCHAIN:
            return documents

        all_chunks = []

        for doc in documents:
            content_length = len(doc.page_content)
            doc_type = doc.metadata.get('file_type', content_type)

            # Choose splitting strategy based on content type and characteristics
            if doc_type == 'markdown' or content_type == 'markdown':
                # Use structure-aware splitting for markdown
                if self.markdown_splitter and '##' in doc.page_content:
                    chunks = self.markdown_splitter.split_documents([doc])
                    # Further split large chunks
                    if any(len(chunk.page_content) > 2000 for chunk in chunks):
                        final_chunks = []
                        for chunk in chunks:
                            if len(chunk.page_content) > 2000:
                                sub_chunks = self.recursive_splitter.split_documents([chunk])
                                final_chunks.extend(sub_chunks)
                            else:
                                final_chunks.append(chunk)
                        chunks = final_chunks
                else:
                    chunks = self.recursive_splitter.split_documents([doc])

            elif doc_type in ['html', 'web_profile']:
                # Use HTML-aware splitting
                if self.html_splitter and any(tag in doc.page_content.lower() for tag in ['<h1>', '<h2>', '<h3>']):
                    chunks = self.html_splitter.split_documents([doc])
                    # Further split if needed
                    if any(len(chunk.page_content) > 2000 for chunk in chunks):
                        final_chunks = []
                        for chunk in chunks:
                            if len(chunk.page_content) > 2000:
                                sub_chunks = self.recursive_splitter.split_documents([chunk])
                                final_chunks.extend(sub_chunks)
                            else:
                                final_chunks.append(chunk)
                        chunks = final_chunks
                else:
                    chunks = self.recursive_splitter.split_documents([doc])

            elif content_length > 5000 and doc_type in ['source_code', 'technical']:
                # Use semantic splitting for long technical documents (if available)
                # For now, fall back to recursive splitting
                chunks = self.recursive_splitter.split_documents([doc])

            elif content_length > 2000:
                # Use recursive splitting for medium-length documents
                chunks = self.recursive_splitter.split_documents([doc])

            elif content_length > 500:
                # Use character splitting for shorter documents
                chunks = self.character_splitter.split_documents([doc])

            else:
                # Keep short documents as single chunks
                chunks = [doc]

            # Add chunk metadata
            for i, chunk in enumerate(chunks):
                chunk.metadata.update({
                    'chunk_index': i,
                    'total_chunks_in_document': len(chunks),
                    'original_document_length': content_length,
                    'chunk_length': len(chunk.page_content),
                    'splitting_strategy': self._get_splitting_strategy_name(content_type, doc_type)
                })

            all_chunks.extend(chunks)

        # Limit total chunks to prevent overwhelming the system
        max_chunks = self.config.get('max_chunks_per_document', 50)
        if len(all_chunks) > max_chunks:
            logger.warning(f"Document produced {len(all_chunks)} chunks, limiting to {max_chunks}")
            all_chunks = all_chunks[:max_chunks]

        return all_chunks

    async def _enhance_chunk_with_llm(self, chunk: Document, chunk_index: int,
                                    content_type: str, user_id: Optional[int]) -> Dict[str, Any]:
        """Enhance chunk with LLM-extracted metadata"""
        try:
            # Build context for LLM enhancement
            context = {
                'content': chunk.page_content,
                'content_type': content_type,
                'file_type': chunk.metadata.get('file_type', content_type),
                'chunk_index': chunk_index
            }

            # Skip LLM enhancement for very short chunks
            if len(chunk.page_content.strip()) < 50:
                return {
                    'content': chunk.page_content,
                    'metadata': chunk.metadata,
                    'enhanced_data': {
                        'skip_reason': 'content_too_short',
                        'original_length': len(chunk.page_content)
                    },
                    'content_hash': hashlib.sha256(chunk.page_content.encode()).hexdigest()
                }

            # Use LLM service for content enhancement
            enhancement_result = await self.llm_service.parse_job_description(
                chunk.page_content,
                context.get('company_name', ''),
                context.get('role_title', ''),
                user_id
            )

            if 'error' not in enhancement_result:
                enhanced_data = enhancement_result
                enhanced_data.pop('processing_metadata', None)  # Remove metadata to avoid nesting
            else:
                enhanced_data = {'error': enhancement_result['error']}

            return {
                'content': chunk.page_content,
                'metadata': chunk.metadata,
                'enhanced_data': enhanced_data,
                'content_hash': hashlib.sha256(chunk.page_content.encode()).hexdigest(),
                'llm_enhancement_successful': 'error' not in enhanced_data
            }

        except Exception as e:
            logger.error(f"LLM enhancement failed for chunk {chunk_index}: {e}")
            return {
                'content': chunk.page_content,
                'metadata': chunk.metadata,
                'enhanced_data': {'enhancement_error': str(e)},
                'content_hash': hashlib.sha256(chunk.page_content.encode()).hexdigest(),
                'llm_enhancement_successful': False
            }

    async def _fallback_processing(self, content: Union[str, bytes, Path],
                                 content_type: str,
                                 metadata: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback processing when LangChain is not available"""
        logger.warning("LangChain not available, using fallback processing")

        try:
            # Simple text extraction
            if isinstance(content, bytes):
                text_content = content.decode('utf-8', errors='ignore')
            elif isinstance(content, Path):
                text_content = content.read_text(encoding='utf-8', errors='ignore')
            else:
                text_content = str(content)

            # Simple chunking (split by paragraphs)
            chunks = []
            paragraphs = text_content.split('\n\n')
            current_chunk = ""
            chunk_index = 0

            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) > 1000:  # Max chunk size
                    if current_chunk:
                        chunks.append({
                            'content': current_chunk.strip(),
                            'metadata': {
                                **(metadata or {}),
                                'chunk_index': chunk_index,
                                'fallback_processing': True,
                                'content_type': content_type
                            },
                            'enhanced_data': {},
                            'content_hash': hashlib.sha256(current_chunk.encode()).hexdigest()
                        })
                        chunk_index += 1
                    current_chunk = paragraph
                else:
                    current_chunk += "\n\n" + paragraph if current_chunk else paragraph

            # Add final chunk
            if current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'metadata': {
                        **(metadata or {}),
                        'chunk_index': chunk_index,
                        'fallback_processing': True,
                        'content_type': content_type
                    },
                    'enhanced_data': {},
                    'content_hash': hashlib.sha256(current_chunk.encode()).hexdigest()
                })

            return {
                'success': True,
                'total_chunks': len(chunks),
                'chunks': chunks,
                'processing_metadata': {
                    'langchain_used': False,
                    'fallback_processing': True,
                    'content_type': content_type
                }
            }

        except Exception as e:
            logger.error(f"Fallback processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_metadata': {
                    'langchain_used': False,
                    'fallback_processing': True,
                    'error_occurred': True
                }
            }

    def _get_splitting_strategy_name(self, content_type: str, doc_type: str = None) -> str:
        """Get human-readable name for splitting strategy used"""
        effective_type = doc_type or content_type

        if effective_type == 'markdown':
            return 'markdown_header_aware'
        elif effective_type in ['html', 'web_profile']:
            return 'html_structure_aware'
        elif effective_type in ['source_code', 'technical']:
            return 'recursive_semantic'
        else:
            return 'adaptive_recursive'

    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics and configuration"""
        return {
            'langchain_available': HAS_LANGCHAIN,
            'configuration': self.config,
            'supported_formats': [
                'pdf', 'markdown', 'html', 'text', 'github'
            ],
            'splitting_strategies': [
                'recursive_character',
                'character_based',
                'markdown_header_aware',
                'html_structure_aware',
                'adaptive_semantic'
            ],
            'max_chunks_per_document': self.config.get('max_chunks_per_document', 50),
            'default_chunk_size': self.config.get('chunk_size', 1000),
            'default_chunk_overlap': self.config.get('chunk_overlap', 200)
        }