from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUI:
    def test_page_loads(self, driver, base_url):
        driver.get(base_url)
        assert "University Timetable" in driver.title or "Vite" in driver.title
        
    def test_header_visible(self, driver, base_url):
        driver.get(base_url)
        header = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "header"))
        )
        assert "University Timetable Management System" in header.text
        
    def test_progress_bar_visible(self, driver, base_url):
        driver.get(base_url)
        progress_bar = driver.find_element(By.CLASS_NAME, "progress-bar")
        steps = progress_bar.find_elements(By.CLASS_NAME, "step")
        assert len(steps) == 3
        
    def test_chatbot_toggle(self, driver, base_url):
        driver.get(base_url)
        chatbot_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "chatbot-toggle"))
        )
        chatbot_btn.click()
        # Chatbot should appear
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chatbot"))
        )
