from fastapi import APIRouter, Form
from fastapi.responses import Response

from twilio.twiml.voice_response import VoiceResponse, Gather


router = APIRouter(
    prefix="/voice/twilio",
    tags=["Twilio Voice"],
)


@router.post("/answer")
async def answer_call():
    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="https://chill-drizzly-slate.ngrok-free.dev/voice/twilio/process",
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

    return Response(
        content=str(response),
        media_type="application/xml",
    )


@router.post("/process")
async def process_speech(
    speech_result: str = Form("", alias="SpeechResult")
):
    response = VoiceResponse()

    if speech_result:
        response.say(
            f"You said: {speech_result}. "
            "Thank you. This is the LeadVoix AI test."
        )
    else:
        response.say(
            "I could not understand you. Goodbye."
        )

    response.hangup()

    return Response(
        content=str(response),
        media_type="application/xml",
    )