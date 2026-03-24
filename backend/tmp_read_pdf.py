import sys
from pypdf import PdfReader

# Windows에서 UTF-8 출력을 강제하기 위해 sys.stdout의 인코딩을 변경
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'c:\Users\Julian\Desktop\Edu\구내식당 메뉴.pdf'
reader = PdfReader(pdf_path)
for i, page in enumerate(reader.pages):
    print(f"--- PAGE {i+1} ---")
    print(page.extract_text())
