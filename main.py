import argparse
from src.crew import scraping_crew, research_crew, email_crew

def run_scraping_crew(query: str):
    """Kicks off the lead scraping crew."""
    print("## Starting the Lead Scraping Crew...")
    print("-------------------------------------")
    scraping_crew.kickoff(inputs={'query': query})
    print("\n\n########################")
    print("## Scraping Crew Work Complete!")
    print("########################\n")

def run_research_crew():
    """Kicks off the business research crew."""
    print("## Starting the Business Research Crew...")
    print("---------------------------------------")
    research_crew.kickoff()
    print("\n\n########################")
    print("## Research Crew Work Complete!")
    print("########################\n")

def run_email_crew():
    """Kicks off the email drafting crew."""
    print("## Starting the Email Drafting Crew...")
    print("------------------------------------")
    email_crew.kickoff()
    print("\n\n########################")
    print("## Email Drafting Crew Work Complete!")
    print("########################\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an AI crew for business outreach.")
    parser.add_argument(
        "crew", 
        type=str, 
        choices=['scrape', 'research', 'email'], 
        help="The name of the crew to run."
    )
    parser.add_argument(
        "--query", 
        type=str, 
        default="HVAC companies in Miami, FL", 
        help="The search query for the scraping crew."
    )

    args = parser.parse_args()

    if args.crew == 'scrape':
        run_scraping_crew(args.query)
    elif args.crew == 'research':
        run_research_crew()
    elif args.crew == 'email':
        run_email_crew() 