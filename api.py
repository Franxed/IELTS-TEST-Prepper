from fpdf import FPDF
import os
from livekit.agents import llm
from typing import Annotated, Optional

class AssistantFnc(llm.FunctionContext):
    def __init__(self) -> None:
        super().__init__()

        # Directory to save generated PDFs
        self.output_dir = r"C:\Users\Franx\Desktop\EasyPeasy_AI\reports"
        os.makedirs(self.output_dir, exist_ok=True)

    @llm.ai_callable(description="Generate a PDF report summarizing IELTS scores and feedback based on evaluation rubrics")
    def generate_pdf_report(
        self,
        fluency_coherence: Annotated[float, llm.TypeInfo(description="Score for Fluency & Coherence")],
        lexical_resource: Annotated[float, llm.TypeInfo(description="Score for Lexical Resource")],
        grammatical_range_accuracy: Annotated[float, llm.TypeInfo(description="Score for Grammatical Range & Accuracy")],
        feedback: Annotated[str, llm.TypeInfo(description="Overall feedback and recommendations")],
        output_path: Optional[str] = None,  # Use Optional[str] for optional parameters
    ) -> str:
        """
        Generates a PDF report summarizing IELTS scores and feedback.

        Args:
            fluency_coherence (float): Score for Fluency & Coherence.
            lexical_resource (float): Score for Lexical Resource.
            grammatical_range_accuracy (float): Score for Grammatical Range & Accuracy.
            feedback (str): Overall feedback and recommendations.
            output_path (str): Optional custom path for the generated PDF.

        Returns:
            str: Path to the generated PDF.
        """
        # Default output path
        if output_path is None:
            output_path = os.path.join(self.output_dir, "IELTS_Report.pdf")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Title
        pdf.cell(200, 10, txt="IELTS Scoring Report", ln=True, align="C")
        pdf.ln(10)

        # Scores Section
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 10, txt="Scores:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Fluency & Coherence: {fluency_coherence}", ln=True)
        pdf.cell(200, 10, txt=f"Lexical Resource: {lexical_resource}", ln=True)
        pdf.cell(200, 10, txt=f"Grammatical Range & Accuracy: {grammatical_range_accuracy}", ln=True)

        pdf.ln(10)

        # Feedback Section
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(200, 10, txt="Feedback:", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 10, txt=feedback)

        # Save PDF
        pdf.output(output_path)
        return output_path
