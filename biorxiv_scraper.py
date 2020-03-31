import sys
sys.path.append("Python")
from biorxiv_month import bioRxivScraper
import json

scraper = bioRxivScraper()

scraped_content = scraper.by_year(start_year=2010,end_year=2020)

with open('biorxiv_data.json', 'w') as fp:
    json.dump(scraped_content, fp)