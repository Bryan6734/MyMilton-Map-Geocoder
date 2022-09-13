import json
import os
import matplotlib.pyplot as plt
import numpy as np
from gmplot import gmplot
from selenium import webdriver  # Google Chrome driver
import selenium.common.exceptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service  # Loading URL
from selenium.webdriver.common.by import By  # HTML Identifiers
from selenium.webdriver.support.select import Select
from sklearn.cluster import KMeans

## HTML Global Variable Declarations
USER_FIELD_NAME = "UserLogin"  # HTML identifier
PASSWORD_FIELD_NAME = "UserPassword"  # HTML identifier
SUBMIT_FIELD_NAME = "df"  # HTML identifier
DIRECTORY_URL = "https://mymustangs.milton.edu/student/directory/"

# Configure Selenium settings
chrome_options = Options()
chrome_options.add_argument("--window-size=950,800")

# Instantiate the Selenium Chrome Driver
service = Service(executable_path="/Users/bryansukidi/Desktop/CS Projects/chromedriver")
driver = webdriver.Chrome(service=service, options=chrome_options)
driver.implicitly_wait(3)

geographical_index = []

def main():
    with open('coordinates.json', 'r') as coordinates_file:
        coordinates = json.load(coordinates_file)

    [print(coordinate) for coordinate in coordinates]

    kmeans = get_kmeans_clustering(coordinates, k=6)
    # graph_coordinate_clusters(coordinates, kmeans)

    gmplot_coordinate_clusters(coordinates, kmeans, "student_locations")

# Load myMilton login credentials from a JSON file
def load_login():
    if os.path.exists('login_info.json'):
        with open('login_info.json', 'r') as login_info:
            login_info = json.load(login_info)
        return login_info['username'], login_info['password']
    else:
        return input("Username: "), input("Password: ")

# Posts login credentials to myMilton
def post_login():
    # Grab login credentials
    USERNAME, PASSWORD = load_login()

    # Open the myMilton login website
    driver.get("https://mymustangs.milton.edu/student/index.cfm?")
    print("Accessing Website: ", driver.title)

    # Wait 0.5 seconds for website loading time (Selenium is asynchronous)
    driver.implicitly_wait(0.5)

    # Post username to username text box
    print(">>> Entering USERNAME")
    username_field = driver.find_element(by=By.NAME, value=USER_FIELD_NAME)
    username_field.send_keys(USERNAME)

    print(">>> Entering PASSWORD")
    # Post password to password text box
    password_field = driver.find_element(by=By.NAME, value=PASSWORD_FIELD_NAME)
    password_field.send_keys(PASSWORD)

    print(">>> Submitting FORM")
    # Click submit button
    submit_button = driver.find_element(by=By.NAME, value=SUBMIT_FIELD_NAME)
    submit_button.click()

    # Validate Login
    print(">>> Validating Login")
    print("Accessing Website: ", driver.title)

# Open the myMilton geographical index from the directory page
def open_geographical_index():
    driver.get(DIRECTORY_URL)
    Select(driver.find_element(By.ID, value="indexes")).select_by_value(
        "1F463A2D0D081F2D161600242C2E4A")
    submit_button = driver.find_element(by=By.NAME, value="s")
    submit_button.click()

    new_url = driver.window_handles[1]
    driver.switch_to.window(new_url)

# Grab all student cities from the geographical index
def scrape_geographical_index():
    cities = []
    for row in range(2, 1145):
        try:
            address = driver.find_element(By.XPATH, check_geographical_column(row)).text
            if address and address != "" and address not in cities:
                print(address)
                cities.append(address)
        except selenium.common.exceptions.NoSuchElementException:
            print("Exception")
            pass

# Filter out all non-city addresses by checking row & column number with XPath
def check_geographical_column(row):
    try:
        return f"/html/body/table/tbody/tr[2]/td/table/tbody/tr[{row}]/td[2]"
    except selenium.common.exceptions.NoSuchElementException:
        pass

# Load geographical index from a JSON file
def load_geographical_index():
    with open('geographical_index.json', 'r') as geographical_index_file:
        return json.load(geographical_index_file)

def open_student_directory():
    driver.get(DIRECTORY_URL)
    Select(driver.find_element(By.ID, value="school")).select_by_value("19611C3D1D020E04070A")
    submit_button = driver.find_element(by=By.NAME, value="s")
    submit_button.click()

    new_url = driver.window_handles[1]
    driver.switch_to.window(new_url)

# Scrape student information
def scrape_student_info():
    students = [elem.text.split("\n") for elem in driver.find_elements(by=By.TAG_NAME, value="td")[3:]]
    addresses = []

    for student in students:
        if student == '':
            continue
        for attribute in student:
            print(attribute)
            if validate_address(attribute):
                addresses.append(f"{student[student.index(attribute) - 1]} {attribute}")
                print(f"{student[student.index(attribute) - 1]} {attribute}")
                break
    return addresses

reg_cities = load_geographical_index()

def validate_address(element):
    if element and element != "" and (
            element.split(" ")[0] in reg_cities or " ".join(element.split(" ")[0:2]) in reg_cities):
        print(f"Valid thru REG CITIES: {element}")
        return True
    else:
        print("Invalid: {}".format(element))
        return False

# CLUSTERING STUDENT ADDRESSES

def graph_coordinate_clusters(coordinates, kmeans):
    coordinates = np.array(coordinates)

    plt.scatter(coordinates[:, 0], coordinates[:, 1], c=kmeans.labels_, cmap='rainbow')
    plt.xlabel('Latitude')
    plt.ylabel('Longitude')
    plt.title('K-Means Clustering on Student Addresses')
    plt.show()

def get_kmeans_clustering(coordinates, k):
    return KMeans(n_clusters=k, random_state=0).fit(coordinates)

# Plot all coordinates
def gmplot_coordinate_clusters(coordinates, kmeans, filename="kmeans_clustering"):
    gmap = gmplot.GoogleMapPlotter(42.389118, -71.097153, 16)  # Create default location

    latitudes = [coordinate[0] for coordinate in coordinates]
    longitudes = [coordinate[1] for coordinate in coordinates]
    cluster_num = [kmeans.labels_[i] for i in range(len(coordinates))]
    cluster_colors = ['red', 'blue', 'green', 'purple', 'orange', 'yellow', 'pink', 'white']

    for lat, long, cluster in zip(latitudes, longitudes, cluster_num):
        gmap.marker(lat, long, color=cluster_colors[cluster], title=f"{lat, long, cluster}")

    gmap.draw(f"/Users/bryansukidi/Desktop/CS Projects/python/MyMilton-Map-Geocoder/{filename}.html")

if __name__ == '__main__':
    main()
