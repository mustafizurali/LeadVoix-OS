from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from backend.app.api import auth
from backend.app.services import user as user_service
from backend.app.utils import dependencies


class AuthIdentityBindingTests(unittest.TestCase):
    def test_canonicalize_email_trims_and_lowercases(self):
        self.assertEqual(user_service.canonicalize_email(" User@Example.COM "), "user@example.com")

    def test_create_user_uses_canonical_email_and_rejects_case_variant_duplicate(self):
        user_input = SimpleNamespace(name="User", email=" User@Example.COM ", password="password")
        db = MagicMock()

        def assign_user_id():
            db.add.call_args_list[0].args[0].id = 1

        db.flush.side_effect = assign_user_id
        with patch.object(user_service, "get_users_by_canonical_email", side_effect=[[], [SimpleNamespace()]]) as lookup, patch.object(
            user_service, "hash_password", return_value="hash"
        ):
            created = user_service.create_user(db, user_input)
            self.assertEqual(created.email, "user@example.com")
            with self.assertRaises(HTTPException) as exc_info:
                user_service.create_user(db, user_input)

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(lookup.call_args_list[0].args[1], "user@example.com")
        self.assertEqual(lookup.call_args_list[1].args[1], "user@example.com")

    def test_authenticate_user_accepts_case_and_whitespace_variant_for_single_legacy_account(self):
        account = SimpleNamespace(hashed_password="hash")

        with patch.object(user_service, "get_users_by_canonical_email", return_value=[account]) as lookup, patch.object(
            user_service, "verify_password", return_value=True
        ):
            self.assertIs(user_service.authenticate_user(MagicMock(), " User@Example.COM ", "password"), account)

        self.assertEqual(lookup.call_args.args[1], " User@Example.COM ")

    def test_authenticate_user_rejects_ambiguous_case_variant_accounts(self):
        with patch.object(user_service, "get_users_by_canonical_email", return_value=[SimpleNamespace(), SimpleNamespace()]):
            self.assertIsNone(user_service.authenticate_user(MagicMock(), "user@example.com", "password"))

    def test_login_uses_canonical_email_and_immutable_user_id_subject(self):
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        credentials = SimpleNamespace(email=" User@Example.COM ", password="password")
        account = SimpleNamespace(id=42, role="owner")

        with patch.object(auth, "authenticate_user", return_value=account) as authenticate, patch.object(
            auth, "create_access_token", return_value="token"
        ) as create_token:
            response = auth.login(request, credentials, MagicMock())

        self.assertEqual(response, {"access_token": "token", "token_type": "bearer"})
        self.assertEqual(authenticate.call_args.args[1], "user@example.com")
        self.assertEqual(create_token.call_args.args[0]["sub"], "42")
        self.assertNotIn("user_id", create_token.call_args.args[0])

    def test_get_current_user_resolves_id_subject_to_its_database_organization(self):
        account = SimpleNamespace(id=42, organization_id=7)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = account
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

        with patch.object(dependencies.jwt, "decode", return_value={"sub": "42"}):
            resolved = dependencies.get_current_user(credentials, db)

        self.assertIs(resolved, account)
        self.assertEqual(resolved.organization_id, 7)
        db.query.assert_called_once_with(dependencies.User)

    def test_get_current_user_rejects_noncanonical_or_email_subjects(self):
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        for subject in ("", " 42", "42 ", "042", "0", "-1", "user@example.com", "9" * 5000, 42):
            with self.subTest(subject=subject), patch.object(dependencies.jwt, "decode", return_value={"sub": subject}):
                with self.assertRaises(HTTPException) as exc_info:
                    dependencies.get_current_user(credentials, MagicMock())
                self.assertEqual(exc_info.exception.status_code, 401)
