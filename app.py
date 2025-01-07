import random

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from flask_cors import CORS
import time
from webdriver_manager.chrome import ChromeDriverManager
import math


def create_webdriver():
    options = webdriver.ChromeOptions()
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    return webdriver.Chrome(service=service, options=options)


driver = create_webdriver()

app = Flask(__name__)
CORS(app)

jobs = []


def fetch_jobs(job_title, source="home"):
    global jobs
    jobs = []
    # to decide from how much page jobs will be fetched
    for page in range(1, 2):
        # To fetch jobs from Indeed
        extract_jobs_from_page(job_title, site='naukri', page=page)
        if source == "search bar":
            # To fetch jobs from Naukri
            extract_jobs_from_page(job_title, site='indeed', page=page)

    return jobs


def extract_jobs_from_page(job_title, site='indeed', page=1):
    base_url = ""
    if site == 'indeed':
        base_url = f"https://in.indeed.com/jobs?q={job_title}&start={(page - 1) * 10}"
    elif site == 'naukri':
        base_url = f"https://www.naukri.com/{job_title}-jobs-{page}"

    print(f"Fetching from {site} - Page {page}: {base_url}")
    driver.get(base_url)
    time.sleep(2)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    if site == 'indeed':
        job_listings = soup.find_all("div", class_="job_seen_beacon")

        for job in job_listings:
            job_id = job.find("a", class_="jcs-JobTitle")["data-jk"] if job.find("a", class_="jcs-JobTitle") else "N/A"
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
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "post_date": post_date.replace("PostedPosted", ""),
                "salary": salary,
                "rating": rating_value,
                "reviews": "reviews",
                "description": description_from_indeed,
                "link": f"https://in.indeed.com{follow_link_from_indeed}"
            })

    elif site == 'naukri':
        job_listings = soup.find_all("div", class_="srp-jobtuple-wrapper")

        for job in job_listings:
            job_id = job["data-job-id"] if "data-job-id" in job.attrs else "N/A"
            title_tag = job.find("a", class_="title")
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            follow_link_from_naukri = title_tag["href"] if title_tag and "href" in title_tag.attrs else "N/A"
            company = job.find("a", class_="comp-name").get_text(strip=True) if job.find("a",
                                                                                         class_="comp-name") else "N/A"
            location = job.find("span", class_="locWdth").get_text(strip=True) if job.find("span",
                                                                                           class_="locWdth") else "N/A"
            experience = job.find("span", class_="expwdth").get_text(strip=True) if job.find("span",
                                                                                             class_="expwdth") else "N/A"
            salary_from_naukri = job.find("span", class_="sal").get_text(strip=True) if job.find("span",
                                                                                                 class_="sal") else "N/A"
            description_from_naukri = job.find("span", class_="job-desc").get_text(strip=True) if job.find("span",
                                                                                                           class_="job-desc") else "N/A"
            post_date = job.find("span", class_="job-post-day").get_text(strip=True) if job.find("span",
                                                                                                 class_="job-post-day") else "N/A"
            rating_tag = job.find("a", class_="rating")
            rating = rating_tag.find("span", class_="main-2").get_text(strip=True) if rating_tag and rating_tag.find(
                "span", class_="main-2") else "N/A"
            reviews_tag = job.find("a", class_="review ver-line")
            reviews_from_naukri = reviews_tag.get_text(strip=True) if reviews_tag else "N/A"

            jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "post_date": post_date,
                "salary": salary_from_naukri,
                "rating": rating,
                "reviews": reviews_from_naukri.replace("Reviews", " "),
                "description": description_from_naukri,
                "link": follow_link_from_naukri
            })


