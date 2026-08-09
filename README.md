# Resume to Portfolio Generator — Backend

Converts a user's resume (`.txt`, `.pdf`, or `.docx`) into structured JSON data using Google's Gemini API. This JSON is used by the frontend to auto-generate a personal portfolio website.

## Tech Stack
- Python
- Flask
- Gemini API (`google-generativeai`)
- pdfplumber (PDF text extraction)
- python-docx (DOCX text extraction)

## Project Structure
```
resume-backend/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── uploads/          (created automatically at runtime)
└── README.md
```

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd resume-backend
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
```
Windows:
```bash
venv\Scripts\activate
```
Mac/Linux:
```bash
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Copy `.env.example` to a new file named `.env`, then add your real Gemini API key:
```
GEMINI_API_KEY=your_actual_api_key_here
```
Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey).

### 5. Run the server
```bash
python app.py
```
Server runs at `http://localhost:5000`.

## API Documentation

### `GET /health`
Health check endpoint.

**Response (200):**
```json
{"status": "ok"}
```

### `POST /generate-portfolio`
Uploads a resume file and returns structured portfolio data.

**Request:**
- Type: `multipart/form-data`
- Field name: `file`
- Accepted file types: `.txt`, `.pdf`, `.docx`
- Max file size: 5MB

**Success Response (200):**
```json
{
  "name": "",
  "title": "",
  "email": "",
  "phone": "",
  "location": "",
  "summary": "",
  "skills": [],
  "experience": [
    {"company": "", "role": "", "duration": "", "description": ""}
  ],
  "education": [
    {"institution": "", "degree": "", "year": ""}
  ],
  "projects": [
    {"name": "", "description": "", "tech": []}
  ],
  "achievements": [],
  "links": {"github": "", "linkedin": "", "portfolio": ""}
}
```

**Error Responses:**
| Status | Meaning |
|---|---|
| 400 | No file sent, no file selected, or invalid file type |
| 422 | File uploaded but no readable text could be extracted |
| 500 | Gemini API call failed, or Gemini did not return valid JSON |

**Example request (curl):**
```bash
curl -X POST -F "file=@resume.pdf" http://localhost:5000/generate-portfolio
```

## How It Works
1. User uploads a resume file (`.txt`, `.pdf`, or `.docx`)
2. Flask validates the file type and size
3. Text is extracted from the file using `pdfplumber` (PDF) or `python-docx` (DOCX), or read directly (TXT)
4. Extracted text is cleaned (extra whitespace/blank lines removed)
5. Cleaned text is sent to Gemini with a structured prompt requesting only JSON output based strictly on resume content
6. Gemini's response is parsed and validated as JSON
7. Structured JSON is returned to the frontend

## Responsible AI Use
- The prompt explicitly instructs Gemini to use only information present in the resume and not invent skills, experience, projects, achievements, companies, dates, or links.
- No passwords, government IDs, financial details, or other highly sensitive information are requested or processed.
- Generated output is treated as a **draft**. Users should review and verify all AI-generated content against their original resume before publishing their portfolio.
- API keys are never hardcoded and are excluded from version control via `.gitignore`.

## AI Tool Usage Disclosure
Claude (Anthropic) was used during development to assist with Flask setup guidance, debugging errors, prompt engineering, and code review/refinement.

## Known Limitations
- Scanned/image-based PDFs with no embedded text layer cannot be processed (no OCR).
- Very unusually formatted resumes (heavy multi-column layouts, tables) may extract text with some section shuffling.
