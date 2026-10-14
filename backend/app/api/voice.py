from fastapi import APIRouter, Form, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

from backend.app.core.config import settings


router = APIRouter(
    prefix="/voice/twilio",
    tags=["Twilio Voice"],
)


def twiml_response(response: VoiceResponse) -> Response:
    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/answer")
async def answer_call():
    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action=f"{settings.BACKEND_BASE_URL.rstrip('/')}/voice/twilio/process",
        method="POST",
        language="en-US",
        speech_timeout="auto",
    )

    gather.say(
        "Hello. I am LeadVoix AI. "
        "I am an artificial intelligence voice assistant. "
        "How can I help you today?"
    )

    response.append(gather)

    response.say(
        "I did not hear anything. Goodbye."
    )
    response.hangup()

    return twiml_response(response)


@router.post("/process")
async def process_speech(
    speech_result: str = Form("", alias="SpeechResult"),
):
    response = VoiceResponse()

    speech_result = speech_result.strip()

    if speech_result:
        safe_speech = speech_result[:1000]
        response.say(
            f"You said: {safe_speech}. "
            "Thank you. This is the LeadVoix AI test."
        )
    else:
        response.say(
            "I could not understand you. Goodbye."
        )

    response.hangup()

    return twiml_response(response)