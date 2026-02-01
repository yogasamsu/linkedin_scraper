import asyncio
import logging
from linkedin_scraper import BrowserManager, JobSearchScraper, JobScraper, CompanyScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Mid-size company ranges (as they appear on LinkedIn)
MID_SIZE_RANGES = [
    "51-200",
    "201-500",
    "501-1,000"
]

async def main():
    # Helper explanation
    print("This script requires 'linkedin_session.json' to exist.")
    print("If you haven't logged in, run 'python3 samples/create_session.py' first.")
    
    # Initialize Browser
    # headless=False allows you to see what's happening and often helps with bot detection
    async with BrowserManager(headless=False) as browser:
        # Load Session
        try:
            await browser.load_session("linkedin_session.json")
            logger.info("Session loaded successfully.")
        except FileNotFoundError:
            logger.error("Session file 'linkedin_session.json' not found. Please log in first.")
            return

        # 1. Search for Jobs
        job_searcher = JobSearchScraper(browser.page)
        keywords = "Finance Manager"
        location = "Indonesia" 
        limit = 10 # Adjust limit as needed
        
        logger.info(f"Searching for '{keywords}' in '{location}' (Limit: {limit})...")
        
        try:
            job_urls = await job_searcher.search(keywords=keywords, location=location, limit=limit)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return
            
        logger.info(f"Found {len(job_urls)} potential jobs. checking company sizes...")

        matching_jobs = []
        job_scraper = JobScraper(browser.page)
        company_scraper = CompanyScraper(browser.page)
        
        # Cache company sizes to avoid re-scraping the same company multiple times
        company_size_cache = {}

        # 2. Process each job
        for i, job_url in enumerate(job_urls):
            logger.info(f"[{i+1}/{len(job_urls)}] Checking job: {job_url}")
            
            try:
                # Scrape Job Details
                job = await job_scraper.scrape(job_url)
                
                if not job.company_linkedin_url:
                    logger.warning(f"  > Skipped: No company URL found for job '{job.job_title}'.")
                    continue

                company_url = job.company_linkedin_url
                
                # Check cache for company size
                if company_url in company_size_cache:
                    company_size = company_size_cache[company_url]
                    logger.info(f"  > Company: {job.company} (Cached Size: {company_size})")
                else:
                    # Scrape Company Details
                    # logger.info(f"  > Scraping company: {company_url}")
                    try:
                        company = await company_scraper.scrape(company_url)
                        company_size = company.company_size if company.company_size else "Unknown"
                        company_size_cache[company_url] = company_size
                        logger.info(f"  > Company: {job.company} (Size: {company_size})")
                    except Exception as e:
                        logger.warning(f"  > Failed to scrape company {company_url}: {e}")
                        company_size = "Error"

                # Filter by size
                # Check if any of the target ranges are substrings of the scraped company size
                if company_size and any(size_range in company_size for size_range in MID_SIZE_RANGES):
                    logger.info("  >>> M A T C H ! <<<")
                    matching_jobs.append({
                        "title": job.job_title,
                        "company": job.company,
                        "size": company_size,
                        "job_url": job.linkedin_url,
                        "company_url": company_url
                    })
                else:
                    pass
                    # logger.info(f"  > Skipped (Not mid-size)")

            except Exception as e:
                logger.error(f"  > Error processing job: {e}")
            
            # Short pause to be polite to the server
            await asyncio.sleep(2)

        # 3. Output results
        print("\n" + "="*80)
        print(f"SEARCH COMPLETE")
        print(f"Found {len(matching_jobs)} matching 'Finance Manager' jobs in Mid-size companies.")
        print("="*80)
        
        for job in matching_jobs:
            print(f"Title:   {job['title']}")
            print(f"Company: {job['company']}")
            print(f"Size:    {job['size']}")
            print(f"Job URL: {job['job_url']}")
            print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())
