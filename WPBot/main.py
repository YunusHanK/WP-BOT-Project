import shutil
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
import time
import re
import os
from datetime import datetime
from ldap3 import Server, Connection, ALL, NTLM
import logging
import zipfile
import schedule


#-------------------------------------------Logging Area-------------------------------------------------------------------------------------


# Global variables
temp_dir = os.environ.get('TEMP', '/tmp')
log_dir = os.path.join(temp_dir, 'WPBot Log')
MAX_LOG_LINES = 20000
LOG_FILE_BASE = 'WPBot'
LOG_FILE_EXT = '.log'

# Create directory if it does not exist
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

def get_next_log_file():
    logcounter  = 1
    while True:
        log_file = os.path.join(log_dir, f"{LOG_FILE_BASE}_{logcounter}{LOG_FILE_EXT}")
        if not os.path.exists(log_file) or sum(1 for _ in open(log_file)) < MAX_LOG_LINES:
            return log_file
        logcounter += 1

def zip_log_file(log_file):
    with open(log_file) as f:
        lines = f.readlines()
        if lines:
            first_line = lines[0]
            last_line = lines[-1]
            first_date_str = first_line.split(' - ')[0]
            last_date_str = last_line.split(' - ')[0]
            first_date = datetime.strptime(first_date_str, '%Y-%m-%d %H:%M:%S,%f')
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d %H:%M:%S,%f')
            base_zip_file_name = f"{first_date.strftime('%d-%m-%Y')}_{last_date.strftime('%d-%m-%Y')}"
            
            counter = 1
            zip_file_name = f"{base_zip_file_name}.zip"
            while os.path.exists(os.path.join(log_dir, zip_file_name)):
                zip_file_name = f"{base_zip_file_name}({counter}).zip"
                counter += 1
                
            zip_file_path = os.path.join(log_dir, zip_file_name)
            with zipfile.ZipFile(zip_file_path, 'w') as zipf:
                zipf.write(log_file, os.path.basename(log_file))
            os.remove(log_file)

def setup_logging():
    log_file = get_next_log_file()
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

def log_and_print(message):
    global MAX_LOG_LINES
    # Check if logging is already configured
    if not logging.getLogger().handlers:
        setup_logging()
    logging.info(message)
    print(message)
    control_zip()

def check_and_zip_logs():
    global log_dir, MAX_LOG_LINES
    for log_file in os.listdir(log_dir):
        if log_file.endswith(LOG_FILE_EXT):
            log_file_path = os.path.join(log_dir, log_file)
            if sum(1 for _ in open(log_file_path)) >= MAX_LOG_LINES:
                zip_log_file(log_file_path)
                setup_logging()

# Set a scheduler to check log files every hour
schedule.every().hour.at(":00").do(check_and_zip_logs)

# Continuously run the scheduler
def control_zip():
    schedule.run_pending()
    time.sleep(1)
    
 #--------------------------------------------LDAP Connection and Browser Settings------------------------------------------------------------

# LDAP server information
ldap_server = 'ldap://DOMAIN'
ldap_user = 'DOMAIN\\USER'
ldap_password = 'PASSWORD'
   
# Establish LDAP connection
server = Server(ldap_server, get_info=ALL)
conn = Connection(server, user=ldap_user, password=ldap_password, authentication=NTLM)

if not conn.bind():
    log_and_print(f"LDAP connection failed: {conn.result}")
    exit()

# Target directory for saving files
target_dir = "TARGET LOCATION" # Folder to move files to
download_dir = os.path.join(os.getcwd(), 'temporary')  # Folder where downloaded files will be saved

options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_dir,  # Folder where downloaded files will be saved
    "download.prompt_for_download": False,  # Do not ask for confirmation for each download
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
# Set ChromeDriver path
chrome_driver_path = './chromedriver.exe'  # Enter the full path of ChromeDriver here
service = Service(chrome_driver_path)
driver = webdriver.Chrome(service=service, options=options)
driver.get('https://web.whatsapp.com')


#-----------------------------------Login Area----------------------------------------------------------------------------------------------

# Scan QR code and connect to WhatsApp Web
log_and_print("Scan the QR code.")
try:
    WebDriverWait(driver, 300).until(EC.presence_of_element_located((By.XPATH, "//*[@id='pane-side']/div[1]/div/div/div[1]/div/div/div/div[2]")))
    log_and_print("Connected!")
except Exception as e:
    log_and_print(f"Element not found within the expected time: {e}")
    driver.quit()
    exit()

