import sys
import json
import requests
import re
from bs4 import BeautifulSoup as bs
import io
from datetime import datetime
import stashapi.log as log

# 设置通用的请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def debug_print(t):
    sys.stderr.write(t + "\n")

def read_json_input():
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    return json.loads(sys.stdin.read())

def clean_text_custom(html_node):
    """
    处理详情描述，保留换行，并优化特定短语的间距
    """
    if not html_node:
        return ""
    
    # 替换 <br> 为换行符
    for br in html_node.find_all("br"):
        br.replace_with("\n")
    
    text = html_node.get_text()
    
    # 格式化逻辑：去除行首尾空格，并确保段落间有双换行
    lines = [line.strip() for line in text.split('\n')]
    result = ""
    for line in lines:
        if line:
            result += line + "\n\n"
    
    final_text = result.strip()

    return final_text

def scrape_scene(url):
    # 创建 Session 对象以保持 Cookie 状态
    session = requests.Session()
    session.headers.update(HEADERS)

    # 核心优化：预先注入年龄确认 Cookie
    # 使用 .helixstudios.com 确保在所有子域名下生效
    cookie_obj = requests.cookies.create_cookie(
        domain='.helixstudios.com', 
        name='ageConfirmed', 
        value='true', 
        path='/'
    )
    session.cookies.set_cookie(cookie_obj)

    try:
        # allow_redirects=True 会自动处理跳转，模拟“刷新”效果
        response = session.get(url, timeout=15, allow_redirects=True)
        
        if response.status_code != 200:
            debug_print(f"Error: HTTP {response.status_code}")
            return None

        # 如果页面内容依然包含年龄确认关键字，尝试二次激活
        if "Confirm You Are Over 18" in response.text or "AgeConfirmation" in response.url:
            session.get("https://www.helixstudios.com/", timeout=10)
            response = session.get(url, timeout=10)

        soup = bs(response.content, 'html.parser')
        
        # 1. 标题
        title = ""
        title_node = soup.select_one('h1.description')
        if title_node:
            title = title_node.get_text().strip()

        # 2. 日期转换 (Jan 2, 2006 -> 2006-01-02)
        date_str = ""
        date_node = soup.select_one('div.release-date')
        if date_node:
            raw_date = date_node.get_text().strip().replace("Released:","")
            try:
                date_obj = datetime.strptime(raw_date, '%b %d, %Y')
                date_str = date_obj.strftime('%Y-%m-%d')
            except:
                date_str = raw_date

        # 3. Details (描述)
        # 针对 Helix 的不同版本页面结构进行适配
        # details_node = soup.select_one('div.scene-description, div.description-text, div#video-description')
        # details = clean_text_custom(details_node)

        # 4. 演员
        performers = []
        perf_nodes = soup.select('div.performer-name, a.performer, .models a')
        for p in perf_nodes:
            name = p.get_text().strip()
            if name:
                performers.append({"Name": name})

        # 5. 标签
        tags = []
        tag_nodes = soup.select('div.tags a, .categories a')
        for t in tag_nodes:
            tags.append({"name": t.get_text().strip()})

        # 6. 工作室与导演
        studio_name = "Helix Studios"
        studio_node = soup.select_one('div.studio span:nth-of-type(2)')
        if studio_node:
            studio_name = studio_node.get_text().strip()

        director = ""
        dir_node = soup.select_one('div.director')
        if dir_node:
            director = dir_node.get_text().replace("Director:", "").strip()

        # 7. 图片 (基于 ID 拼接 AdultEmpire CDN)
        image_url = ""
        # 优先尝试 canonical 链接或特定 ID 节点提取
        img_link_node = soup.select_one('h5.modal-title a')
        href_attr = img_link_node.get('href', '') if img_link_node else ""

        match = re.search(r'/(\d+)/', href_attr)
        if match:
            image_url = f"https://imgs1cdn.adultempire.com/bn/960/{match.group(1)}-custom-default.jpg"

        return {
            "Title": title,
            "Date": date_str,
            # "Details": details,
            "Studio": {"Name": studio_name},
            "Performers": performers,
            "Tags": tags,
            "Director": director,
            "Image": image_url,
            "URL": url
        }

    except Exception as e:
        debug_print(f"Exception occurred: {str(e)}")
        return None

if __name__ == '__main__':
    args = sys.argv
    if len(args) > 1 and args[1] == 'sceneByURL':
        try:
            input_data = read_json_input()
            scene_url = input_data.get('url')
            if scene_url:
                result = scrape_scene(scene_url)
                if result:
                    print(json.dumps(result))
        except Exception as e:
            debug_print(f"Main loop error: {str(e)}")
