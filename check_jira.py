from jira_client import JiraClient


client = JiraClient()

issues = client.get_filter_issues()


for issue in issues[:5]:

    print(
        issue.key,
        issue.summary,
        issue.assignee
    )