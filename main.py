from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever

app = FastAPI()

# Add CORS middleware to allow browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

model = OllamaLLM(model="hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest")

template = """
You are an expert in answering questions about a pizza restaurant. Be concise and friendly in your responses.

Previous conversation context:
{history}

Here are some relevant reviews: {reviews}

Current question: {question}

Please provide a direct and helpful response based on the reviews and previous context.
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

class Message(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: List[Message]
    new_question: str

@app.get("/")
def read_root():
    return FileResponse("index.html")

@app.post("/ask")
async def ask_question(chat_data: ChatHistory):
    # Format chat history
    history = "\n".join([
        f"{'Assistant' if msg.role == 'assistant' else 'User'}: {msg.content}"
        for msg in chat_data.messages[-4:]  # Keep last 4 messages for context
    ])
    
    # Get relevant reviews for the new question
    reviews = retriever.invoke(chat_data.new_question)
    
    # Generate response
    result = chain.invoke({
        "history": history,
        "reviews": reviews,
        "question": chat_data.new_question
    })
    
    return {"answer": result}