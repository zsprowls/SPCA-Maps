from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from moviepy.editor import ImageSequenceClip
import subprocess
from flask import Flask, jsonify, render_template
import threading
import webbrowser
import json
import platform

app = Flask(__name__)

# Global variable to store the data
pantry_data = None

@app.route('/')
def index():
    return render_template('pantry_map.html')

@app.route('/data')
def get_data():
    return jsonify(pantry_data)

def load_data():
    global pantry_data
    with open('processed_pantry_data.json', 'r') as f:
        pantry_data = json.load(f)

def create_heatmap_video():
    # Load the data
    load_data()
    
    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=lambda: app.run(port=5000))
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server a moment to start up
    print("Waiting for server to start...")
    time.sleep(5)  # Increased wait time
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')  # Updated headless mode
    chrome_options.add_argument('--window-size=1920,940')  # Changed to even height
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Handle Mac ARM64 (M1/M2) architecture
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        print("Detected Mac ARM64 architecture")
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        service = Service()
    else:
        print("Using standard Chrome setup")
        service = Service(ChromeDriverManager().install())
    
    frames = []  # Initialize frames list outside try block
    driver = None
    
    try:
        # Initialize the Chrome driver
        print("Starting Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set window size explicitly
        driver.set_window_size(1920, 940)
        
        # Open the map page
        print("Loading map page...")
        driver.get('http://127.0.0.1:5000')  # Using 127.0.0.1 instead of localhost
        
        # Wait for the map to load
        print("Waiting for map to load...")
        try:
            WebDriverWait(driver, 30).until(  # Increased timeout to 30 seconds
                EC.presence_of_element_located((By.ID, 'map'))
            )
            print("Map element found!")
        except Exception as e:
            print(f"Error waiting for map: {str(e)}")
            print("Current page source:")
            print(driver.page_source)
            raise
        
        # Switch to heatmap view
        print("Switching to heatmap view...")
        heatmap_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Heat Map')]")
        heatmap_button.click()
        
        # Create screenshots directory if it doesn't exist
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        # Get the date slider
        date_slider = driver.find_element(By.ID, 'dateSlider')
        
        # Take screenshots at different dates
        print("Taking screenshots...")
        for i in range(0, 101, 2):  # Step by 2 for smoother animation
            print(f"Processing frame {i}%...")
            # Update slider value
            driver.execute_script(f"arguments[0].value = {i}; arguments[0].dispatchEvent(new Event('input'));", date_slider)
            time.sleep(0.5)  # Wait for map to update
            
            # Take screenshot
            screenshot_path = f'screenshots/frame_{i:03d}.png'
            driver.save_screenshot(screenshot_path)
            frames.append(screenshot_path)
        
        # Create video from screenshots
        print("Creating video...")
        clip = ImageSequenceClip(frames, fps=10)
        clip.write_videofile('heatmap_animation.mp4', 
                           codec='libx264',
                           audio=False,
                           preset='medium',
                           ffmpeg_params=['-pix_fmt', 'yuv420p', '-vf', 'scale=1920:940'])
        
        print("Video created successfully: heatmap_animation.mp4")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if driver:
            print("Current URL:", driver.current_url)
            print("Page source:", driver.page_source)
        raise
    finally:
        if driver:
            driver.quit()
        
        # Clean up screenshots if any were created
        if frames:
            for frame in frames:
                if os.path.exists(frame):
                    os.remove(frame)
            if os.path.exists('screenshots'):
                os.rmdir('screenshots')

if __name__ == '__main__':
    create_heatmap_video() 