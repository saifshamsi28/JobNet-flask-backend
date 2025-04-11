import re
import spacy
from pdfminer.high_level import extract_text
from nltk.corpus import stopwords

nlp = spacy.load("en_core_web_sm")
STOPWORDS = set(stopwords.words('english'))

def extract_text_from_pdf(file_path):
    return extract_text(file_path)

def clean_text(text):
    text = text.lower()
    return ' '.join([word for word in text.split() if word not in STOPWORDS])

def extract_skills(text):
    skills_db = {"python", "java", "spring boot", "flask", "django", "kotlin", "c", "c++", "mysql", "sql", "mongodb",
                 "firebase", "android", "docker", "rest apis", "git", "github", "postman", "gcp", "aws",
                 "room database", "xml", "html", "css", "react", "node.js"}
    text_lower = text.lower()
    return sorted({skill for skill in skills_db if skill in text_lower})

def extract_experience(text):
    patterns = [
        r'(\d+)\s*(?:\+)?\s*years?',
        r'since\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}',
        r'from\s+\d{4}\s+to\s+\d{4}'
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group()
    return "Less than 1 year"

def extract_phone(text):
    match = re.search(r'(\+?\d{1,3})?[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{4}', text)
    return match.group() if match else None

def extract_email(text):
    match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', text)
    return match.group() if match else None

def extract_urls(text):
    urls = re.findall(r'https?://[^\s,;)\]]+', text)
    urls_dict = {"linkedin": None, "github": None, "portfolio": None}
    for url in urls:
        if 'linkedin' in url.lower():
            urls_dict["linkedin"] = url
        elif 'github' in url.lower():
            urls_dict["github"] = url
        else:
            urls_dict["portfolio"] = url  # fallback
    return urls_dict

def extract_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if re.search(r'\b(md|mohammad|mr|ms|miss|mrs)?\s?saif', line.lower()):  # fuzzy match
            return line.title()
    return lines[0].strip().title()

def extract_resume_info(file_path):
    text = extract_text_from_pdf(file_path)
    cleaned_text = clean_text(text)

    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "linkedin": extract_urls(text)["linkedin"],
        "github": extract_urls(text)["github"],
        "portfolio": extract_urls(text)["portfolio"],
        "skills": extract_skills(cleaned_text),
        "experience": extract_experience(text),
        "raw_text_snippet": text[:1000]
    }
