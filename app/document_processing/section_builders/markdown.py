from __future__ import annotations

import re
import uuid

from langchain_text_splitters import MarkdownHeaderTextSplitter

from app.document_processing.schemas import (
    ParentSection,
    ParsedDocument,
    StructuredDocument,
)
from app.document_processing.section_builders.base import (
    BaseSectionBuilder,
)


class MarkdownSectionBuilder(BaseSectionBuilder):

    PAGE_MARKER_PATTERN = re.compile(
        r"<!-- PAGE:(\d+) -->"
    )

    HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.+)$",
        re.MULTILINE,
    )

    def __init__(self) -> None:

        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ],
            strip_headers=False,
        )

    async def build(
        self,
        parsed_document: ParsedDocument,
    ) -> StructuredDocument:

        merged_markdown = self._merge_pages(
            parsed_document,
        )

        documents = self.splitter.split_text(
            merged_markdown,
        )

        sections: list[ParentSection] = []

        for index, document in enumerate(documents):

            markdown = document.page_content

            page_numbers = self._extract_page_numbers(
                markdown,
            )

            markdown = self._remove_page_markers(
                markdown,
            ).strip()

            heading, heading_level = self._extract_heading(
                markdown,
            )

            sections.append(
                ParentSection(
                    id=str(index),
                    heading=heading,
                    heading_level=heading_level,
                    markdown=markdown,
                    page_numbers=page_numbers,
                )
            )

        return StructuredDocument(
            sections=sections,
        )

    def _merge_pages(
        self,
        parsed_document: ParsedDocument,
    ) -> str:

        parts: list[str] = []

        for page in parsed_document.pages:

            parts.append(
                f"<!-- PAGE:{page.page_number} -->"
            )

            parts.append(
                page.markdown
            )

        return "\n\n".join(parts)

    def _extract_page_numbers(
        self,
        markdown: str,
    ) -> list[int]:

        pages = {
            int(page)
            for page in self.PAGE_MARKER_PATTERN.findall(
                markdown,
            )
        }

        return sorted(pages)

    def _remove_page_markers(
        self,
        markdown: str,
    ) -> str:

        return self.PAGE_MARKER_PATTERN.sub(
            "",
            markdown,
        )

    def _extract_heading(
        self,
        markdown: str,
    ) -> tuple[str, int]:

        match = self.HEADING_PATTERN.search(
            markdown,
        )

        if match is None:
            return (
                "Untitled",
                0,
            )

        hashes, heading = match.groups()

        return (
            heading.strip(),
            len(hashes),
        )