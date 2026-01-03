import os
import re
import uuid
import json
import asyncio
import sys
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import logging
from dataclasses import dataclass, asdict

# Core LangChain imports
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.memory import ConversationSummaryBufferMemory
from langchain.schema import Document

# Enhanced document processing
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pymupdf  # PyMuPDF for better PDF handling
from docx import Document as DocxDocument
import io
import base64
from concurrent.futures import ThreadPoolExecutor

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

GOOGLE_API_KEY = ""

MODEL_ID = "gemini-2.5-flash"

llm = ChatGoogleGenerativeAI(
    model=MODEL_ID,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3,
)




def summarizer(responses: list):
    # convert AIMessage objects to strings if they exist
    responses_text = "\n".join([r.content if isinstance(r, AIMessage) else str(r) for r in responses])
    
    summary_prompt = f"You are an intelligent summarization assistant. You will receive a list of responses provided by users:\n{responses_text}\nYour task is to generate a concise, coherent, and meaningful summary of all these responses. Combine similar points, highlight the key ideas, avoid repetition, and keep it clear and readable. Provide the summary in 3-5 sentences maximum."
    
    result = llm.invoke(summary_prompt)
    # ensure the result is a string
    return str(result)



