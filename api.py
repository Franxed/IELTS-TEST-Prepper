from fpdf import FPDF
import os
from livekit.agents import llm
from typing import Annotated, Optional


class AssistantFnc(llm.FunctionContext):
    def __init__(self) -> None:
        super().__init__()
        # Directory to save generated PDFs
        self.output_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(self.output_dir, exist_ok=True)

    @llm.ai_callable(
        description="Generate a PDF report summarizing IELTS scores and feedback based on evaluation rubrics"
    )
    def generate_pdf_report(
        self,
        fluency_coherence: Annotated[float, llm.TypeInfo(description="Score for Fluency & Coherence")],
        lexical_resource: Annotated[float, llm.TypeInfo(description="Score for Lexical Resource")],
        grammatical_range_accuracy: Annotated[float, llm.TypeInfo(description="Score for Grammatical Range & Accuracy")],
        feedback: Annotated[str, llm.TypeInfo(description="Overall feedback and recommendations")],
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generates a PDF report summarizing IELTS scores and feedback.

        Args:
            fluency_coherence (float): Score for Fluency & Coherence.
            lexical_resource (float): Score for Lexical Resource.
            grammatical_range_accuracy (float): Score for Grammatical Range & Accuracy.
            feedback (str): Overall feedback and recommendations.
            output_path (Optional[str]): Optional custom path for the generated PDF.

        Returns:
            str: Path to the generated PDF.
        """
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

        try:
            pdf.output(output_path)
        except Exception as e:
            raise RuntimeError(f"Failed to generate PDF at {output_path}: {e}")

        return output_path


if __name__ == "__main__":
    # Test PDF generation standalone
    sample_scores = {
        "Fluency & Coherence": 7,
        "Lexical Resource": 6,
        "Grammatical Range & Accuracy": 7,
        "Pronunciation": 6,
    }
    sample_recommendations = {
        "Fluency & Coherence": "Practice speaking continuously for fewer pauses.",
        "Lexical Resource": "Expand your vocabulary by learning synonyms and idioms.",
        "Grammatical Range & Accuracy": "Work on constructing complex sentences.",
        "Pronunciation": "Focus on word stress and intonation patterns.",
    }
    assistant_fnc = AssistantFnc()
    pdf_path = assistant_fnc.generate_pdf_report(
        fluency_coherence=sample_scores["Fluency & Coherence"],
        lexical_resource=sample_scores["Lexical Resource"],
        grammatical_range_accuracy=sample_scores["Grammatical Range & Accuracy"],
        feedback="\n".join(f"{k}: {v}" for k, v in sample_recommendations.items())
    )
    print(f"PDF report generated at: {pdf_path}")
