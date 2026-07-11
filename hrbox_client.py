import requests

from config import config


class HrboxClient:
    def __init__(self):
        config.reload()
        self.base_url = config.HRBOX_BASE_URL
        self.api_key = config.HRBOX_API_KEY
        self.username = config.HRBOX_USERNAME
        self.password = config.HRBOX_PASSWORD

    def is_configured(self):
        return bool(self.base_url and (self.api_key or (self.username and self.password)))

    def get_team_absences(self):
        if not self.is_configured():
            return []

        headers = {
            "Accept": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.get(
                f"{self.base_url}/api/absences",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
        except Exception:
            return []

        try:
            data = response.json()
        except ValueError:
            return []

        if isinstance(data, dict):
            return data.get("items", [])
        return data
