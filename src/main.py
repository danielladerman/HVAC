import argparse
import pandas as pd
import re
from src.tools.google_maps_tool import GoogleMapsTool
from src.tools.google_sheets_tool import GoogleSheetsTool
from src.tools.search_tools import SearchTools
from src.tools.email_tool import EmailTool
import datetime
import os
from openai import OpenAI

ALL_COLUMNS = [
    "Business Name", "Website", "Phone Number", "Status", 
    "Email", "Contact Name", "Reviews", "Email Draft", "Email Sent Date"
]

def scrape_leads(location, max_leads, clear_sheet):
    """Scrape leads from Google Maps and save them to Google Sheets."""
    print(f"Scraping up to {max_leads} HVAC leads from {location}...")
    maps_tool = GoogleMapsTool()
    sheets_tool = GoogleSheetsTool()
    
    if clear_sheet:
        print("Clearing the sheet...")
        sheets_tool.clear_sheet()
    
    # Ensure all required columns are present in the sheet
    sheets_tool.ensure_columns_exist(ALL_COLUMNS)
    
    # Get existing websites to avoid duplicates
    print("Fetching existing websites to prevent duplicates...")
    existing_websites = sheets_tool.get_all_column_values("Website")
    existing_websites = set(filter(None, existing_websites)) # Filter out empty strings and create a set for fast lookups
    print(f"Found {len(existing_websites)} existing websites in the sheet.")

    results = maps_tool.find_hvac_companies(location, max_leads=max_leads)
    leads_df = pd.DataFrame(results['leads'])

    if not leads_df.empty:
        # Filter out leads that are already in the sheet based on website
        original_count = len(leads_df)
        leads_df = leads_df[~leads_df['Website'].isin(existing_websites)]
        new_leads_count = len(leads_df)
        print(f"Found {original_count} leads, {new_leads_count} are new.")

        if new_leads_count > 0:
            # Add a status column for tracking, the rest will be aligned by append_rows
            leads_df['Status'] = 'New'
            sheets_tool.append_rows(leads_df)
            print(f"Successfully scraped and saved {new_leads_count} new leads.")
        else:
            print("No new unique leads to add.")
    else:
        print("No leads found.")

def enrich_leads():
    """Enrich leads by finding contact information for each website."""
    if not os.getenv("PERPLEXITY_API_KEY") or not os.getenv("OPENAI_API_KEY"):
        print("Error: PERPLEXITY_API_KEY or OPENAI_API_KEY not found in .env file. Cannot enrich leads.")
        return

    print("Enriching leads...")
    sheets_tool = GoogleSheetsTool()
    search_tool = SearchTools()
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    lead_to_enrich = sheets_tool.get_next_task(status_to_find='New')

    if not lead_to_enrich:
        print("No new leads to enrich.")
        return
        
    if not lead_to_enrich.get('Website'):
        print(f"Skipping lead with no website: {lead_to_enrich.get('Business Name')}")
        sheets_tool.update_row(lead_to_enrich['row_index'], {"Status": "No Website"})
        return

    website_url = lead_to_enrich['Website']
    company_name = lead_to_enrich.get('Business Name')
    print(f"Found new lead to enrich: {company_name} with website {website_url}")
    
    final_email = ""
    contact_name = ""

    # Step 1: Direct website scrape for email. It's fast and sometimes works.
    print(f"Step 1: Scraping {website_url} directly for emails...")
    scraped_info = search_tool.scrape_website_for_contact_info(website_url)
    if scraped_info and scraped_info.get('emails'):
        final_email = scraped_info['emails'][0]  # Take the first one found
        print(f"Found email via direct scraping: {final_email}")
    else:
        print("No email found via direct scraping.")

    # Step 2: If no email from scraping, use a focused Perplexity search.
    if not final_email:
        print("Step 2: Asking Perplexity for the best contact email...")
        email_query = f"What is the best contact email address for the company '{company_name}' with website {website_url}?"
        perplexity_email_result = search_tool.search_internet(email_query)
        
        # Use regex to find emails in the result. It's more reliable for this specific task.
        found_emails = re.findall(r'[\w.-]+@[\w.-]+', perplexity_email_result)
        if found_emails:
            final_email = found_emails[0]
            print(f"Found email via Perplexity: {final_email}")
        else:
            print("Perplexity could not find a contact email.")
            final_email = "Not Found"

    # Step 3: Separately, search for the contact name.
    print("Step 3: Asking Perplexity for the main contact person...")
    name_query = f"Who is the owner, founder, or main manager of the company '{company_name}' with website {website_url}?"
    perplexity_name_result = search_tool.search_internet(name_query)

    # Step 4: Use OpenAI to cleanly extract the name.
    if "I did not find any information" not in perplexity_name_result and perplexity_name_result:
        print("Step 4: Using OpenAI to extract the name from Perplexity's response...")
        extraction_prompt = f"""
        From the following text, extract only the person's full name.
        Provide ONLY the full name. If no name is found, write NOT_FOUND.

        Text:
        {perplexity_name_result}
        """
        extraction_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": extraction_prompt}],
            temperature=0,
        )
        extracted_name = extraction_response.choices[0].message.content.strip()
        
        if "NOT_FOUND" not in extracted_name:
            contact_name = extracted_name
            print(f"Extracted contact name: {contact_name}")
        else:
            print("Could not extract a specific contact name.")
    else:
        print("Perplexity could not find a contact person.")

    update_data = {
        "Email": final_email,
        "Contact Name": contact_name,
        "Status": "Enriched"
    }
    sheets_tool.update_row(lead_to_enrich['row_index'], update_data)
    print(f"Enrichment complete for: {company_name}. Email: {final_email}, Contact: {contact_name}")


