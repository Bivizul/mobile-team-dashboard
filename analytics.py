from collections import defaultdict


class Analytics:


    def __init__(self, issues):
        self.issues = issues
        self.done_statuses = ["Tech Review", "Ready To Test", "In Test", "Done", "Reject"]
        from utils import parse_date


    def summary(self):

        estimate = sum(
            i.estimate
            for i in self.issues
        )

        logged = sum(
            i.logged
            for i in self.issues
        )

        done_statuses = ["Tech Review", "Ready To Test", "In Test", "Done", "Reject"]
        in_progress_statuses = ["In Progress"]

        tasks_done = 0
        tasks_in_progress = 0

        for issue in self.issues:
            if issue.status in done_statuses:
                tasks_done += 1
            elif issue.status in in_progress_statuses:
                tasks_in_progress += 1
        
        tasks_total = len(self.issues)
        tasks_remaining_to_start = tasks_total - tasks_done - tasks_in_progress

        return {

            "tasks":
                tasks_total,

            "tasks_done":
                tasks_done,
            
            "tasks_in_progress":
                tasks_in_progress,

            "tasks_remaining_to_start":
                tasks_remaining_to_start,

            "estimate":
                estimate,

            "logged":
                logged,

            "remaining":
                sum(
                    (min(0, i.estimate - i.logged) if i.status in self.done_statuses else (i.estimate - i.logged))
                    for i in self.issues
                ),

            "progress":
                round(
                    tasks_done / tasks_total * 100,
                    1
                )
                if tasks_total
                else 0
        }



    def developers(self, br547_worklogs=None, feature_start_date=None):

        result = defaultdict(
            lambda:{
                "tasks":0,
                "estimate":0,
                "logged":0,
                "br547_logged": 0,
                "remaining":0,
                "efficiency": 0,
                "real_effort": 0 # Projected total time: logged + remaining for tasks + br547
            }
        )


        for issue in self.issues:
            developer = result[issue.assignee]
            developer["tasks"] += 1
            developer["estimate"] += issue.estimate
            developer["logged"] += issue.logged

            # Logic: Show negative if exceeded. For Done tasks, don't show positive remaining.
            diff = issue.estimate - issue.logged
            if issue.status in self.done_statuses:
                eff_remaining = min(0, diff)
            else:
                eff_remaining = diff

            developer["remaining"] += eff_remaining

            # Real effort: spent time for done, max(estimate, logged) for others
            if issue.status in self.done_statuses:
                projected = issue.logged
            else:
                projected = max(issue.estimate, issue.logged)

            developer["real_effort"] += projected

        if br547_worklogs:
            from utils import parse_date
            for worklog in br547_worklogs:
                author = worklog.get("author", {})
                author_name = author.get("displayName") or author.get("name")
                if author_name:
                    author_name = author_name.strip()
                    worklog_started = parse_date(worklog.get("started"))
                    if not feature_start_date or (worklog_started and worklog_started >= feature_start_date):
                        # Only add time to developers who are already in the results
                        # (i.e., they belong to the current mobile team scope/filter)
                        for existing_name in result.keys():
                            if existing_name.lower() == author_name.lower():
                                time_spent = worklog.get("timeSpentSeconds", 0)
                                result[existing_name]["br547_logged"] += time_spent
                                result[existing_name]["real_effort"] += time_spent
                                break


        for developer in result.values():
            if developer["logged"] > 0:
                developer["efficiency"] = round(
                    developer["estimate"] / developer["logged"] * 100,
                    1
                )

        return dict(sorted(result.items()))



    def developers_with_logged_time(self, br547_worklogs=None, feature_start_date=None):

        result = defaultdict(
            lambda:{
                "tasks":0,
                "estimate":0,
                "logged":0,
                "br547_logged": 0,
                "remaining":0,
                "efficiency": 0,
                "real_effort": 0
            }
        )

        issues_with_logged_time = [
            issue for issue in self.issues if issue.logged > 0
        ]

        for issue in issues_with_logged_time:
            developer = result[issue.assignee]
            developer["tasks"] += 1
            developer["estimate"] += issue.estimate
            developer["logged"] += issue.logged

            diff = issue.estimate - issue.logged
            if issue.status in self.done_statuses:
                eff_remaining = min(0, diff)
            else:
                eff_remaining = diff

            developer["remaining"] += eff_remaining

            if issue.status in self.done_statuses:
                projected = issue.logged
            else:
                projected = max(issue.estimate, issue.logged)

            developer["real_effort"] += projected

        if br547_worklogs:
            from utils import parse_date
            for worklog in br547_worklogs:
                author = worklog.get("author", {})
                author_name = author.get("displayName") or author.get("name")
                if author_name:
                    author_name = author_name.strip()
                    worklog_started = parse_date(worklog.get("started"))
                    if not feature_start_date or (worklog_started and worklog_started >= feature_start_date):
                        # For this table, we ONLY count time for developers who already have logged time
                        # on tasks from the filter.
                        for existing_name in list(result.keys()):
                            if existing_name.lower() == author_name.lower():
                                time_spent = worklog.get("timeSpentSeconds", 0)
                                result[existing_name]["br547_logged"] += time_spent
                                result[existing_name]["real_effort"] += time_spent
                                break

                        # We don't add new developers to this specific table if they only have BR-547 time
                        # but no logged time on tasks from the filter.

        for developer in result.values():
            if developer["logged"] > 0:
                developer["efficiency"] = round(
                    developer["estimate"] / developer["logged"] * 100,
                    1
                )

        return dict(sorted(result.items()))


    def totals_with_logged_time(self, developers_data=None):
        issues_with_logged_time = [
            issue for issue in self.issues if issue.logged > 0
        ]

        estimate = sum(
            i.estimate
            for i in issues_with_logged_time
        )

        logged = sum(
            i.logged
            for i in issues_with_logged_time
        )

        br547_logged = 0
        if developers_data:
            br547_logged = sum(d.get("br547_logged", 0) for d in developers_data.values())

        return {

            "tasks":
                len(issues_with_logged_time),

            "estimate":
                estimate,

            "logged":
                logged,

            "br547_logged":
                br547_logged,

            "remaining":
                sum(
                    (min(0, i.estimate - i.logged) if i.status in self.done_statuses else (i.estimate - i.logged))
                    for i in issues_with_logged_time
                ),

            "efficiency":
                round(
                    estimate / logged * 100,
                    1
                )
                if logged
                else 0
        }



    def task_list(self):

        return [
            issue for issue in self.issues
            if issue.logged > issue.estimate
        ]
    
    def totals(self, developers_data=None):

        estimate = sum(
            i.estimate
            for i in self.issues
        )

        logged = sum(
            i.logged
            for i in self.issues
        )

        br547_logged = 0
        if developers_data:
            br547_logged = sum(d.get("br547_logged", 0) for d in developers_data.values())

        return {

            "tasks":
                len(self.issues),

            "estimate":
                estimate,

            "logged":
                logged,

            "br547_logged":
                br547_logged,

            "remaining":
                sum(
                    (min(0, i.estimate - i.logged) if i.status in self.done_statuses else (i.estimate - i.logged))
                    for i in self.issues
                ),

            "efficiency":
                round(
                    estimate / logged * 100,
                    1
                )
                if logged
                else 0
        }