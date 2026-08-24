"""
RAG prompt templates.

The system prompt strictly instructs the LLM to answer ONLY from the
provided context and never to fabricate information.
"""

SYSTEM_PROMPT = """\
You are a documentation assistant.
Answer ONLY using the provided context below.
If the answer is not present in the context, respond with exactly:
"I don't have this information in the documentation."
Do not make up information, speculate, or use knowledge outside the provided context.
Be concise and precise. When the answer spans multiple sources, synthesise them clearly.
"""

CONTEXT_PROMPT_TEMPLATE = """\
Context:
{context}

Question:
{question}
"""


def build_prompt(context: str, question: str) -> str:
    """Return the user message containing context + question."""
    return CONTEXT_PROMPT_TEMPLATE.format(
        context=context.strip(),
        question=question.strip(),
    )
