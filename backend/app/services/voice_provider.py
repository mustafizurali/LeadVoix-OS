from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class VoiceProvider(ABC):

    @abstractmethod
    def initiate_call(
        self,
        to_number: str,
        from_number: str,
        agent_id: int,
        call_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def end_call(
        self,
        provider_call_id: str,
    ) -> Dict[str, Any]:
        pass
