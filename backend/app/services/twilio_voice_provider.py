
from typing import Any, Dict

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

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
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=(
                    f"{settings.BACKEND_BASE_URL.rstrip('/')}"
                    "/voice/twilio/answer"
                ),
                method="POST",
            )

            return {
                "provider_call_id": call.sid,
                "status": call.status,
                "to_number": to_number,
                "from_number": from_number,
                "agent_id": agent_id,
            }

        except TwilioRestException as exc:
            raise RuntimeError(
                f"Twilio call creation failed: {exc.msg}"
            ) from exc

    def end_call(
        self,
        provider_call_id: str,
    ) -> Dict[str, Any]:
        try:
            call = self.client.calls(
                provider_call_id
            ).update(
                status="completed"
            )

            return {
                "provider_call_id": call.sid,
                "status": call.status,
            }

        except TwilioRestException as exc:
            raise RuntimeError(
                f"Twilio call termination failed: {exc.msg}"
            ) from exc