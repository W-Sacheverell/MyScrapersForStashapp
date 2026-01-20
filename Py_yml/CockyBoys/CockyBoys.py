import sys
import json
import requests
import re
from bs4 import BeautifulSoup as bs
import io
from datetime import datetime

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def read_json_input():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    return json.loads(sys.stdin.read())

def clean_details(html_node):
    if not html_node:
        return ""
    
    # 移除 "Description" 标题
    header = html_node.find('h2')
    if header:
        header.decompose()

    # 将 <br> 替换为换行符
    for br in html_node.find_all("br"):
        br.replace_with("\n")

    # 获取文本
    text = html_node.get_text()

    # 格式化处理：确保段落之间有空行，并清理多余空格
    lines = [line.strip() for line in text.split('\n')]
    # 过滤掉空的列表元素，但保留段落感
    result = ""
    for line in lines:
        if line:
            result += line + "\n\n"
    final_text = result.strip()
    return re.sub(r"Enjoy,\s*\n+", "Enjoy,\n", final_text)

def scrape_scene(url):
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None

    soup = bs(response.content, 'html.parser')
    
    # 提取标题 (og:title)
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title:
        title = og_title["content"]

    # 提取日期并转换格式 (01/02/2006 -> 2006-01-02)
    date_str = ""
    date_label = soup.find("strong", string=re.compile("Released:"))
    if date_label:
        raw_date = date_label.next_sibling.strip()
        try:
            date_str = datetime.strptime(raw_date, '%m/%d/%Y').strftime('%Y-%m-%d')
        except:
            date_str = raw_date

    # 提取 Details (按预期保留换行)
    details_node = soup.find("div", class_="movieDesc")
    details = clean_details(details_node)

    # 提取演员
    performers = []
    perf_nodes = soup.select('div.movieModels span a.name')
    for p in perf_nodes:
        performers.append({
            "Name": p.get('title', '').replace('“', '').replace('”', '').strip(),
            "URLs": [f"https://cockyboys.com{p['href']}"]
        })

    # 提取标签
    tags = []
    tag_label = soup.find("strong", string=re.compile("Categorized Under:"))
    if tag_label:
        tag_links = tag_label.find_next_siblings("a")
        tags = [{"name": t.get_text().strip()} for t in tag_links]

    # 提取工作室
    studio_name = ""
    og_site = soup.find("meta", property="og:site_name")
    if og_site:
        studio_name = og_site["content"]

	# img
    img = ""
    og_img = soup.find("meta", property="og:image")
    if og_img:
        img = og_img["content"]

    return {
        "Title": title,
        "Date": date_str,
        "Details": details,
        "Studio": {"Name": studio_name},
        "Performers": performers,
        "Tags": tags,
        "Image": img,
        "URL": url
    }

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1 and args[1] == 'sceneByURL':
        input_data = read_json_input()
        scene_url = input_data.get('url')
        result = scrape_scene(scene_url)
        print(json.dumps(result))
