# 📄 Intelligent Document Assistant

A full-stack **Retrieval-Augmented Generation (RAG)** application that allows users to upload documents and ask questions about their content.

The application supports **PDF, DOCX, and TXT** files. It extracts document text, converts it into vector embeddings, stores them in a **FAISS vector store**, retrieves relevant content, and generates grounded answers using **Google Gemini**.

The system is designed to answer questions based only on the uploaded document context.

---

## 🚀 Features

- 🔐 User Signup and Login
- 🔑 JWT Authentication
- 🔒 Password Hashing using bcrypt
- 📄 Upload PDF, DOCX, and TXT documents
- 📝 Automatic text extraction
- ✂️ Intelligent document chunking
- 🧠 Local embeddings using Sentence Transformers
- 🔎 Semantic search using FAISS
- 🤖 RAG-based question answering using Google Gemini
- 🛡️ Grounded answers to reduce hallucination
- 💬 Document-based chat interface
- 🗂️ Multiple document support
- 📜 Conversation history
- 🔐 User document ownership and access control
- 🌐 REST API using FastAPI
- 🖥️ Interactive frontend using Streamlit

---

# 🏗️ Architecture

```text
Streamlit Frontend
(frontend/app.py)
        │
        │ HTTP Requests
        ▼
FastAPI Backend
(backend/api.py)
        │
        ├──────────────► Authentication
        │                (auth.py)
        │
        ├──────────────► Document Upload
        │                (upload.py)
        │
        ├──────────────► RAG Pipeline
        │                (rag.py)
        │
        ├──────────────► Chat Service
        │                (chat.py)
        │
        ▼
SQLite Database
(User, Document, Chat History)

RAG Pipeline:
Document
   │
   ▼
Text Extraction
   │
   ▼
Text Chunking
   │
   ▼
Embeddings
(all-MiniLM-L6-v2)
   │
   ▼
FAISS Vector Store
   │
   ▼
Semantic Search
   │
   ▼
Relevant Context
   │
   ▼
Google Gemini
   │
   ▼
Grounded Answer
```

---

# 🔄 RAG Pipeline

```text
User uploads document
        │
        ▼
Document Text Extraction
(PDF / DOCX / TXT)
        │
        ▼
Text Chunking
(RecursiveCharacterTextSplitter)
        │
        ▼
Generate Embeddings
(all-MiniLM-L6-v2)
        │
        ▼
Store Vectors
(FAISS)
        │
        ▼
User asks a Question
        │
        ▼
Convert Question into Embedding
        │
        ▼
Semantic Similarity Search
        │
        ▼
Retrieve Top Relevant Chunks
        │
        ▼
Send Context + Question to Gemini
        │
        ▼
Generate Grounded Answer
```

---

# 🧠 How the RAG System Works

## 1. Document Upload

Users can upload:

- PDF
- DOCX
- TXT

The uploaded document is processed using:

```text
upload.py
```

The application extracts text from the uploaded document.

---

## 2. Text Chunking

Large documents are divided into smaller chunks before generating embeddings.

The application uses:

```python
RecursiveCharacterTextSplitter
```

Configuration:

```text
Chunk Size: 900 characters
Chunk Overlap: 100 characters
```

The overlap helps preserve context between consecutive chunks.

The splitter attempts to split text using meaningful boundaries such as:

1. Paragraphs
2. Lines
3. Sentences
4. Words

This helps maintain semantic coherence.

---

## 3. Embedding Generation

Each text chunk is converted into a numerical vector using:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Embeddings represent the semantic meaning of text.

This allows the application to perform semantic search instead of only keyword matching.

---

## 4. FAISS Vector Store

The generated embeddings are stored using:

```text
FAISS
```

FAISS performs efficient similarity search.

The application creates one vector store per document:

```text
vectorstore/

├── doc_1/
├── doc_2/
├── doc_3/
```

This ensures that semantic search is restricted to the document currently selected by the user.

---

## 5. Question Processing

When a user asks a question:

```text
User Question
        │
        ▼
Convert Question to Embedding
        │
        ▼
Search FAISS
        │
        ▼
Retrieve Top 6 Relevant Chunks
        │
        ▼
Send Context + Question to Gemini
        │
        ▼
Generate Answer
```

The system retrieves:

```text
Top K = 6 chunks
```

These chunks are provided to the LLM as context.

---

## 6. Grounded Answer Generation

The retrieved document content is sent to Google Gemini along with a system prompt.

