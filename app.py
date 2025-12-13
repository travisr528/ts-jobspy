"""
Flask Web Service for Job Search API
Serves job_results.csv for Make.com to retrieve.
Runs job searches on a schedule (every 12 hours).
"""
from flask import Flask, send_file, jsonify
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Track last search time
last_search_time = None
search_in_progress = False


def run_job_search():
    """Execute the job search script."""
    global last_search_time, search_in_progress
    
    if search_in_progress:
        print("Search already in progress, skipping...")
        return False
    
    search_in_progress = True
    try:
        print(f"\n{'='*60}")
        print(f"Starting scheduled search at {datetime.now()}")
        print('='*60)
        
        # Import and run the search
        from run_search_render import main
        job_count = main()
        
        last_search_time = datetime.now()
        print(f"Search completed. Found {job_count} jobs.")
        return True
        
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        search_in_progress = False


def scheduled_search():
    """Background thread that runs searches every 12 hours."""
    while True:
        try:
            run_job_search()
        except Exception as e:
            print(f"Scheduled search error: {e}")
        
        # Sleep for 12 hours (43200 seconds)
        print(f"\nNext search in 12 hours...")
        time.sleep(43200)


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        "status": "running",
        "service": "Job Search Scraper",
        "last_search": last_search_time.isoformat() if last_search_time else None,
        "search_in_progress": search_in_progress
    })


@app.route('/health')
def health():
    """Detailed health check."""
    file_exists = os.path.exists('job_results.csv')
    file_time = None
    file_size = 0
    
    if file_exists:
        stat = os.stat('job_results.csv')
        file_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
        file_size = stat.st_size
    
    return jsonify({
        "status": "healthy" if file_exists else "waiting",
        "csv_exists": file_exists,
        "csv_updated": file_time,
        "csv_size_bytes": file_size,
        "last_search": last_search_time.isoformat() if last_search_time else None,
        "search_in_progress": search_in_progress
    })


@app.route('/job_results.csv')
def get_results():
    """Serve the job results CSV file."""
    if os.path.exists('job_results.csv'):
        return send_file(
            'job_results.csv',
            mimetype='text/csv',
            as_attachment=True,
            download_name='job_results.csv'
        )
    return jsonify({"error": "No results available yet"}), 404


@app.route('/run-search')
def trigger_search():
    """Manually trigger a job search (for testing)."""
    if search_in_progress:
        return jsonify({
            "status": "already_running",
            "message": "A search is already in progress"
        }), 409
    
    # Run search in background thread
    thread = threading.Thread(target=run_job_search)
    thread.start()
    
    return jsonify({
        "status": "started",
        "message": "Job search started in background",
        "check_status": "/health"
    })


@app.route('/jobs')
def get_jobs_json():
    """Return job results as JSON (alternative to CSV)."""
    if not os.path.exists('job_results.csv'):
        return jsonify({"error": "No results available", "jobs": []}), 404
    
    import pandas as pd
    df = pd.read_csv('job_results.csv')
    
    return jsonify({
        "count": len(df),
        "updated": datetime.fromtimestamp(os.stat('job_results.csv').st_mtime).isoformat(),
        "jobs": df.to_dict(orient='records')
    })


# Start background scheduler when app starts
scheduler_thread = threading.Thread(target=scheduled_search, daemon=True)
scheduler_started = False


@app.before_request
def start_scheduler():
    """Start the scheduler on first request."""
    global scheduler_started
    if not scheduler_started:
        scheduler_thread.start()
        scheduler_started = True


if __name__ == '__main__':
    # Run initial search on startup
    print("Running initial job search...")
    run_job_search()
    
    # Start the Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
