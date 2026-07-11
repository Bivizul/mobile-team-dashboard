import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    JIRA_URL = os.getenv("JIRA_URL")
    # JIRA_EMAIL = os.getenv("JIRA_EMAIL")
    JIRA_TOKEN = os.getenv("JIRA_TOKEN")
    JIRA_FILTER_ID = os.getenv("JIRA_FILTER_ID")


config = Config()