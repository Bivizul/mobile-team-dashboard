from datetime import datetime, date

from flask import Flask, render_template, request

from jira_client import JiraClient
from analytics import Analytics
from hrbox_client import HrboxClient
from utils import hours, parse_date, calculate_feature_deadline


BR547_ISSUE_KEY = "BR-547"


app = Flask(__name__)


app.jinja_env.filters["hours"] = hours



@app.route("/")
def index():

    jira = JiraClient()
    hrbox = HrboxClient()

    epic_link = request.args.get("epic_link", "").strip()
    fix_version = request.args.get("fix_version", "").strip()
    feature_start_date = request.args.get("feature_start_date", "").strip()
    working_hours_per_day = request.args.get("working_hours_per_day", "8").strip()

    issues = jira.get_filter_issues(
        epic_link=epic_link,
        fix_version=fix_version,
    )

    analytics = Analytics(
        issues
    )

    assignees = sorted({issue.assignee for issue in issues if issue.assignee and issue.assignee != "Unassigned"})
    hrbox_absences = hrbox.get_team_absences()
    hrbox_status = getattr(hrbox, "last_status", "unknown")
    hrbox_error = getattr(hrbox, "last_error", None)
    current_year = date.today().year

    start_date = parse_date(feature_start_date) or date.today()
    try:
        working_hours = float(working_hours_per_day)
    except ValueError:
        working_hours = 8.0
    working_hours = max(1.0, working_hours)

    developer_estimates = [data["estimate"] for data in analytics.developers().values()]
    largest_developer_estimate = max(developer_estimates) if developer_estimates else 0
    largest_developer_estimate_hours = largest_developer_estimate / 3600
    deadline_date = calculate_feature_deadline(start_date, largest_developer_estimate_hours, working_hours)

    br547_issue_data = jira.get_issue_time_data(BR547_ISSUE_KEY)
    br547_logged_since_start = 0
    updated_date = parse_date(br547_issue_data.get("updated", ""))
    if not start_date or not updated_date or updated_date >= start_date:
        br547_logged_since_start = br547_issue_data.get("logged", 0)

    br547_worklog_by_author = jira.get_issue_worklog_by_author(BR547_ISSUE_KEY)

    def is_current_year_absence(absence):
        start_date = parse_date(absence.get("startDate") or absence.get("from") or absence.get("start") or absence.get("dateFrom"))
        end_date = parse_date(absence.get("endDate") or absence.get("to") or absence.get("end") or absence.get("dateTo"))
        if start_date and start_date.year == current_year:
            return True
        if end_date and end_date.year == current_year:
            return True
        return False

    def days_until(absence):
        start_date = parse_date(absence.get("startDate") or absence.get("from") or absence.get("start") or absence.get("dateFrom"))
        if not start_date:
            return None
        return (start_date - date.today()).days

    filtered_absences = []
    for absence in hrbox_absences:
        if not is_current_year_absence(absence):
            continue
        if any(
            assignee.lower() in str(absence.get("personName", "")).lower()
            or assignee.lower() in str(absence.get("employeeName", "")).lower()
            or assignee.lower() in str(absence.get("name", "")).lower()
            for assignee in assignees
        ) or not assignees:
            absence_record = dict(absence)
            absence_record["_days_until"] = days_until(absence)
            filtered_absences.append(absence_record)

    filtered_absences.sort(key=lambda item: item.get("_days_until") if item.get("_days_until") is not None else 99999)

    return render_template(

        "index.html",

        summary=
            analytics.summary(),

        developers=
            analytics.developers(),

        br547_worklog_by_author=
            br547_worklog_by_author,

        developers_with_logged_time=
            analytics.developers_with_logged_time(),

        totals_with_logged_time=
            analytics.totals_with_logged_time(),

        totals=
            analytics.totals(),

        issues=
            analytics.task_list(),

        hrbox_absences=
            filtered_absences,

        hrbox_configured=
            hrbox.is_configured(),

        hrbox_status=
            hrbox_status,

        hrbox_error=
            hrbox_error,

        epic_options=
            jira.get_epic_options(),

        fix_version_options=
            jira.get_fix_version_options(),

        selected_epic=
            epic_link,

        selected_fix_version=
            fix_version,

        feature_start_date=
            start_date.strftime("%Y-%m-%d") if start_date else "",

        feature_deadline=
            deadline_date.strftime("%Y-%m-%d") if deadline_date else "",

        feature_deadline_hint=
            f"Based on the largest developer estimate ({largest_developer_estimate_hours:.1f} h) and {working_hours:.1f} working hours/day",

        working_hours_per_day=
            working_hours,

        br547_logged_since_start=
            br547_logged_since_start,
    )



if __name__ == "__main__":

    app.run(
        debug=True
    )