import sys    
import json    
import requests    
import re    
from bs4 import BeautifulSoup as bs    
import io    
from datetime import datetime    
    
# 设置请求头    
HEADERS = {    
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'    
}    
    
def debug_print(t):    
    sys.stderr.write(str(t) + "\n")    
    
def read_json_input():    
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')    
    return json.loads(sys.stdin.read())    
    
def scrape_scene(url):    
    try:    
        response = requests.get(url, headers=HEADERS, timeout=15)    
        if response.status_code != 200:    
            debug_print(f"Error: HTTP {response.status_code}")    
            return None    
    
        soup = bs(response.content, 'html.parser')    
            
        # 提取 //script[@id="__NEXT_DATA__"] 元素    
        next_data_script = soup.find('script', id='__NEXT_DATA__')    
        if not next_data_script:    
            debug_print("Error: Could not find __NEXT_DATA__ script tag")    
            return None    
    
        # 解析 JSON 文本    
        json_text = json.loads(next_data_script.string)    
        content = json_text["props"]["pageProps"]["content"]    
    
        title = content["title"]    
    
        i_d = content["id"]    
        scene_code = content["scene_code"]    
        code = f"id={i_d}&scene_code={scene_code}"    # hate to drop the other one so I add them both
    
        publish_date = content["publish_date"]    
        date_str = ""    
        if publish_date:    
            try:    
                date_str = datetime.strptime(publish_date, "%Y/%m/%d %H:%M:%S").strftime("%Y-%m-%d")    
            except Exception as e:    
                debug_print(f"Date conversion error: {e}")    
                date_str = publish_date    
    
        studio = content["site"] if content["site"] else "Blake Mason"    
    
        models = content["models"]    
        performers = []    
        for model in models:    
            performers.append({"Name": model})    
    
        tags = content["tags"]    
        tag_name = []    
        for tag in tags:    
            tag_name.append({"Name": tag})    
    
        details = content["description"]    
    
        thumbnail = content["thumbnail"]    
        img = ""    
        if thumbnail:    
            if thumbnail.startswith("//"):    
                img = "https:" + thumbnail    
            else:    
                img = thumbnail    
    
        return {    
            "Title": title,    
            "Date": date_str,    
            "Code": code,    
            "Details": details,    
            "Studio": {"Name": studio},
            "Performers": performers,    
            "Tags": tag_name,    
            "Image": img,    
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
