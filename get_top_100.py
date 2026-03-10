from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

def get_top100_cards(date="2025-06-01"):
    url = f"https://www.card-gorilla.com/chart/check100?term=monthly&date={date}"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    card_data = []

    try:
        # 리스트 wrap 요소가 나타날 때까지 대기
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "rk_lst"))
        )
        
        # 페이지 소스 파싱
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # li 태그들 추출 (보내주신 구조 반영)
        card_elements = soup.select("ul.rk_lst > li")
        
        for el in card_elements:
            # 광고 구좌(class="ad")는 건너뜀
            if "ad" in el.get("class", []):
                continue
                
            try:
                # 카드 이름과 카드사 추출
                name = el.select_one(".card_name").get_text(strip=True)
                corp = el.select_one(".corp_name span").get_text(strip=True)
                
                # 상세 페이지 URL 추출 방식 수정
                # 현재 href가 javascript:; 이므로, img 태그의 src에서 카드 ID를 추출하거나
                # 상세보기 버튼의 경로를 확인해야 합니다.
                # 이미지 경로 예시: .../card/2749/card_img/... -> 여기서 2749가 ID
                img_tag = el.select_one(".card_img img")
                if img_tag and 'src' in img_tag.attrs:
                    src = img_tag['src']
                    # URL에서 숫자(ID) 부분 추출
                    card_id = src.split('/card/')[1].split('/')[0]
                    detail_url = f"https://www.card-gorilla.com/card/detail/{card_id}"
                else:
                    detail_url = "URL을 찾을 수 없음"

                card_data.append({
                    "name": name,
                    "corp": corp,
                    "detail_url": detail_url
                })
                
            except Exception as e:
                print(f"[항목 추출 에러] {e}")
                continue

    except Exception as e:
        print(f"[전체 크롤링 에러] {e}")
    finally:
        driver.quit()

    return card_data