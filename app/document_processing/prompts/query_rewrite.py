from __future__ import annotations


class QueryRewritePromptBuilder:

    @staticmethod
    def build(
        query: str,
    ) -> str:

        return f"""
You are a search query optimizer for a Retrieval-Augmented Generation (RAG) system.

Your job is to rewrite the user's query so it retrieves the most relevant documents from a vector database.

Rules:

- Preserve the user's original intent.
- Expand abbreviations where appropriate.
- Add closely related synonyms only when they improve retrieval.
- Make the query explicit and self-contained.
- Do NOT answer the question.
- Do NOT invent facts.
- Do NOT include explanations.
- Output only the rewritten query.

User Query:

{query}

Rewritten Query:
""".strip()