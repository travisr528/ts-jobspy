from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime

# Configure your search parameters
jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter"],
    search_term="knowledge management",
    location="Remote",
    results_wanted=50,
    hours_old=168,  # Last 7 days
    country_indeed="USA"
)

# Add timestamp
jobs['date_found'] = datetime.now().strftime('%Y-%m-%d')

# Save to CSV
jobs.to_csv('job_results.csv', index=False)
```

4. Commit the file to your repository
5. Note that you will customize search_term, location, and results_wanted based on your preferences

**Deploying JobSpy on Render:**
1. Log into Render.com dashboard
2. Click New, then select Cron Job (not Web Service)
3. Connect your GitHub account when prompted
4. Select your forked jobspy repository
5. Configure the cron job settings:
   - Name: job-scraper-knowledge-management
   - Schedule: 0 */12 * * * (runs every 12 hours at midnight and noon UTC)
   - Build Command: pip install -r requirements.txt
   - Start Command: python run_search.py
6. Add environment variables if required by JobSpy
7. Click Create Cron Job
8. Wait for initial deployment to complete

**Testing JobSpy Deployment:**
1. Navigate to your cron job in Render dashboard
2. Click Manual Deploy to trigger an immediate run
3. Watch the deployment logs for errors
4. Verify that job_results.csv appears in the job's file system
5. Download the CSV file to review its contents
6. Confirm that job listings match your search criteria
7. Verify all expected fields are populated: job title, company, location, URL, description
8. Note the file path or URL where results are accessible

**Making Results Accessible to Make.com:**
1. If using Render, files are accessible at https://your-service.onrender.com/job_results.csv
2. Test this URL in your browser to ensure the CSV downloads
3. Save this URL for use in Make.com configuration
4. Consider setting up a simple web server if direct file access is not available

## Building Your First Make.com Scenario: Job Discovery and Initial Processing

The job discovery workflow monitors your JobSpy output, processes new listings, analyzes them with Grok, and populates your tracking spreadsheet.

**Creating the Base Scenario:**
1. Log into Make.com dashboard
2. Click Create a new scenario
3. The scenario editor opens with a blank canvas
4. You will add modules by clicking the + icon
5. Modules connect visually showing data flow from left to right

**Adding Schedule Trigger:**
1. Click the + icon to add the first module
2. Search for "Schedule" in the module directory
3. Select the Schedule module
4. Configure the schedule settings:
   - Interval: Every 12 hours
   - Start time: 00:30 (12:30 AM UTC)
   - Additional run: 12:30 (12:30 PM UTC)
5. This timing allows JobSpy to complete before Make.com retrieves results
6. Click OK to save the trigger

**Retrieving JobSpy Results:**
1. Click the + icon to the right of the Schedule module
2. Search for "HTTP" and select Make a request
3. Configure the HTTP request:
   - URL: Your Render URL for job_results.csv
   - Method: GET
   - Parse response: Yes
4. Click OK to save the module
5. The HTTP module will automatically detect CSV format

**Testing Initial Modules:**
1. Click Run once at the bottom of the scenario editor
2. Watch the execution flow through modules
3. Schedule trigger fires immediately in test mode
4. HTTP module retrieves the CSV file
5. Click on the HTTP module to inspect retrieved data
6. Verify job listings appear in the output
7. Check that all fields are properly parsed

**Adding Iterator for Job Processing:**
1. Click + after the HTTP module
2. Search for "Iterator"
3. Select Iterator module
4. Configure to iterate over the array of jobs from HTTP response
5. Map the Array field to the data output from HTTP module
6. Click OK to save
7. All subsequent modules will execute once per job

**Checking for Duplicate Jobs:**
1. Click + after Iterator
2. Search for "Google Sheets"
3. Select Search rows
4. Authenticate your Google account when prompted
5. Grant Make.com permission to access Google Sheets
6. Configure the search:
   - Spreadsheet: Job Search Tracker 2024
   - Sheet: Sheet1
   - Column: F (Job URL)
   - Search term: Map to the job URL from Iterator output
   - Maximum number of returned rows: 1
7. Click OK to save
8. This search identifies whether the job already exists

**Adding Router for Conditional Processing:**
1. Click + after Google Sheets search module
2. Search for "Router"
3. Select Router module
4. Router creates multiple paths based on conditions
5. You will configure two routes: one for new jobs, one for existing jobs

**Configuring New Job Route:**
1. Click the top route emanating from Router
2. Click Set up a filter
3. Configure the filter:
   - Label: New Job
   - Condition: Total number of bundles from Google Sheets search
   - Operator: Equal to
   - Value: 0
4. Click OK to save filter
5. This route processes only jobs not found in your spreadsheet

**Analyzing Jobs with Grok:**
1. On the New Job route, click + to add a module
2. Search for "xAI" or "Grok"
3. Select the appropriate Grok module (likely "Create a completion" or similar)
4. Authenticate with your xAI account when prompted
5. Configure the Grok prompt with the following structure:
```
Analyze this job posting and provide structured assessment:

