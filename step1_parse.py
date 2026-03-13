"""
Step 1: raw JSON → 정제 JSON
Claude API를 사용해서 카드 혜택 데이터를 구조화된 형태로 변환합니다.

실행방법:
    python step1_parse.py
    python step1_parse.py --input data/raw/cards_all.json  # 100개 파일 사용 시
"""

import json
import os   
import time
import argparse
from pathlib import Path
import urllib.request
import urllib.error
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
INPUT_FILE  = "card_check_top100.json"
REFINED_DIR = Path("data/refined")
FAILED_DIR  = Path("data/failed")
LOG_FILE    = Path("logs/parse_result.json")
OUTPUT_FILE = Path("data/refined/cards_refined.json") 

# 폴더 없으면 자동 생성
REFINED_DIR.mkdir(parents=True, exist_ok=True)
FAILED_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

VALID_CATEGORIES = {
    '식비', '생활비', '교통비', '통신비', '쇼핑',
    '의료', '교육', '여가비', '뷰티', '기타'
}
VALID_BENEFIT_TYPES = {
    'cashback_rate', 'cashback_fixed', 'discount_rate',
    'free_service', 'mileage', 'point'
}

# ─────────────────────────────────────────
# LLM 프롬프트
# ─────────────────────────────────────────
SYSTEM_PROMPT = """너는 한국 카드 혜택 데이터를 구조화된 JSON으로 변환하는 전문가야.
반드시 JSON만 출력해. 설명, 마크다운 코드블록(```), 주석 전혀 없이 순수 JSON만."""

def build_user_prompt(card: dict) -> str:
    return f"""다음 카드 데이터를 아래 JSON 스키마로 변환해줘.

## 출력 스키마
{{
  "card_name": "카드 이름",
  "company": "카드사 이름",
  "card_type": "신용" 또는 "체크",
  "image_url": "이미지 URL",
  "source_url": "출처 URL",
  "fee": "연회비 정보",
  "required_performance": 전월실적 숫자(원 단위, 없으면 0),
  "benefits": [
    {{
      "category": "카테고리",
      "benefit_type": "혜택유형",
      "benefit_value": 숫자 또는 null,
      "benefit_unit": "%" 또는 "KRW" 또는 null,
      "benefit_summary": "한 줄 요약 (UI 표시용)",
      "raw_description": "원문 그대로"
    }}
  ]
}}

## category 규칙 (반드시 아래 중 하나만 사용)
- 식비: 외식, 배달, 카페, 베이커리
- 생활비: 마트, 편의점, 생필품
- 교통비: 대중교통, 택시, 주유, 주차
- 통신비: 휴대폰요금, 인터넷, OTT 구독
- 쇼핑: 온라인쇼핑, 의류, 전자기기
- 의료: 병원, 약국
- 교육: 학원, 도서, 온라인강의
- 여가비: 영화, 공연, 여행, 숙박, 공항라운지, 해외이용
- 뷰티: 미용실, 네일
- 기타: 위에 해당 안 되는 것, ATM, 기본혜택, 수수료면제

## benefit_type 규칙 (반드시 아래 중 하나만 사용)
- cashback_rate: 비율 캐시백 (예: 5% 캐시백)
- cashback_fixed: 정액 캐시백 (예: 3,000원 캐시백)
- discount_rate: 비율 할인 (예: 5% 할인)
- free_service: 무료 제공 서비스 (예: 공항라운지 무료)
- mileage: 마일리지/포인트 적립
- point: 포인트 적립

## benefit_value / benefit_unit 규칙
- cashback_rate, discount_rate: 숫자(%), benefit_unit = "%"
- cashback_fixed: 숫자(원), benefit_unit = "KRW"
- free_service: null, benefit_unit = null
- mileage: 최대 적립률(%), benefit_unit = "%"
- 여러 비율이 있으면 대표값(최대값) 사용

## benefit_summary 규칙
- 20자 이내로 핵심만
- 예시: "편의점 5% 할인", "대중교통 캐시백 3천원", "공항라운지 무료 입장"

## 주의사항
- 하나의 benefit_details 항목에 여러 혜택이 섞여 있으면 혜택별로 분리해서 여러 개로 만들어
- 예: "편의점 5% 할인 + 대중교통 1% 할인" → 2개의 benefit 항목으로 분리
- required_performance: "전월실적없음" → 0, "전월실적20만원 이상" → 200000
- card_type: card_name에 "체크"가 있으면 "체크", 없으면 "신용"

## 변환할 카드 데이터
for detail in card.get("benefit_details", []):
    if len(detail.get("description", "")) > 500:
        detail["description"] = detail["description"][:500]
{json.dumps(card, ensure_ascii=False, indent=2)}
"""

# ─────────────────────────────────────────
# Claude API 호출
# ─────────────────────────────────────────
def call_claude_api(card: dict) -> str:
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(card)}
        ],
        "max_tokens": 6000
    }

    api_base = os.environ.get("OPENAI_API_BASE", "https://api.openai.com")
    api_key  = os.environ.get("OPENAI_API_KEY")

    # 임시 확인용
    print(f"  → URL: {api_base}/v1/chat/completions")
    print(f"  → KEY: {api_key[:10] if api_key else 'None'}...")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{api_base}/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
        