def find_reviews():
    """Find reviews for a company and add them to the sheet."""
    print("Finding reviews...")
    sheets_tool = GoogleSheetsTool()
    search_tool = SearchTools()

    lead_to_review = sheets_tool.get_next_task(status_to_find='Enriched')

    if lead_to_review:
        company_name = lead_to_review.get('Business Name')
        print(f"Found enriched lead to find reviews for: {company_name}")
        
        query = f"Find customer reviews for the HVAC company '{company_name}'"
        reviews_result = search_tool.search_internet(query)
        
        # We will just save the whole text result for now. This can be refined later.
        update_data = {
            "Reviews": reviews_result if reviews_result else "No reviews found.",
            "Status": "Reviewed"
        }
        sheets_tool.update_row(lead_to_review['row_index'], update_data)
        print(f"Found and saved reviews for: {company_name}")
    else:
        print("No enriched leads to find reviews for.")


def synthesize_email():
    """Synthesizes a personalized email for a reviewed lead."""
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file. Cannot synthesize email.")
        return

    print("Synthesizing email...")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    sheets_tool = GoogleSheetsTool()

    lead_to_email = sheets_tool.get_next_task(status_to_find='Reviewed')

    if lead_to_email:
        company_name = lead_to_email.get('Business Name', '')
        reviews = lead_to_email.get('Reviews', '')
        contact_name = lead_to_email.get('Contact Name', '')
        print(f"Found reviewed lead to synthesize email for: {company_name}")

        prompt = f"""
        Based on the following information about '{company_name}', an HVAC company, draft a personalized outreach email.
        The goal is to propose our AI consulting services to help them automate tasks and improve response times.

        Company Name: {company_name}
        Customer Reviews: "{reviews}"

        Generate ONLY the body for a personalized outreach email. Do NOT include a subject line.
        The email should be professional, concise, and friendly. It should reference the company's reputation based on the reviews, and offer a free audit.
        Here is a template to follow, but adapt it based on the reviews:

        Hi [Contact Name],

        Hope you're doing well. I came across {company_name} and was really impressed by [mention something positive from the reviews or their general reputation].

        I run a small AI automation consultancy focused specifically on HVAC businesses. Right now, we're offering a free audit to help companies like yours identify ways to:

        - Recover missed leads with 24/7 chatbots and voice agents
        - Automate repetitive tasks like scheduling, follow-ups, and CRM updates
        - Improve response times without adding headcount

        We're looking to partner with just one or two companies in your area this month to custom-build solutions around real bottlenecks. No pressure or pitch — just a free audit to show what's possible.

        Would you be open to a quick call next week to see if it's worth exploring?

        Best,
        
        Daniel Laderman
        """
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        draft = response.choices[0].message.content

        # Use company name as fallback for the greeting
        greeting_name = contact_name if contact_name and contact_name.strip() else company_name
        final_draft = draft.replace('[Contact Name]', greeting_name)

        update_data = {
            "Email Draft": final_draft,
            "Status": "Drafted"
        }
        sheets_tool.update_row(lead_to_email['row_index'], update_data)
        print(f"Synthesized and saved email for: {company_name}")
    else:
        print("No reviewed leads to synthesize an email for.")


