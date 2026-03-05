# Selenium Automation Testing Guide

## Setup

1. **Install test dependencies:**
```bash
pip install -r tests/requirements.txt
```

2. **Ensure Chrome browser is installed**

3. **Start backend and frontend servers:**
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Running Tests

### Run all tests:
```bash
python run_tests.py
```

### Run specific test file:
```bash
pytest tests/test_ui.py -v
```

### Run with HTML report:
```bash
pytest tests/ -v --html=tests/report.html --self-contained-html
```

### Run specific test:
```bash
pytest tests/test_ui.py::TestUI::test_page_loads -v
```

## Test Structure

- `conftest.py` - Pytest fixtures (WebDriver setup)
- `test_ui.py` - UI component tests
- `test_workflow.py` - End-to-end workflow tests
- `page_objects.py` - Page Object Model classes

## Writing New Tests

Use Page Object Model pattern:

```python
from page_objects import HomePage

def test_example(driver, base_url):
    driver.get(base_url)
    home = HomePage(driver)
    assert "Timetable" in home.get_header_text()
```

## Tips

- Tests run on Chrome by default
- Implicit wait: 10 seconds
- HTML reports generated in `tests/report.html`
- Ensure servers are running before tests
