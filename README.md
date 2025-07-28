# Round 1A - PDF Outline Extractor

## 🔹 Overview
This script processes multiple PDF documents and extracts a summarized structure based on a given **persona** and their **task**. It selects only the most relevant high-level sections across documents.

## 🔹 Input
- PDF files inside `/input/`
- A predefined persona and job intent (used internally)

## 🔹 Output
- A single `output.json` file placed inside `/output/`
- Includes top matching sections based on persona-role keywords

## 🔹 Tech Stack
- Python 3.10
- PyMuPDF 1.22.3
- Docker (for containerized run)

## 🔹 How to Run
```bash
docker build -t pdf-outline-extractor:latest .
docker run --rm -v "%cd%/app/input":/app/input -v "%cd%/app/output":/app/output --network none pdf-outline-extractor:latest
