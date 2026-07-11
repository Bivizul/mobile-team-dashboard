from flask import Flask, render_template

from jira_client import JiraClient
from analytics import Analytics
from utils import hours


app = Flask(__name__)


app.jinja_env.filters["hours"] = hours



@app.route("/")
def index():

    jira = JiraClient()

    issues = jira.get_filter_issues()


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
            analytics.task_list()
    )



if __name__ == "__main__":

    app.run(
        debug=True
    )