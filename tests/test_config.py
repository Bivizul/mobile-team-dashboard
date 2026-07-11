import os
import unittest
from datetime import date
from unittest.mock import Mock, patch

from config import Config
from hrbox_client import HrboxClient
from jira_client import JiraClient
from utils import calculate_feature_deadline


class ConfigTests(unittest.TestCase):
    def test_config_reload_reads_updated_environment_values(self):
        config = Config()

        os.environ["JIRA_FILTER_ID"] = "999"
        config.reload()
        self.assertEqual(config.JIRA_FILTER_ID, "999")

        os.environ["JIRA_FILTER_ID"] = "111"
        config.reload()
        self.assertEqual(config.JIRA_FILTER_ID, "111")


class DeadlineCalculationTests(unittest.TestCase):
    def test_calculate_feature_deadline_uses_working_hours_per_day(self):
        start_date = date(2026, 7, 1)

        deadline = calculate_feature_deadline(start_date, 12, 4)

        self.assertEqual(deadline, date(2026, 7, 3))


class JiraClientTests(unittest.TestCase):
    @patch("jira_client.requests.Session.get")
    def test_get_issue_time_data_reads_logged_time_from_jira_issue(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "fields": {
                "updated": "2026-07-10T12:00:00.000+0000",
                "timetracking": {"timeSpentSeconds": 7200},
            }
        }
        mock_get.return_value = response

        client = JiraClient()
        data = client.get_issue_time_data("BR-547")

        self.assertEqual(data["logged"], 7200)
        self.assertEqual(data["updated"], "2026-07-10T12:00:00.000+0000")

    @patch("jira_client.requests.Session.get")
    def test_get_issue_worklog_by_author_aggregates_time_per_developer(self, mock_get):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "worklogs": [
                {"author": {"displayName": "Alice"}, "timeSpentSeconds": 1800},
                {"author": {"displayName": "Alice"}, "timeSpentSeconds": 3600},
                {"author": {"displayName": "Bob"}, "timeSpentSeconds": 5400},
            ]
        }
        mock_get.return_value = response

        client = JiraClient()
        data = client.get_issue_worklog_by_author("BR-547")

        self.assertEqual(data["Alice"], 5400)
        self.assertEqual(data["Bob"], 5400)


class HrboxClientTests(unittest.TestCase):
    def test_resolves_relative_form_actions_against_the_login_host(self):
        client = HrboxClient()
        login_url = "https://tenant.hrbox.io/auth/login?redirect_uri=https%3A%2F%2Ftenant.hrbox.io%2Fcore%2Fvacation%2Fteam"

        resolved_url = client._resolve_form_action_url("/auth/login", login_url)

        self.assertEqual(resolved_url, "https://tenant.hrbox.io/auth/login")

    def test_builds_login_url_from_the_configured_tenant(self):
        client = HrboxClient()
        client.base_url = "https://tenant.hrbox.io"
        client.vacation_url = "https://tenant.hrbox.io/core/vacation/team"

        login_url = client._build_login_url()

        self.assertIn("https://tenant.hrbox.io/auth/login", login_url)
        self.assertIn("auth_tenant=tenant.hrbox.io", login_url)


if __name__ == "__main__":
    unittest.main()