The model is instructed to:

```text
Use ONLY the provided document context.
Do not use outside knowledge.
Do not guess or hallucinate.
```

If the required information is not available in the retrieved context, the application responds:

```text
I couldn't find that in the document.
```

This helps reduce hallucination.

---

# 📂 Project Structure

```text
Intelligent-Document-Assistant/
│
├── backend/
│   │
│   ├── api.py
│   ├── auth.py
│   ├── chat.py
│   ├── database.py
│   ├── models.py
│   ├── rag.py
│   ├── schemas.py
│   ├── upload.py
│   └── requirements.txt
│
├── frontend/
│   │
│   ├── app.py
│   └── requirements.txt
│
└── README.md
```

---

# ⚙️ Backend Components

## `api.py`

The main FastAPI application.

It provides REST API endpoints for:

- User signup
- User login
- Current user information
- Document upload
- Document listing
- Chat with a document
- Chat history

Main API endpoints:

```text
POST   /signup
POST   /login
GET    /me

POST   /upload
GET    /documents

POST   /chat

GET    /history/{document_id}
```

---

## `auth.py`

Handles authentication and security.

Responsibilities include:

- Password hashing
- Password verification
- JWT token generation
- JWT token validation
- Current user authentication

Technologies used:

```text
bcrypt
JWT
OAuth2PasswordBearer
```

---

## `database.py`

Configures the database connection.

The application uses:

```text
SQLite
```

with:

```text
SQLAlchemy
```

It provides:

- Database engine
- Session management
- Base model
- Database dependency

Each API request receives a database session.

The session is automatically closed after the request finishes.

---

## `models.py`

Defines SQLAlchemy ORM models.

### User

Stores:

```text
id
username
email
hashed_password
created_at
```

A user can own multiple documents.

---

### Document

Stores:

```text
id
filename
filepath
vectorstore_path
owner_id
uploaded_at
```

Each document belongs to a specific user.

---

### ChatHistory

Stores:

```text
id
user_id
document_id
question
answer
timestamp
```

This allows users to access previous conversations.

---

## `upload.py`

Handles document processing.

Responsibilities include:

- File upload
- File validation
- Saving uploaded files
- PDF text extraction
- DOCX text extraction
- TXT text extraction

The extracted text is passed to the RAG pipeline.

---

## `rag.py`

Handles the complete document indexing process.

Responsibilities:

1. Split document text into chunks
2. Generate embeddings
3. Create a FAISS vector store
4. Save the FAISS index
5. Load the vector store
6. Perform semantic similarity search

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
```

---

## `chat.py`

Connects the RAG pipeline with Google Gemini.

Process:

```text
User Question
      │
      ▼
Retrieve Relevant Chunks
      │
      ▼
Build Context
      │
      ▼
Send Context + Question to Gemini
      │
      ▼
Generate Grounded Answer
```

The model uses a low temperature:

```text
Temperature: 0.2
```

This helps produce more consistent and factual responses.

---

# 🔐 Authentication Flow

## Signup

```text
User Signup
      │
      ▼
Password Hashing
      │
      ▼
Store User in SQLite
```

Passwords are hashed before being stored.

---

## Login

```text
Username + Password
        │
        ▼
Find User in Database
        │
        ▼
Verify Password
        │
        ▼
Generate JWT Token
        │
        ▼
Return Access Token
```

The frontend sends the token with protected API requests:

```text
Authorization: Bearer <JWT_TOKEN>
```

The backend validates the token before allowing access.

---

# 📄 Document Upload Flow

```text
User uploads document
        │
        ▼
FastAPI /upload
        │
        ▼
Verify authenticated user
        │
        ▼
Save file locally
        │
        ▼
Extract text
        │
        ▼
Create Document record
        │
        ▼
Chunk text
        │
        ▼
Generate embeddings
        │
        ▼
Create FAISS index
        │
        ▼
Save vectorstore path
        │
        ▼
Return document information
```

---

# 💬 Chat Flow

```text
User selects document
        │
        ▼
User asks question
        │
        ▼
POST /chat
        │
        ▼
Verify JWT Token
        │
        ▼
Verify Document Ownership
        │
        ▼
Load FAISS Vector Store
        │
        ▼
Semantic Search
        │
        ▼
Retrieve Top 6 Relevant Chunks
        │
        ▼
Build Context
        │
        ▼
Send Context + Question to Gemini
        │
        ▼
Generate Grounded Answer
        │
        ▼
