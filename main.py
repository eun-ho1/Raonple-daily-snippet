import os
import requests
from datetime import datetime, timedelta

# 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    # KST 기준 어제 날짜
    target_dt = datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """노션 블록을 읽어 HTML 줄바꿈이 적용된 텍스트로 변환합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "본문을 불러오지 못했습니다."

    blocks = response.json().get('results', [])
    lines = []
    num_counter = 1
    
    for block in blocks:
        b_type = block['type']
        
        # 모든 텍스트 블록에서 데이터 추출 시도
        if b_type in block:
            rich_texts = block[b_type].get('rich_text', [])
            if not rich_texts:
                # 내용이 없는 빈 줄 처리
                lines.append("")
                continue
                
            text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            # 1. 제목 처리 (굵게 표시 및 위아래 간격)
            if b_type.startswith('heading_'):
                lines.append(f"<br><b>{text}</b>")
                num_counter = 1
            
            # 2. 동그라미 리스트 처리 (특수기호 대신 표준 기호 사용)
            elif b_type == 'bulleted_list_item':
                lines.append(f"• {text}")
            
            # 3. 숫자 리스트 처리
            elif b_type == 'numbered_list_item':
                lines.append(f"{num_counter}. {text}")
                num_counter += 1
            
            # 4. 일반 문단 및 기타
            else:
                lines.append(text)
                num_counter = 1

    # ⭐️ 핵심 해결책: \n으로 합친 후 모든 개행을 <br>로 강제 치환
    final_text = "<br>".join(lines).strip()
    return final_text

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    for page in results:
        props = page['properties']
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data: continue
        
        name = member_data['name'].strip()
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            # 본문 내용 추출
            page_content = get_page_body_content(page['id'])
            
            # 페이지 제목 가져오기
            title_list = props.get('제목', {}).get('title', [])
            page_title = title_list[0]['plain_text'] if title_list else "Daily Snippet"

            # 제목과 본문을 합쳐서 전송
            full_content = f"<b>{page_title}</b><br>{page_content}"

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": full_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name}님 데이터 전송: {response.status_code}")

if __name__ == "__main__":
    run_automation()
