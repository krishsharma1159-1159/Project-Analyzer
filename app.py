import os
import json
import logging
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pdfplumber
from docx import Document
import google.generativeai as genai
from dotenv import load_dotenv
import main

# ---------- Setup ----------
logging.basicConfig(level=logging.INFO)

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing. Please set it in your .env file.")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-flash-latest")

app = Flask(__name__, static_folder=None)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB limit

RESUME_SCHEMA_PROMPT = """
You are a resume parser. Extract structured data from the resume text below.
Return ONLY valid JSON, no markdown formatting, no explanations, no ```json fences, no extra text before or after.

Use exactly this structure:
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

Rules:
- Use ONLY information explicitly present in the resume text below. Do not use outside knowledge.
- If a field isn't found in the resume, use an empty string "" or empty array [].
- Do not invent, guess, or infer skills, experience, projects, achievements, companies, dates, or links that are not explicitly written in the resume text.
- "title" means the person's professional title/role (e.g. "Computer Science Student", "Software Developer"), not their name.
- Keep the "summary" field concise (1-2 sentences), strictly factual, and based only on what the resume states — no added motivational language or unsupported claims.
- Keep experience/project descriptions concise (1-2 sentences) and factual.

Resume text:
"""


# ---------- Helper functions ----------

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_text(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def extract_text(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()

    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    elif ext == 'pdf':
        text = ""
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text

    elif ext == 'docx':
        doc = Document(filepath)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    return ""

def generate_resume_json(resume_text):
    resume_text = clean_text(resume_text)
    full_prompt = RESUME_SCHEMA_PROMPT + resume_text

    try:
        response = model.generate_content(full_prompt)
        raw_output = response.text.strip()
    except Exception as e:
        logging.error(f"Gemini API call failed: {e}")
        return {"error": "Gemini API request failed. Please check your API key or try again later."}

    raw_output = raw_output.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        logging.error(f"JSON parse failed. Raw output: {raw_output}")
        return {"error": "Failed to parse JSON from Gemini", "raw_output": raw_output}

# ---------- Frontend routes ----------
# Serves the static site (frontend.html, the 4 portfolio templates, and the
# shared render script) from the SAME Flask process, so `python app.py` is
# the only command needed. Only these known files are exposed — not the
# whole project folder (keeps .env, uploads/, etc. off-limits).
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_STATIC_FILES = {
    'frontend.html',
    'portfolio1.html',
    'portfolio2.html',
    'portfolio3.html',
    'portfolio4.html',
    'portfolio-render.js',
}

@app.route('/')
def serve_frontend():
    return send_from_directory(FRONTEND_DIR, 'frontend.html')
 
 
@app.route('/<path:filename>')
def serve_static_file(filename):
    if filename not in ALLOWED_STATIC_FILES:
        return jsonify({"error": "Not found"}), 404
    return send_from_directory(FRONTEND_DIR, filename)



# ---------- Routes ----------

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


@app.route('/generate-portfolio', methods=['POST'])
def generate_portfolio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only .txt, .pdf, .docx files are allowed"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    resume_text = extract_text(filepath)
    if not resume_text.strip():
        return jsonify({"error": "Could not extract any text from this file. It may be a scanned image or corrupted."}), 422

    structured_data = generate_resume_json(resume_text)

    if "error" in structured_data:
        return jsonify(structured_data), 500

    return jsonify(structured_data), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
