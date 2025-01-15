import csv
import multiprocessing
import os
import time

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

load_dotenv()


def setup_browser():
    """Initialize and return a Selenium WebDriver instance."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service("./chromedriver.exe")
    return webdriver.Chrome(service=service, options=options)


def login(browser, username, password):
    """Perform login with redirection handling."""
    redirected = False
    while True:
        # Step 1: Access the login page
        if not redirected:
            url = "https://scele.cs.ui.ac.id/login/index.php"
            browser.get(url)

        # Use BeautifulSoup to parse the page
        soup = BeautifulSoup(browser.page_source, 'html.parser')

        # Extract the logintoken
        token_input = soup.find("input", {"name": "logintoken"})
        if not token_input:
            print("No logintoken found. Exiting loop.")
            return False
        logintoken = token_input["value"]
        print(f"Extracted logintoken: {logintoken}")

        # Find and fill out the username and password fields
        username_field = browser.find_element(By.NAME, "username")
        password_field = browser.find_element(By.NAME, "password")

        username_field.send_keys(username)
        password_field.send_keys(password)

        # Submit the form
        login_button = browser.find_element(By.ID, "loginbtn")
        login_button.click()

        time.sleep(2)

        # Check if redirected back to login page
        if "login" in browser.current_url:
            print("Redirected to login page. Retrying...")
            redirected = True
        else:
            print("Logged in successfully.")
            return True  # Exit loop after successful login


def check_courses(start_id, end_id, results, lock):
    """Check courses in the given ID range and store results in a shared list."""
    browser = setup_browser()

    # Ambil username dan password dari environment variables
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    # Ensure login before starting the iteration
    if not login(browser, username, password):
        browser.quit()
        return

    for course_id in range(start_id, end_id + 1):
        enrol_url = f"https://scele.cs.ui.ac.id/enrol/index.php?id={course_id}"
        browser.get(enrol_url)

        soup = BeautifulSoup(browser.page_source, 'html.parser')
        result = {"course_id": course_id, "status": "", "details": ""}

        # Check if there's an error message
        error_box = soup.find("div", {"data-rel": "fatalerror", "class": "errorbox"})
        if error_box:
            error_message = error_box.find("p", {"class": "errormessage"}).text
            result["status"] = "Error"
            result["details"] = error_message
            print(f"Course ID {course_id}: Error - {error_message}")
        # Check if redirected to another page
        elif "course/view.php" in browser.current_url:
            soup = BeautifulSoup(browser.page_source, 'html.parser')  # Re-parse the new page
            course_header = soup.find("div", {"class": "page-header-headings"})
            if course_header:
                course_name = course_header.find("h1").text.strip()
                result["status"] = "Success"
                result["details"] = course_name
                print(f"Course ID {course_id}: Found course - {course_name}")
        # Check for the course name without redirect
        else:
            course_header = soup.find("div", {"class": "page-header-headings"})
            if course_header:
                course_name = course_header.find("h1").text.strip()
                result["status"] = "Success"
                result["details"] = course_name
                print(f"Course ID {course_id}: Found course - {course_name}")
            else:
                result["status"] = "No course"
                result["details"] = "No course found, but no error or redirect."
                print(f"Course ID {course_id}: No course found, but no error or redirect.")

        with lock:  # Ensure results are added in a thread-safe manner
            results.append(result)

    browser.quit()


def retry_missing_ids(missing_ids, results, lock):
    """Retry missing IDs in parallel and store results in a shared list."""
    num_processes = 8  # Number of parallel retry processes
    ids_per_process = len(missing_ids) // num_processes

    processes = []

    for i in range(num_processes):
        start_index = i * ids_per_process
        end_index = (i + 1) * ids_per_process if i != num_processes - 1 else len(missing_ids)
        p = multiprocessing.Process(target=check_courses,
                                    args=(missing_ids[start_index], missing_ids[end_index - 1], results, lock))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()


def find_missing_ids(total_ids, results):
    """Find and return missing IDs that are not in the results."""
    existing_ids = {result["course_id"] for result in results}
    return [course_id for course_id in range(1, total_ids + 1) if course_id not in existing_ids]


if __name__ == "__main__":
    num_processes = 8
    total_ids = 4096
    ids_per_process = total_ids // num_processes

    manager = multiprocessing.Manager()
    results = manager.list()  # Shared list for storing results across processes
    lock = multiprocessing.Lock()  # Lock for synchronizing access to results

    processes = []

    for i in range(num_processes):
        start_id = i * ids_per_process + 1
        end_id = (i + 1) * ids_per_process if i != num_processes - 1 else total_ids
        p = multiprocessing.Process(target=check_courses, args=(start_id, end_id, results, lock))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    # Retry missing IDs recursively until there are no missing IDs
    while True:
        missing_ids = find_missing_ids(total_ids, results)
        if not missing_ids:
            break
        print(f"Retrying missing IDs: {missing_ids}")
        retry_missing_ids(missing_ids, results, lock)

    # Sort results by course_id before exporting to CSV
    sorted_results = sorted(results, key=lambda x: x["course_id"])

    # Export results to CSV
    with open("courses_results.csv", "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["course_id", "status", "details"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(sorted_results)

    print("Results have been exported to courses_results.csv.")
