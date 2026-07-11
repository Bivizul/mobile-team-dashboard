from flask import Flask, render_template, request

from jira_client import JiraClient
from analytics import Analytics
from hrbox_client import HrboxClient
from utils import hours


app = Flask(__name__)


app.jinja_env.filters["hours"] = hours



@app.route("/")
def index():

    jira = JiraClient()
    hrbox = HrboxClient()

    epic_link = request.args.get("epic_link", "").strip()
    fix_version = request.args.get("fix_version", "").strip()

    issues = jira.get_filter_issues(
        epic_link=epic_link,
        fix_version=fix_version,
    )

    analytics = Analytics(
        issues
    )

    return render_template(

        "index.html",

        summary=
            analytics.summary(),

        developers=
            analytics.developers(),

        developers_with_logged_time=
            analytics.developers_with_logged_time(),

        totals_with_logged_time=
            analytics.totals_with_logged_time(),

        totals=
            analytics.totals(),

        issues=
            analytics.task_list(),

        hrbox_absences=
            hrbox.get_team_absences(),

        hrbox_configured=
            hrbox.is_configured(),

        epic_options=
            jira.get_epic_options(),

        fix_version_options=
            jira.get_fix_version_options(),

        selected_epic=
            epic_link,

        selected_fix_version=
            fix_version,
    )



if __name__ == "__main__":

    app.run(
        debug=True
    )