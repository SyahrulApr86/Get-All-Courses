## Course Scraper using Selenium and Multiprocessing

This project is a Python-based web scraper designed to automate the process of retrieving information about courses from the SCELE website using Selenium, BeautifulSoup, and multiprocessing.

### Features
- **Parallel course checking**: Utilizes Python's `multiprocessing` module to scrape multiple course pages in parallel, significantly reducing execution time.
- **Retry mechanism**: Automatically retries scraping for any missing course IDs that may have been skipped or encountered errors.
- **Headless browser**: Uses Selenium in headless mode to improve performance.
- **CSV export**: Exports the collected course data into a CSV file.
- **Environment variable support**: Username and password are securely loaded from a `.env` file.

---

## Prerequisites

1. **Python 3.8+**
2. **Google Chrome**
3. **ChromeDriver**
4. **Required Python packages**:

   Install the required packages using the following command:
   ```bash
   pip install -r requirements.txt
   ```

---

## Setup

1. **Create a `.env` file** in the root directory of the project and add your SCELE credentials:
   ```plaintext
   USERNAME=your_username
   PASSWORD=your_password
   ```

2. **Ensure ChromeDriver is installed and available**.

3. **Run the script**:
   ```bash
   python scraper.py
   ```

---

## How It Works

### 1. Browser Setup
The script initializes a headless Selenium WebDriver using the following options:
- `--headless`: Runs the browser in headless mode (without a GUI).
- `--disable-gpu`: Disables GPU acceleration.
- `--no-sandbox`: Disables the sandbox mode.

### 2. Login Process
The `login()` function:
- Opens the login page of the SCELE website.
- Extracts the `logintoken` using BeautifulSoup.
- Fills in the username and password fields.
- Submits the form and checks if the login was successful.

### 3. Course Checking
The `check_courses()` function:
- Iterates over a range of course IDs.
- Sends a request to the enrollment page for each course.
- Parses the response using BeautifulSoup to extract the course name or error message.
- Stores the result in a shared list (`results`).

### 4. Multiprocessing
The script divides the total range of course IDs into smaller chunks and assigns each chunk to a separate process using `multiprocessing.Process`. This allows the scraper to run multiple processes in parallel, improving efficiency.

### 5. Retry Mechanism
After the initial scraping, the script checks for any missing course IDs and retries them in parallel until all IDs have been successfully processed.

### 6. CSV Export
Once all courses have been checked, the results are sorted by `course_id` and written to a CSV file named `courses_results.csv`.

---

## Output
The script generates a CSV file with the following columns:
- `course_id`: The ID of the course.
- `status`: The status of the course retrieval (e.g., "Success", "Error", "No course").
- `details`: Additional details, such as the course name or error message.

---

## Example Output
Here is an example of the CSV file generated by the script:

```csv
course_id,status,details
1,Error,Course not found
2,Success,[Reg] Pemrograman Lanjut (A)
3,No course,No course found, but no error or redirect.
...
```

---

## Customization
- **Number of processes**: You can change the number of parallel processes by modifying the `num_processes` variable.
- **Range of course IDs**: The range of course IDs to check can be adjusted by changing `total_ids`.

---

## Troubleshooting

1. **ChromeDriver issues**: If you encounter errors related to ChromeDriver, ensure that your version of Chrome matches the version of ChromeDriver managed by `webdriver-manager`.

2. **Login errors**: If the script fails to log in, double-check your credentials in the `.env` file.

---

## License
This project is licensed under the MIT License.

