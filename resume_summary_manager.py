import os
import json
import hashlib
import time
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

class ResumeSummaryManager:
    """
    Manages job-specific resume summaries with on-demand generation.
    Only generates summaries when actually needed for answering job questions.
    """
    
    def __init__(self, summaries_dir="resume_summaries"):
        self.summaries_dir = summaries_dir
        self.client = OpenAI()
        
        # Create summaries directory if it doesn't exist
        os.makedirs(self.summaries_dir, exist_ok=True)
    
    def get_job_specific_summary(self, resume_pdf_path, company_name=None, fallback_summary=""):
        """
        Get or generate a job-specific resume summary.
        
        Args:
            resume_pdf_path (str): Path to the job-specific resume PDF
            company_name (str): Company name for file naming (optional)
            fallback_summary (str): Fallback summary if generation fails
            
        Returns:
            str: The resume summary text
        """
        try:
            # Validate resume PDF path
            if not resume_pdf_path or not os.path.exists(resume_pdf_path):
                print(f"[ResumeSummary] Resume PDF not found: {resume_pdf_path}")
                return fallback_summary
            
            # Generate summary filename
            if company_name:
                summary_filename = f"{self._clean_company_name(company_name)}_resume_summary.txt"
            else:
                # Use hash of resume path as fallback
                resume_hash = hashlib.md5(resume_pdf_path.encode()).hexdigest()[:8]
                summary_filename = f"resume_{resume_hash}_summary.txt"
            
            summary_path = os.path.join(self.summaries_dir, summary_filename)
            
            print(f"[ResumeSummary] Looking for existing summary: {summary_filename}")
            
            # Check if summary already exists and is recent
            if self._should_use_existing_summary(summary_path, resume_pdf_path):
                print(f"[ResumeSummary] ✅ Using existing summary: {summary_filename}")
                with open(summary_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            
            # Generate new summary
            print(f"[ResumeSummary] 🔄 Generating NEW summary for: {os.path.basename(resume_pdf_path)}")
            print(f"[ResumeSummary] Company: {company_name}")
            summary = self._generate_summary_from_pdf(resume_pdf_path)
            
            if summary:
                # Save the new summary
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"[ResumeSummary] ✅ Summary saved: {summary_filename}")
                return summary
            else:
                print(f"[ResumeSummary] ❌ Failed to generate summary, using fallback")
                return fallback_summary
                
        except Exception as e:
            print(f"[ResumeSummary] Error getting job-specific summary: {e}")
            return fallback_summary
    
    def _clean_company_name(self, company_name):
        """Clean company name for use in filename."""
        if not company_name:
            return "unknown_company"
        
        # Remove special characters and replace spaces with underscores
        cleaned = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_'))
        cleaned = cleaned.replace(' ', '_').replace('-', '_')
        cleaned = cleaned.strip('_')
        
        # Limit length
        if len(cleaned) > 50:
            cleaned = cleaned[:50]
        
        return cleaned.lower()
    
    def _should_use_existing_summary(self, summary_path, resume_pdf_path):
        """Check if existing summary is recent enough to use."""
        if not os.path.exists(summary_path):
            return False
        
        try:
            # Check if summary file is newer than resume PDF
            summary_time = os.path.getmtime(summary_path)
            resume_time = os.path.getmtime(resume_pdf_path)
            
            # Use existing summary if it's newer than the resume PDF
            return summary_time > resume_time
        except Exception:
            return False
    
    def _generate_summary_from_pdf(self, pdf_path):
        """Generate a structured summary from a resume PDF."""
        try:
            # Extract text from PDF
            reader = PdfReader(pdf_path)
            raw_text = []
            for page in reader.pages:
                text = page.extract_text() or ""
                raw_text.append(text)
            raw_text = "\n".join(raw_text).strip()
            
            if not raw_text:
                print(f"[ResumeSummary] No text extracted from PDF: {pdf_path}")
                return None
            
            print(f"[ResumeSummary] Extracted {len(raw_text)} characters from PDF")
            
            # Generate structured summary using LLM
            system_message = {
                "role": "system",
                "content": "You are a résumé-parsing assistant. Produce a structured summary under these headings: Education, Employment History, Projects, Skills (hard and soft). For Projects, include detailed descriptions, technologies used, methodologies, and outcomes. Return the summary in plain text format with clear section headers."
            }
            
            user_message = {
                "role": "user",
                "content": (
                    "Below is the full text of my résumé (PDF-extracted). "
                    "Please return a concise, multi-section summary under the exact headings:\n"
                    "  • Education\n"
                    "  • Employment History\n"
                    "  • Projects (include detailed descriptions, technologies used, methodologies, and outcomes for each project)\n"
                    "  • Skills (separate hard vs. soft skills)\n\n"
                    "IMPORTANT: For Projects section, extract complete project information including:\n"
                    "- Project name and duration\n"
                    "- Detailed description of what was accomplished\n"
                    "- Technologies, frameworks, and tools used\n"
                    "- Methodologies and approaches\n"
                    "- Outcomes and results achieved\n\n"
                    "Here is my résumé text:\n\n"
                    "```\n"
                    + raw_text[:25000]  # trim if it's extremely long
                    + "\n```"
                )
            }
            
            print("[ResumeSummary] Sending résumé text to GPT-3.5-turbo for summarization...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[system_message, user_message],
                temperature=0.0,
            )
            
            # Log usage
            try:
                usage = response.usage
                pt = usage.prompt_tokens
                ct = usage.completion_tokens
                tt = usage.total_tokens
                ir, orate = (0.03, 0.06) if "gpt-4" in response.model else (0.0015, 0.002)
                ic = pt * ir / 1000
                oc = ct * orate / 1000
                tc = ic + oc
                print(f"[{response.model} usage] prompt={pt}, completion={ct}, total={tt} tokens;"
                      f" cost_input=${ic:.4f}, cost_output=${oc:.4f}, cost_total=${tc:.4f}")
            except Exception:
                print(f"[{response.model} usage] ⚠️ failed to read response.usage")
            
            resume_summary = response.choices[0].message.content.strip()
            print(f"[ResumeSummary] Generated resume summary ({len(resume_summary)} characters)")
            
            # Read and merge extra content from Extra.docx
            extra_content = self._read_extra_docx_content()
            final_summary = self._merge_summary_with_extra_content(resume_summary, extra_content)
            
            return final_summary
            
        except Exception as e:
            print(f"[ResumeSummary] Error generating summary from PDF: {e}")
            return None
    
    def cleanup_old_summaries(self, max_age_days=30):
        """Clean up old summary files."""
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for filename in os.listdir(self.summaries_dir):
                if filename.endswith('_resume_summary.txt'):
                    file_path = os.path.join(self.summaries_dir, filename)
                    file_age = current_time - os.path.getmtime(file_path)
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        print(f"[ResumeSummary] Cleaned up old summary: {filename}")
        except Exception as e:
            print(f"[ResumeSummary] Error cleaning up old summaries: {e}")
    
    def _read_extra_docx_content(self):
        """Read content from Extra.docx file and return as text."""
        try:
            extra_file_path = os.path.join(self.summaries_dir, "Extra.docx")
            if not os.path.exists(extra_file_path):
                print(f"[ResumeSummary] Extra.docx not found at {extra_file_path}")
                return ""
            
            doc = Document(extra_file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text.strip())
            
            extra_content = "\n".join(content)
            print(f"[ResumeSummary] ✅ Loaded Extra.docx content ({len(extra_content)} characters)")
            return extra_content
            
        except Exception as e:
            print(f"[ResumeSummary] Error reading Extra.docx: {e}")
            return ""
    
    def _merge_summary_with_extra_content(self, resume_summary, extra_content):
        """Merge resume summary with extra content from Extra.docx."""
        if not extra_content:
            return resume_summary
        
        # Add a separator and the extra content
        merged_summary = resume_summary + "\n\n" + "="*50 + "\n" + "ADDITIONAL INFORMATION" + "\n" + "="*50 + "\n\n" + extra_content
        
        print(f"[ResumeSummary] ✅ Merged summary with Extra.docx content")
        return merged_summary 