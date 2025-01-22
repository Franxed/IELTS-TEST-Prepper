import asyncio
import json
import os
import traceback

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero

from api import AssistantFnc  # Your custom PDF generation and additional functions

# Load environment variables
load_dotenv()

#Load Livekit's playroom for llm plugin: https://agents-playground.livekit.io/#cam=1&mic=1&video=0&audio=1&chat=1&theme_color=cyan
""""""

async def get_user_message():
    """
    Simulated helper to receive user messages via console input.
    In a production audio scenario, this could be replaced by an audio input manager.
    """
    loop = asyncio.get_running_loop()
    try:
        # For testing purposes, using console input.
        return await loop.run_in_executor(None, input, "Enter user message: ")
    except EOFError:
        # In non-interactive scenarios, return a signal to exit.
        print("DEBUG: EOFError encountered; returning 'exit'")
        return "exit"


def process_llm_output_for_pdf(llm_output: str):
    """
    Parses the provided JSON string into scores and recommendations.
    Expected format (example):
    {
      "scores": {
         "Fluency & Coherence": 7,
         "Lexical Resource": 6,
         "Grammatical Range & Accuracy": 7,
         "Pronunciation": 6
      },
      "recommendations": {
         "Fluency & Coherence": "Speak continuously with fewer pauses.",
         "Lexical Resource": "Expand your vocabulary.",
         "Grammatical Range & Accuracy": "Review complex sentence constructions.",
         "Pronunciation": "Focus on word stress and intonation."
      }
    }
    """
    try:
        data = json.loads(llm_output)
        scores = data.get("scores", {})
        recommendations = data.get("recommendations", {})
        print("DEBUG: LLM output parsed successfully.")
        return scores, recommendations
    except Exception as e:
        print("DEBUG: Error parsing LLM output:", e)
        return {}, {}


