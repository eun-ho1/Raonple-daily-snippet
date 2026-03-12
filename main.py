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

def get_full_text_recursive(block_id, indent_level=0):
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
    
    # 들여쓰기용 공백 (한 단계당 스페이스 4칸)
    padding = "    " * indent_level

    for block in blocks:
        b_type = block.get('type')
        if not b_type: continue
        
        block_data = block.get(b_type, {})
        rich_texts = block_data.get('rich_text', [])
        current_text = "".join([rt.get('plain_text', '') for rt in rich_texts])
        
        if current_text.strip():
            # ⭐️ 변경: HTML 태그(<b>, <br>)를 제거하고 마크다운/텍스트 포맷 사용
            if b_type.startswith('heading'):
                # 제목은 구분선과 함께 강조
                all_text_lines.append(f"\n[ {current_text} ]")
            elif b_type == 'bulleted_list_item':
                all_text_lines.append(f"{padding}• {current_text}")
            elif b_type == 'numbered_list_item':
                all_text_lines.append(f"{padding}- {current_text}")
            else:
                all_text_lines.append(f"{padding}{current_text}")

        # 하위 블록(들여쓰기) 처리
        if block.get('has_children'):
            child_text = get_full_text_recursive(block['id'], indent_level + 1)
            if child_text:
                all_text_lines.append(child_text)

    # ⭐️ 변경: <br> 대신 표준 줄바꿈 \n 사용
    return "\n".join(all_text_lines)

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 당일 데이터 기준 (디버깅용)
    target_date = (datetime.utcnow() + timedelta(hours=9)).strftime("%Y-%m-%d")
    print(f"🔍 디버깅 대상 날짜: {target_date}")
    
    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    if not results:
        print(f"⚠️ {target_date}에 해당하는 노션 페이지를 찾지 못했습니다.")
        return

    for page in results:
        props = page['properties']
        m_data = props.get('팀원', {}).get('select') or (props.get('팀원', {}).get('multi_select') or [None])[0]
        if not m_data: continue
        
        name = m_data['name'].strip()
        if name in TEAM_INFO:
            full_content = get_full_text_recursive(page['id'])
            
            # 제목 추출
            title_list = props.get('제목', {}).get('title', [])
            title = title_list[0]['plain_text'] if title_list else "Daily Snippet"
            
            # ⭐️ 최종 전송 텍스트 구성 (HTML 제거)
            final_body = f"{title}\n\n{full_content}"

            payload = {
                "user_email": TEAM_INFO[name],
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": final_body
            }
            
            # 전송 데이터 확인용 로그
            print(f"--- [{name}님 전송 페이로드 확인] ---")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            
            response = requests.post(API_URL, json=payload)
            print(f"🚀 전송 결과: {response.status_code}")

if __name__ == "__main__":
    run_automation()
