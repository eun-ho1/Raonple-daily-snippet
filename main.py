import os
import requests
from datetime import datetime, timedelta

# 1. 설정 및 환경 변수
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8" # 예: https://api.daily-snippet.com/v1/post

# 2. 팀원 매핑 (이름: 이메일)
TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "팀원2이름": "email2@gachon.ac.kr", # 실제 노션 이름과 이메일로 수정하세요
    "팀원3이름": "email3@gachon.ac.kr",
    "팀원4이름": "email4@gachon.ac.kr"
}

def get_today_kst():
    """한국 시간(KST) 기준으로 오늘 날짜 반환"""
    return (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")

def fetch_notion_logs():
    """노션에서 오늘 날짜의 모든 로그를 가져옴"""
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    today = get_today_kst()
    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": today }
        }
    }
    
    response = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    return response.json().get('results', [])

def run_automation():
    logs = fetch_notion_logs()
    if not logs:
        print("오늘 기록된 로그가 없습니다.")
        return

    # 팀원별로 내용 취합 (한 사람이 여러 줄 썼을 경우 대비)
    member_summaries = {}

    for page in logs:
        props = page['properties']
        
        # 노션 컬럼 데이터 추출
        try:
            name = props['팀원']['select']['name']
            title = props['제목']['title'][0]['plain_text']
            # '오늘 결론/다음 액션' 내용이 있으면 가져오고 없으면 빈 문자열
            action_list = props['오늘 결론/다음 액션']['rich_text']
            action = f" -> {action_list[0]['plain_text']}" if action_list else ""
            
            content_line = f"• {title}{action}"
            
            if name in TEAM_INFO:
                email = TEAM_INFO[name]
                if email not in member_summaries:
                    member_summaries[email] = []
                member_summaries[email].append(content_line)
        except (KeyError, IndexError):
            continue

    # 3. Daily Snippet API 호출
    for email, contents in member_summaries.items():
        payload = {
            "user_email": email,
            "api_id": SNIPPET_API_KEY,
            "snippet_date": get_today_kst(),
            "content": "\n".join(contents)
        }
        
        res = requests.post(API_URL, json=payload)
        
        if res.status_code == 200:
            print(f"✅ 전송 성공: {email}")
        else:
            print(f"❌ 전송 실패 ({res.status_code}): {email} - {res.text}")

if __name__ == "__main__":
    run_automation()
