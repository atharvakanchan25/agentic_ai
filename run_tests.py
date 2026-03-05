import subprocess
import sys

def run_tests():
    print("Starting Selenium Tests...")
    print("=" * 50)
    
    # Run pytest with HTML report
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--html=tests/report.html",
        "--self-contained-html"
    ])
    
    if result.returncode == 0:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
    
    print(f"\nReport: tests/report.html")
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
