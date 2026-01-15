import sys    
import json    
import html
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
            
        # 提取 //script 元素    
        next_data_script = soup.find('script', class_="schema-premium")    
        if not next_data_script:    
            debug_print("Error: Could not find __NEXT_DATA__ script tag")    
            return None    
    
        # 解析 JSON 文本    
        json_text = json.loads(next_data_script.string)    
        content = json_text[0]
        title = html.unescape(content["name"])
        code = list(filter(None, content["url"].split("/")))[-1]
        date = content["datePublished"][:10]
        studio = content["publisher"]["name"] if content["publisher"]["name"] else "Latin Boyz"

        performers_names_list = title.split(html.unescape("&#8211"))[-1].replace(" ","").split("&")
        performers = []
        for name in performers_names_list:
            performers.append({"Name": name})

        tags_names_list = content["keywords"].split(", ")
        tags = []
        for name in tags_names_list:
            tags.append({"Name": name})

        promo_words = "MEMBERS   CLICK HERE TO ENTER THE MEMBERS ZONE\nNOT A MEMBER?   CLICK HERE TO JOIN NOW"
        promo_words_2 = "MEMBERS   CLICK HERE TO ENTER THE MEMBERS ZONE\nNOT A MEMBER?   CLICK HERE TO JOIN NOW"
        description = html.unescape(content["articleBody"]).replace(promo_words, "").replace(promo_words_2, "").replace("     ", "").replace("\t", "")
        details_list = list(filter(None, description.split("\n")))
        if len(details_list) >= 3:
            head_words = f"*{details_list[0]}* | *{details_list[1]}*\n\n"
            main_descriptions = "\n\n".join(details_list[2:])
            details = head_words + main_descriptions
        else:
            details = "\n\n".join(details_list)

        img = content["image"]["url"] 
        url_ = content["url"]
        return {    
            "Title": title,    
            "Date": date,    
            "Code": code,    
            "Details": details,    
            "Studio": {"Name": studio},
            "Performers": performers,    
            "Tags": tags,    
            "Image": img,    
            "URL": url_    
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
