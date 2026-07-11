import re
from datetime import date

import requests
from urllib.parse import quote, urlparse

from config import config


class HrboxClient:
    def __init__(self):
        config.reload()
        self.base_url = config.HRBOX_BASE_URL.rstrip("/") if config.HRBOX_BASE_URL else ""
        self.api_key = config.HRBOX_API_KEY
        self.username = config.HRBOX_USERNAME
        self.password = config.HRBOX_PASSWORD
        self.vacation_url = (
            config.HRBOX_VACATION_URL
            or f"{self.base_url}/core/vacation/team?user_list_key=4605abe2-2672-4741-9fb2-b93bc1d0666c&year={date.today().year}&position="
        ).strip()
        self.session = requests.Session()
        self.last_status = "unknown"
        self.last_error = None

    def is_configured(self):
        return bool(self.base_url and (self.api_key or (self.username and self.password)))

    def _get_csrf_token(self, login_page_text):
        match = re.search(r'name="_csrf"[^>]+value="([^"]+)"', login_page_text)
        if match:
            return match.group(1)
        return None

    def _get_form_fields(self, html_text):
        fields = {}
        for match in re.finditer(r'<input[^>]+name="([^"]+)"[^>]+value="([^"]*)"', html_text, re.I):
            fields[match.group(1)] = match.group(2)
        return fields

    def _prompt_for_mfa_code(self):
        print("HRBox requested MFA/OTP confirmation. Enter the code from your authenticator app or email.")
        print("Press Enter to skip if you do not need to continue with MFA.")
        code = input("HRBox MFA/OTP code (blank to skip): ").strip()
        return code or None

    def _build_login_url(self):
        parsed_base = urlparse(self.base_url)
        tenant = parsed_base.netloc or "blackhubgames.hrbox.io"
        redirect_uri = self.vacation_url or self.base_url
        login_host = f"https://{tenant}" if tenant else "https://auth.hrbox.io"
        return f"{login_host}/auth/login?redirect_uri={quote(redirect_uri, safe='')}&auth_tenant={quote(tenant, safe='')}"

    def _resolve_form_action_url(self, form_action, default_url):
        if not form_action:
            return default_url or self._build_login_url()

        if form_action.startswith(("http://", "https://")):
            return form_action

        if form_action.startswith("//"):
            return f"https:{form_action}"

        if form_action.startswith("/"):
            parsed_default = urlparse(default_url or self.base_url or "https://auth.hrbox.io")
            if parsed_default.netloc:
                return f"{parsed_default.scheme or 'https'}://{parsed_default.netloc}{form_action}"
            return f"https://auth.hrbox.io{form_action}"

        parsed_default = urlparse(default_url or self.base_url or "https://auth.hrbox.io")
        if parsed_default.netloc:
            return f"{parsed_default.scheme or 'https'}://{parsed_default.netloc}/{form_action}"
        return f"https://auth.hrbox.io/{form_action}"

    def _is_mfa_challenge(self, html_text):
        lowered = html_text.lower()
        if any(token in lowered for token in [
            "two-factor",
            "two factor",
            "mfa",
            "otp",
            "one-time",
            "verification code",
            "authentication code",
            "authenticator",
            "email confirmation",
            "code sent",
            "enter the code",
        ]):
            return True

        return bool(re.search(r'(name="(?:code|otp|token|totp|verification_code)"|id="(?:code|otp|token|totp|verification_code)")', html_text, re.I))

    def _looks_like_login_page(self, html_text):
        lowered = html_text.lower()
        return any(token in lowered for token in [
            "loginform[email]",
            "loginform[password]",
            "name=\"email\"",
            "name=\"password\"",
            "forgot your password",
            "sign in",
            "log in",
        ])

    def _submit_form(self, html_text, default_url, payload, referer):
        form_action_match = re.search(r'<form[^>]+action="([^"]+)"', html_text, re.I)
        form_action = form_action_match.group(1) if form_action_match else default_url or "/auth/login"
        post_url = self._resolve_form_action_url(form_action, default_url)

        return self.session.post(
            post_url,
            data=payload,
            headers={"User-Agent": "Mozilla/5.0", "Referer": referer},
            timeout=30,
            allow_redirects=True,
        )

    def _login(self):
        if not self.username or not self.password:
            self.last_error = "HRBox credentials are missing"
            return False

        login_url = self._build_login_url()

        try:
            login_page = self.session.get(login_url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            login_page.raise_for_status()
        except Exception as exc:
            self.last_error = f"Unable to open HRBox login page: {exc}"
            return False

        csrf_token = self._get_csrf_token(login_page.text)
        payload = self._get_form_fields(login_page.text)
        payload.update({
            "LoginForm[email]": self.username,
            "LoginForm[password]": self.password,
        })
        if csrf_token:
            payload["_csrf"] = csrf_token

        try:
            response = self._submit_form(login_page.text, login_url, payload, login_url)
            if response.ok and "/auth/login" not in response.url:
                self.last_error = None
                return True

            if self._is_mfa_challenge(response.text) or self._looks_like_login_page(response.text):
                print("HRBox returned a sign-in or verification page. If MFA/OTP is enabled, enter the code below.")
                mfa_code = self._prompt_for_mfa_code()
                if mfa_code:
                    mfa_payload = self._get_form_fields(response.text)
                    mfa_payload.update({
                        "LoginForm[email]": self.username,
                        "LoginForm[password]": self.password,
                        "code": mfa_code,
                        "otp": mfa_code,
                        "token": mfa_code,
                        "totp": mfa_code,
                        "verification_code": mfa_code,
                    })
                    if self._get_csrf_token(response.text):
                        mfa_payload["_csrf"] = self._get_csrf_token(response.text)
                    response = self._submit_form(response.text, response.url, mfa_payload, response.url)
                    if response.ok and "/auth/login" not in response.url:
                        self.last_error = None
                        return True

            self.last_error = f"HRBox login failed with status {response.status_code}"
            return False
        except Exception as exc:
            self.last_error = f"HRBox login request failed: {exc}"
            return False

    def _extract_vacations_from_html(self, html_text):
        records = []
        for match in re.finditer(r'(?i)(?:vacation|leave|absence|holiday).*?([0-9]{4}-[0-9]{2}-[0-9]{2})', html_text):
            records.append({"raw": match.group(0)[:200]})
        return records

    def get_team_absences(self):
        if not self.is_configured():
            self.last_status = "not_configured"
            return []

        if self.username and self.password:
            login_ok = self._login()
            if not login_ok:
                self.last_status = "login_failed"
                return []

        headers = {
            "Accept": "text/html,application/json,*/*",
            "User-Agent": "Mozilla/5.0",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        vacation_url = self.vacation_url or f"{self.base_url}/core/vacation/team"
        try:
            response = self.session.get(vacation_url, headers=headers, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            self.last_status = "request_failed"
            self.last_error = f"HRBox request failed: {exc}"
            return []

        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                data = response.json()
            except ValueError:
                self.last_status = "invalid_json"
                self.last_error = "HRBox returned invalid JSON"
                return []
            if isinstance(data, list):
                self.last_status = "ok"
                return data
            if isinstance(data, dict):
                for key in ["items", "data", "results", "vacations", "records", "absences"]:
                    value = data.get(key)
                    if isinstance(value, list):
                        self.last_status = "ok"
                        return value
                self.last_status = "empty"
                self.last_error = "HRBox returned an empty or unsupported payload"
                return []

        html_text = response.text
        if "vacation" not in html_text.lower() and "leave" not in html_text.lower():
            self.last_status = "empty"
            self.last_error = "HRBox page did not contain leave data"
            return []

        records = self._extract_vacations_from_html(html_text)
        self.last_status = "ok" if records else "empty"
        if not records:
            self.last_error = "HRBox page loaded but no leave records were extracted"
        return records
