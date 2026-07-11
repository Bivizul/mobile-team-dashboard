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

            "fields":
                [
                    "summary",
                    "status",
                    "assignee",
                    "issuetype",
                    "timetracking"
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


    def map_issue(self, raw):

        fields = raw["fields"]


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
                f"{self.base_url}/browse/{raw['key']}"
        )