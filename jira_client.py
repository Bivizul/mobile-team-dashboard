import requests

from config import config
from models.issue import Issue


class JiraClient:

    def __init__(self):

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


    def get_filter_issues(self):

        url = (
            f"{self.base_url}"
            f"/rest/api/2/filter/"
            f"{config.JIRA_FILTER_ID}"
        )


        response = self.session.get(url)

        response.raise_for_status()


        jql = response.json()["jql"]


        print("Using JQL:")
        print(jql)


        return self.search(jql)



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
                )
        )