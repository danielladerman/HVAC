# HVAC Automated Lead Generation System

This project is a command-line tool for automating the process of finding, enriching, and contacting new sales leads for HVAC businesses. It uses a combination of Google APIs, web scraping, and AI to build a lead list and draft personalized outreach emails.

## Features

- **Scrape Leads**: Finds HVAC companies in a specified location using Google Maps.
- **Enrich Leads**: Gathers contact information (email and contact name) for the scraped leads using Perplexity AI.
- **Find Reviews**: Searches for customer reviews for the companies.
- **Synthesize Emails**: Uses OpenAI's GPT-4 to draft personalized outreach emails based on the company's information and reviews.
- **Send Emails**: Sends the drafted emails using a configured SMTP server.
- **Follow-up**: Placeholder for future follow-up campaign functionality.

## Setup

Follow these steps to get the project running on your local machine.

### 1. Prerequisites

- Python 3.9+
- A Google Cloud Platform project with the Google Maps and Google Sheets APIs enabled.
- A service account for your Google Cloud project with credentials downloaded as a JSON file.
- API keys for OpenAI and Perplexity AI.
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) for sending emails.

### 2. Installation

Clone the repository to your local machine:
```bash
git clone <your-repo-url>
cd <repository-folder>
```

It's recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Configuration

Rename the `intense-hour-427605-v6-4f484685ddf0.json` file you downloaded from Google Cloud to match the name in your `.gitignore` or update the path in `src/tools/google_sheets_tool.py`.

Create a `.env` file in the root of the project directory and add the following information:

```env
# Google
GOOGLE_MAPS_API_KEY="your-google-maps-api-key"
GOOGLE_SHEETS_CREDENTIALS_PATH="intense-hour-427605-v6-4f484685ddf0.json" # Or your actual file name

# AI APIs
OPENAI_API_KEY="your-openai-api-key"
PERPLEXITY_API_KEY="your-perplexity-api-key"

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME="your-gmail-address@gmail.com"
SMTP_PASSWORD="your-gmail-app-password"
SENDER_EMAIL="your-gmail-address@gmail.com"
```

### 4. Google Sheet Setup

1.  Create a new Google Sheet (e.g., named "HVAC Outreach Campaign").
2.  Open the sheet and share it with the client email address found in your service account's JSON file (it looks like `...iam.gserviceaccount.com`). Give it "Editor" permissions.
3.  The script will automatically create the necessary columns on the first run.

## Usage

All commands are run from the root of the project directory.

### Scrape Leads
Finds new leads and adds them to the Google Sheet. The `--clear` flag will wipe the sheet before adding new leads.

```bash
python3 -m src.main scrape "Brooklyn NY" --max_leads 10 --clear
```

### Enrich Leads
Finds contact information for the next available lead with the status "New".

```bash
python3 -m src.main enrich
```

### Find Reviews
Finds reviews for the next available lead with the status "Enriched".

```bash
python3 -m src.main reviews
```

### Synthesize Email
Drafts a personalized email for the next available lead with the status "Reviewed".

```bash
python3 -m src.main synthesize
```

### Send Email
Sends the drafted email for the next available lead with the status "Drafted".

```bash
python3 -m src.main send
```

### Run Full Pipeline
You can chain the commands to run the full process automatically.

```bash
python3 -m src.main scrape "Brooklyn NY" --max_leads 1 --clear && \
python3 -m src.main enrich && \
python3 -m src.main reviews && \
python3 -m src.main synthesize && \
python3 -m src.main send
``` 