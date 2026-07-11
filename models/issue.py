from dataclasses import dataclass


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

    from dataclasses import dataclass