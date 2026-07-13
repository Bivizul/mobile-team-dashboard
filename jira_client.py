import requests

from config import config
from models.issue import Issue


class JiraClient:

    def __init__(self):

        config.reload()

        self.session = requests.Session()

        self.session.headers.update(
            {
                "Authorization":
                    f"Bearer {config.JIRA_TOKEN}",

                "Accept":
                    "application/json"
            }
        )

        self.base_url = config.JIRA_URL
        self.done_statuses = [s.lower() for s in ["Tech Review", "Ready To Test", "In Test", "Done", "Reject", "Closed", "Resolved"]]


    def get_filter_jql(self):

        url = (
            f"{self.base_url}"
            f"/rest/api/2/filter/"
            f"{config.JIRA_FILTER_ID}"
        )

        response = self.session.get(url)
        response.raise_for_status()

        return response.json()["jql"]


    def get_filter_issues(self, epic_link=None, fix_version=None):

        jql = self.get_filter_jql()

        jql = self.apply_filters(
            jql,
            epic_link=epic_link,
            fix_version=fix_version,
        )

        print("Using JQL:")
        print(jql)

        return self.search(jql)


    def apply_filters(self, jql, epic_link=None, fix_version=None):

        conditions = []

        if epic_link:
            conditions.append(f'"Epic Link" = "{epic_link}"')

        if fix_version:
            conditions.append(f'fixVersion = "{fix_version}"')

        if not conditions:
            return jql

        return f"({jql}) AND {' AND '.join(conditions)}"


    def search(self, jql):

        url = (
            f"{self.base_url}"
            "/rest/api/2/search"
        )


        params = {

            "jql": jql,

            "maxResults": 100,

            "expand": "changelog",

            "fields":
                [
                    "summary",
                    "status",
                    "assignee",
                    "issuetype",
                    "timetracking",
                    "updated",
                    "created",
                    "resolutiondate"
                ]
        }


        response = self.session.get(
            url,
            params=params
        )


        response.raise_for_status()


        data = response.json()


        print(
            "Loaded issues:",
            len(data["issues"])
        )


        return [
            self.map_issue(issue)
            for issue in data["issues"]
        ]


    def get_issue_time_data(self, issue_key):
        response = self.session.get(
            f"{self.base_url}/rest/api/2/issue/{issue_key}",
            params={
                "fields": ["updated", "timetracking", "worklog"],
            },
        )
        response.raise_for_status()

        data = response.json()
        fields = data.get("fields", {})
        tracking = fields.get("timetracking") or {}
        worklog_data = fields.get("worklog", {}) or {}

        worklogs = worklog_data.get("worklogs", [])
        total_worklogs = worklog_data.get("total", 0)

        # If there are more worklogs than returned in the initial response, fetch them all
        if total_worklogs > len(worklogs):
            url = f"{self.base_url}/rest/api/2/issue/{issue_key}/worklog"
            while len(worklogs) < total_worklogs:
                response = self.session.get(
                    url,
                    params={
                        "startAt": len(worklogs),
                        "maxResults": 100,
                    },
                )
                response.raise_for_status()
                page_data = response.json()
                new_worklogs = page_data.get("worklogs", [])
                if not new_worklogs:
                    break
                worklogs.extend(new_worklogs)

        return {
            "updated": fields.get("updated", ""),
            "logged": tracking.get("timeSpentSeconds", 0),
            "worklogs": worklogs,
        }

    def get_epic_options(self):

        response = self.session.get(
            f"{self.base_url}/rest/api/2/search",
            params={
                "jql": "issuetype = Epic",
                "maxResults": 100,
                "fields": ["summary", "key"],
            },
        )
        response.raise_for_status()

        data = response.json()

        options = [
            {
                "value": issue["key"],
                "label": f"{issue['fields']['summary']} ({issue['key']})",
            }
            for issue in data.get("issues", [])
        ]

        return sorted(options, key=lambda item: item["label"].lower())


    def get_fix_version_options(self):

        jql = self.get_filter_jql()

        response = self.session.get(
            f"{self.base_url}/rest/api/2/search",
            params={
                "jql": jql,
                "maxResults": 100,
                "fields": ["fixVersions"],
            },
        )
        response.raise_for_status()

        data = response.json()

        versions = []
        for issue in data.get("issues", []):
            for version in issue.get("fields", {}).get("fixVersions", []):
                name = version.get("name")
                if name and name not in versions:
                    versions.append(name)

        return sorted(
            [{"value": version, "label": version} for version in versions],
            key=lambda item: item["label"].lower(),
        )

    def _find_done_date(self, changelog):
        histories = changelog.get("histories", [])
        for history in sorted(histories, key=lambda x: x.get("created")):
            for item in history.get("items", []):
                if item.get("field") == "status":
                    from_status = item.get("fromString", "").lower()
                    to_status = item.get("toString", "").lower()
                    if from_status == "in progress" and to_status in self.done_statuses:
                        return history.get("created")
        return None

    def map_issue(self, raw):

        fields = raw["fields"]
        changelog = raw.get("changelog", {})


        tracking = (
            fields.get(
                "timetracking"
            )
            or {}
        )


        assignee = (
            fields.get(
                "assignee"
            )
        )

        done_date = self._find_done_date(changelog)


        return Issue(

            key=raw["key"],

            summary=fields["summary"],

            status=fields["status"]["name"],

            assignee=
                assignee["displayName"]
                if assignee
                else "Unassigned",


            issue_type=
                fields["issuetype"]["name"],


            estimate=
                tracking.get(
                    "originalEstimateSeconds",
                    0
                ),

            logged=
                tracking.get(
                    "timeSpentSeconds",
                    0
                ),

            remaining=
                tracking.get(
                    "remainingEstimateSeconds",
                    0
                ),

            jira_url=
                f"{self.base_url}/browse/{raw['key']}",

            updated=fields.get("updated", ""),
            created=fields.get("created", ""),
            resolution_date=fields.get("resolutiondate", ""),
            done_date=done_date
        )