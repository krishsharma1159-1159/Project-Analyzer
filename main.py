import fitz
import codecs
import docx2txt
import cv2
import pytesseract

from io import BytesIO
import numpy as np

def check_type(filename, data):
    filename = filename.lower()

    if filename.endswith(".pdf"):
        return extract_with_pymupdf(data)
    elif filename.endswith(".txt"):
        return read_with_codecs(data)
    elif filename.endswith(".docx"):
        return extract_with_docx2txt(data)
    elif filename.endswith((".png", ".jpg", ".jpeg")):
        return ocr_opencv_pytesseract(data)
    else:
        raise ValueError("Unsupported file type")


def extract_with_pymupdf(data):
    with fitz.open(stream=data, filetype="pdf") as doc:
        text = "".join(page.get_text() for page in doc)
    return text


def read_with_codecs(data):
    text = codecs.decode(data, "utf-8")
    return text


def extract_with_docx2txt(data):
    text = docx2txt.process(BytesIO(data))
    return text


def ocr_opencv_pytesseract(data):
    image_array = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Unable to read image.")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    text = pytesseract.image_to_string(thresh)
    return text