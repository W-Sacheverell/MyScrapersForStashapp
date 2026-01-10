import sys
import json
import requests
from bs4 import BeautifulSoup as bs
import io
import re
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def read_json_input():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    return json.loads(sys.stdin.read())

def parse_duration(text):
    # 将 "1 hrs. 45 mins." 转换为 "1:45:00"
    try:
        match = re.search(r'(\d+)\s*hrs\.\s*(\d+)\s*mins\.', text)
        if match:
            return f"{match.group(1)}:{match.group(2)}:00"
    except:
        pass
    return ""

def scrape_movie(url):
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.set('ageConfirmed', 'true', domain='.falconstudios.com', path='/')

    response = session.get(url, timeout=15, allow_redirects=True)
    if response.status_code != 200:
        return None

    soup = bs(response.content, 'html.parser')
    
    # 基本信息
    title = soup.select_one('div.video-title h1').get_text().strip()
    if title.lower().endswith(", the"):
        # 如果是，则删除结尾的 ", the" (不分大小写长度为 5)，并在前面加 "The "
       name = "The " + title[:-5].strip()
    else:
        # 如果不是，则不作其他处理
        name = title
    
    date_node = soup.select_one('div.release-date')
    date_str = ""
    if date_node:
        try:
            date_str = datetime.strptime(date_node.get_text().strip(), '%b %d, %Y').strftime('%Y-%m-%d')
        except: pass

    # 时长处理
    duration = ""
    date_nodes = soup.select('div.release-date')
    if len(date_nodes) > 1:
        duration = parse_duration(date_nodes[1].get_text())

    # 简介 (Synopsis)
    synopsis = ""
    syn_node = soup.select_one('div.synopsis')
    if syn_node:
        synopsis = syn_node.get_text(separator="\n\n").strip()

	# 图片处理
    front_img = ""
    back_img = ""
    carousel_imgs = soup.select('div#viewLargeBoxcover div.carousel-item img')
    
    if len(carousel_imgs) > 0:
        # 获取正面图片并替换尺寸
        front_img = carousel_imgs[0].get('src', '').replace("/10/", "/550/")
        
        # 处理背面图片
        temp_back = ""
        if len(carousel_imgs) > 1:
            temp_back = carousel_imgs[1].get('src', '').replace("/10/", "/550/")
        
        # 检测提取的链接是否符合背面图格式 (ID后面带b)
        # 正则解释：匹配 /product/550/数字b/
        if temp_back and re.search(r'/product/\d+/\d+b/', temp_back):
            back_img = temp_back
        else:
            # 如果不符合格式，则基于 front_img 的 ID 后面强行加 'b'
            # 正则解释：在 /product/550/数字/ 的数字后面插入 b
            back_img = re.sub(r'(/product/\d+/(\d+))/', r'\1b/', front_img)

    # 标签
    tags = [{"name": a.get_text().strip()} for a in soup.select('div.categories a')]

    return {
        "Name": name,
        "Date": date_str,
        "Duration": duration,
        "Synopsis": synopsis,
        "Front_Image": front_img,
        "Back_Image": back_img,
        "Tags": tags,
        "URL": url
    }

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'groupByURL':
        input_data = read_json_input()
        result = scrape_movie(input_data.get('url'))
        if result:
            print(json.dumps(result))
