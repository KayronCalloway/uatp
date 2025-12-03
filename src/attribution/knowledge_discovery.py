"""
Knowledge Discovery Module for AKC System

This module provides automated discovery and verification of knowledge sources
through integration with external databases and heuristic analysis.
"""

import asyncio
import re
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
import aiohttp
import json

from .akc_system import KnowledgeSource, KnowledgeSourceType, VerificationStatus

logger = logging.getLogger(__name__)


@dataclass
class ExternalSource:
    """External database/API source for knowledge discovery"""

    name: str
    api_url: str
    api_key: Optional[str] = None
    rate_limit: int = 60  # requests per minute
    supported_types: List[KnowledgeSourceType] = None

    def __post_init__(self):
        if self.supported_types is None:
            self.supported_types = [KnowledgeSourceType.ACADEMIC_PAPER]


class KnowledgeDiscovery:
    """Knowledge discovery and verification system"""

    def __init__(self):
        self.external_sources = self._initialize_external_sources()
        self.citation_patterns = self._initialize_citation_patterns()
        self.session: Optional[aiohttp.ClientSession] = None

    def _initialize_external_sources(self) -> List[ExternalSource]:
        """Initialize external knowledge sources"""
        return [
            ExternalSource(
                name="CrossRef",
                api_url="https://api.crossref.org/works",
                supported_types=[KnowledgeSourceType.ACADEMIC_PAPER],
            ),
            ExternalSource(
                name="OpenLibrary",
                api_url="https://openlibrary.org/api/books",
                supported_types=[KnowledgeSourceType.BOOK],
            ),
            ExternalSource(
                name="GitHub",
                api_url="https://api.github.com/repos",
                supported_types=[KnowledgeSourceType.CODE_REPOSITORY],
            ),
            ExternalSource(
                name="arXiv",
                api_url="https://export.arxiv.org/api/query",
                supported_types=[KnowledgeSourceType.ACADEMIC_PAPER],
            ),
            ExternalSource(
                name="ORCID",
                api_url="https://pub.orcid.org/v3.0",
                supported_types=[KnowledgeSourceType.EXPERT_KNOWLEDGE],
            ),
        ]

    def _initialize_citation_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize regex patterns for citation detection"""
        return {
            "doi": re.compile(r"10\.\d{4,}/[^\s]+"),
            "arxiv": re.compile(r"arXiv:(\d{4}\.\d{4,5})(v\d+)?"),
            "isbn": re.compile(r"ISBN[:\s]*((?:97[89])?\d{9}[\dXx])"),
            "pmid": re.compile(r"PMID[:\s]*(\d+)"),
            "url": re.compile(r"https?://[^\s]+"),
            "github": re.compile(r"github\.com/([^/]+/[^/\s]+)"),
            "citation": re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\((\d{4})\)"),
            "reference": re.compile(r"\[(\d+)\]"),
            "title_in_quotes": re.compile(r'"([^"]+)"'),
        }

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def discover_from_content(self, content: str) -> List[KnowledgeSource]:
        """Discover knowledge sources from content text"""
        discovered_sources = []

        # Extract potential citations and references
        citations = self._extract_citations(content)

        # Process each citation type
        for citation_type, values in citations.items():
            if citation_type == "doi":
                discovered_sources.extend(await self._discover_from_dois(values))
            elif citation_type == "arxiv":
                discovered_sources.extend(await self._discover_from_arxiv(values))
            elif citation_type == "isbn":
                discovered_sources.extend(await self._discover_from_isbn(values))
            elif citation_type == "github":
                discovered_sources.extend(await self._discover_from_github(values))
            elif citation_type == "url":
                discovered_sources.extend(await self._discover_from_urls(values))

        return discovered_sources

    def _extract_citations(self, content: str) -> Dict[str, List[str]]:
        """Extract citations from content using regex patterns"""
        citations = {}

        for citation_type, pattern in self.citation_patterns.items():
            matches = pattern.findall(content)
            if matches:
                if citation_type == "arxiv":
                    # arXiv pattern returns tuples, we want just the ID
                    matches = [
                        match[0] if isinstance(match, tuple) else match
                        for match in matches
                    ]
                citations[citation_type] = matches

        return citations

    async def _discover_from_dois(self, dois: List[str]) -> List[KnowledgeSource]:
        """Discover sources from DOIs using CrossRef API"""
        sources = []

        if not self.session:
            return sources

        for doi in dois:
            try:
                url = f"https://api.crossref.org/works/{doi}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        work = data.get("message", {})

                        # Extract authors
                        authors = []
                        for author in work.get("author", []):
                            given = author.get("given", "")
                            family = author.get("family", "")
                            if given and family:
                                authors.append(f"{given} {family}")
                            elif family:
                                authors.append(family)

                        # Extract publication date
                        pub_date = None
                        if "published-print" in work:
                            date_parts = work["published-print"].get(
                                "date-parts", [[]]
                            )[0]
                            if len(date_parts) >= 3:
                                pub_date = datetime(
                                    date_parts[0], date_parts[1], date_parts[2]
                                )

                        source = KnowledgeSource(
                            id=f"doi_{doi.replace('/', '_')}",
                            type=KnowledgeSourceType.ACADEMIC_PAPER,
                            title=work.get("title", ["Unknown"])[0],
                            authors=authors,
                            publication_date=pub_date,
                            doi=doi,
                            url=work.get("URL"),
                            verification_status=VerificationStatus.VERIFIED,
                            confidence_score=0.9,
                            metadata={
                                "journal": work.get("container-title", [""])[0],
                                "publisher": work.get("publisher", ""),
                                "volume": work.get("volume", ""),
                                "issue": work.get("issue", ""),
                                "pages": work.get("page", ""),
                                "source": "CrossRef",
                            },
                        )
                        sources.append(source)

            except Exception as e:
                logger.error(f"Error discovering DOI {doi}: {e}")
                continue

        return sources

    async def _discover_from_arxiv(self, arxiv_ids: List[str]) -> List[KnowledgeSource]:
        """Discover sources from arXiv IDs"""
        sources = []

        if not self.session:
            return sources

        for arxiv_id in arxiv_ids:
            try:
                url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        xml_content = await response.text()

                        # Parse XML (simplified - would need proper XML parser)
                        import xml.etree.ElementTree as ET

                        root = ET.fromstring(xml_content)

                        # Find entry
                        entry = root.find(".//{http://www.w3.org/2005/Atom}entry")
                        if entry is not None:
                            title_elem = entry.find(
                                ".//{http://www.w3.org/2005/Atom}title"
                            )
                            title = (
                                title_elem.text if title_elem is not None else "Unknown"
                            )

                            # Extract authors
                            authors = []
                            for author in entry.findall(
                                ".//{http://www.w3.org/2005/Atom}author"
                            ):
                                name_elem = author.find(
                                    ".//{http://www.w3.org/2005/Atom}name"
                                )
                                if name_elem is not None:
                                    authors.append(name_elem.text)

                            # Extract publication date
                            pub_date = None
                            published_elem = entry.find(
                                ".//{http://www.w3.org/2005/Atom}published"
                            )
                            if published_elem is not None:
                                pub_date = datetime.fromisoformat(
                                    published_elem.text.replace("Z", "+00:00")
                                )

                            source = KnowledgeSource(
                                id=f"arxiv_{arxiv_id}",
                                type=KnowledgeSourceType.ACADEMIC_PAPER,
                                title=title.strip(),
                                authors=authors,
                                publication_date=pub_date,
                                url=f"https://arxiv.org/abs/{arxiv_id}",
                                verification_status=VerificationStatus.VERIFIED,
                                confidence_score=0.85,
                                metadata={"arxiv_id": arxiv_id, "source": "arXiv"},
                            )
                            sources.append(source)

            except Exception as e:
                logger.error(f"Error discovering arXiv {arxiv_id}: {e}")
                continue

        return sources

    async def _discover_from_isbn(self, isbns: List[str]) -> List[KnowledgeSource]:
        """Discover sources from ISBNs using OpenLibrary API"""
        sources = []

        if not self.session:
            return sources

        for isbn in isbns:
            try:
                url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        book_data = data.get(f"ISBN:{isbn}", {})

                        if book_data:
                            # Extract authors
                            authors = []
                            for author in book_data.get("authors", []):
                                authors.append(author.get("name", ""))

                            # Extract publication date
                            pub_date = None
                            if "publish_date" in book_data:
                                try:
                                    pub_date = datetime.strptime(
                                        book_data["publish_date"], "%Y"
                                    )
                                except ValueError:
                                    pass

                            source = KnowledgeSource(
                                id=f"isbn_{isbn}",
                                type=KnowledgeSourceType.BOOK,
                                title=book_data.get("title", "Unknown"),
                                authors=authors,
                                publication_date=pub_date,
                                isbn=isbn,
                                url=book_data.get("url"),
                                verification_status=VerificationStatus.VERIFIED,
                                confidence_score=0.9,
                                metadata={
                                    "publisher": ", ".join(
                                        pub.get("name", "")
                                        for pub in book_data.get("publishers", [])
                                    ),
                                    "pages": book_data.get("number_of_pages"),
                                    "source": "OpenLibrary",
                                },
                            )
                            sources.append(source)

            except Exception as e:
                logger.error(f"Error discovering ISBN {isbn}: {e}")
                continue

        return sources

    async def _discover_from_github(
        self, repo_paths: List[str]
    ) -> List[KnowledgeSource]:
        """Discover sources from GitHub repository paths"""
        sources = []

        if not self.session:
            return sources

        for repo_path in repo_paths:
            try:
                url = f"https://api.github.com/repos/{repo_path}"
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Extract contributors
                        contributors_url = (
                            f"https://api.github.com/repos/{repo_path}/contributors"
                        )
                        authors = []

                        async with self.session.get(
                            contributors_url
                        ) as contrib_response:
                            if contrib_response.status == 200:
                                contributors = await contrib_response.json()
                                authors = [
                                    c.get("login", "") for c in contributors[:5]
                                ]  # Top 5 contributors

                        # Extract creation date
                        pub_date = None
                        if "created_at" in data:
                            pub_date = datetime.fromisoformat(
                                data["created_at"].replace("Z", "+00:00")
                            )

                        source = KnowledgeSource(
                            id=f"github_{repo_path.replace('/', '_')}",
                            type=KnowledgeSourceType.CODE_REPOSITORY,
                            title=data.get("name", "Unknown"),
                            authors=authors,
                            publication_date=pub_date,
                            repository_url=data.get("html_url"),
                            url=data.get("html_url"),
                            license=data.get("license", {}).get("name")
                            if data.get("license")
                            else None,
                            verification_status=VerificationStatus.VERIFIED,
                            confidence_score=0.8,
                            metadata={
                                "language": data.get("language", ""),
                                "stars": data.get("stargazers_count", 0),
                                "forks": data.get("forks_count", 0),
                                "description": data.get("description", ""),
                                "source": "GitHub",
                            },
                        )
                        sources.append(source)

            except Exception as e:
                logger.error(f"Error discovering GitHub repo {repo_path}: {e}")
                continue

        return sources

    async def _discover_from_urls(self, urls: List[str]) -> List[KnowledgeSource]:
        """Discover sources from generic URLs"""
        sources = []

        if not self.session:
            return sources

        for url in urls:
            try:
                # Skip if already processed as specific type
                if any(
                    domain in url for domain in ["github.com", "arxiv.org", "doi.org"]
                ):
                    continue

                async with self.session.get(url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()

                        # Extract metadata from HTML
                        title = self._extract_title_from_html(content)
                        authors = self._extract_authors_from_html(content)

                        # Determine source type based on URL
                        source_type = self._determine_source_type_from_url(url)

                        source = KnowledgeSource(
                            id=f"url_{hash(url)}",
                            type=source_type,
                            title=title or "Unknown",
                            authors=authors,
                            url=url,
                            verification_status=VerificationStatus.PENDING,
                            confidence_score=0.5,
                            metadata={
                                "source": "URL_Discovery",
                                "domain": url.split("/")[2] if "/" in url else url,
                            },
                        )
                        sources.append(source)

            except Exception as e:
                logger.error(f"Error discovering URL {url}: {e}")
                continue

        return sources

    def _extract_title_from_html(self, html_content: str) -> Optional[str]:
        """Extract title from HTML content"""
        title_pattern = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
        match = title_pattern.search(html_content)
        if match:
            return match.group(1).strip()

        # Try meta title
        meta_title_pattern = re.compile(
            r'<meta[^>]*name=["\']title["\'][^>]*content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        match = meta_title_pattern.search(html_content)
        if match:
            return match.group(1).strip()

        return None

    def _extract_authors_from_html(self, html_content: str) -> List[str]:
        """Extract authors from HTML content"""
        authors = []

        # Try meta author
        author_patterns = [
            r'<meta[^>]*name=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta[^>]*property=["\']author["\'][^>]*content=["\']([^"\']+)["\']',
        ]

        for pattern in author_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            authors.extend(matches)

        return authors[:5]  # Limit to 5 authors

    def _determine_source_type_from_url(self, url: str) -> KnowledgeSourceType:
        """Determine source type based on URL patterns"""
        domain = url.split("/")[2] if "/" in url else url.lower()

        if any(
            pattern in domain for pattern in ["blog", "medium", "dev.to", "hashnode"]
        ):
            return KnowledgeSourceType.BLOG_POST
        elif any(pattern in domain for pattern in ["wikipedia", "wiki"]):
            return KnowledgeSourceType.DOCUMENTATION
        elif any(pattern in domain for pattern in ["stackoverflow", "stackexchange"]):
            return KnowledgeSourceType.DOCUMENTATION
        elif any(pattern in domain for pattern in ["youtube", "vimeo"]):
            return KnowledgeSourceType.EXPERT_KNOWLEDGE
        else:
            return KnowledgeSourceType.DOCUMENTATION

    async def verify_source_external(
        self, source: KnowledgeSource
    ) -> Tuple[VerificationStatus, float]:
        """Verify a source using external APIs"""
        if source.doi:
            return await self._verify_doi(source.doi)
        elif source.isbn:
            return await self._verify_isbn(source.isbn)
        elif source.repository_url and "github.com" in source.repository_url:
            return await self._verify_github_repo(source.repository_url)
        else:
            return VerificationStatus.PENDING, 0.5

    async def _verify_doi(self, doi: str) -> Tuple[VerificationStatus, float]:
        """Verify DOI using CrossRef API"""
        try:
            if not self.session:
                return VerificationStatus.PENDING, 0.5

            url = f"https://api.crossref.org/works/{doi}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return VerificationStatus.VERIFIED, 0.95
                else:
                    return VerificationStatus.REJECTED, 0.1
        except Exception as e:
            logger.error(f"Error verifying DOI {doi}: {e}")
            return VerificationStatus.UNKNOWN, 0.3

    async def _verify_isbn(self, isbn: str) -> Tuple[VerificationStatus, float]:
        """Verify ISBN using OpenLibrary API"""
        try:
            if not self.session:
                return VerificationStatus.PENDING, 0.5

            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if f"ISBN:{isbn}" in data:
                        return VerificationStatus.VERIFIED, 0.9
                    else:
                        return VerificationStatus.REJECTED, 0.1
                else:
                    return VerificationStatus.UNKNOWN, 0.3
        except Exception as e:
            logger.error(f"Error verifying ISBN {isbn}: {e}")
            return VerificationStatus.UNKNOWN, 0.3

    async def _verify_github_repo(
        self, repo_url: str
    ) -> Tuple[VerificationStatus, float]:
        """Verify GitHub repository"""
        try:
            if not self.session:
                return VerificationStatus.PENDING, 0.5

            # Extract repo path from URL
            repo_path = repo_url.replace("https://github.com/", "")
            url = f"https://api.github.com/repos/{repo_path}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Higher confidence for popular repositories
                    stars = data.get("stargazers_count", 0)
                    confidence = min(0.9, 0.6 + (stars / 1000) * 0.3)
                    return VerificationStatus.VERIFIED, confidence
                else:
                    return VerificationStatus.REJECTED, 0.1
        except Exception as e:
            logger.error(f"Error verifying GitHub repo {repo_url}: {e}")
            return VerificationStatus.UNKNOWN, 0.3

    async def batch_discover_and_verify(
        self, contents: List[str]
    ) -> List[KnowledgeSource]:
        """Batch discover and verify sources from multiple content pieces"""
        all_sources = []

        # Discover sources from all content
        for content in contents:
            sources = await self.discover_from_content(content)
            all_sources.extend(sources)

        # Remove duplicates based on ID
        unique_sources = {}
        for source in all_sources:
            if source.id not in unique_sources:
                unique_sources[source.id] = source
            else:
                # Increment usage count for duplicates
                unique_sources[source.id].usage_count += 1

        # Verify sources
        verified_sources = []
        for source in unique_sources.values():
            status, confidence = await self.verify_source_external(source)
            source.verification_status = status
            source.confidence_score = confidence
            verified_sources.append(source)

        return verified_sources