#-------------------------------------Message Checking-------------------------------------------------------------------------------------------
# Function to detect messages and files
def check_new_messages():
    try:
        new_messages = driver.find_elements(By.XPATH, "//*[@id='pane-side']/div[1]/div/div/div")
        log_and_print(str(len(new_messages))+" Chats found.")
        for message in new_messages:
            try:
                message.click()
                time.sleep(2)
                process_message()
            except Exception as e:
                log_and_print(f"Message could not be clicked or an error occurred: {e}")
    except Exception as e:
        log_and_print(f"No new messages or an error occurred: {e}")

# Function to determine the type of message and perform appropriate action
def process_message():
    try:
        messages = driver.find_elements(By.CLASS_NAME, 'message-in')
        messages.reverse()
        log_and_print(f"{len(messages)} messages found")
        only_normal_and_voice = True  # Flag: if only normal messages and voice recordings
        for index, msg in enumerate(messages):
            try:
                log_and_print(f"Processing message {index+1}...")
                album_btn = msg.find_element(By.XPATH, './/div[@aria-label="Open image"]')
                album_btn.click()
                time.sleep(8)
            except:
                None
            try:
                if is_image_album(msg):
                    handle_image_album(msg, index)
                    only_normal_and_voice = False
                elif is_document(msg):
                    log_and_print("Document found")
                    handle_document(msg, index)
                    only_normal_and_voice = False
                else:
                    log_and_print("Normal message or voice recording found, ignoring...")

                    continue
            except Exception as e:
                log_and_print(f"Message could not be processed: {e}")

        if only_normal_and_voice:
            delete_chat()
    except Exception as e:
        log_and_print(f"Messages not found: {e}")

#--------------------------------------Processing Area---------------------------------------------------------------------------------------------

def is_image_album(msg):
    try:
        msg.find_element(By.XPATH, './/img[contains(@src, "blob:")]')
        time.sleep(1)
        return True                                          
    except:
        time.sleep(1)
        return False

def is_document(msg):
    try:
        msg.find_element(By.XPATH, './/span[@title="PDF"]')
        return True
    except:
        time.sleep(1)
        return False
    
def album_image_finder(index,msg):
    try:
        i=1
        downloaded_urls = set()
        for i in range(index):
            try:
                album_image = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, './/img[contains(@src, "blob:")]')))
                album_image_src = album_image.get_attribute('src')
                time.sleep(1)
                if album_image_src not in downloaded_urls:
                    type_finder("jpg", index, i,msg)
                    downloaded_urls.add(album_image_src)
                
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[2]/div[3]/div/div')))
                next_button.click()
                time.sleep(2)
            except Exception as e:
                log_and_print("Error:", e)
                
        downloaded_urls = None
        time.sleep(1)
        close_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[8]/div'))
        )
        close_button.click()
    except Exception as e:
        log_and_print("Error:", e)
        
def handle_image_album(msg, index):
    try:    
        try:  
            album_box = msg.find_element(By.XPATH, './/div[@aria-label="Open image"]')
            album_box.click()
            time.sleep(1)
            total_image = driver.find_element(By.XPATH, './/span[@class="_alhf _ao3e"]')
            total_image_Num = total_image.text
            symbol = "/"
            cleaned_text = total_image_Num.replace(" ", "")
            time.sleep(1)
            position = cleaned_text.find(symbol)
            if position != -1:
                result = cleaned_text[position + 1:]
            else:
                result = cleaned_text
            album_Num = int(result)
            time.sleep(1)
            log_and_print("Downloading album...")
            album_image_finder(album_Num,msg)
        except:
            log_and_print("Downloading single image...")
            try:
                time.sleep(2)
                album_image = driver.find_element(By.XPATH, './/img[contains(@src, "blob:")]')
                album_image_src = album_image.get_attribute('src')
                type_finder("jpg", index, 0,msg)
                time.sleep(2)
                close_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/span[3]/div/div/div[2]/div/div[1]/div[2]/div/div[8]/div')))
                close_button.click()
            except Exception as e:
                log_and_print(f"An error occurred during single image processing: {e}")
        massage_delete(msg)
        time.sleep(1)
    except Exception as e:
        log_and_print("Error:",e)    
    log_and_print("Proceeding to the next message...")

def handle_document(msg, index):
    log_and_print("Processing PDF")
    msg.click()
    try:
        time.sleep(5)  # Give enough time for the file to download
        move_and_rename_file(index,0)
        
    except Exception as e:
        log_and_print(f"Document could not be downloaded: {e}")
    massage_delete(msg)
    time.sleep(1)
    log_and_print("Proceeding to the next message...")
    
