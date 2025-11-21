import requests
import json
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configuration
BASE_URL = "https://jpicftw.com/category/lifestyle/"
OUTPUT_FILE = "videos.json"
PAGES_TO_SCRAPE = 3

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

def fetch_video_url(post_url):
    try:
        response = requests.get(post_url, headers=get_headers(), timeout=10)
        if response.status_code != 200: return None
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Method 1: Direct .mp4 link
        mp4_link = soup.find('a', href=re.compile(r'\.mp4$'))
        if mp4_link: return mp4_link['href']
            
        # Method 2: "影片在此" text link
        for a in soup.find_all('a'):
            if "影片在此" in a.get_text(): return a['href']
        return None
    except: return None

def scrape():
    new_videos = []
    print("Starting scrape...")
    
    for page in range(1, PAGES_TO_SCRAPE + 1):
        url = f"{BASE_URL}page/{page}/" if page > 1 else BASE_URL
        try:
            response = requests.get(url, headers=get_headers(), timeout=15)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('article')
            
            for article in articles:
                try:
                    title_tag = article.find('h2', class_='entry-title')
                    if not title_tag: continue
                    link = title_tag.find('a')
                    if not link: continue
                    
                    post_url = link['href']
                    title = link.get_text(strip=True)
                    
                    date_tag = article.find('time', class_='entry-date')
                    date = date_tag['datetime'].split('T')[0] if date_tag else "Unknown"
                    
                    print(f"Found: {title}")
                    video_url = fetch_video_url(post_url)
                    
                    if video_url:
                        new_videos.append({"date": date, "topic": title, "url": video_url})
                except Exception as e: print(f"Error parsing article: {e}")
        except Exception as e: print(f"Page error: {e}")

    # Merge with existing
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f: existing = json.load(f)
        except: existing = []
    else: existing = []
    
    # Deduplicate by URL
    video_map = {v['url']: v for v in existing}
    for v in new_videos: video_map[v['url']] = v
    
    final_list = list(video_map.values())
    final_list.sort(key=lambda x: x['date'], reverse=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    print(f"Done. Total videos: {len(final_list)}")

if __name__ == "__main__":
    scrape()
