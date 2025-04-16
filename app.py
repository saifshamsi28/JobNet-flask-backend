import time
import random
import pickle
import re

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import docx
import re
import spacy
from nltk.corpus import stopwords
from flask import Flask, request, jsonify
import os
from resume_parser import extract_resume_info

app = Flask(__name__)
CORS(app)


def create_webdriver():
    options = Options()

    # Optional: Disable headless mode for debugging
    options.add_argument('--headless')  # Uncomment for production
    options.add_argument('--no-sandbox')  # Disable sandbox (required for environments like Render)
    options.add_argument('--disable-dev-shm-usage')  # Reduce memory usage issues
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920x1080')
    options.add_argument('--disable-blink-features=AutomationControlled')

    # Random user-agents to avoid detection
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    ]
    random_user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={random_user_agent}")

    # Disable automation flags to reduce detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)

    # Bypass WebDriver detection
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """
        }
    )
    return driver

def save_cookies(driver, filename="cookies.pkl"):
    cookies = driver.get_cookies()
    with open(filename, "wb") as file:
        pickle.dump(cookies, file)

def load_cookies(driver, filename="cookies.pkl"):
    try:
        with open(filename, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
    except FileNotFoundError:
        print("No saved cookies found.")

# def scrape_full_job_description(url):
    # driver = create_webdriver()
    #
    # try:
    #     # Step 1: Visit the main page to load initial cookies
    #     driver.get("https://www.indeed.com/")
    #     time.sleep(random.uniform(2, 5))  # Random sleep to mimic human behavior
    #
    #     # Step 2: Load cookies if available
    #     load_cookies(driver)
    #
    #     # Step 3: Visit the job URL
    #     driver.get(url)
    #     time.sleep(random.uniform(5, 10))  # Wait for potential CAPTCHA or page loading
    #
    #     # Step 4: Save cookies to persist the session
    #     save_cookies(driver)
    #
    #     # Step 5: Extract job details using BeautifulSoup
    #     WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    #     soup = BeautifulSoup(driver.page_source, 'html.parser')
    #
    #     # Extract job details
    #     id_tag = soup.find("meta", {"property": "indeed:jobKey"})
    #     id = id_tag["content"] if id_tag else "N/A"
    #
    #     title_tag = soup.find("h1", class_="jobsearch-JobInfoHeader-title")
    #     title = title_tag.get_text(strip=True) if title_tag else "N/A"
    #
    #     company_tag = soup.find("div", {"data-company-name": "true"})
    #     company = company_tag.get_text(strip=True) if company_tag else "N/A"
    #
    #     location_tag = soup.find("div", {"data-testid": "inlineHeader-companyLocation"})
    #     location = location_tag.get_text(strip=True) if location_tag else "N/A"
    #
    #     post_date_tag = soup.find("span", class_="jobsearch-HiringInsights-entry--bullet")
    #     post_date = post_date_tag.get_text(strip=True) if post_date_tag else "N/A"
    #
    #     salary_tag = soup.find("div", {"data-testid": "jobsearch-JobInfoHeader-salary"})
    #     salary = salary_tag.get_text(strip=True) if salary_tag else "N/A"
    #
    #     rating_tag = soup.find("div", class_="css-1unnuiz e37uo190")
    #     rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"
    #
    #     description_tag = soup.find("div", class_=re.compile(r"jobsearch-JobComponent-description"))
    #     description = str(description_tag) if description_tag else "N/A"
    #
    #     job_details = {
    #         "id": id,
    #         "title": title,
    #         "company": company,
    #         "location": location,
    #         "post_date": post_date,
    #         "salary": salary,
    #         "rating": rating,
    #         "description": description,
    #         "link": url
    #     }
    #
    #     print(job_details)
    #     return job_details
    #
    # finally:
    #     driver.quit()

driver = create_webdriver()

jobs = []

def fetch_jobs(job_title, source="home"):
    global jobs
    jobs = []

    # to decide from how much page jobs will be fetched
    # for page in range(1, 3):

        # Fetch jobs from Indeed if the source is "search bar"
        # if source == "search bar" or source == "home":
        #     extract_jobs_from_page(job_title)
        #     break
        # else:
            # Fetch jobs from Naukri
    extract_jobs_from_page(job_title, site='naukri')

    return jobs


def extract_jobs_from_home_page():
    """
    This function loads the Naukri home page, scrolls to load the popular jobs,
    and then extracts each job's details (logo, created date, job title, job link,
    company name, rating, location, and experience) from the 'popular-jobs-container'.
    """
    # jobs = []  # local list to store job details
    # driver = None
    # print("calling home page method")
    driver = create_webdriver()

    try:
        home_url = "https://www.indeed.com"
        print(f"Fetching details from: {home_url}")
        driver.get(home_url)

        time.sleep(5)  # Wait for the page to load

        # Scroll multiple times to load dynamic content
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, document.body.scrollHeight/3);")
            time.sleep(3)

        # Click a button if necessary to load jobs (modify selector as needed)
        try:
            button = driver.find_element(By.XPATH, "//button[contains(text(),'View All Jobs')]")
            if button:
                button.click()
                time.sleep(5)  # Wait for jobs to load
        except NoSuchElementException:
            print("No button found, continuing...")

        soup = BeautifulSoup(driver.page_source, "html.parser")
        print()

        # Find the "popular jobs" section
        popular_jobs_container = soup.find("div", class_="popular-jobs-container")
        print(f"Popular jobs container: {popular_jobs_container}")

        if not popular_jobs_container:
            print("No popular jobs container found on the home page.")
            return jobs

        # Find all job cards
        job_cards = popular_jobs_container.find_all("div", class_="swiper-slide popular-jobs-chip")
        for card in job_cards:
            logo_url = ""
            created_date = ""

            # Extract logo
            logo_container = card.find("div", class_="logo-container")
            if logo_container:
                comp_logo_div = logo_container.find("div", class_="comp-logo")
                if comp_logo_div:
                    logo_img = comp_logo_div.find("img")
                    if logo_img:
                        logo_url = logo_img.get("src", "")

                created_date_tag = logo_container.find("span", class_="created-date")
                if created_date_tag:
                    created_date = created_date_tag.get_text(strip=True)

            # Extract Job Title and Link
            job_title = ""
            job_link = ""
            job_title_tag = card.find("a", class_="job-title")
            if job_title_tag:
                job_title = job_title_tag.get_text(strip=True)
                job_link = job_title_tag.get("href", "")
                if job_link.startswith("/"):
                    job_link = "https://www.naukri.com" + job_link

            # Extract Company Name
            company_name = card.find("a", class_="comp-name").get_text(strip=True) if card.find("a", class_="comp-name") else "N/A"

            # Extract Job Location
            location_tag = card.find("span", class_="locWdth")
            location = location_tag.get_text(strip=True) if location_tag else "N/A"

            jobs.append({
                "title": job_title,
                "company": company_name,
                "location": location,
                "logo": logo_url,
                "created_date": created_date,
                "link": job_link
            })

            print(jobs)
        return jobs

    except Exception as e:
        print(f"Error fetching popular jobs: {str(e)}")
        return []

    finally:
        driver.quit()



def extract_jobs_from_page(job_title, site='indeed', page=1):
    local_driver = None
    try:
        base_url = ""
        if site == 'indeed':
            base_url = f"https://in.indeed.com/jobs?q={job_title}&start={(page - 1) * 3}"
        elif site == 'naukri':
            job_title_encoded = job_title.replace(" ", "%20")  # Encode spaces properly
            base_url = f"https://www.naukri.com/{job_title_encoded}-jobs-in-india?k={job_title_encoded}&l=india&page={page}"

        print(f"Fetching from {site} - Page {page}: {base_url}")
        local_driver = create_webdriver()
        local_driver.get(base_url)
        time.sleep(3)
        local_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        soup = BeautifulSoup(local_driver.page_source, "html.parser")

        if site == 'indeed':
            job_listings = soup.find_all("div", class_="job_seen_beacon")

            for job in job_listings:
                id = job.find("a", class_="jcs-JobTitle")["data-jk"] if job.find("a", class_="jcs-JobTitle") else "N/A"
                title_tag = job.find("h2", class_="jobTitle")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                follow_link_from_indeed = title_tag.find("a")["href"] if title_tag and title_tag.find("a") else "N/A"
                company = job.find("span", {"data-testid": "company-name"}).get_text(strip=True) if job.find("span", {
                    "data-testid": "company-name"}) else "N/A"
                location = job.find("div", {"data-testid": "text-location"}).get_text(strip=True) if job.find("div", {
                    "data-testid": "text-location"}) else "N/A"
                post_date = job.find("span", {"data-testid": "myJobsStateDate"}).get_text(strip=True) if job.find("span", {
                    "data-testid": "myJobsStateDate"}) else "N/A"
                salary = job.find("div", class_="salary-snippet-container").get_text(strip=True) if job.find("div",
                                                                                                             class_="salary-snippet-container") else "N/A"
                rating_value = job.find("span", {"aria-hidden": "true"}).get_text(strip=True) if job.find("span", {
                    "aria-hidden": "true"}) else "N/A"
                description_list = job.find("div", class_="css-156d248 eu4oa1w0")
                description_from_indeed = description_list.get_text(strip=True) if description_list else "N/A"

                jobs.append({
                    "id": id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "post_date": post_date.replace("PostedPosted", ""),
                    "salary": salary,
                    "rating": rating_value,
                    "reviews": "reviews",
                    "description": description_from_indeed,
                    "full_description": None,
                    "link": f"https://in.indeed.com{follow_link_from_indeed}"
                })

        elif site == 'naukri':
            job_listings = soup.find_all("div", class_="srp-jobtuple-wrapper")

            for job in job_listings:
                # Extract job ID from the URL if not found directly in attributes
                follow_link_from_naukri = job.find("a", class_="title")["href"] if job.find("a", class_="title") else "N/A"
                id = job.get("data-job-id", None) or (follow_link_from_naukri.split("-")[-1] if follow_link_from_naukri != "N/A" else "N/A")

                # The rest of the job parsing remains the same
                title_tag = job.find("a", class_="title")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"
                company = job.find("a", class_="comp-name").get_text(strip=True) if job.find("a", class_="comp-name") else "N/A"
                location = job.find("span", class_="locWdth").get_text(strip=True) if job.find("span", class_="locWdth") else "N/A"
                experience = job.find("span", class_="expwdth").get_text(strip=True) if job.find("span", class_="expwdth") else "N/A"
                salary_from_naukri = job.find("span", class_="sal").get_text(strip=True) if job.find("span", class_="sal") else "N/A"
                description_from_naukri = job.find("span", class_="job-desc").get_text(strip=True) if job.find("span", class_="job-desc") else "N/A"
                post_date = job.find("span", class_="job-post-day").get_text(strip=True) if job.find("span", class_="job-post-day") else "N/A"
                rating_tag = job.find("a", class_="rating")
                rating = rating_tag.find("span", class_="main-2").get_text(strip=True) if rating_tag and rating_tag.find("span", class_="main-2") else "N/A"
                reviews_tag = job.find("a", class_="review ver-line")
                reviews_from_naukri = reviews_tag.get_text(strip=True) if reviews_tag else "N/A"

                jobs.append({
                    "id": id,
                    "title": title,
                    "company": company,
                    "location": location,
                    "post_date": post_date,
                    "salary": salary_from_naukri,
                    "rating": rating,
                    "reviews": reviews_from_naukri.replace("Reviews", " "),
                    "description": description_from_naukri,
                    "full_description": None,
                    "link": follow_link_from_naukri
                })
    except Exception as e:
        print(f"Error during scraping: {e}")
        return {"error": str(e), "job title ": job_title}

    finally:
        if local_driver:
            local_driver.quit()


def scrape_full_job_description(url):
        driver = create_webdriver()
        try:
            # Step 1: Visit the main page to load initial cookies
            # driver.get("https://in.indeed.com")

            # Only set cookies for the correct domain
            # for cookie in cook:
            #     driver.add_cookie({
            #         'name': cookie['name'],
            #         'value': cookie['value'],
            #         'domain': 'in.indeed.com'  # Make sure the domain matches
            #     })

            # time.sleep(random.uniform(6, 10))  # Random sleep to mimic human behavior

            # Step 2: Load cookies if available
            # load_cookies(driver)

            # Step 3: Visit the job URL
            driver.get(url)
            time.sleep(5)
            # time.sleep(random.uniform(5, 10))  # Wait for potential CAPTCHA or page loading

            # Step 4: Save cookies to persist the session
            # save_cookies(driver)

            # Step 5: Extract job details using BeautifulSoup
            # WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            # print(f"sout: {soup}")
            if "indeed.com" in url:
                # Extract job details
                id_tag = soup.find("meta", {"property": "indeed:jobKey"})
                id = id_tag["content"] if id_tag else "N/A"

                title_tag = soup.find("h1", class_="jobsearch-JobInfoHeader-title")
                title = title_tag.get_text(strip=True) if title_tag else "N/A"

                company_tag = soup.find("div", {"data-company-name": "true"})
                company = company_tag.get_text(strip=True) if company_tag else "N/A"

                location_tag = soup.find("div", {"data-testid": "inlineHeader-companyLocation"})
                location = location_tag.get_text(strip=True) if location_tag else "N/A"

                post_date_tag = soup.find("span", class_="jobsearch-HiringInsights-entry--bullet")
                post_date = post_date_tag.get_text(strip=True) if post_date_tag else "N/A"

                salary_tag = soup.find("div", {"data-testid": "jobsearch-JobInfoHeader-salary"})
                salary = salary_tag.get_text(strip=True) if salary_tag else "N/A"

                rating_tag = soup.find("div", class_="css-1unnuiz e37uo190")
                rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

                description_tag = soup.find("div", class_=re.compile(r"jobsearch-JobComponent-description"))
                description = str(description_tag) if description_tag else "N/A"

                job_details = {
                    "id": "N/A",
                    "title": title,
                    "company": company,
                    "location": location,
                    "post_date": post_date,
                    "salary": salary,
                    "rating": rating,
                    "reviews": "",
                    "openings": "openings",
                    "applicants": "applicants",
                    "description": description,
                    "full_description": None,
                    "link": url
                }

                print(job_details)
                return job_details

            elif "naukri.com" in url:
                # Naukri job details extraction
                title_tag = soup.find("h1", class_="styles_jd-header-title__rZwM1")
                title = title_tag.text.strip() if title_tag else "N/A"

                company_tag = soup.find("div", class_="styles_jd-header-comp-name__MvqAI").find("a")
                company = company_tag.text.strip() if company_tag else "N/A"

                rating_tag = soup.find("span", class_="styles_amb-rating__4UyFL")
                rating = rating_tag.text.strip() if rating_tag else "N/A"
                reviews_tag = soup.find("span", class_="styles_amb-reviews__0J1e3")
                reviews = reviews_tag.text.strip() if reviews_tag else "N/A"

                experience_tag = soup.find("div", class_="styles_jhc__exp__k_giM")
                experience = experience_tag.text.strip() if experience_tag else "N/A"

                salary_tag = soup.find("div", class_="styles_jhc__salary__jdfEC")
                salary = salary_tag.text.strip() if salary_tag else "N/A"

                location_tag = soup.find("span", class_="styles_jhc__location__W_pVs").find("a")
                location = location_tag.text.strip() if location_tag else "N/A"

                stats_container = soup.find("div", class_="styles_jhc__jd-stats__KrId0")
                posted_date, openings, applicants = "N/A", "N/A", "N/A"
                if stats_container:
                    stats_spans = stats_container.find_all("span", class_="styles_jhc__stat__PgY67")
                    for stat in stats_spans:
                        label = stat.find("label").text.strip() if stat.find("label") else ""
                        if label == "Posted:":
                            posted_date = stat.find_next("span").text.strip()
                        elif label == "Openings:":
                            openings = stat.find_next("span").text.strip()
                        elif label == "Applicants:":
                            applicants = stat.find_next("span").text.strip()

                # description_tag = soup.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
                # description = description_tag.get_text(separator="\n").strip() if description_tag else "N/A"
                description_tag = soup.find("section", class_=re.compile(r"styles_job-desc-container."))
                description = str(description_tag) if description_tag else "N/A"
                # print(f"desc tag with html: {description_tag}")
                print(f"desc with html: {description}")
                # print(description)
                # description = re.sub(r'\n +', '\n', description)
                #
                # skills_tags = soup.find_all("a", class_="styles_chip__7YCfG")
                # key_skills = "\n".join([f"• {skill.text.strip()}" for skill in skills_tags])
                #
                # formatted_text = f"{description}\n\nKey Skills:\n{key_skills}"
                # print(f"description: {description}")

                job_details = {
                    "id": "N/A",
                    "title": title,
                    "company": company,
                    "location": location,
                    "post_date": posted_date,
                    "salary": salary,
                    "rating": rating,
                    "reviews": reviews,
                    "openings": openings,
                    "applicants": applicants,
                    "description": description,
                    "full_description": description,
                    "link": url
                }
            else:
                raise ValueError("Unsupported job URL")

            return job_details

        except Exception as e:
            print(f"Error during scraping: {e}")
            return {"error": str(e), "url": url}

        finally:
            if driver:
                driver.quit()


@app.route('/home', methods=['GET'])
def show_jobs():
    try:
        job_title = request.args.get('job_title')
        jobs = fetch_jobs(job_title, "home")
        print(f"returned number of jobs: {len(jobs)}")
        return jsonify(jobs), 200
    except Exception as e:
        print(f"Error fetching jobs : {str(e)}")
        return jsonify({"error": "Failed to fetch job details"}), 500
    finally:
        if driver is not None:
            driver.quit()


@app.route('/jobs', methods=['GET'])
def search_jobs():
    try:
        job_title = request.args.get('job_title')
        print(job_title)
        jobs = fetch_jobs(job_title, "search bar")
        print(f"returned number of jobs: {len(jobs)}")
        return jsonify(jobs), 200
    except Exception as e:
        print(f"Error fetching jobs : {str(e)}")
        return jsonify({"error": "Failed to fetch job details"}), 500
    finally:
        if driver is not None:
            driver.quit()


@app.route('/url', methods=['GET'])
def get_job_description():
    job_url = request.args.get("url")
    try:
        job_url = job_url.strip()  # Remove any trailing newlines or spaces
        print(f"Url received: {job_url}")

        job = scrape_full_job_description(job_url)
        if job:
            return jsonify(job), 200  # Return success with job details
        else:
            return jsonify({"error": "Failed to fetch job details"}), 500  # Indicate failure to fetch job details
    except Exception as e:
        print(f"Error fetching job description: {str(e)}")
        return jsonify({"error": "An error occurred while processing the request"}), 500
    finally:
        if driver is not None:
            driver.quit()

#resume handling feature
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/parse-resume', methods=['POST'])
def parse_resume():
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No resume file uploaded'}), 400

        resume_file = request.files['resume']
        print(f"Received resume file: {resume_file.filename}")

        filename = resume_file.filename.lower()

        # Save temporarily for parsing
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        resume_file.save(temp_path)

        extracted_info = extract_resume_info(temp_path)

        # Cleanup
        os.remove(temp_path)

        return jsonify(extracted_info), 200

    except Exception as e:
        print(f"Error parsing resume: {str(e)}")
        return jsonify({'error': str(e)}), 500

# url="https://in.indeed.com/viewjob?cmp=Hyeongshin-Automotive-Industry&t=Java+Developer&jk=5af65e630dccdc9c&xpse=SoBf67I31HUmb2W3VJ0LbzkdCdPP&xfps=eb45e92e-ff44-4a9d-acc0-9c52c042a0d7&xkcb=SoBD67M327IF5FAx4r0IbzkdCdPP&vjs=3"
# print(scrape_full_job_description(url))

# print(extract_jobs_from_home_page())
# print(fetch_jobs("android developer","home"))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
