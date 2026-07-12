from datetime import datetime, date

from flask import Flask, render_template, request, jsonify

from jira_client import JiraClient
from analytics import Analytics
from hrbox_client import HrboxClient
from utils import hours, parse_date, calculate_feature_deadline
from persistence import load_state, save_state, update_filters, update_vacation, update_vacation_columns, clear_vacations


BR547_ISSUE_KEY = "BR-547"


app = Flask(__name__)


app.jinja_env.filters["hours"] = hours



@app.route("/")
def index():

    jira = JiraClient()
    hrbox = HrboxClient()
    state = load_state()
    filters = state.get("filters", {})
    scoped_all = state.get("scoped_data", {})

    # 1. Determine the scope from request or global fallback
    epic_link = request.args.get("epic_link", filters.get("epic_link", "")).strip()
    fix_version = request.args.get("fix_version", filters.get("fix_version", "")).strip()

    from persistence import get_scope_key
    scope_key = get_scope_key(epic_link, fix_version)
    scoped_data = scoped_all.get(scope_key, {})

    # 2. Get other params, preferring request -> scoped -> global
    req_start_date = request.args.get("feature_start_date")
    req_working_hours = request.args.get("working_hours_per_day")

    feature_start_date = req_start_date if req_start_date is not None else scoped_data.get("feature_start_date", filters.get("feature_start_date", ""))
    working_hours_per_day = req_working_hours if req_working_hours is not None else scoped_data.get("working_hours_per_day", filters.get("working_hours_per_day", "8"))

    feature_start_date = feature_start_date.strip()
    working_hours_per_day = working_hours_per_day.strip()

    # 3. Save if ANY relevant param is in request
    if any(k in request.args for k in ["epic_link", "fix_version", "feature_start_date", "working_hours_per_day"]):
        update_filters(
            epic_link,
            fix_version,
            req_start_date, # Pass actual request value (might be None if not in form)
            req_working_hours
        )

    all_department_issues = jira.get_filter_issues()
    all_department_assignees = sorted({
        issue.assignee for issue in all_department_issues
        if issue.assignee and issue.assignee != "Unassigned"
    })

    issues = jira.get_filter_issues(
        epic_link=epic_link,
        fix_version=fix_version,
    )

    # Filter out "Reject" tasks with zero logged time
    issues = [
        i for i in issues
        if not (i.status.lower() == "reject" and i.logged == 0)
    ]

    analytics = Analytics(
        issues
    )

    assignees = sorted({issue.assignee for issue in issues if issue.assignee and issue.assignee != "Unassigned"})
    hrbox_absences = hrbox.get_team_absences()
    hrbox_status = getattr(hrbox, "last_status", "unknown")
    hrbox_error = getattr(hrbox, "last_error", None)
    current_year = date.today().year

    # Use the resolved feature_start_date (from request, scoped data or global filters)
    parsed_start_date = parse_date(feature_start_date)
    start_date = parsed_start_date or date.today()

    try:
        working_hours = float(working_hours_per_day)
    except ValueError:
        working_hours = 8.0
    working_hours = max(1.0, working_hours)

    br547_issue_data = jira.get_issue_time_data(BR547_ISSUE_KEY)
    br547_worklogs = br547_issue_data.get("worklogs", [])

    br547_logged_since_start = 0
    for wl in br547_worklogs:
        wl_date = parse_date(wl.get("started"))
        if not parsed_start_date or (wl_date and wl_date >= parsed_start_date):
            br547_logged_since_start += wl.get("timeSpentSeconds", 0)

    developers_data = analytics.developers(
        br547_worklogs=br547_worklogs,
        feature_start_date=parsed_start_date,
    )
    developers_with_logged_time_data = analytics.developers_with_logged_time(
        br547_worklogs=br547_worklogs,
        feature_start_date=parsed_start_date,
    )

    developer_estimates = [data["estimate"] for data in developers_data.values()]
    largest_developer_estimate = max(developer_estimates) if developer_estimates else 0
    largest_developer_estimate_hours = largest_developer_estimate / 3600
    deadline_date = calculate_feature_deadline(start_date, largest_developer_estimate_hours, working_hours)

    developer_real_efforts = [data["real_effort"] for data in developers_data.values()]
    largest_developer_real_effort = max(developer_real_efforts) if developer_real_efforts else 0
    largest_developer_real_effort_hours = largest_developer_real_effort / 3600
    real_delivery_date = calculate_feature_deadline(start_date, largest_developer_real_effort_hours, working_hours)

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
            for assignee in all_department_assignees
        ) or not all_department_assignees:
            absence_record = dict(absence)
            absence_record["_days_until"] = days_until(absence)
            filtered_absences.append(absence_record)

    filtered_absences.sort(key=lambda item: item.get("_days_until") if item.get("_days_until") is not None else 99999)

    return render_template(

        "index.html",

        summary=
            analytics.summary(),

        developers=developers_data,

        developers_with_logged_time=
            developers_with_logged_time_data,

        totals_with_logged_time=
            analytics.totals_with_logged_time(developers_data=developers_with_logged_time_data),

        totals=
            analytics.totals(developers_data=developers_data),

        issues=
            analytics.task_list(),

        new_tasks=
            analytics.new_tasks_list(),

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
            parsed_start_date.strftime("%Y-%m-%d") if parsed_start_date else "",

        feature_deadline=
            deadline_date.strftime("%Y-%m-%d") if deadline_date else "",

        real_delivery_date=
            real_delivery_date.strftime("%Y-%m-%d") if real_delivery_date else "",

        feature_deadline_hint=
            f"Target completion based on initial estimates ({largest_developer_estimate_hours:.1f} h) at {working_hours:.1f} h/day capacity.",

        real_delivery_hint=
            f"Forecasted completion based on: actual time spent on 'Done' tasks, current estimate (or spent if higher) for others, and meeting overhead since feature start ({largest_developer_real_effort_hours:.1f} h total effort).",

        working_hours_per_day=
            working_hours,

        br547_logged_since_start=
            sum(d.get("br547_logged", 0) for d in developers_data.values()),

        vacations_state=
            state.get("vacations", {}),

        vacation_columns_count=
            state.get("vacationColumnsCount", 1),

        all_department_assignees=
            all_department_assignees,
    )


@app.route("/api/vacation", methods=["POST"])
def api_update_vacation():
    data = request.json
    update_vacation(data["name"], data["index"], data["start"], data["end"])
    return jsonify({"status": "ok"})


@app.route("/api/vacation/columns", methods=["POST"])
def api_update_columns():
    data = request.json
    update_vacation_columns(data["count"])
    return jsonify({"status": "ok"})


@app.route("/api/vacation/clear", methods=["POST"])
def api_clear_vacations():
    clear_vacations()
    return jsonify({"status": "ok"})



if __name__ == "__main__":

    app.run(
        debug=True
    )