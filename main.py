import os
import requests
from datetime import datetime, timedelta

# 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8" # 여기에 본인의 API 주소를 넣으세요.

TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "2donggeon@gachon.ac.kr",
    "유신": "wooxx3377@gachon.ac.kr",
    "형균": "gudrbs14@gachon.ac.kr"
}

def get_full_text_recursive(block_id):
    """
    블록 ID를 받아 해당 블록의 텍스트와 하위(들여쓰기 된) 블록의 텍스트를 
    모두 합쳐서 하나의 문자열로 반환합니다.
    """
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
        
        # 1. 현재 블록의 텍스트 추출
        block_data = block.get(b_type, {})
        rich_texts = block_data.get('rich_text', [])
        current_text = "".join([rt.get('plain_text', '') for rt in rich_texts])
        
        # 텍스트가 있다면 포맷팅해서 추가
        if current_text.strip():
            if b_type.startswith('heading'):
                all_text_lines.append(f"<br><b>{current_text}</b>")
            elif b_type == 'bulleted_list_item':
                all_text_lines.append(f"• {current_text}")
            else:
                all_text_lines.append(current_text)

        # ⭐️ 2. 핵심: 이 블록 아래에 들여쓰기 된 내용(Children)이 있는지 확인
        if block.get('has_children'):
            # 하위 내용을 가져오기 위해 자기 자신(함수)을 다시 호출 (재귀)
            child_text = get_full_text_recursive(block['id'])
            if child_text:
                # 하위 내용은 시각적 구분을 위해 공백(들여쓰기)을 추가
                indented_child = child_text.replace("• ", "&nbsp;&nbsp;&nbsp;• ")
                all_text_lines.append(indented_child)

    # 모든 줄을 HTML 줄바꿈 태그로 합침
    return "<br>".join(all_text_lines)

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 어제 날짜 데이터 조회 (KST)
    target_date = (datetime.utcnow() + timedelta(hours=9) - timedelta(days=1)).strftime("%Y-%m-%d")
    query = {"filter": {"property": "날짜", "date": {"equals": target_date}}}
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    results = res.json().get('results', [])

    for page in results:
        props = page['properties']
        m_data = props.get('팀원', {}).get('select') or (props.get('팀원', {}).get('multi_select') or [None])[0]
        if not m_data: continue
        
        name = m_data['name'].strip()
        if name in TEAM_INFO:
            # 재귀 함수 호출로 본문 전체 긁어오기
            full_content = get_full_text_recursive(page['id'])
            
            # 전송 페이로드 구성
            payload = {
                "user_email": TEAM_INFO[name],
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": full_content
            }
            
            response = requests.post(API_URL, json=payload)
            print(f"✅ {name}님 전송 완료: {response.status_code}")

if __name__ == "__main__":
    run_automation()
