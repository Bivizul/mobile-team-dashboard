from dataclasses import dataclass, field


@dataclass
class Issue:
    key: str
    summary: str

    status: str

    assignee: str

    issue_type: str
    estimate: int
    logged: int
    remaining: int
    jira_url: str = ""
    updated: str = ""
    created: str = ""
    resolution_date: str = ""
    done_date: str = ""
    components: list[str] = field(default_factory=list)
    department: str = ""
