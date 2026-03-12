import os
import requests
import json
from datetime import datetime, timedelta

# 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "2donggeon@gachon.ac.kr",
    "유신": "wooxx3377@gachon.ac.kr",
    "형균": "gudrbs14@gachon.ac.kr"
}

def get_full_text_recursive(block_id):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return ""

    blocks = response.json().get('results', [])
    all_text_lines = []

    for block in blocks:
        b_type = block.get('type')
        if not b_type: continue
        
        block_data = block.get(b_type, {})
        rich_texts = block_data.get('rich_text', [])
        current_text = "".join([rt.get('plain_text', '') for rt in rich_texts])
        
        if current_text.strip():
            if b_type.startswith('heading'):
                all_text_lines.append(f"<br><b>{current_text}</b>")
            elif b_type == 'bulleted_list_item':
                all_text_lines.append(f"• {current_text}")
            else:
                all_text_lines.append(current_text)

        if block.get('has_children'):
            child_text = get_full_text_recursive(block['id'])
            if child_text:
                indented_child = child_text.replace("• ", "&nbsp;&nbsp;&nbsp;• ")
                all_text_lines.append(indented_child)

    return "<br>".join(all_text_lines)

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # ⭐️ 수정 포인트: 어제(- timedelta(days=1))를 삭제하고 오늘 날짜로 변경
    target_date = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")
    print(f"🔍 조회 기준 날짜: {target_date}")
    
    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print(f"⚠️ {target_date} 날짜에 해당하는 데이터가 노션에 없습니다.")
        return

    for page in results:
        props = page['properties']
        m_data = props.get('팀원', {}).get('select') or (props.get('팀원', {}).get('multi_select') or [None])[0]
        if not m_data: continue
        
        name = m_data['name'].strip()
        if name in TEAM_INFO:
            full_content = get_full_text_recursive(page['id'])
            
            payload = {
                "user_email": TEAM_INFO[name],
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": full_content
            }
            
            # ⭐️ 디버깅용: 실제로 전송되는 데이터를 로그에 출력
            print(f"--- [{name}님 전송 데이터 상세] ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print("-----------------------------------")
            
            response = requests.post(API_URL, json=payload)
            print(f"🚀 {name}님 서버 응답 상태: {response.status_code}")

if __name__ == "__main__":
    run_automation()
