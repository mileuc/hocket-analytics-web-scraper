from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException
import pandas as pd
import time

CHROME_DRIVER_PATH = "C:\Development\chromedriver.exe"
STAT_URL = "https://www.naturalstattrick.com/playerteams.php?stdoi=oi"


class NaturalStatBot:
    def __init__(self):
        self.driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH)
        self.url = ""
        self.dict = {}

    def set_filters(self):
        self.driver.get(STAT_URL)
        time.sleep(5)
        select_from_season = Select(self.driver.find_element_by_name("fromseason"))
        select_from_season.select_by_visible_text("2020-2021")
        select_to_season = Select(self.driver.find_element_by_name("thruseason"))
        select_to_season.select_by_visible_text("2020-2021")
        select_season_format = Select(self.driver.find_element_by_name("stype"))
        select_season_format.select_by_visible_text("Regular Season")
        select_rate_option = Select(self.driver.find_element_by_name("rate"))
        select_rate_option.select_by_visible_text("Rates")
        open_more_filters = self.driver.find_element_by_id("filterlb")
        open_more_filters.click()
        time.sleep(3)
        select_team_option = Select(self.driver.find_element_by_name("team"))
        select_team_option.select_by_visible_text("Calgary Flames")
        time.sleep(3)
        minimum_toi_input = self.driver.find_element_by_name("toi")
        minimum_toi_input.clear()
        minimum_toi_input.send_keys("100")
        time.sleep(3)
        form_inputs = self.driver.find_elements_by_css_selector("form input")
        # print(form_inputs)
        for form_input in form_inputs:
            if form_input.get_attribute("type") == "submit":
                form_input.click()
        self.url = self.driver.current_url

    def create_csv(self):
        response = requests.get(self.url)
        contents = response.text
        soup = BeautifulSoup(contents, "html.parser")

        header_names = []
        header_num = 0
        header_row = soup.find(name="thead")
        # print(header_row)
        headers = soup.find_all(name="th")
        num_of_fields = len(headers)
        print(num_of_fields)     # should equal 54, as in each row will have 54 fields
        for header in headers:
            if header_num == 0:
                header_name = "ID"
            else:
                header_name = header.text
            header_num += 1
            print(f"{header_num}. {header_name}")
            header_names.append((header_name, []))  # append a tuple with the header name and an empty array


        table = soup.find(id="players")
        table_body = table.find(name="tbody")
        data_rows = table_body.find_all(name="tr")
        for row in data_rows:
            data_values = row.find_all(name="td")
            # if row is not of the same size as number of fields in header, it's not from our table
            if len(data_values) != num_of_fields:
                break
            col_index = 0
            for value in data_values:
                data_text = value.text
                # if col_index > 0:
                try:
                    if col_index > 3:  # Every field after Games Played should have two decimal places
                        data_num = float(data_text)
                        header_names[col_index][1].append('{:.2f}'.format(round(data_num, 2)))  # keep trailing zeros
                    else:   # Games Played Field (which should be an integer)
                        data_num = int(data_text)
                        header_names[col_index][1].append(data_num)
                    # if header_names[col_index][0] == "TOI" or header_names[col_index][0] == "TOI/GP":
                    #     data_time = datetime.strptime(data_text, "%M:%S")
                    #     header_names[col_index][1].append(round(data_time, 2))
                    # else:
                    #     data_num = int(data_text)
                    #     header_names[col_index][1].append(data_num)
                except (ValueError, TypeError):  # If the field is non-numerical, like Player, Position
                    header_names[col_index][1].append(data_text)
                # append data to empty list of each column
                col_index += 1

        # check that each column has the same number of entries
        print([len(column_data) for (title, column_data) in header_names])
        print(header_names)

        data_dict = {header: data for (header, data) in header_names}
        df = pd.DataFrame(data_dict)
        print(df.head())
        df.to_csv("flames_2020-21_player_data.csv", encoding='utf-8', index=False)

bot = NaturalStatBot()
bot.set_filters()
bot.create_csv()

# df = pd.read_csv(