def send_email_command():
    """Sends a personalized email to a lead."""
    required_vars = ["SMTP_SERVER", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "SENDER_EMAIL"]
    if not all(os.getenv(var) for var in required_vars):
        print("Error: One or more SMTP environment variables are not set in .env file. Cannot send email.")
        return

    print("Sending email...")
    sheets_tool = GoogleSheetsTool()
    email_tool = EmailTool()

    lead_to_send = sheets_tool.get_next_task(status_to_find='Drafted')

    if lead_to_send:
        recipient_email = lead_to_send.get('Email')
        email_draft = lead_to_send.get('Email Draft')
        company_name = lead_to_send.get('Business Name')
        
        if recipient_email and recipient_email != 'Not Found' and email_draft:
            # Simple subject line, can be improved
            subject = f"A Free AI Transformation Audit for {company_name}"
            
            print(f"Sending email to {recipient_email} for {company_name}...")
            result = email_tool.send_email(to=recipient_email, subject=subject, body=email_draft)
            print(result)

            update_data = {
                "Status": "Sent",
                "Email Sent Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            sheets_tool.update_row(lead_to_send['row_index'], update_data)
        else:
            print(f"Cannot send email for {company_name}. Missing email address or draft.")
            sheets_tool.update_row(lead_to_send['row_index'], {"Status": "Send Failed"})
    else:
        print("No drafted emails to send.")


def run_follow_up_campaigns():
    """Runs follow-up email campaigns for leads that have been contacted."""
    print("Running follow-up campaigns...")
    sheets_tool = GoogleSheetsTool()
    
    # This is a placeholder for a more complex follow-up logic.
    # For now, it just finds leads that have been sent an email.
    contacted_leads = sheets_tool.get_next_task(status_to_find='Sent')

    if contacted_leads:
        print("Found leads for follow-up, but the logic is not yet implemented.")
        # Here you would check the 'Email Sent Date' and send a follow-up if enough time has passed.
    else:
        print("No leads ready for a follow-up.")

def main():
    parser = argparse.ArgumentParser(description="HVAC Lead Generation Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape leads from Google Maps")
    scrape_parser.add_argument("location", type=str, help="The location to search for HVAC companies (e.g., 'Brooklyn NY')")
    scrape_parser.add_argument("--max_leads", type=int, default=50, help="Maximum number of leads to scrape")
    scrape_parser.add_argument("--clear", action="store_true", help="Clear the sheet before scraping")

    # Enrich command
    subparsers.add_parser("enrich", help="Enrich leads with contact information")

    # Reviews command
    subparsers.add_parser("reviews", help="Find reviews for a company")
    
    # Synthesize command
    subparsers.add_parser("synthesize", help="Synthesize a personalized email")
    
    # Send command
    subparsers.add_parser("send", help="Send a personalized email")
    
    # Follow-up command
    subparsers.add_parser("followup", help="Run follow-up campaigns")

    args = parser.parse_args()

    if args.command == "scrape":
        scrape_leads(args.location, args.max_leads, args.clear)
    elif args.command == "enrich":
        enrich_leads()
    elif args.command == "reviews":
        find_reviews()
    elif args.command == "synthesize":
        synthesize_email()
    elif args.command == "send":
        send_email_command()
    elif args.command == "followup":
        run_follow_up_campaigns()

if __name__ == "__main__":
    main()
