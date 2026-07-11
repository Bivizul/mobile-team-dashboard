import os
import unittest

from config import Config


class ConfigTests(unittest.TestCase):
    def test_config_reload_reads_updated_environment_values(self):
        config = Config()

        os.environ["JIRA_FILTER_ID"] = "999"
        config.reload()
        self.assertEqual(config.JIRA_FILTER_ID, "999")

        os.environ["JIRA_FILTER_ID"] = "111"
        config.reload()
        self.assertEqual(config.JIRA_FILTER_ID, "111")


if __name__ == "__main__":
    unittest.main()
