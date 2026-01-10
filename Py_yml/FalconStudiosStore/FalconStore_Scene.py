import sys
import json
import requests
from bs4 import BeautifulSoup as bs
import io
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def read_json_input():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    return json.loads(sys.stdin.read())

def scrape_scene(url):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.set('ageConfirmed', 'true', domain='.falconstudios.com', path='/')

    response = session.get(url, timeout=15, allow_redirects=True)
    if response.status_code != 200:
        return None

    soup = bs(response.content, 'html.parser')
    
    # Title
    title = ""
    title_node = soup.select_one('div.video-title h1')
    if title_node:
        title = title_node.get_text().strip()

    # Date (Jan 2, 2006 -> 2006-01-02)
    date_str = ""
    date_node = soup.select_one('div.release-date')
    if date_node:
        raw_date = date_node.get_text().strip()
        try:
            date_str = datetime.strptime(raw_date, '%b %d, %Y').strftime('%Y-%m-%d')
        except:
            date_str = ""

    # Studio & Director
    studio = ""
    studio_node = soup.select_one('div.studio a[data-label="Studio"]')
    if studio_node:
        studio = studio_node.get_text().strip()

    director = ""
    dir_node = soup.select_one('a[data-label="Director"]')
    if dir_node:
        director = dir_node.get_text().strip()

    # Performers
    performers = []
    perf_nodes = soup.select('div.video-performer a')
    for p in perf_nodes:
        performers.append({"Name": p.get_text().strip()})

    return {
        "Title": title,
        "Date": date_str,
        "Studio": {"Name": studio},
        "Director": director,
        "Performers": performers,
        "URL": url
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'sceneByURL':
        input_data = read_json_input()
        result = scrape_scene(input_data.get('url'))
        if result:
            print(json.dumps(result))
