import os
import sys
from playwright.sync_api import sync_playwright
from src.generators.profile_generator import ProfileGenerator
from src.database.db_manager import DatabaseManager
from src.scrapers.zitouna_scraper import ZitounaScraper 
from src.scrapers.attijari_scraper import AttijariScraper
from src.utils.logger import setup_logger

logger = setup_logger("main")

import argparse

def main():
    parser = argparse.ArgumentParser(description="Credit Eligibility Tool - Phase 1")
    parser.add_argument("--bank", type=str, help="Specify bank to scrape (Zitouna or Attijari). Default: all", default="all")
    parser.add_argument("--count", type=int, help="Number of profiles to generate/process", default=50)
    args = parser.parse_args()

    logger.info(f"Starting Credit Eligibility Tool - Phase 1 - Multi-Bank Scaling (Target: {args.bank})")

    # 1. Initialize Database
    try:
        db = DatabaseManager()
        db.init_db()
        # Clear existing data as requested
        if args.bank.lower() == "all" or args.bank.lower() == "zitouna": # Only clear if starting fresh or running first bank
             db.clear_logs()
    except Exception as e:
        logger.critical("Failed to initialize database. Exiting.")
        sys.exit(1)

    # 2. Generate Profiles
    generator = ProfileGenerator()
    profile_count = args.count
    profiles = generator.generate_profiles(count=profile_count, output_csv=f"data/profiles_batch_{profile_count}.csv")

    # 3. Scrapers Setup
    all_scrapers = [
        ZitounaScraper(headless=True),
        AttijariScraper(headless=True)
    ]
    
    # Filter based on args
    scrapers = all_scrapers
    if args.bank.lower() == "zitouna":
        scrapers = [s for s in all_scrapers if isinstance(s, ZitounaScraper)]
    elif args.bank.lower() == "attijari":
        scrapers = [s for s in all_scrapers if isinstance(s, AttijariScraper)]

    # 4. Run Scraping Loop
    logger.info(f"Starting scaling simulation for {profile_count} profiles across {len(scrapers)} banks...")
    
    with sync_playwright() as p:
        for scraper in scrapers:
            bank_name = scraper.__class__.__name__.replace('Scraper', '')
            logger.info(f"--- Starting simulation for BANK: {bank_name} ---")
            
            try:
                scraper.start_browser(p)
                
                for i, profile in enumerate(profiles):
                    try:
                        logger.info(f"[{bank_name}] [{i+1}/{profile_count}] Processing profile {profile['id']}...")
                        
                        result = scraper.run(p, profile)
                        
                        if result.get('result_status') == 'ERROR':
                            logger.error(f"Error processing {profile['id']} at {bank_name}: {result.get('error_message')}")
                        else:
                            # Add details to profile_data for DB storage
                            profile_with_details = profile.copy()
                            if result.get('details'):
                                profile_with_details['refusal_reason'] = result.get('details')
                            
                            # Save to DB
                            db.insert_result(
                                profile_data=profile_with_details,
                                bank_name=result.get('bank_name', bank_name),
                                result_status=result.get('result_status', 'UNKNOWN'),
                                monthly_payment=result.get('monthly_payment'),
                                interest_rate=result.get('interest_rate')
                            )
                    except Exception as profile_err:
                        logger.error(f"Unexpected error for profile {profile['id']} at {bank_name}: {profile_err}")
                
            except Exception as e:
                logger.error(f"Critical error with scraper {bank_name}: {e}")
            finally:
                if scraper:
                    scraper.close_browser()

    db.close()
    logger.info("========================================")
    logger.info(f"Simulation Run Completed for: {args.bank}")
    logger.info("========================================")

if __name__ == "__main__":
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    main()