# ─────────────────────────────────────────
# 정제 결과 검증
# ─────────────────────────────────────────
def validate_refined(refined: dict) -> list[str]:
    """검증 실패 이유 목록 반환. 빈 리스트면 통과."""
    errors = []

    required_fields = ["card_name", "company", "card_type", "benefits"]
    for field in required_fields:
        if not refined.get(field):
            errors.append(f"필수 필드 없음: {field}")

    benefits = refined.get("benefits", [])
    if not isinstance(benefits, list) or len(benefits) == 0:
        errors.append("benefits가 비어있거나 리스트가 아님")
        return errors

    for i, b in enumerate(benefits):
        cat = b.get("category")
        if cat not in VALID_CATEGORIES:
            errors.append(f"benefits[{i}] 잘못된 category: '{cat}'")

        btype = b.get("benefit_type")
        if btype not in VALID_BENEFIT_TYPES:
            errors.append(f"benefits[{i}] 잘못된 benefit_type: '{btype}'")

        # 비율형인데 value 없으면 경고
        if btype in ("cashback_rate", "discount_rate"):
            if b.get("benefit_value") is None:
                errors.append(f"benefits[{i}] {btype}인데 benefit_value가 null")

        if not b.get("benefit_summary"):
            errors.append(f"benefits[{i}] benefit_summary 없음")

    return errors

# ─────────────────────────────────────────
# 단일 카드 처리
# ─────────────────────────────────────────
def process_card(card: dict) -> dict:
    """
    반환값:
    {
        "status": "success" | "skip" | "failed",
        "card_name": ...,
        "refined": {...} or None,
        "error": "..." or None
    }
    """
    card_name = card.get("card_name", "unknown")
    output_path = REFINED_DIR / f"{card_name}.json"

    # 이미 처리된 카드는 스킵 (재실행 안전)
    if output_path.exists():
        print(f"  ⏭  스킵 (이미 처리됨): {card_name}")
        return {
            "status": "skip",
            "card_name": card_name,
            "refined": json.loads(output_path.read_text(encoding="utf-8")),
            "error": None
        }

    print(f"  🔄 처리 중: {card_name}")

    try:
        # 1. LLM 호출
        raw_text = call_claude_api(card)

        # 2. JSON 파싱 (코드블록 제거 방어)
        clean_text = raw_text.strip()
        if clean_text.startswith("```"):
            lines = clean_text.split("\n")
            clean_text = "\n".join(lines[1:-1])  # 첫줄/마지막줄 제거

        refined = json.loads(clean_text)

        # 3. 검증
        errors = validate_refined(refined)
        if errors:
            raise ValueError(f"검증 실패: {errors}")

        # 4. 중간 저장
        output_path.write_text(
            json.dumps(refined, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  ✅ 완료: {card_name} ({len(refined['benefits'])}개 혜택)")

        return {"status": "success", "card_name": card_name, "refined": refined, "error": None}

    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ 실패: {card_name} → {error_msg}")

        # 실패 케이스 저장
        failed_path = FAILED_DIR / f"{card_name}.json"
        failed_path.write_text(
            json.dumps({"card_name": card_name, "error": error_msg, "raw_card": card},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        return {"status": "failed", "card_name": card_name, "refined": None, "error": error_msg}

# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main(input_file: str):
    print(f"\n{'='*50}")
    print(f"Step 1: raw JSON → 정제 JSON")
    print(f"입력 파일: {input_file}")
    print(f"{'='*50}\n")

    # raw JSON 로드
    raw_cards = json.loads(Path(input_file).read_text(encoding="utf-8"))
    print(f"총 {len(raw_cards)}개 카드 로드됨\n")

    results = {"success": [], "skip": [], "failed": []}

    for i, card in enumerate(raw_cards, 1):
        print(f"[{i}/{len(raw_cards)}]")
        result = process_card(card)
        results[result["status"]].append(result["card_name"])

        # API 과부하 방지 (연속 호출 시 딜레이)
        if result["status"] != "skip" and i < len(raw_cards):
            time.sleep(1)

    # 결과 요약
    print(f"\n{'='*50}")
    print(f"파싱 완료 요약")
    print(f"  성공: {len(results['success'])}개")
    print(f"  스킵: {len(results['skip'])}개")
    print(f"  실패: {len(results['failed'])}개")
    if results["failed"]:
        print(f"  실패 목록: {results['failed']}")
    print(f"{'='*50}")

    # 전체 정제 결과를 파일 하나로 합치기
    all_refined = []
    for card_name in results["success"] + results["skip"]:
        f = REFINED_DIR / f"{card_name}.json"
        if f.exists():
            all_refined.append(json.loads(f.read_text(encoding="utf-8")))
    
    OUTPUT_FILE.write_text(
        json.dumps(all_refined, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"통합 파일 저장됨: {OUTPUT_FILE} ({len(all_refined)}개)")

    # 로그 저장
    LOG_FILE.parent.mkdir(exist_ok=True)
    LOG_FILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n로그 저장됨: {LOG_FILE}")
    print(f"정제 파일 위치: {REFINED_DIR}/")

    if results["failed"]:
        print(f"\n⚠️  실패한 카드는 {FAILED_DIR}/ 에서 확인하세요.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=INPUT_FILE, help="입력 JSON 파일 경로")
    args = parser.parse_args()
    main(args.input)
