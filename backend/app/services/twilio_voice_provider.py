from typing import Any, Dict, Optional

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
        call_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            caller_id = from_number or settings.TWILIO_PHONE_NUMBER
            base_url = (settings.BACKEND_BASE_URL or "").rstrip("/")

            query_parts = [f"agent_id={agent_id}"]
            if call_id is not None:
                query_parts.append(f"call_id={call_id}")
            query_str = f"?{'&'.join(query_parts)}"

            status_callback_url = (
                f"{base_url}/voice/twilio/status-callback{query_str}"
            )

            if "localhost" in base_url or "127.0.0.1" in base_url or not base_url:
                call = self.client.calls.create(
                    to=to_number,
                    from_=caller_id,
                    url="http://demo.twilio.com/docs/voice.xml",
                    method="GET",
                )
            else:
                call = self.client.calls.create(
                    to=to_number,
                    from_=caller_id,
                    url=f"{base_url}/voice/twilio/answer{query_str}",
                    method="POST",
                    status_callback=status_callback_url,
                    status_callback_event=[
                        "initiated",
                        "ringing",
                        "answered",
                        "completed",
                    ],
                    status_callback_method="POST",
                )

            return {
                "provider_call_id": call.sid,
                "status": call.status,
                "to_number": to_number,
                "from_number": caller_id,
                "agent_id": agent_id,
                "call_id": call_id,
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

        except Exception as exc:
            import traceback
            traceback.print_exc()
            error_msg = getattr(exc, 'msg', str(exc))
            print("\n>>> ASOL TWILIO ERROR:", error_msg, "\n")

            from fastapi import HTTPException
            raise HTTPException(
                status_code=502,
                detail=f"Twilio Error: {error_msg}"
            )
