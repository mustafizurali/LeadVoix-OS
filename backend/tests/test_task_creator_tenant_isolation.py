from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from backend.app.services.call_processing_worker import resolve_task_creator_id


class _Query:
    def __init__(self, result):
        self.result = result

    def filter(self, *_conditions):
        return self

    def order_by(self, *_ordering):
        return self

    def first(self):
        return self.result


class TaskCreatorTenantIsolationTests(unittest.TestCase):
    def test_uses_matching_lead_owner_without_querying_users(self):
        db = MagicMock()
        agent_call = SimpleNamespace(organization_id=2)
        lead = SimpleNamespace(owner_id=20)

        creator_id = resolve_task_creator_id(db, agent_call, matched_lead=lead)

        self.assertEqual(creator_id, 20)
        db.query.assert_not_called()

    def test_uses_organization_local_user_when_no_owner_exists(self):
        db = MagicMock()
        db.query.return_value = _Query((20,))
        agent_call = SimpleNamespace(organization_id=2)

        creator_id = resolve_task_creator_id(db, agent_call)

        self.assertEqual(creator_id, 20)
        db.query.assert_called_once()
        db.add.assert_not_called()

    def test_no_organization_user_creates_local_system_user_without_global_fallback(self):
        db = MagicMock()
        db.query.return_value = _Query(None)
        agent_call = SimpleNamespace(organization_id=2)

        def assign_system_user_id():
            db.add.call_args.args[0].id = 200

        db.flush.side_effect = assign_system_user_id

        creator_id = resolve_task_creator_id(db, agent_call)

        self.assertEqual(creator_id, 200)
        db.query.assert_called_once()
        system_user = db.add.call_args.args[0]
        self.assertEqual(system_user.organization_id, 2)
        self.assertEqual(system_user.email, "system_ai_org2@leadvoix.internal")
