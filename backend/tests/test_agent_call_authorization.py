from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from backend.app.api import agent_call
from backend.app.schemas.agent_call import AgentCallUpdate


class _Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *_conditions):
        return self

    def first(self):
        return self.result


class AgentCallAuthorizationTests(unittest.TestCase):
    def test_get_authorized_call_returns_same_organization_call_without_name_error(self):
        call = SimpleNamespace(id=10, agent_id=4, organization_id=2)
        db = MagicMock()
        db.query.return_value = _Query(call)

        self.assertIs(agent_call.get_authorized_call(db, 4, 10, 2), call)
        db.query.assert_called_once_with(agent_call.AgentCall)

    def test_get_authorized_call_hides_cross_organization_call(self):
        db = MagicMock()
        db.query.return_value = _Query(None)

        with self.assertRaises(HTTPException) as exc_info:
            agent_call.get_authorized_call(db, 4, 10, 99)

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Agent call not found")

    def test_authorization_routes_use_authorized_call(self):
        current_user = SimpleNamespace(organization_id=2)
        agent = SimpleNamespace(id=4, organization_id=2)

        for route in ("get_call", "initiate_call", "end_call", "update_call", "delete_call"):
            with self.subTest(route=route):
                db = MagicMock()
                call = SimpleNamespace(
                    id=10,
                    agent_id=4,
                    organization_id=2,
                    caller_phone="+14155552671",
                    provider_call_id=None if route == "initiate_call" else "CA123",
                )
                with (
                    patch.object(agent_call, "get_authorized_agent", return_value=agent) as authorized_agent,
                    patch.object(agent_call, "get_authorized_call", return_value=call) as authorized_call,
                    patch.object(agent_call, "initiate_voice_call", return_value=call),
                    patch.object(agent_call, "end_voice_call", return_value=call),
                    patch.object(agent_call, "update_agent_call", return_value=call),
                    patch.object(agent_call, "delete_agent_call"),
                ):
                    if route == "get_call":
                        result = agent_call.get_call(4, 10, db, current_user)
                    elif route == "initiate_call":
                        result = agent_call.initiate_call(4, 10, "+14155552671", db, current_user)
                    elif route == "end_call":
                        result = agent_call.end_call(4, 10, db, current_user)
                    elif route == "update_call":
                        result = agent_call.update_call(4, 10, AgentCallUpdate(), db, current_user)
                    else:
                        result = agent_call.delete_call(4, 10, db, current_user)

                self.assertTrue(result is call or result is None)
                authorized_call.assert_called_once_with(db, 4, 10, 2)
                if route in {"initiate_call", "end_call"}:
                    authorized_agent.assert_called_once()
