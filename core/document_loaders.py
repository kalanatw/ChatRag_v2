import os
import json
from langchain_community.document_loaders import UnstructuredWordDocumentLoader, UnstructuredExcelLoader
from langchain_community.document_loaders import PyPDFLoader
import extract_msg
import aspose.words as aw
# from pptxtopdf import convert
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re

def extract_text_from_pdf(pdf_path, component):
    try:
        text = []
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()  # Returns a list of document objects (one per page)
            
        for doc in docs:
            page_text = doc.page_content  
            if page_text:
                formatted_text = f"This content belongs to the {component} component.\n\n{page_text}"
                text.append({'text': formatted_text}) 
                    
        os.remove(pdf_path)
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return []
        
def extract_text_from_docx(docx_path, component):
    try:
        text = []
        loader = UnstructuredWordDocumentLoader(docx_path)
        docs = loader.load()  # Returns a list of document objects (one per section/page)

        for doc in docs:
            formatted_text = f"This content belongs to the {component} component.\n\n{doc.page_content}"
            text.append({'text': formatted_text})
        os.remove(docx_path)
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        os.remove(docx_path)
        return []

def convert_doc_to_pdf(doc_path):
    doc = aw.Document(doc_path)
    pdf_path = doc_path.replace('.doc', '.pdf')
    doc.save(pdf_path)
    os.remove(doc_path)
    return pdf_path

def clean_text(content):
    cleaned_content = re.sub(r'[■�]+', ' ', content) 
    cleaned_content = re.sub(r'[^\x00-\x7F]+', ' ', cleaned_content)
    cleaned_content = re.sub(r'[\x00-\x1F\x7F]+', ' ', cleaned_content)
    return cleaned_content.strip()        

def convert_msg_to_pdf(msg_path):
    try:
        pdf_path = msg_path.replace(".msg", ".pdf")
        
        # Load the .msg file
        msg = extract_msg.Message(msg_path)
        msg_subject = msg.subject or "No Subject"
        msg_body = msg.body or "No Content"
        msg.close()
        
        msg.body = clean_text(msg_body)
        
        # Create PDF
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        
        # Add subject
        c.drawString(100, 750, f"Subject: {msg_subject}")
        
        # Split the body into multiple lines to fit in the PDF
        text_lines = msg_body.split("\n")
        y_position = 730
        for line in text_lines:
            if y_position < 50:  # Avoid writing beyond the page limit
                c.showPage()  # Create new page
                y_position = 750  # Reset y position for new page
                c.setFont("Helvetica", 12)
            c.drawString(50, y_position, line[:100])  # Limit line width
            y_position -= 15
        
        c.save()
        os.remove(msg_path)
        
        # Ensure the new PDF file exists
        if os.path.exists(pdf_path):
            print(f"PDF successfully created: {pdf_path}")
            return pdf_path
        else:
            raise FileNotFoundError(f"Conversion failed: {pdf_path} not found")
    
    except Exception as e:
        print(f"Error converting .msg to .pdf: {e}")
        return None
        
# def convert_pptx_to_pdf(pptx_path):
#     output_path=None
#     try:
#         convert(pptx_path, output_path)
#         print(f"PDF successfully created from {pptx_path}")
#         os.remove(pptx_path)    
#     except Exception as e:
#         print(f"Error converting .pptx to .pdf: {e}")
#         os.remove(pptx_path) 
#         return None   
        
def extract_text_from_xlsx(xlsx_path, component):
    try:
        text = []
        loader = UnstructuredExcelLoader(xlsx_path)
        docs = loader.load()  # List of document objects
        print(f"{docs}")
            
        for doc in docs:
            formatted_text = f"This content belongs to the {component} component.\n\n{doc.page_content}"
            text.append({'text': formatted_text})
        
        os.remove(xlsx_path)
        return text
    except Exception as e:
        print(f"Error extracting text from XLSX: {e}")
        os.remove(xlsx_path)
        return []
    