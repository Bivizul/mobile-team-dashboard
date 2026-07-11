# Jira Team Dashboard

Simple Flask dashboard for viewing Jira issues and team progress.

## Requirements

- Python 3.10+
- A running Jira instance with API access

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Bivizul/jira-team-dashboard.git
   cd jira-team-dashboard
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   - Copy [.env.example](.env.example) to .env
   - Fill in the Jira API settings
   - Fill in the HRBox credentials if you want to enable leave-calendar integration

5. Run the app:
   ```bash
   python app.py
   ```

The dashboard will be available at http://127.0.0.1:5000.

## Project structure

```text
jira-team-dashboard/
├── app.py
├── config.py
├── jira_client.py
├── analytics.py
├── requirements.txt
├── .env.example
├── README.md
├── models/
│   └── issue.py
├── templates/
│   └── index.html
└── static/
    └── style.css
```