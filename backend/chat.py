"""
chat.py
Module 4 - Chat Interface.

Ties together Module 3 (RAG retrieval) with an LLM to produce a
grounded answer: retrieve the most relevant chunks for the question,
then ask Gemini to answer USING ONLY those chunks.

Design choices (worth knowing if asked in interview):
- The prompt explicitly instructs the model to say it doesn't know
  rather than guess, if the retrieved context doesn't contain the
  answer. This is the core anti-hallucination technique in RAG - the
  model is not being asked "what do you know about X", it's being
  asked "given ONLY this text, answer X".
- We pass k=6 chunks (~4-5k chars) as context - enough for the model
  to have real material to work with, without stuffing the prompt
  with irrelevant text that could dilute the answer. Bumped from an
  earlier k=4 after finding that structured, multi-item documents
  (like a resume with several projects) need more retrieved chunks to
  reliably cover every item, not just the ones most similar to the
  literal wording of the question.
- Temperature is kept low (0.2) because we want faithful, consistent
  answers grounded in the document, not creative variation.
"""

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

import rag

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

SYSTEM_PROMPT = (
    "You are a document assistant. Answer the user's question using ONLY "
    "the context provided below, which was retrieved from a document they "
    "uploaded. Do not use any outside knowledge.\n\n"
    "If the context does not contain enough information to answer the "
    "question, say clearly: \"I couldn't find that in the document.\" "
    "Do not guess or make up an answer.\n\n"
    "Keep your answer concise and directly grounded in the context."
)

_llm = None  # lazy-loaded singleton, same pattern as rag.py's embedder


def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        if not GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY not set. Add it to a .env file in the project "
                "root: GOOGLE_API_KEY=your_key_here "
                "(get a free key at https://aistudio.google.com/apikey)"
            )
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.2,
        )
    return _llm


def answer_question(vectorstore_path: str, question: str, k: int = 6) -> str:
    """
    Runs the full RAG chat step:
      1. Retrieve the k most relevant chunks for the question (Module 3)
      2. Build a prompt that grounds the LLM in ONLY those chunks
      3. Return the model's answer as plain text
    """
    chunks = rag.semantic_search(vectorstore_path, question, k=k)

    if not chunks:
        return "I couldn't find that in the document."

    context = "\n\n---\n\n".join(chunks)

    llm = get_llm()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context}\n\nQuestion: {question}"),
    ]

    response = llm.invoke(messages)
    return response.content
