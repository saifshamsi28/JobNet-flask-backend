import re
import fitz  # PyMuPDF
import spacy
from nltk.corpus import stopwords

nlp = spacy.load("en_core_web_sm")
STOPWORDS = set(stopwords.words("english"))


def extract_text_and_links_from_pdf(file_path):
    text = ""
    urls = set()

    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
            links = page.get_links()
            for link in links:
                if "uri" in link:
                    urls.add(link["uri"])
    return text, list(urls)

def clean_text(text):
    text = text.lower()
    return ' '.join(word for word in text.split() if word not in STOPWORDS)

def format_to_camel_case(skill):
    """Converts strings like 'spring boot' → 'Spring Boot'."""
    return ' '.join(word.capitalize() for word in skill.split())

def extract_skills(text):
    skills_db = {
        "python", "java", "spring boot", "flask", "django", "kotlin", "c", "c++", "mysql", "sql", "mongodb",
        "firebase", "android", "docker", "rest apis", "git", "github", "postman", "gcp", "aws",
        "room database", "xml", "html", "css", "react", "node.js"
    }
    text_lower = text.lower()
    matched_skills = {skill for skill in skills_db if skill in text_lower}
    return sorted([format_to_camel_case(skill) for skill in matched_skills])


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

# def extract_email(text):
#     match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', text)
#     return match.group() if match else None

def extract_phone(text):
    match = re.search(r'(\+?\d{1,3})?[\s\-]?\(?\d{3,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{4}', text)
    return match.group() if match else None

def extract_urls(url_list):
    urls_dict = {"linkedin": None, "github": None, "portfolio": None}
    for url in url_list:
        if "linkedin.com/in" in url.lower():
            urls_dict["linkedin"] = url
        elif "github.com/" in url.lower():
            # Prefer profile (not repo)
            if url.count("/") == 3:  # https://github.com/username
                urls_dict["github"] = url
        elif "mailto:" not in url and not any(x in url for x in ["leetcode", "geeksforgeeks", "github", "linkedin"]):
            urls_dict["portfolio"] = url
    return urls_dict

def extract_email(text, url_list):
    # 1. Look for mailto: from extracted URLs
    for url in url_list:
        if url.startswith("mailto:"):
            return url.replace("mailto:", "").strip()

    # 2. Fallback to regex in raw text
    match = re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', text)
    return match.group() if match else None


def extract_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        if re.search(r'\b(md|mohammad|mr|ms|miss|mrs)?\s?saif', line.lower()):
            return line.title()
    return lines[0].strip().title()

def extract_resume_info(file_path):
    text, found_links = extract_text_and_links_from_pdf(file_path)
    cleaned_text = clean_text(text)

    urls = extract_urls(found_links)

    return {
        "name": extract_name(text),
        "email": extract_email(text,found_links),
        "phone": extract_phone(text),
        "linkedin": urls["linkedin"],
        "github": urls["github"],
        "portfolio": urls["portfolio"],
        "skills": extract_skills(cleaned_text),
        "experience": extract_experience(text),
        "raw_text_snippet": text
    }