Save Question + Answer
        │
        ▼
Return Answer
```

---

# 🖥️ Frontend

The frontend is built using:

```text
Streamlit
```

The frontend communicates with the backend using:

```text
HTTP Requests
```

using the `requests` library.

The frontend does not directly access:

- SQLite database
- FAISS vector store
- Authentication logic
- Google Gemini

All operations go through the FastAPI REST API.

This keeps the frontend and backend decoupled.

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic

## Authentication

- JWT
- OAuth2
- bcrypt

## RAG

- LangChain
- Sentence Transformers
- HuggingFace Embeddings
- FAISS

## LLM

- Google Gemini

## Frontend

- Streamlit
- Requests

---

# 📦 Installation

## 1. Clone the Repository

```bash
git clone https://github.com/k-yadagiri/Intelligent-Document-Assistant.git
```

```bash
cd Intelligent-Document-Assistant
```

---

# 🔧 Backend Setup

Navigate to the backend folder:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment.

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file inside the backend folder.

```text
GOOGLE_API_KEY=your_google_api_key
JWT_SECRET_KEY=your_secret_key
```

⚠️ Never upload your `.env` file to GitHub.

---

# ▶️ Run the Backend

From the backend folder:

```bash
uvicorn api:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

FastAPI Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 🖥️ Frontend Setup

Open a new terminal.

Navigate to:

```bash
cd frontend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Streamlit application:

```bash
streamlit run app.py
```

The application will open at:

```text
http://localhost:8501
```

---

# 🔒 Security Features

## Password Hashing

Passwords are not stored directly.

They are hashed using:

```text
bcrypt
```

---

## JWT Authentication

Protected API routes require a valid JWT token.

---

## Document Ownership

Every document belongs to a specific user.

The backend verifies document ownership before allowing access.

Conceptually:

```python
document.owner_id == current_user.id
```

This prevents users from accessing another user's documents simply by guessing a document ID.

---

## Environment Variables

Sensitive information such as:

```text
GOOGLE_API_KEY
JWT_SECRET_KEY
```

is stored in:

```text
.env
```

The `.env` file should not be uploaded to GitHub.

---

# 🎯 Key Design Decisions

## Why RAG Instead of Fine-Tuning?

This application needs to answer questions based on user-uploaded documents.

Fine-tuning would require modifying or retraining a model when new information is introduced.

RAG is more suitable because:

- No model retraining is required
- New documents can be indexed immediately
- Information remains external to the LLM
- Relevant context is retrieved dynamically
- The model can answer based on the uploaded document

---

## Why FAISS?

FAISS provides efficient similarity search over vector embeddings.

Advantages:

- Fast
- Free
- Open source
- Suitable for local development

---

## Why Sentence Transformers?

The application uses:

```text
all-MiniLM-L6-v2
```

because it:

- Runs locally
- Is lightweight
- Produces semantic embeddings
- Does not require a paid embedding API
- Works offline after the model is downloaded

---

## Why SQLite?

SQLite was selected because this project is designed as a prototype and assignment project.

Advantages:

- No separate database server is required
- Easy setup
- Lightweight
- Suitable for local development

For a large-scale production application with multiple concurrent users, PostgreSQL would be a better choice.

---

## Why Separate Frontend and Backend?

The Streamlit frontend communicates with FastAPI through HTTP requests.

Advantages:

- Clear separation of responsibilities
- Easier maintenance
- Better scalability
- Frontend can be replaced independently
- Backend APIs can support multiple clients

---

# ⚠️ Known Limitations

- SQLite is suitable for local development but not ideal for large-scale production.
- FAISS indexes are stored locally.
- Scanned image-only PDFs are not supported because OCR is not implemented.
- No refresh token mechanism.
- Google Gemini requires an API key and internet connection.
- Local FAISS storage would need to be replaced or shared for multi-server deployment.

---

# 🔮 Future Improvements

Possible improvements include:

- OCR support for scanned documents
- PostgreSQL database
- Cloud vector database
- Multi-document chat
- Document deletion
- Improved conversation management
- Refresh tokens
- Role-based access control
- Docker containerization
- Cloud deployment
- Source citations in answers
- Hybrid search
- Reranking
- Conversation memory

---

# 👨‍💻 Author

**Yadagiri Kuruva**

B.Tech Graduate in Computer Science and Engineering  
Specialization: Artificial Intelligence and Data Science

GitHub: https://github.com/k-yadagiri

---

# ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub!
