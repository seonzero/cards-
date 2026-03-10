import csv
import time
from get_top_100 import get_top100_cards 
from get_detail import get_card_detail 

all_data = []
top_cards = get_top100_cards("2025-06-01")

for card in top_cards:
    try:
        print(f"크롤링 중: {card['name']} ({card['detail_url']})")
        detail = get_card_detail(card['detail_url'])
        print("상세정보:", detail)
        card.update(detail)
        all_data.append(card)
        time.sleep(1)
    except Exception as e:
        print(f"[에러] {card['name']} 에서 오류 발생: {e}")

# CSV 저장
# CSV 저장 전 데이터가 있는지 확인
if not all_data:
    print("수집된 데이터가 없습니다. 사이트 구조나 연결 상태를 확인하세요.")
else:
    with open("cardgorilla_check100.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)
    print(f"성공적으로 {len(all_data)}개의 데이터를 저장했습니다.")