Job Title: {{job title from Iterator}}
Company: {{company name from Iterator}}
Location: {{location from Iterator}}
Description: {{job description from Iterator}}

My background: I am an experienced knowledge management professional with expertise in [customize with your key qualifications].

Please provide your analysis in the following JSON format:
{
  "match_score": [0-100 score based on requirements alignment],
  "priority_level": ["High", "Medium", or "Low"],
  "key_requirements": "[bullet list of top 5 requirements]",
  "company_summary": "[2-3 sentence summary of company and role context]"
}
```

6. Map the placeholders to actual data from Iterator output
7. Customize the "My background" section with your real qualifications
8. Click OK to save the module

**Adding Job to Tracking Spreadsheet:**
1. Click + after the Grok module on the New Job route
2. Search for "Google Sheets"
3. Select Add a row
4. Configure the row addition:
   - Spreadsheet: Job Search Tracker 2024
   - Sheet: Sheet1
   - Map each column to appropriate data:
     - Job ID: Use Make.com function {{now}} + {{random}} to create unique ID
     - Date Found: {{now}}
     - Company Name: {{company from Iterator}}
     - Position Title: {{job title from Iterator}}
     - Location: {{location from Iterator}}
     - Job URL: {{url from Iterator}}
     - Posting Date: {{posting date from Iterator if available}}
     - Application Deadline: Leave empty or map if available
     - Match Score: {{match_score from Grok JSON}}
     - Priority Level: {{priority_level from Grok JSON}}
     - Current Status: "New" (hardcoded)
     - Company Research Summary: {{company_summary from Grok JSON}}
     - Key Requirements: {{key_requirements from Grok JSON}}
     - Resume Version: Leave empty
     - Cover Letter Version: Leave empty
     - Application Date: Leave empty
     - Last Contact Date: Leave empty
     - Next Action: "Review opportunity" (hardcoded)
5. Click OK to save the module

**Handling Existing Jobs:**
1. Click the second route from Router (the one without filter)
2. This route processes jobs already in your spreadsheet
3. For now, leave this route empty to skip processing
4. Later you might add update logic if job details change

**Saving and Testing Complete Workflow:**
1. Click the three dots menu near the scenario name
2. Select Rename and enter "Job Discovery and Initial Processing"
3. Click Save (disk icon at bottom)
4. Click Run once to test with live data
5. Watch execution flow through all modules
6. Verify that new jobs are analyzed by Grok
7. Check your Google Sheet to confirm new rows appear
8. Review the data quality in each column
9. Make adjustments to mapping or prompts as needed

**Enabling Automatic Execution:**
1. Toggle the Scheduling switch at the bottom left to ON
2. The scenario will now run every 12 hours automatically
3. Monitor the execution history for the first few runs
4. Check Google Sheets after each execution to verify new jobs appear

## Creating the Company Research Enhancement Workflow

While your initial job discovery workflow includes basic company research from Grok, a separate scenario provides deeper intelligence on high-priority opportunities.

**Creating the Research Scenario:**
1. From Make.com dashboard, click Create a new scenario
2. Name it "Deep Company Research"
3. This workflow triggers when you mark jobs as high priority

**Configuring Watch Changes Trigger:**
1. Add Google Sheets module as first step
2. Select Watch Changes (or Watch Rows if Watch Changes unavailable)
3. Authenticate Google account if needed
4. Configure the trigger:
   - Spreadsheet: Job Search Tracker 2024
   - Sheet: Sheet1
   - Watch for: Updated rows
   - Limit: 10 rows per execution
   - Interval: Every 15 minutes
5. This trigger monitors for spreadsheet changes every 15 minutes

**Filtering for High-Priority New Jobs:**
1. After the trigger, add a Filter module
2. Configure filter conditions:
   - Priority Level equals "High"
   - AND Current Status equals "New" OR "Researching"
3. Only jobs meeting both conditions proceed through workflow

**Conducting Deep Research with Grok:**
1. Add Grok module after the filter
2. Configure comprehensive research prompt:
```
Conduct detailed research on this company and role:

Company: {{Company Name from trigger}}
Position: {{Position Title from trigger}}
Job URL: {{Job URL from trigger}}

Research and provide detailed analysis in these areas:

1. Company Overview: Size, industry, founding, headquarters, public/private status
2. Recent Developments: News from past 3 months, product launches, organizational changes
3. Financial Health: Revenue trends, funding rounds, stability indicators
4. Leadership Team: Key executives, their backgrounds, recent statements
5. Culture and Values: Employee reviews themes, stated mission and values
6. Knowledge Management Context: Current KM initiatives, challenges, or gaps mentioned publicly
7. Strategic Priorities: Recent executive communications about company direction
8. Competitive Position: Market standing and differentiators

Provide response in detailed narrative format organized by these sections. Include specific examples, quotes, and sources where possible.
