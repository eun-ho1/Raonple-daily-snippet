import os
import requests
from datetime import datetime, timedelta

# 1. 환경 변수 설정
NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = os.environ.get('DATABASE_ID')
SNIPPET_API_KEY = os.environ.get('SNIPPET_API_KEY', '8195198d-500e-4082-aefd-bab59bfda0bf')
API_URL = "https://n8n.1000.school/webhook/0a43fbad-cc6d-4a5f-8727-b387c27de7c8"

# 2. 팀원 매핑 (노션 이름 : 이메일)
TEAM_INFO = {
    "은호": "jeh0224@gachon.ac.kr",
    "동건": "donggun_email@example.com",
    "유신": "yusin_email@example.com"
}

def get_target_date_kst():
    """테스트를 위해 현재 '오늘' 날짜를 가져오도록 일시 수정했습니다."""
    # 실제 배포 시 어제 데이터를 보내려면 아래 - timedelta(days=1) 주석을 해제하세요.
    target_dt = datetime.utcnow() + timedelta(hours=9)  - timedelta(days=1)
    return target_dt.strftime("%Y-%m-%d")

def get_page_body_content(page_id):
    """페이지 본문을 추출합니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ 본문 로드 실패: {response.text}")
        return ""

    blocks = response.json().get('results', [])
    lines = []
    num_counter = 1
    
    for block in blocks:
        b_type = block['type']
        if b_type in ['paragraph', 'bulleted_list_item', 'numbered_list_item', 'heading_1', 'heading_2', 'heading_3']:
            rich_texts = block[b_type].get('rich_text', [])
            text = "".join([rt.get('plain_text', '') for rt in rich_texts])
            
            if b_type == 'bulleted_list_item':
                text = f"• {text}"
            elif b_type == 'numbered_list_item':
                text = f"{num_counter}. {text}"
                num_counter += 1
            else:
                num_counter = 1
            lines.append(text)
        elif b_type == 'divider':
            lines.append("---")
            num_counter = 1
    
    return "\n".join(lines).strip()

def run_automation():
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    target_date = get_target_date_kst()
    print(f"🔍 시스템 확인: 현재 {target_date} 날짜의 데이터를 찾고 있습니다.")

    query = {
        "filter": {
            "property": "날짜",
            "date": { "equals": target_date }
        }
    }
    
    res = requests.post(f"https://api.notion.com/v1/databases/{DATABASE_ID}/query", headers=headers, json=query)
    
    if res.status_code != 200:
        print(f"❌ 노션 쿼리 실패: {res.text}")
        return

    results = res.json().get('results', [])
    print(f"📊 검색 결과: {len(results)}개의 행을 찾았습니다.")

    for page in results:
        props = page['properties']
        
        # 팀원 확인
        member_data = props.get('팀원', {}).get('select') or props.get('팀원', {}).get('multi_select', [None])[0]
        if not member_data:
            print("⚠️ 팀원 정보가 없는 행은 건너뜁니다.")
            continue
        
        name = member_data['name'].strip()
        print(f"👤 데이터 발견: {name}")
        
        if name in TEAM_INFO:
            email = TEAM_INFO[name]
            page_content = get_page_body_content(page['id'])
            
            # 본문이 비었을 때의 처리
            if not page_content:
                print(f"ℹ️ {name}님의 페이지 본문이 비어있어 제목으로 대체합니다.")
                title_list = props.get('제목', {}).get('title', [])
                page_content = title_list[0]['plain_text'] if title_list else "내용 없음"

            print(f"📝 전송할 내용 맛보기: {page_content[:20]}...")

            payload = {
                "user_email": email,
                "api_id": SNIPPET_API_KEY,
                "snippet_date": target_date,
                "content": page_content
            }
            
            # 줄바꿈 문제 해결을 위한 replace (필요시 사용)
            # payload["content"] = payload["content"].replace("\n", "<br>")

            response = requests.post(API_URL, json=payload)
            print(f"🚀 {name}({email}) API 응답 코드: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ 전송 실패 상세: {response.text}")
        else:
            print(f"❓ {name}님은 TEAM_INFO 매핑에 등록되어 있지 않습니다.")

if __name__ == "__main__":
    run_automation()
