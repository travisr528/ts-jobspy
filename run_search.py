"""
Job Search Scraper for Render Deployment
Scrapes LinkedIn for knowledge management jobs, filters, and outputs CSV.
Make.com will handle Grok analysis and Google Sheets integration.
"""
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime
import sys

# Configuration
MIN_SALARY = 130000
SEARCH_TERMS = [
    '"knowledge management"',
    '"knowledge manager"',
    '"knowledge lead"',
    '"technical writer"',
    '"information architect"',
    '"ServiceNow knowledge"'
]

# Keywords for relevance filtering
RELEVANT_KEYWORDS = [
    'knowledge management', 'knowledge manager', 'knowledge lead',
    'knowledge specialist', 'knowledge analyst', 'knowledge coordinator',
    'knowledge engineer', 'servicenow knowledge', 'knowledge product owner',
    'knowledge base', 'kb manager', 'kb lead', 'km manager', 'km lead',
    'km specialist', 'km analyst', 'knowledge ops', 'knowledge operations',
    'knowledge strategist', 'knowledge architect', 'technical writer',
    'information architect', 'content architect', 'self-service manager',
    'self service manager', 'deflection'
]

# Terms to exclude
EXCLUDE_TERMS = ['intern', 'entry-level', 'entry level', 'part-time', 'part time', 'contractor']


def is_relevant(title):
    """Check if job title contains relevant keywords."""
    return any(kw in str(title).lower() for kw in RELEVANT_KEYWORDS)


def salary_ok(row):
    """Check if salary meets minimum requirement."""
    min_amt = row.get('min_amount')
    max_amt = row.get('max_amount')
    
    # If no salary info, include it (let Make.com/Grok evaluate)
    if pd.isna(min_amt) and pd.isna(max_amt):
        return True
    
    # Check if either min or max meets threshold
    return (pd.notna(max_amt) and max_amt >= MIN_SALARY) or \
           (pd.notna(min_amt) and min_amt >= MIN_SALARY)


def scrape_jobs_for_term(search_term):
    """Scrape both remote and Austin jobs for a search term."""
    jobs_list = []
    
    # Remote jobs
    try:
        remote_jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=search_term,
            location="United States",
            is_remote=True,
            results_wanted=50,
            hours_old=168,  # Last 7 days
            full_description=True  # ADDED: Fetch full job descriptions
        )
        if len(remote_jobs) > 0:
            jobs_list.append(remote_jobs)
            print(f"    ✓ {len(remote_jobs)} remote jobs")
    except Exception as e:
        print(f"    ✗ Remote error: {e}")
    
    # Austin jobs
    try:
        austin_jobs = scrape_jobs(
            site_name=["linkedin"],
            search_term=search_term,
            location="Austin, Texas",
            results_wanted=50,
            hours_old=168,
            full_description=True  # ADDED: Fetch full job descriptions
        )
        if len(austin_jobs) > 0:
            jobs_list.append(austin_jobs)
            print(f"    ✓ {len(austin_jobs)} Austin jobs")
    except Exception as e:
        print(f"    ✗ Austin error: {e}")
    
    return jobs_list


def main():
    """Main scraping function."""
    print(f"Starting job search at {datetime.now()}")
    print("=" * 60)
    
    all_jobs_list = []
    
    # Search each term
    for i, search_term in enumerate(SEARCH_TERMS):
        print(f"\n[{i+1}/{len(SEARCH_TERMS)}] Searching: {search_term}")
        jobs = scrape_jobs_for_term(search_term)
        all_jobs_list.extend(jobs)
    
    print("\n" + "=" * 60)
    
    # Check if we got any results
    if not all_jobs_list:
        print("ERROR: No jobs found!")
        # Create empty CSV so endpoint doesn't fail
        pd.DataFrame().to_csv('job_results.csv', index=False)
        sys.exit(1)
    
    # Combine all results
    print("\nProcessing results...")
    all_jobs = pd.concat(all_jobs_list, ignore_index=True)
    print(f"  Total jobs before processing: {len(all_jobs)}")
    
    # Check if descriptions were fetched
    if 'description' in all_jobs.columns:
        desc_count = all_jobs['description'].notna().sum()
        print(f"  Jobs with descriptions: {desc_count}/{len(all_jobs)}")
    
    # Deduplicate by URL
    all_jobs = all_jobs.drop_duplicates(subset=['job_url'], keep='first')
    print(f"  After URL deduplication: {len(all_jobs)}")
    
    # Filter by relevance
    all_jobs['relevant'] = all_jobs['title'].apply(is_relevant)
    filtered_jobs = all_jobs[all_jobs['relevant']].drop(columns=['relevant'])
    print(f"  After relevance filter: {len(filtered_jobs)}")
    
    # Filter by salary
    filtered_jobs = filtered_jobs[filtered_jobs.apply(salary_ok, axis=1)]
    print(f"  After salary filter (>=${MIN_SALARY:,}): {len(filtered_jobs)}")
    
    # Exclude junior/contractor roles
    filtered_jobs = filtered_jobs[
        ~filtered_jobs['title'].str.lower().str.contains('|'.join(EXCLUDE_TERMS), na=False)
    ]
    print(f"  After excluding junior/contract: {len(filtered_jobs)}")
    
    # Deduplicate by title + company
    filtered_jobs = filtered_jobs.drop_duplicates(subset=['title', 'company'], keep='first')
    print(f"  After title+company dedup: {len(filtered_jobs)}")
    
    # Add date found
    filtered_jobs['date_found'] = datetime.now().strftime('%Y-%m-%d')
    
    # Select columns for CSV output (what Make.com needs)
    output_columns = [
        'date_found', 'company', 'title', 'location', 'job_url',
        'date_posted', 'min_amount', 'max_amount', 'description'
    ]
    
    # Only include columns that exist
    available_columns = [col for col in output_columns if col in filtered_jobs.columns]
    output_df = filtered_jobs[available_columns]
    
    # Truncate descriptions to avoid CSV issues (keep first 2000 chars)
    if 'description' in output_df.columns:
        output_df['description'] = output_df['description'].apply(
            lambda x: str(x)[:2000] if pd.notna(x) else ''
        )
    
    # Save to CSV
    output_df.to_csv('job_results.csv', index=False)
    print(f"\n✓ Saved {len(output_df)} jobs to job_results.csv")
    
    print("\n" + "=" * 60)
    print(f"Job search completed at {datetime.now()}")
    
    return len(output_df)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