def scrape_full_job_description(url):
    try:
        # driver = create_webdriver()
        driver.get(url)
        time.sleep(2)  # Adjust as necessary
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Extract and return job details here
    except Exception as e:
        print("Error while accessing WebDriver:", e)
        raise e

    print(f"fetching full details from: {url}")

    if ("indeed.com" in url):
        # Extract job ID
        job_id_tag = soup.find("meta", {"property": "indeed:jobKey"})
        job_id = job_id_tag["content"] if job_id_tag else "N/A"

        # Extract job title
        title_tag = soup.find("h1", class_="jobsearch-JobInfoHeader-title")
        title = title_tag.get_text(strip=True) if title_tag else "N/A"

        # Extract company name
        company_tag = soup.find("div", {"data-company-name": "true"})
        company = company_tag.get_text(strip=True) if company_tag else "N/A"

        # Extract job location
        location_tag = soup.find("div", {"data-testid": "inlineHeader-companyLocation"})
        location = location_tag.get_text(strip=True) if location_tag else "N/A"

        # Extract post date
        post_date_tag = soup.find("span", class_="jobsearch-HiringInsights-entry--bullet")
        post_date = post_date_tag.get_text(strip=True) if post_date_tag else "N/A"

        # Extract salary information
        salary_tag = soup.find("div", {"data-testid": "jobsearch-OtherJobDetailsContainer"})
        if salary_tag:
            salary_span = salary_tag.find("span", class_="css-19j1a75 eu4oa1w0")
            salary = salary_span.get_text(strip=True) if salary_span else "N/A"
        else:
            salary = "N/A"

        # Extract rating
        rating_tag = soup.find("div", class_="css-1unnuiz e37uo190")
        rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

        job_details = {
            "job_id": job_id,
            "title": title,
            "company": company,
            "location": location,
            "post_date": post_date,
            "salary": salary,
            "rating": rating,
            "reviews": "N/A",
            "openings": "N/A",
            "applicants": "N/A",
            "description": rating,
            "link": url
        }
        # Extract job description
        # Extract and format job description
        description_tag = soup.find("div", class_="jobsearch-JobComponent-description")
        if description_tag:
            job_description = description_tag.get_text(separator="\n").strip()
            # Split description into lines and add markers for headings and bullets
            formatted_description = []
            is_full_heading = 0
            for line in job_description.split('\n'):
                line = line.strip()
                if line == "Full job description":
                    is_full_heading = 1

                if is_full_heading == 0:
                    continue

                if ":" in line and len(line) < 25:  # Likely a heading
                    formatted_description.append("[HEADING]" + line)
                elif line:  # Regular content or bullet point
                    if len(line) > 2:
                        formatted_description.append("[BULLET]" + line)
            job_details['description'] = "\n".join(formatted_description)
        else:
            job_details['description'] = "N/A"

        # Construct link to job
        link = url

        # Store extracted details in a dictionary

        print(job_details['description'])
        print(job_details['title'])
        return job_details
    elif "naukri.com" in url:
        # Extracting job title
        title_tag = soup.find("h1", class_="styles_jd-header-title__rZwM1")
        title = title_tag.text.strip() if title_tag else None

        # Extracting company name
        company_tag = soup.find("div", class_="styles_jd-header-comp-name__MvqAI").find("a")
        company = company_tag.text.strip() if company_tag else None

        # Extracting rating and number of reviews
        rating_tag = soup.find("span", class_="styles_amb-rating__4UyFL")
        rating = rating_tag.text.strip() if rating_tag else "N/A"
        reviews_tag = soup.find("span", class_="styles_amb-reviews__0J1e3")
        reviews = reviews_tag.text.strip() if reviews_tag else "N/A"

        # Extracting experience
        experience_tag = soup.find("div", class_="styles_jhc__exp__k_giM")
        experience = experience_tag.text.strip() if experience_tag else "N/A"

        # Extracting salary
        salary_tag = soup.find("div", class_="styles_jhc__salary__jdfEC")
        salary = salary_tag.text.strip() if salary_tag else "N/A"

        # Extracting location
        location_tag = soup.find("span", class_="styles_jhc__location__W_pVs").find("a")
        location = location_tag.text.strip() if location_tag else "N/A"

        # Extracting posted date, openings, and applicants
        # Locate the container for job statistics first
        stats_container = soup.find("div", class_="styles_jhc__jd-stats__KrId0")

        # Initialize values to None in case any elements are missing
        posted_date, openings, applicants = None, None, None

        if stats_container:
            # Find all stats spans within the container
            stats_spans = stats_container.find_all("span", class_="styles_jhc__stat__PgY67")

            for stat in stats_spans:
                label = stat.find("label").text.strip() if stat.find("label") else ""

                if label == "Posted:":
                    posted_date = stat.find_next("span").text.strip()
                elif label == "Openings:":
                    openings = stat.find_next("span").text.strip()
                elif label == "Applicants:":
                    applicants = stat.find_next("span").text.strip()

        # print("Posted Date:", posted_date)
        # print("Openings:", openings)
        # print("Applicants:", applicants)

        import re

        # Extracting job description with line breaks for formatting
        description_tag = soup.find("div", class_="styles_JDC__dang-inner-html__h0K4t")
        description = description_tag.get_text(separator="\n").strip() if description_tag else None

        # Replace multiple \n with a single \n in the description
        description = re.sub(r'\n +', '\n', description) if description else ""

        # Extracting key skills and formatting them as a list with new lines
        skills_tags = soup.find_all("a", class_="styles_chip__7YCfG")
        key_skills = "\n".join([f"• {skill.text.strip()}" for skill in skills_tags])

        # Combine description and key skills with a header for key skills
        formatted_text = f"{description}\n\nKey Skills:\n{key_skills}"

        # Print or return extracted details
        job_details = {
            "job_id": "job_id",
            "title": title,
            "company": company,
            "location": location,
            "post_date": posted_date,
            "salary": salary,
            "rating": rating,
            "reviews": reviews,
            "openings": openings,
            "applicants": applicants,
            "description": formatted_text,
            "link": url
        }

        return job_details


@app.route('/home', methods=['GET'])
def show_jobs():
    try:
        job_title = request.args.get('job_title')
        jobs = fetch_jobs(job_title, "home")
        return jsonify(jobs)
    except Exception as e:
        global driver
        driver.quit()
        driver = create_webdriver()
        job_title = request.args.get('job_title')
        jobs = fetch_jobs(job_title)
        return jsonify(jobs)


@app.route('/jobs', methods=['GET'])
def search_jobs():
    try:
        job_title = request.args.get('job_title')
        print(job_title)
        jobs = fetch_jobs(job_title, "search bar")
        return jsonify(jobs)
    except Exception as e:
        global driver
        driver.quit()
        driver = create_webdriver()
        job_title = request.args.get('job_title')
        jobs = fetch_jobs(job_title)
        return jsonify(jobs)


@app.route('/getJobDescription', methods=['GET'])
def get_job_description():
    job_url = request.args.get("job_url")
    try:
        print(f"Url received: {job_url}")
        job = scrape_full_job_description(job_url)
        return jsonify(job)
    except Exception as e:
        # If the driver session is closed, reinitialize it
        print("Reinitializing driver...")
        global driver
        driver.quit()
        driver = create_webdriver()
        job = scrape_full_job_description(job_url)
        return jsonify(job)


print(fetch_jobs("Data Scientist", "Search bar"))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
