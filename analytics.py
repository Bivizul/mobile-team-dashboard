from collections import defaultdict


class Analytics:


    def __init__(self, issues):
        self.issues = issues


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
                    i.remaining
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



    def developers(self):

        result = defaultdict(
            lambda:{
                "tasks":0,
                "estimate":0,
                "logged":0,
                "remaining":0,
                "efficiency": 0
            }
        )


        for issue in self.issues:

            developer = result[
                issue.assignee
            ]


            developer["tasks"] += 1

            developer["estimate"] += (
                issue.estimate
            )

            developer["logged"] += (
                issue.logged
            )

            developer["remaining"] += (
                issue.remaining
            )

        for developer in result.values():
            if developer["logged"] > 0:
                developer["efficiency"] = round(
                    developer["estimate"] / developer["logged"] * 100,
                    1
                )

        return dict(sorted(result.items()))



    def developers_with_logged_time(self):

        result = defaultdict(
            lambda:{
                "tasks":0,
                "estimate":0,
                "logged":0,
                "remaining":0,
                "efficiency": 0
            }
        )

        issues_with_logged_time = [
            issue for issue in self.issues if issue.logged > 0
        ]

        for issue in issues_with_logged_time:

            developer = result[
                issue.assignee
            ]


            developer["tasks"] += 1

            developer["estimate"] += (
                issue.estimate
            )

            developer["logged"] += (
                issue.logged
            )

            developer["remaining"] += (
                issue.remaining
            )

        for developer in result.values():
            if developer["logged"] > 0:
                developer["efficiency"] = round(
                    developer["estimate"] / developer["logged"] * 100,
                    1
                )

        return dict(sorted(result.items()))


    def totals_with_logged_time(self):
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


        return {

            "tasks":
                len(issues_with_logged_time),

            "estimate":
                estimate,

            "logged":
                logged,

            "remaining":
                sum(
                    i.remaining
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
    
    def totals(self):

        estimate = sum(
            i.estimate
            for i in self.issues
        )

        logged = sum(
            i.logged
            for i in self.issues
        )

        return {

            "tasks":
                len(self.issues),

            "estimate":
                estimate,

            "logged":
                logged,

            "remaining":
                sum(
                    i.remaining
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