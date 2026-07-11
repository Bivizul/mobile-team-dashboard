import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    def __init__(self):
        self.reload()

    def reload(self):
        load_dotenv(
            dotenv_path=Path(__file__).resolve().parent / ".env",
            override=False,
        )

        self.JIRA_URL = os.getenv("JIRA_URL")
        self.JIRA_TOKEN = os.getenv("JIRA_TOKEN")
        self.JIRA_FILTER_ID = os.getenv("JIRA_FILTER_ID")

        self.HRBOX_BASE_URL = os.getenv("HRBOX_BASE_URL")
        self.HRBOX_API_KEY = os.getenv("HRBOX_API_KEY")
        self.HRBOX_USERNAME = os.getenv("HRBOX_USERNAME")
        self.HRBOX_PASSWORD = os.getenv("HRBOX_PASSWORD")
        self.HRBOX_VACATION_URL = os.getenv("HRBOX_VACATION_URL")


config = Config()