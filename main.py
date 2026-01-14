import os
import requests
from datetime import datetime, timedelta

# 환경 변수 로드
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DATABASE_ID = os.environ['DATABASE_ID']
API_URL = "실제_포스트_받는_URL_주소" # 예: https://api.daily-snippet.com/post

TEAM_INFO = {
    "동건": "jeh0224@gachon.ac.kr",
    "팀원2이름": "email2@gachon.ac.kr",
    "팀원3이름": "email3@gachon.ac.kr",
    "팀원4이름": "email4@gachon.ac.kr"
}

def fetch_notion_data():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    # 오늘 날짜 (KST 기준 처리를 위해 필요시 조정)
    today = (datetime.now() + timedelta(hours=9)).strftime("%Y-%m-%d")
    
    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": today }
        }
    }
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    return res.json().get('results', [])

def run():
    pages = fetch_notion_data()
    for page in pages:
        props = page['properties']
        # 노션 컬럼명과 일치해야 함
        member_name = props['팀원']['select']['name']
        title = props['제목']['title'][0]['plain_text']
        
        if member_name in TEAM_INFO:
            payload = {
                "user_email": TEAM_INFO[member_name],
                "api_id": "8195198d-500e-4082-aefd-bab59bfda0bf",
                "snippet_date": (datetime.now() + timedelta(hours=9)).strftime("%Y-%m-%d"),
                "content": f"활동: {title}"
            }
            response = requests.post(API_URL, json=payload)
            print(f"{member_name} 전송 완료: {response.status_code}")

if __name__ == "__main__":
    run()
