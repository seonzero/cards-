"""
Step 2: 정제 JSON → PostgreSQL 적재
data/refined/ 폴더의 JSON 파일들을 읽어서 DB에 upsert합니다.

실행 전 필요한 패키지:
    pip install psycopg2-binary

실행방법:
    python step2_load.py
    python step2_load.py --db "postgresql://user:password@localhost:5432/mydb"

환경변수로도 설정 가능:
    export DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
"""

import json
import os
import argparse
from pathlib import Path

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
REFINED_DIR  = Path("data/refined")
DEFAULT_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/card_db"  # ← 여기 수정
)

# ─────────────────────────────────────────
# DB 연결
# ─────────────────────────────────────────
def get_connection(db_url: str):
    try:
        import psycopg2
        return psycopg2.connect(db_url)
    except ImportError:
        raise ImportError("psycopg2가 없습니다. 'pip install psycopg2-binary' 실행 후 다시 시도하세요.")

# ─────────────────────────────────────────
# 테이블 생성 (없으면)
# ─────────────────────────────────────────
CREATE_TABLES_SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS cards (
    card_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_name            VARCHAR(100) NOT NULL,
    company              VARCHAR(50),
    card_type            VARCHAR(10),
    image_url            TEXT,
    source_url           TEXT,
    fee                  VARCHAR(100),
    required_performance INTEGER DEFAULT 0,
    created_at           TIMESTAMP DEFAULT NOW(),
    updated_at           TIMESTAMP DEFAULT NOW(),
    UNIQUE (card_name, company)
);

CREATE TABLE IF NOT EXISTS card_benefits (
    benefit_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id         UUID NOT NULL REFERENCES cards(card_id) ON DELETE CASCADE,
    category        VARCHAR(50),
    benefit_type    VARCHAR(20),
    benefit_value   NUMERIC,
    benefit_unit    VARCHAR(5),
    benefit_summary TEXT,
    raw_description TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_card_benefits_card_id  ON card_benefits(card_id);
CREATE INDEX IF NOT EXISTS idx_card_benefits_category ON card_benefits(category);
"""

def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLES_SQL)
    conn.commit()
    print("  테이블 준비 완료")

# ─────────────────────────────────────────
# 카드 upsert
# ─────────────────────────────────────────
def upsert_card(conn, refined: dict) -> str:
    """카드를 upsert하고 card_id를 반환"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO cards (card_name, company, card_type, image_url, source_url, fee, required_performance)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (card_name, company)
            DO UPDATE SET
                card_type            = EXCLUDED.card_type,
                image_url            = EXCLUDED.image_url,
                source_url           = EXCLUDED.source_url,
                fee                  = EXCLUDED.fee,
                required_performance = EXCLUDED.required_performance,
                updated_at           = NOW()
            RETURNING card_id
        """, (
            refined.get("card_name"),
            refined.get("company"),
            refined.get("card_type"),
            refined.get("image_url"),
            refined.get("source_url"),
            refined.get("fee"),
            refined.get("required_performance", 0),
        ))
        card_id = str(cur.fetchone()[0])
    return card_id

def insert_benefits(conn, card_id: str, benefits: list):
    """기존 혜택 삭제 후 재삽입 (카드 단위 전체 교체)"""
    with conn.cursor() as cur:
        # 기존 혜택 전부 삭제
        cur.execute("DELETE FROM card_benefits WHERE card_id = %s", (card_id,))

        # 새 혜택 삽입
        for b in benefits:
            cur.execute("""
                INSERT INTO card_benefits
                    (card_id, category, benefit_type, benefit_value, benefit_unit, benefit_summary, raw_description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                card_id,
                b.get("category"),
                b.get("benefit_type"),
                b.get("benefit_value"),
                b.get("benefit_unit"),
                b.get("benefit_summary"),
                b.get("raw_description"),
            ))

# ─────────────────────────────────────────
# 단일 파일 적재
# ─────────────────────────────────────────
def load_one_file(conn, filepath: Path) -> dict:
    """
    반환값: {"status": "success"|"failed", "card_name": ..., "benefit_count": ..., "error": ...}
    """
    try:
        refined = json.loads(filepath.read_text(encoding="utf-8"))
        card_name = refined.get("card_name", filepath.stem)

        card_id = upsert_card(conn, refined)
        benefits = refined.get("benefits", [])
        insert_benefits(conn, card_id, benefits)

        conn.commit()
        print(f"  ✅ {card_name} → {len(benefits)}개 혜택 적재")
        return {"status": "success", "card_name": card_name, "benefit_count": len(benefits), "error": None}

    except Exception as e:
        conn.rollback()
        error_msg = str(e)
        print(f"  ❌ {filepath.name} 실패 → {error_msg}")
        return {"status": "failed", "card_name": filepath.stem, "benefit_count": 0, "error": error_msg}

# ─────────────────────────────────────────
# 결과 확인 쿼리
# ─────────────────────────────────────────
def print_summary(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cards")
        card_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM card_benefits")
        benefit_count = cur.fetchone()[0]

        cur.execute("""
            SELECT c.card_name, c.company, COUNT(b.benefit_id) as benefit_count
            FROM cards c
            LEFT JOIN card_benefits b ON c.card_id = b.card_id
            GROUP BY c.card_id, c.card_name, c.company
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        rows = cur.fetchall()

    print(f"\n{'='*50}")
    print(f"DB 적재 현황")
    print(f"  전체 카드 수: {card_count}개")
    print(f"  전체 혜택 수: {benefit_count}개")
    print(f"\n  최근 적재된 카드:")
    for row in rows:
        print(f"    - {row[0]} ({row[1]}): {row[2]}개 혜택")
    print(f"{'='*50}")

# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main(db_url: str):
    print(f"\n{'='*50}")
    print(f"Step 2: 정제 JSON → PostgreSQL 적재")
    print(f"DB: {db_url.split('@')[-1] if '@' in db_url else db_url}")  # 비밀번호 숨기기
    print(f"{'='*50}\n")

    # 정제 파일 목록
    refined_files = list(REFINED_DIR.glob("*.json"))
    if not refined_files:
        print(f"⚠️  {REFINED_DIR}/ 에 정제된 파일이 없습니다.")
        print(f"   먼저 step1_parse.py를 실행하세요.")
        return

    print(f"정제 파일 {len(refined_files)}개 발견\n")

    conn = get_connection(db_url)

    try:
        # 테이블 생성
        create_tables(conn)

        # 각 파일 적재
        results = {"success": [], "failed": []}
        for i, filepath in enumerate(sorted(refined_files), 1):
            print(f"[{i}/{len(refined_files)}]")
            result = load_one_file(conn, filepath)
            results[result["status"]].append(result)

        # 요약
        print(f"\n적재 완료: 성공 {len(results['success'])}개 / 실패 {len(results['failed'])}개")
        if results["failed"]:
            print("실패 목록:")
            for r in results["failed"]:
                print(f"  - {r['card_name']}: {r['error']}")

        # DB 현황 출력
        print_summary(conn)

    finally:
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_URL,
        help="PostgreSQL 접속 URL (예: postgresql://user:pw@host:5432/dbname)"
    )
    args = parser.parse_args()
    main(args.db)
