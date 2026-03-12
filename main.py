def get_full_text_recursive(block_id):
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Notion-Version": "2022-06-28"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200: return ""

    blocks = response.json().get('results', [])
    all_text_lines = []

    for block in blocks:
        b_type = block.get('type')
        if not b_type: continue
        
        block_data = block.get(b_type, {})
        rich_texts = block_data.get('rich_text', [])
        current_text = "".join([rt.get('plain_text', '') for rt in rich_texts])
        
        if current_text.strip():
            # ⭐️ 수정: HTML 태그(<br>, <b>)를 모두 제거하고 마크다운/텍스트 형식 사용
            if b_type.startswith('heading'):
                all_text_lines.append(f"\n[ {current_text} ]")
            elif b_type == 'bulleted_list_item':
                all_text_lines.append(f"• {current_text}")
            elif b_type == 'numbered_list_item':
                all_text_lines.append(f"- {current_text}")
            else:
                all_text_lines.append(current_text)

        if block.get('has_children'):
            child_text = get_full_text_recursive(block['id'])
            if child_text:
                # ⭐️ 수정: 들여쓰기도 HTML 공백 대신 실제 공백 사용
                indented_child = child_text.replace("• ", "    • ").replace("- ", "    - ")
                all_text_lines.append(indented_child)

    # ⭐️ 수정: <br> 대신 표준 줄바꿈 \n 사용
    return "\n".join(all_text_lines)
