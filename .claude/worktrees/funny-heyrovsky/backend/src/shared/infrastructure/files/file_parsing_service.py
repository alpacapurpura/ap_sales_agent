import io
from fastapi import UploadFile
import pypdf
import docx
import structlog

logger = structlog.get_logger()

class FileParsingService:
    """
    Service for parsing text from uploaded files (PDF, DOCX, TXT/MD).
    """
    
    @staticmethod
    async def parse_file(file: UploadFile) -> str:
        """
        Parses an uploaded file and returns its text content.
        """
        content = await file.read()
        filename = file.filename.lower()
        
        try:
            if filename.endswith(".pdf"):
                return FileParsingService.parse_pdf(content)
            elif filename.endswith(".docx"):
                return FileParsingService.parse_docx(content)
            elif filename.endswith(".txt") or filename.endswith(".md"):
                # Try UTF-8, fallback to latin-1 if needed
                try:
                    return content.decode("utf-8")
                except UnicodeDecodeError:
                    return content.decode("latin-1")
            else:
                logger.warning("Unsupported file type", filename=filename)
                return ""
        except Exception as e:
            logger.error("Error parsing file", filename=filename, error=str(e))
            # Return empty string on error to allow process to continue with other inputs
            return ""
        finally:
            # Reset file cursor if needed elsewhere, though usually read once
            await file.seek(0)

    @staticmethod
    def parse_pdf(content: bytes) -> str:
        text = ""
        try:
            pdf_file = io.BytesIO(content)
            reader = pypdf.PdfReader(pdf_file)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            logger.error("PDF parsing error", error=str(e))
            raise e
        return text

    @staticmethod
    def parse_docx(content: bytes) -> str:
        text = ""
        try:
            docx_file = io.BytesIO(content)
            doc = docx.Document(docx_file)
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text += paragraph.text + "\n"
        except Exception as e:
            logger.error("DOCX parsing error", error=str(e))
            raise e
        return text