def convert_pnumber(input_str):
    # Remove +90 part and spaces from the phone number (+90 for Turkiye, if you are in another country you need to change this)
    phone_number = re.sub(r'^\+90\s?', '', input_str)
    phone_number = phone_number.replace(' ', '')
    remaining_str = phone_number[10:]
    phone_number = phone_number[:10]
    result = phone_number + remaining_str
    return result

def type_finder(types, msg_index, img_index,msg):
    match types:
        case "jpg":
            try:
                download_img = msg.find_element(By.XPATH, '//div[contains(aria-label,"Download") or contains(@title,"Download")]')
                download_img.click()
            except:
                open_menu = msg.find_element(By.XPATH, '//div[contains(@title,"Menu") or contains(@aria-label,"Menu")]')
                open_menu.click()
                time.sleep(1)
                download_menu = msg.find_element(By.XPATH, '//div[contains(text(),"Download")]')
                download_menu.click()
            time.sleep(8)
            move_and_rename_file(msg_index, img_index)
            
        case _:
            return "Unknown value"

def move_and_rename_file(index, img_index):
    
    try:

        # Get list of downloaded files
        downloaded_files = [f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))]
        if not downloaded_files:
            log_and_print("No downloaded file found.")
            exit()

        # Sort downloaded files by timestamp
        downloaded_files = sorted([os.path.join(download_dir, f) for f in downloaded_files], key=os.path.getctime)

        # Check temporary file name and find the correct file name
        latest_file = None
        for file in downloaded_files:
            if file.endswith(".tmp"):
                continue
            latest_file = file
            break

        if latest_file is None:
            log_and_print("No valid file found.")
            exit()
        time.sleep(5)
        # Wait to verify the file has been downloaded
        if not os.path.exists(latest_file):
            log_and_print(f"File not found: {latest_file}")
            exit()

        # Create new file name
        today_date = datetime.today().strftime('%Y-%m-%d')
        sender_info = driver.find_element(By.XPATH, '//header//span[@dir="auto"]').text
        sender_info = convert_pnumber(sender_info)
        new_file_name = f"{sender_info}_msg-{index}_image-{img_index}{os.path.splitext(latest_file)[1]}"  # Replace with actual indexing

        # Create target folder
        date_folder = os.path.join(target_dir, today_date)
        if not os.path.exists(date_folder):
            try:
                os.makedirs(date_folder)
            except FileExistsError:
                log_and_print(f"Folder already exists: {date_folder}")

        new_file_path = os.path.join(date_folder, new_file_name)
        
        # Check if file exists and create a unique name
        counter = 1
        original_new_file_path = new_file_path
        while os.path.exists(new_file_path):
            new_file_name = f"{sender_info}_msg-{index}_image-{img_index}_{counter}{os.path.splitext(latest_file)[1]}"
            new_file_path = os.path.join(date_folder, new_file_name)
            counter += 1

        # Move and rename the file
        shutil.move(latest_file, new_file_path)
        log_and_print(f"File moved and renamed: {new_file_path}")

    except Exception as e:
        log_and_print(f"File could not be moved or renamed: {e}")

#--------------------------------------------Message and Chat Deletion------------------------------------------------------------------------------

def delete_chat():
    try:
        menu_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="main"]/header/div[3]/div/div[3]/div/div')))
        menu_button.click()
        time.sleep(1)
        delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[text()="Delete chat"]')))
        delete_button.click()
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/div/span[2]/div/div/div/div/div/div/div[3]/div/button[2]')))
        confirm_button.click()
        log_and_print("Chat deleted.")
    except Exception as e:
        log_and_print(f"Chat could not be deleted: {e}")

def massage_delete(msg):
    try:
        log_and_print("Starting message deletion process...")
        action = ActionChains(driver)
        action.move_to_element(msg).perform()
        time.sleep(1)
        span_to_click = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, './/span[@data-icon="down-context"]')))
        span_to_click.click()
        time.sleep(1)
        delete_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(),"Delete") or contains(text(),"Delete all")]')))
        delete_button.click()
        time.sleep(1)
        confirm_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[contains(text(),"Delete for me")]')))
        confirm_button.click()
        time.sleep(1)
        log_and_print("Message deleted.")
    except Exception as e:
        log_and_print(f"Message could not be deleted: {e}")

#-------------------------------------------File Checking and Loop Processing----------------------------------------------------------------------
try:
    while True:
        check_new_messages()
        time.sleep(20)
except KeyboardInterrupt:
    log_and_print("Program stopped.")
finally:
    driver.quit()
