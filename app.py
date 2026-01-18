"""
XE Currency Rate Scraper - Flask Application
Scrapes historical USD/CAD rates from XE.com with rate limiting
"""

import time
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

app = Flask(__name__)

# ============================================================================
# RATE LIMITING CONFIGURATION
# ============================================================================

class RateLimiter:
    """Custom rate limiter to avoid getting blocked by XE"""
    
    def __init__(self, min_delay=2.0, max_delay=4.0, burst_limit=5, burst_cooldown=15.0):
        self.min_delay = min_delay  # Minimum seconds between requests
        self.max_delay = max_delay  # Maximum seconds between requests
        self.burst_limit = burst_limit  # Max requests before cooldown
        self.burst_cooldown = burst_cooldown  # Cooldown after burst
        self.request_count = 0
        self.last_request_time = 0
        self.session_start = time.time()
    
    def wait(self):
        """Wait appropriate time before next request"""
        self.request_count += 1
        
        # Every burst_limit requests, take a longer break
        if self.request_count % self.burst_limit == 0:
            delay = self.burst_cooldown + random.uniform(0, 5)
            print(f"[Rate Limiter] Burst cooldown: {delay:.1f}s")
        else:
            delay = random.uniform(self.min_delay, self.max_delay)
        
        # Ensure minimum time since last request
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            sleep_time = delay - elapsed
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        return delay


# Global rate limiter instance
rate_limiter = RateLimiter(
    min_delay=2.5,      # At least 2.5 seconds between requests
    max_delay=5.0,      # Up to 5 seconds between requests
    burst_limit=5,      # After 5 requests...
    burst_cooldown=20.0 # ...wait 20 seconds
)


# ============================================================================
# WEB SCRAPER
# ============================================================================

def get_headers():
    """Rotate user agents to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    ]
    
    return {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }


def scrape_xe_rate(date_str):
    """
    Scrape USD/CAD rate from XE for a specific date
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        dict with date, rate, and status
    """
    # Apply rate limiting
    rate_limiter.wait()
    
    # XE currency tables URL format
    url = f"https://www.xe.com/currencytables/?from=USD&date={date_str}"
    
    try:
        session = requests.Session()
        response = session.get(url, headers=get_headers(), timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Find the CAD row in the currency table
        # XE uses a table structure, we look for CAD currency
        cad_rate = None
        
        # Method 1: Look for table rows
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            cell_text = [cell.get_text(strip=True) for cell in cells]
            
            # Look for CAD in the row
            for i, text in enumerate(cell_text):
                if 'CAD' in text or 'Canadian Dollar' in text:
                    # The rate is typically in the next columns
                    for j in range(i+1, len(cell_text)):
                        try:
                            rate = float(cell_text[j].replace(',', ''))
                            if 0.5 < rate < 2.5:  # Reasonable USD/CAD range
                                cad_rate = rate
                                break
                        except ValueError:
                            continue
                    if cad_rate:
                        break
            if cad_rate:
                break
        
        # Method 2: Alternative parsing if table method fails
        if not cad_rate:
            # Look for any element containing CAD rate data
            text_content = soup.get_text()
            if 'CAD' in text_content:
                import re
                # Look for patterns like "CAD 1.3456" or similar
                patterns = [
                    r'CAD[^\d]*(\d+\.\d+)',
                    r'Canadian Dollar[^\d]*(\d+\.\d+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, text_content)
                    if match:
                        try:
                            rate = float(match.group(1))
                            if 0.5 < rate < 2.5:
                                cad_rate = rate
                                break
                        except ValueError:
                            continue
        
        if cad_rate:
            return {
                'date': date_str,
                'rate': cad_rate,
                'status': 'success'
            }
        else:
            return {
                'date': date_str,
                'rate': None,
                'status': 'not_found',
                'error': 'CAD rate not found in page'
            }
            
    except requests.exceptions.Timeout:
        return {
            'date': date_str,
            'rate': None,
            'status': 'error',
            'error': 'Request timed out'
        }
    except requests.exceptions.RequestException as e:
        return {
            'date': date_str,
            'rate': None,
            'status': 'error',
            'error': str(e)
        }
    except Exception as e:
        return {
            'date': date_str,
            'rate': None,
            'status': 'error',
            'error': f'Parsing error: {str(e)}'
        }


def get_date_range(start_date, end_date):
    """Generate list of dates between start and end (inclusive)"""
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)
    return dates


# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/')
def index():
    """Main page with date picker"""
    return render_template('index.html')


@app.route('/api/scrape', methods=['POST'])
def scrape_rates():
    """API endpoint to scrape rates for a date range"""
    data = request.get_json()
    
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({'error': 'Start and end dates are required'}), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    if start_date > end_date:
        return jsonify({'error': 'Start date must be before end date'}), 400
    
    # Limit date range to prevent abuse
    days_diff = (end_date - start_date).days
    if days_diff > 90:
        return jsonify({'error': 'Date range cannot exceed 90 days to prevent rate limiting issues'}), 400
    
    dates = get_date_range(start_date, end_date)
    results = []
    
    for i, date_str in enumerate(dates):
        print(f"[Scraper] Fetching rate for {date_str} ({i+1}/{len(dates)})")
        result = scrape_xe_rate(date_str)
        results.append(result)
    
    return jsonify({
        'success': True,
        'results': results,
        'total': len(results),
        'successful': sum(1 for r in results if r['status'] == 'success')
    })


@app.route('/api/scrape-single', methods=['POST'])
def scrape_single_rate():
    """API endpoint to scrape a single date (for progressive loading)"""
    data = request.get_json()
    date_str = data.get('date')
    
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    result = scrape_xe_rate(date_str)
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
