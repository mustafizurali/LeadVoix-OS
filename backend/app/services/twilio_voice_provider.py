from typing import Dict, Any

import httpx
from twilio.rest import Client

from backend.app.core.config import settings
from backend.app.services.voice_provider import VoiceProvider


class TwilioVoiceProvider(VoiceProvider):

    def __init__(self):
        self.client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
        )

    def initiate_call(
        self,
        to_number: str,
        from_number: str,
        agent_id: int,
    ) -> Dict[str, Any]:

        url = (
            f"https://api.twilio.com/2010-04-01/"
            f"Accounts/{settings.TWILIO_ACCOUNT_SID}/Calls.json"
        )

        data = {
            "To": to_number,
            "Url": (
                "https://webhooks.twilio.com/v1/Voice/Template/"
                "voice_text_to_speech"
            ),
        }

        response = httpx.post(
            url,
            data=data,
            auth=(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
            ),
            timeout=30.0,
        )

        response.raise_for_status()

        result = response.json()

        return {
            "provider_call_id": result["sid"],
            "status": result["status"],
            "to_number": to_number,
            "from_number": from_number,
            "agent_id": agent_id,
        }

    def end_call(
        self,
        provider_call_id: str,
    ) -> Dict[str, Any]:

        call = self.client.calls(
            provider_call_id
        ).update(
            status="completed"
        )

        return {
            "provider_call_id": call.sid,
            "status": call.status,
        }