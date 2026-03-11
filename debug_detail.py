from selenium import webdriver
from selenium.webdriver.common.by import By
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1280,900")
driver = webdriver.Chrome(options=options)

driver.get("https://www.card-gorilla.com/card/detail/2749")
time.sleep(2)

benefits = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
print(f"총 dl 개수: {len(benefits)}")

# dl[0] 클릭 전 전체 HTML 확인
print("\n[클릭 전] dl[0] outerHTML:")
print(benefits[0].get_attribute('outerHTML')[:800])

# dl[0] 클릭
benefits[0].click()
time.sleep(1)

# 클릭 후 다시 가져오기
benefits = driver.find_elements(By.CSS_SELECTOR, "div.bene_area dl")
print("\n[클릭 후] dl[0] outerHTML:")
print(benefits[0].get_attribute('outerHTML')[:1500])

driver.quit()