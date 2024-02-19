import os
import time
import warnings
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import boto3
import icalendar
import numpy as np
import pandas as pd
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

warnings.simplefilter(action="ignore", category=FutureWarning)


def get_html():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280x1696")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-client-side-phishing-detection")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.binary_location = "/opt/chrome-linux/chrome"

    service = Service(executable_path="/opt/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    ROSTER_WEBSITE = os.environ.get("ROSTER_WEBSITE")
    ROSTER_USERNAME = os.environ.get("ROSTER_USERNAME")
    ROSTER_PASSWORD = os.environ.get("ROSTER_PASSWORD")

    if not ROSTER_WEBSITE or not ROSTER_USERNAME or not ROSTER_PASSWORD:
        raise ValueError("Environment variables for the roster website, username, and password must be set.")

    html = []
    try:
        driver.get(f"{ROSTER_WEBSITE}/index.php")

        # Wait for the login input fields to be loaded
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "q22")))
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "q45")))

        # Fill in the login credentials
        driver.find_element(By.ID, "q22").send_keys(ROSTER_USERNAME)
        driver.find_element(By.ID, "q45").send_keys(ROSTER_PASSWORD)

        driver.execute_script("login();")

        expected_url = f"{ROSTER_WEBSITE}/index_main.php"

        WebDriverWait(driver, 1).until(EC.url_to_be(expected_url))
        if driver.current_url == expected_url:
            print("Login successful, redirected to dashboard.")
        else:
            print("Login failed, still on login page.")

        driver.get(f"{ROSTER_WEBSITE}/roster/index.php")
        if driver.current_url == f"{ROSTER_WEBSITE}/roster/index.php":
            print("Successfully navigated to the roster page.")
        else:
            print("Failed to navigate to the roster page.")

        previous_html = ""
        for _ in range(2):
            WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "shiftlist")))

            shiftlist_div = driver.find_element(By.ID, "shiftlist")
            current_html = shiftlist_div.get_attribute("outerHTML")

            if current_html != previous_html:
                html.append(current_html)
                previous_html = current_html
            else:
                print("Warning: Duplicate content detected. The page might not have updated as expected.")

            if _ < 1:
                driver.execute_script("rnext();")
                time.sleep(1)

        return html
    finally:
        driver.quit()


def get_shifts_dataframe(html) -> pd.DataFrame:
    soup = BeautifulSoup(html, "html.parser")  # type: ignore

    # Find all divs that represent individual shifts
    shift_divs = soup.find_all("div", style=lambda value: value and "background-color" in value)  # type: ignore

    dates = []
    times = []

    for div in shift_divs:
        # Extracting the date
        date_span = div.find("span", class_="ib5")
        dates.append(date_span.text if date_span else "")

        # Extracting the time (if available)
        time_span = div.find("span", class_="ib6")
        times.append(time_span.text if time_span else "")

    # Assuming the rest of your DataFrame creation and manipulation logic remains the same...
    shifts = pd.DataFrame(data={"date": dates, "time": times})
    shifts = shifts.replace("\xa0", np.nan)

    def extract_times(cell):
        if pd.isnull(cell) or cell.strip() == "":
            return (None, None)
        try:
            start, end = cell.split("-")
            return (start.strip(), end.strip())
        except ValueError:
            return (None, None)

    def update_end_date(row):
        if pd.isnull(row["startTime"]) or pd.isnull(row["endTime"]):
            return row["endTime"]

        # Parse the 'start' and 'end' times
        time_format = "%H:%M"
        try:
            start_time = pd.to_datetime(row["start"], format=time_format).time()
            end_time = pd.to_datetime(row["end"], format=time_format).time()
        except ValueError:  # In case 'start' or 'end' time is not provided or cannot be parsed
            return row["endTime"]

        # Combine the 'date' from 'startTime' with 'start' and 'end' times
        start_datetime = pd.Timestamp.combine(row["startTime"].date(), start_time)
        end_datetime = pd.Timestamp.combine(row["endTime"].date(), end_time)

        # If the 'end' time is before the 'start' time, adjust 'end_datetime' to the next day
        if end_datetime <= start_datetime:
            end_datetime += pd.Timedelta(days=1)

        return end_datetime

    shifts[["start", "end"]] = shifts["time"].apply(extract_times).apply(pd.Series)
    shifts = shifts.drop(["time"], axis=1)
    shifts["startTime"] = pd.to_datetime(shifts["date"] + " " + shifts["start"], format="%d/%m/%y %H:%M")
    shifts["endTime"] = pd.to_datetime(shifts["date"] + " " + shifts["end"], format="%d/%m/%y %H:%M")
    shifts["endTime"] = shifts.apply(update_end_date, axis=1)
    shifts["endTime"] = pd.to_datetime(shifts["endTime"])

    return shifts


def generate_calandar(shifts: pd.DataFrame):
    # get the month as a string fro mthe dataframe
    shifts["date"] = pd.to_datetime(shifts["date"], format="%d/%m/%y")
    month = shifts["date"].iloc[0].strftime("%B")

    cal = icalendar.Calendar()
    cal.add("prodid", "-//AutoCal//test.com//")
    cal.add("version", "2.0")

    for _, row in shifts.iterrows():
        if pd.isnull(row["start"]):
            continue

        event = icalendar.Event()
        event.add("summary", "RBHW")
        event.add("dtstart", row["startTime"])
        event.add("dtend", row["endTime"])
        cal.add_component(event)

    file_path = f"/tmp/{month}.ics"
    with open(file_path, "wb") as c:
        c.write(cal.to_ical())

    return file_path


def send_email(calendar_file_path: str):
    TO_EMAIL = os.environ.get("TO_EMAIL")
    FROM_EMAIL = os.environ.get("FROM_EMAIL")

    if not TO_EMAIL or not FROM_EMAIL:
        raise ValueError("Environment variables for the 'to' and 'from' email addresses must be set.")

    ses = boto3.client("ses")

    msg = MIMEMultipart("mixed")
    msg["Subject"] = "RBWH Roster"
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL

    msg_body = MIMEMultipart("alternative")
    month_name = calendar_file_path.split("/")[-1].replace(".ics", "")
    textpart = MIMEText(f"Hello, this is your roster for {month_name}.", _charset="UTF-8")

    msg_body.attach(textpart)
    msg.attach(msg_body)
    with open(calendar_file_path, "rb") as f:
        att = MIMEApplication(f.read())

    file_name = calendar_file_path.split("/")[-1]
    att.add_header("Content-Disposition", "attachment", filename=file_name)

    msg.attach(att)

    try:
        response = ses.send_raw_email(
            Source=msg["From"],
            Destinations=[msg["To"]],
            RawMessage={
                "Data": msg.as_string(),
            },
        )
        print(response["MessageId"])
    except ClientError as e:
        print(e.response["Error"]["Message"])


# def main():
#     html = get_html()
#     shifts = [get_shifts_dataframe(content) for content in html]
#     months = [generate_calandar(shift) for shift in shifts]
#     for month in months:
#         send_email(month)


# if __name__ == "__main__":
#     main()


def handler(event, context):
    html = get_html()
    shifts = [get_shifts_dataframe(content) for content in html]
    months = [generate_calandar(shift) for shift in shifts]
    for month in months:
        send_email(month)

    return {"statusCode": 200, "body": "Emails sent successfully"}
