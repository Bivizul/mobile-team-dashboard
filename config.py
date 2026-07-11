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


config = Config()