import os
import re
from pathlib import Path
from typing import Tuple


class ResumeExtractor:
    supported_formats = {".pdf", ".docx", ".doc", ".txt"}

    def extract_from_file(self, file_path: str) -> Tuple[str, dict]:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            return self._from_pdf(file_path)
        if ext in {".docx", ".doc"}:
            return self._from_docx(file_path)
        if ext == ".txt":
            return self._from_txt(file_path)
        raise ValueError(f"Unsupported format: {ext}")

    def _from_pdf(self, path: str) -> Tuple[str, dict]:
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError(
                "pdfplumber is not installed. Run: pip install pdfplumber"
            )
        parts = []
        with pdfplumber.open(path) as pdf:
            pages = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    parts.append(text)
        return "\n".join(parts), {"format": "pdf", "pages": pages, "file_size": os.path.getsize(path)}

    def _from_docx(self, path: str) -> Tuple[str, dict]:
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError(
                "python-docx is not installed. Run: pip install python-docx"
            )
        doc = Document(path)
        parts = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(parts), {"format": "docx", "paragraphs": len(parts), "file_size": os.path.getsize(path)}

    def _from_txt(self, path: str) -> Tuple[str, dict]:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return text, {"format": "txt", "lines": len(text.splitlines()), "file_size": os.path.getsize(path)}

    def parse_structure(self, text: str) -> dict:
        return {
            "contact": self._extract_contact(text),
            "summary": self._extract_section(text, ["summary", "objective", "profile"]),
            "experience": self._extract_section(text, ["experience", "work history", "employment"]),
            "education": self._extract_section(text, ["education", "qualifications", "certifications"]),
            "skills": self._extract_section(text, ["skills", "technical skills", "competencies"]),
        }

    def _extract_contact(self, text: str) -> dict:
        contact = {}
        email = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if email:
            contact["email"] = email.group()
        phone = re.search(r"[\+]?[\d\s\-\(\)]{10,}", text)
        if phone:
            contact["phone"] = phone.group().strip()
        linkedin = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
        if linkedin:
            contact["linkedin"] = linkedin.group()
        github = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)
        if github:
            contact["github"] = github.group()
        return contact

    def _extract_section(self, text: str, keywords: list) -> str:
        lines = text.split("\n")
        collected = []
        inside = False
        for line in lines:
            lower = line.lower()
            if any(kw in lower for kw in keywords):
                inside = True
                continue
            if inside and line and not line[0].isspace():
                if any(kw in lower for kw in ["experience", "education", "skills", "projects", "summary", "objective"]):
                    break
            if inside and line.strip():
                collected.append(line)
        return "\n".join(collected).strip()
