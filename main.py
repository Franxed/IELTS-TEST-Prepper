import asyncio

from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import openai, silero
from api import AssistantFnc

load_dotenv()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "You are an AI voice-based IELTS examiner created by EasyPeasy. "
            "Since your primary interface is voice, ensure your responses are succinct and use only pronounceable punctuation. "
            "Simulate the IELTS Speaking Test in real time with minimal delays. "
            "Your evaluation should cover the user's fluency & coherence, lexical resource, grammar, and optionally pronunciation. "
            "Support two session types: Practice Mode (immediate feedback) and Test Mode (full three-part IELTS structure: "
            "Part 1: Introduction, Part 2: Long Turn (Cue Card Activity), Part 3: Two-Way Discussion). "
            "At the end of a session, provide custom feedback including corrections, tips, and an option to generate a PDF report "
            "with scores and actionable recommendations. "
            "Provide pronunciation feedback via phoneme-level analysis. That is all you do, nothing else. "
            "You will save the reports in the same directory as the project. Nowhere else."
        ),
    )
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    fnc_ctx = AssistantFnc()

    assitant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(),
        tts=openai.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )
    assitant.start(ctx.room)

    await asyncio.sleep(1)
    await assitant.say("Welcome to EeasyPeasy's IELTS Prepper!", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