async def async_generate_pdf(fnc_ctx, scores, recommendations, output_pdf_path):
    """
    Generates a PDF report in a separate thread to avoid blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    pdf_path = await loop.run_in_executor(
        None,
        fnc_ctx.generate_pdf_report,
        scores["Fluency & Coherence"],
        scores["Lexical Resource"],
        scores["Grammatical Range & Accuracy"],
        "\n".join(
            f"{key}: {rec}" for key, rec in recommendations.items()
        ),
        output_pdf_path,
    )
    return pdf_path


async def entrypoint(ctx: JobContext):
    """
    Main entrypoint for the IELTS speaking test simulation. It sets up the initial context,
    connects to the LiveKit room in audio mode, and starts the voice assistant.
    It handles two modes:
      - Practice Mode (instant feedback per response)
      - Test Mode (full IELTS test simulation with three parts)
    It also supports commands to end test, generate a PDF, view a sample PDF, and exit the session.
    """
    # Create the initial system context for the LLM.
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are an AI voice-based IELTS examiner created by EasyPeasy that explains your services clearly. "
            "Ensure your responses are succinct and use only pronounceable punctuation. "
            "Help users practice speaking English by simulating a real IELTS speaking test. "
            "Your evaluation covers fluency & coherence, lexical resource, grammatical range & accuracy, "
            "and optionally pronunciation (with phoneme-level feedback). "
            "Support two session types: Practice Mode (instant feedback) and Test Mode (full IELTS structure: "
            "Part 1: Introduction, Part 2: Long Turn, Part 3: Two-Way Discussion). "
            "At the end of a session, provide corrections, tips, vocabulary suggestions, and an option to generate a PDF "
            "report summarizing scores and recommendations. "
            "Store PDF reports in the project directory. "
            "To control the session, say 'end test' (simulate evaluation), 'generate pdf', 'sample pdf', or 'exit' or 'quit' to end the session."
        )
    )

    # Connect to the LiveKit room (using audio only).
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Create an instance of your custom function context.
    fnc_ctx = AssistantFnc()

    # Initialize the voice assistant with the plugins.
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )

    # Start the assistant.
    assistant.start(ctx.room)
    await asyncio.sleep(1)  # brief pause before greeting
    await assistant.say("Welcome to EasyPeasy's IELTS Prepper. How can I help you today?", allow_interruptions=True)

    # Main conversation loop.
    latest_llm_output = None
    while True:
        user_message = await get_user_message()
        print(f"DEBUG: User said: {user_message}")

        # Exit or quit command.
        if user_message.strip().lower() in ["exit", "quit"]:
            print("DEBUG: Exit command received. Ending session.")
            await assistant.say("Ending session. Goodbye!", allow_interruptions=True)
            break

        # Simulate finishing a test.
        elif "end test" in user_message.lower():
            print("DEBUG: 'end test' command recognized. Simulating evaluation...")
            # Simulate an LLM evaluation response (in production, this would be an actual call)
            simulated_llm_response = json.dumps({
                "scores": {
                    "Fluency & Coherence": 7,
                    "Lexical Resource": 6,
                    "Grammatical Range & Accuracy": 7,
                    "Pronunciation": 6
                },
                "recommendations": {
                    "Fluency & Coherence": "Try to speak continuously with fewer pauses.",
                    "Lexical Resource": "Expand your vocabulary by learning synonyms and idioms.",
                    "Grammatical Range & Accuracy": "Practice forming complex sentences using varied tenses.",
                    "Pronunciation": "Focus on stressing the correct syllables."
                }
            })
            latest_llm_output = simulated_llm_response
            print("DEBUG: Test evaluation stored.")
            await assistant.say("Test finished. Evaluation has been processed. You may say 'generate pdf' to receive your report.", allow_interruptions=True)

        # Command to generate PDF from the simulated evaluation.
        elif "generate pdf" in user_message.lower():
            print("DEBUG: 'generate pdf' command recognized.")
            if latest_llm_output:
                scores, recommendations = process_llm_output_for_pdf(latest_llm_output)
                if not scores or not recommendations:
                    await assistant.say("Error processing evaluation data. Please try again.", allow_interruptions=True)
                    continue

                # Set output directory and file name.
                output_dir = os.path.join(os.getcwd(), "reports")
                os.makedirs(output_dir, exist_ok=True)
                output_pdf_path = os.path.join(output_dir, "IELTS_Report.pdf")
                try:
                    pdf_path = await async_generate_pdf(fnc_ctx, scores, recommendations, output_pdf_path)
                    print(f"DEBUG: PDF generated successfully: {pdf_path}")
                    await assistant.say("Your IELTS report has been generated and saved.", allow_interruptions=True)
                except Exception as e:
                    print("DEBUG: Error generating PDF:", e)
                    traceback.print_exc()
                    await assistant.say("There was an error generating your report.", allow_interruptions=True)
            else:
                await assistant.say("No evaluation data available. Please finish a test first.", allow_interruptions=True)

        # Command to generate a sample PDF using predefined data.
        elif "sample pdf" in user_message.lower():
            print("DEBUG: 'sample pdf' command recognized.")
            sample_scores = {
                "Fluency & Coherence": 8,
                "Lexical Resource": 7,
                "Grammatical Range & Accuracy": 8,
                "Pronunciation": 7,
            }
            sample_recommendations = {
                "Fluency & Coherence": "Keep up the flow and try to reduce long pauses.",
                "Lexical Resource": "Use a variety of vocabulary to express your ideas.",
                "Grammatical Range & Accuracy": "Pay attention to sentence complexity and correct tense usage.",
                "Pronunciation": "Practice enunciation and intonation for clearer speech.",
            }
            output_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(output_dir, exist_ok=True)
            output_pdf_path = os.path.join(output_dir, "Sample_IELTS_Report.pdf")
            try:
                pdf_path = await async_generate_pdf(fnc_ctx, sample_scores, sample_recommendations, output_pdf_path)
                print(f"DEBUG: Sample PDF generated successfully: {pdf_path}")
                await assistant.say("A sample IELTS report has been generated and saved.", allow_interruptions=True)
            except Exception as e:
                print("DEBUG: Error generating sample PDF:", e)
                traceback.print_exc()
                await assistant.say("There was an error generating the sample report.", allow_interruptions=True)
        else:
            # General conversational response using the assistant.
            response = f"Received your input: {user_message}"
            await assistant.say(response, allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
