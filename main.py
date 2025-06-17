#!/usr/bin/env python3
"""
HoopsFactory Video Downloader
A script to automatically download videos from HoopsFactory for a specific day.
"""

import sys
import asyncio
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
from pathlib import Path
import argparse
from typing import Optional, List
import os

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from dotenv import load_dotenv
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
load_dotenv()


class HoopsFactoryDownloader:
    def __init__(
        self,
        email: str,
        password: str,
        download_dir: str = "./downloads",
        headless: bool = True,
    ):
        """
        Initialize the HoopsFactory downloader.

        Args:
            email (str): Login email
            password (str): Login password
            download_dir (str): Directory to save downloaded videos
            headless (bool): Run browser in headless mode
        """
        self.email = email
        self.password = password
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.base_url = "https://hoopsfactory.com"  # Update with actual URL

    async def setup_browser(self):
        """Setup Playwright browser with appropriate options."""
        self.playwright = await async_playwright().start()

        # Launch browser with additional arguments to improve headless behavior
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless, 
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",  # Overcome limited resource problems
                "--disable-gpu",  # Helps with headless rendering issues
                "--window-size=1920,1080"  # Ensure large viewport
            ]
        )

        # Create context with download settings and proper user agent
        self.context = await self.browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"  # Modern user agent
        )

        # Create page
        self.page = await self.context.new_page()
        
    async def wait_for_visible(self, selector, timeout=60000):
        """Wait for an element to be visible and force it to be visible if needed."""
        try:
            # Try regular waiting first
            await self.page.wait_for_selector(selector, state='visible', timeout=timeout/3)
            return True
        except Exception:
            logging.warning(f"Element {selector} not naturally visible, trying to force visibility...")
            
            # Try to make the element visible using JavaScript if not naturally visible
            try:
                await self.page.evaluate(f"""(selector) => {{
                    const el = document.querySelector(selector);
                    if (el) {{
                        el.style.display = 'block';
                        el.style.visibility = 'visible';
                        el.style.opacity = '1';
                    }}
                }}""", selector)
                
                # Additional wait to ensure element is present in the DOM
                await self.page.wait_for_selector(selector, timeout=timeout/2)
                return True
            except Exception as e:
                logging.error(f"Failed to make element {selector} visible: {str(e)}")
                return False

    async def close_browser(self):
        """Close browser and cleanup resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, "playwright"):
            await self.playwright.stop()

    def get_previous_wednesday(self):
        """
        Get the previous Wednesday date from today.

        Returns:
            str: Date in YYYYMMDD format
        """
        today = datetime.now()
        days_since_wednesday = (today.weekday() - 2) % 7
        
        if days_since_wednesday == 0:
            # Today is Wednesday, get last Wednesday
            prev_wednesday = today - timedelta(days=7)
        else:
            # Get the most recent Wednesday
            prev_wednesday = today - timedelta(days=days_since_wednesday)
        
        return prev_wednesday.strftime("%Y%m%d")

    async def login(self, login_url: str):
        """
        Login to HoopsFactory website using the provided credentials.

        Args:
            login_url (str): URL of the login page

        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logging.info(f"Navigating to login page: {login_url}")
            await self.page.goto(login_url)

            # Wait for login form to be available
            await self.page.wait_for_selector('form[name="login"]', timeout=10000)
            logging.info("Login form found, proceeding with login...")

            logging.debug(f"Filling in login credentials... with email: {self.email}")
            # Fill email field
            await self.page.fill('input[name="email-login"]', self.email)
            logging.debug("Filling in password...")

            # Fill password field
            await self.page.fill('input[name="password-login"]', self.password)

            logging.debug("Submitting login form...")
            # Click login button
            await self.page.click('button[id="validate-login-form"]')

            # Wait for page to load after login
            await self.page.wait_for_load_state("networkidle", timeout=15000)

            # Check if login was successful by looking for error messages or redirect
            current_url = self.page.url
            # Check if redirected to my-account page (successful login)
            if "my-account" in current_url.lower():
                logging.info("Login successful!")
                return True
            else:
                logging.warning("Login failed. Please check your credentials.")
                return False

        except Exception as e:
            logging.error(f"Error during login: {str(e)}")
            return False

    async def select_filters(self):
        """
        Select the required filters: HF Paris center, Rucker Park court, and next Wednesday.

        Returns:
            bool: True if filters selected successfully, False otherwise
        """
        try:
            logging.info("Setting up video filters...")

            # Select center: HF Paris (value="0")
            await self.page.click("#center_list .item-link")
            # Use our custom method with longer timeout for elements that may not be initially visible
            # if not await self.wait_for_visible("#videos_centers", timeout=60000):
            # Try JavaScript fallback if element not visible
            await self.page.evaluate("""() => {
                // Try to open the filter dropdown by mimicking user interaction
                const centerList = document.querySelector("#center_list .item-link");
                if (centerList) centerList.click();
                
                // Wait a moment and try to make the select visible directly
                setTimeout(() => {
                    const select = document.querySelector("#videos_centers");
                    if (select) {
                        select.style.display = "block";
                        select.style.visibility = "visible";
                    }
                }, 1000);
            }""")
                
            # Try to select the option via JavaScript if the selector is hidden
            await self.page.evaluate("""() => {
                const select = document.querySelector("#videos_centers");
                if (select) {
                    select.value = "0";
                    // Trigger change event
                    const event = new Event('change', { bubbles: true });
                    select.dispatchEvent(event);
                }
            }""")
            logging.info("Selected HF Paris center")

            # Select court: 3. Rucker Park (value="3")
            await self.page.click("#court_list .item-link")
            # await self.wait_for_visible("#videos_courts", timeout=60000)
            
            # Try to select the option via JavaScript
            await self.page.evaluate("""() => {
                const select = document.querySelector("#videos_courts");
                if (select) {
                    select.value = "3";
                    // Trigger change event
                    const event = new Event('change', { bubbles: true });
                    select.dispatchEvent(event);
                }
            }""")
            logging.info("Selected Rucker Park court")

            # Select date: Previous Wednesday
            prev_wednesday = self.get_previous_wednesday()
            await self.page.click("#day_list .item-link")
            # await self.wait_for_visible("#videos_days", timeout=60000)

            # Try to select the previous Wednesday date using JavaScript
            try:
                js_code = """(date) => {
                    const select = document.querySelector("#videos_days");
                    if (select) {
                        // Check if the option exists
                        let optionExists = Array.from(select.options).some(opt => opt.value === date);
                        if (optionExists) {
                            select.value = date;
                            // Trigger change event
                            const event = new Event('change', { bubbles: true });
                            select.dispatchEvent(event);
                            return true;
                        }
                        return false;
                    }
                    return false;
                }"""
                await self.page.evaluate(js_code, prev_wednesday)
                logging.info(f"Selected date: {prev_wednesday}")
                
                # Click OK button to confirm date selection
                await self.page.evaluate("""() => {
                    const okButton = document.querySelector('a.link.sheet-close');
                    if (okButton) {
                        okButton.click();
                    }
                }""")
                logging.info("Clicked OK button to confirm date selection")
            except Exception as e:
                logging.warning(
                    f"Date {prev_wednesday} not available, keeping all dates selected: {str(e)}"
                )

            # Keep all hours selected (default)
            logging.info("Keeping all hours selected")
            
            # Add a short wait to allow filters to be applied
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error selecting filters: {str(e)}")
            return False

    async def get_video_links(self) -> List[str]:
        """
        Extract video download links from the current page.
        Filter for videos only between 12:00 and 13:30.

        Returns:
            List[str]: List of video URLs with metadata
        """
        try:
            # Wait for video cards to load
            await self.page.wait_for_selector('.card', timeout=60000)
            await asyncio.sleep(3)
            
            # Extract video information using JavaScript
            video_data = await self.page.evaluate("""() => {
                const videos = [];
                const cards = document.querySelectorAll('.card');
                
                cards.forEach((card, index) => {
                    const downloadLink = card.querySelector('a.download.external');
                    const titleElement = card.querySelector('.product-name');
                    const videoElement = card.querySelector('video');
                    
                    if (downloadLink && titleElement) {
                        const downloadUrl = downloadLink.getAttribute('href');
                        const title = titleElement.textContent.trim();
                        
                        // Extract direct video URL from download link
                        const urlParams = new URLSearchParams(downloadUrl.split('?')[1]);
                        const directVideoUrl = urlParams.get('path');
                        
                        // Also try to get video src directly
                        const videoSrc = videoElement ? videoElement.getAttribute('src') : null;
                        
                        if (directVideoUrl || videoSrc) {
                            videos.push({
                                title: title,
                                downloadUrl: downloadUrl,
                                directUrl: directVideoUrl,
                                videoSrc: videoSrc,
                                index: index
                            });
                        }
                    }
                });
                
                return videos;
            }""")
            
            # Filter videos by time (only keep videos between 12:00 and 13:30)
            filtered_videos = []
            for video in video_data:
                try:
                    # Extract time from title (format: "14/06/2025 11h00")
                    import re
                    time_match = re.search(r'(\d{1,2})h(\d{2})', video['title'])
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2))
                        time_value = hour * 100 + minute
                        
                        # Check if time is between 12:00 (1200) and 13:30 (1330)
                        if 1200 <= time_value <= 1330:
                            filtered_videos.append(video)
                            logging.info(f"Keeping video: {video['title']}")
                        else:
                            logging.info(f"Skipping video {video['title']} (outside 12:00-13:30 range)")
                    else:
                        # If we can't determine time, include it
                        logging.warning(f"Could not determine time for: {video['title']} - including it")
                        filtered_videos.append(video)
                except Exception as e:
                    logging.warning(f"Error filtering video by time: {str(e)} - including video: {video['title']}")
                    filtered_videos.append(video)
            
            logging.info(f"Found {len(video_data)} total videos, filtered to {len(filtered_videos)} videos between 12:00-13:30")
            return filtered_videos

        except Exception as e:
            logging.error(f"Error extracting video links: {str(e)}")
            return []

    async def download_video(self, video_data: dict, date_str: str):
        """
        Download a single video file using the browser's download functionality.

        Args:
            video_data (dict): Video information including URLs and title
            date_str (str): Date string for folder organization
        """
        try:
            import re  # Import re module at the beginning of the method
            
            # Create safe filename from title
            safe_title = re.sub(r'[^\w\s-]', '', video_data['title']).strip()
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            filename = f"{safe_title}.mp4"
            
            logging.info(f"Downloading: {video_data['title']}")

            # Create date-based folder
            date_folder = self.download_dir / date_str
            date_folder.mkdir(exist_ok=True)

            # Set up download path
            download_path = date_folder / filename

            # Method 1: Try direct video URL first
            video_url = video_data.get('directUrl') or video_data.get('videoSrc')
            
            if video_url:
                logging.info(f"Attempting direct download from: {video_url}")
                try:
                    # Use requests to download directly
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Referer': self.base_url
                    }
                    
                    response = requests.get(video_url, headers=headers, stream=True)
                    response.raise_for_status()
                    
                    with open(download_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    
                    logging.info(f"Successfully downloaded: {filename}")
                    return True
                    
                except Exception as e:
                    logging.warning(f"Direct download failed: {str(e)}, trying browser download...")

            # Method 2: Use browser download functionality
            try:
                # Set up download behavior
                await self.page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })

                # Navigate to the download URL
                download_url = video_data['downloadUrl']
                logging.info(f"Using browser download for: {download_url}")
                
                # Start waiting for download
                async with self.page.expect_download() as download_info:
                    await self.page.goto(download_url)
                
                download = await download_info.value
                
                # Save the download
                await download.save_as(download_path)
                logging.info(f"Successfully downloaded via browser: {filename}")
                return True
                
            except Exception as e:
                logging.error(f"Browser download failed: {str(e)}")

            # Method 3: JavaScript-based download trigger
            try:
                logging.info("Attempting JavaScript download trigger...")
                
                # Go back to videos page
                await self.page.goto(f"{self.base_url}/videos")
                await asyncio.sleep(2)
                
                # Find and click the download button using JavaScript
                download_result = await self.page.evaluate(f"""
                    (index) => {{
                        const cards = document.querySelectorAll('.card');
                        if (cards[index]) {{
                            const downloadBtn = cards[index].querySelector('a.download.external');
                            if (downloadBtn) {{
                                downloadBtn.click();
                                return true;
                            }}
                        }}
                        return false;
                    }}
                """, video_data['index'])
                
                if download_result:
                    logging.info(f"Triggered download for: {video_data['title']}")
                    await asyncio.sleep(5)  # Wait for download to start
                    return True
                
            except Exception as e:
                logging.error(f"JavaScript download trigger failed: {str(e)}")

            return False

        except Exception as e:
            logging.error(f"Error downloading {video_data.get('title', 'unknown')}: {str(e)}")
            return False

    async def download_videos(self):
        """
        Main method to download all videos for the specified date.

        Returns:
            bool: True if download process completed successfully
        """
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            try:
                if retry_count > 0:
                    logging.info(f"Retry attempt {retry_count}/{max_retries}...")
                    if self.headless and retry_count == max_retries:
                        logging.info("Switching to non-headless mode for final attempt")
                        self.headless = False
                
                await self.setup_browser()

                # Navigate to login page
                login_url = f"{self.base_url}/login"
                await self.page.goto(login_url)
                await asyncio.sleep(2)

                if not await self.login(login_url):
                    if retry_count < max_retries:
                        retry_count += 1
                        continue
                    return False

                # Navigate to videos page
                videos_url = f"{self.base_url}/videos"
                await self.page.goto(videos_url)
                await asyncio.sleep(2)

                # Set up filters
                if not await self.select_filters():
                    if retry_count < max_retries:
                        retry_count += 1
                        continue
                    return False

                # Get video data
                video_data_list = await self.get_video_links()

                if not video_data_list:
                    logging.warning("No videos found for the specified criteria")
                    if retry_count < max_retries:
                        retry_count += 1
                        continue
                    return True
                
                # Get date for folder name
                date_str = self.get_previous_wednesday()
                
                # Download each video
                successful_downloads = 0
                for video_data in video_data_list:
                    if await self.download_video(video_data, date_str):
                        successful_downloads += 1
                    await asyncio.sleep(2)  # Small delay between downloads

                logging.info(
                    f"Download completed! {successful_downloads}/{len(video_data_list)} videos downloaded to {self.download_dir}/{date_str}"
                )
                return True

            except Exception as e:
                logging.error(f"Error in download process: {str(e)}")
                if retry_count < max_retries:
                    retry_count += 1
                    logging.info(f"Will retry... ({retry_count}/{max_retries})")
                    await asyncio.sleep(2)
                    continue
                return False
            finally:
                await self.close_browser()


async def main():
    """Main function to run the downloader."""
    parser = argparse.ArgumentParser(
        description="Download HoopsFactory videos for previous Wednesday"
    )
    parser.add_argument("--email", default=os.getenv("EMAIL"), help="Login email")
    parser.add_argument("--password", default=os.getenv("PASSWORD"), help="Login password")
    parser.add_argument(
        "--download-dir", default=os.getenv("DOWNLOAD_DIR", "./downloads"), help="Download directory"
    )
    parser.add_argument(
        "--headless", action="store_true", default=(os.getenv("HEADLESS", "True").lower() == "true"),
        help="Run browser in headless mode (default: True unless HEADLESS env var is set to 'false')"
    )
    parser.add_argument(
        "--no-headless", action="store_true", help="Run browser in visible (non-headless) mode"
    )
    parser.add_argument(
        "--base-url", default=os.getenv("BASE_URL", "https://hoopsfactory.com"), help="Base URL of the website"
    )

    args = parser.parse_args()

    # Handle headless mode flags
    headless = args.headless
    if args.no_headless:
        headless = False

    # Create downloader instance
    downloader = HoopsFactoryDownloader(
        email=args.email,
        password=args.password,
        download_dir=args.download_dir,
        headless=headless,
    )

    # Override base URL if provided
    downloader.base_url = args.base_url

    # Run the download process
    success = await downloader.download_videos()

    if success:
        logging.info("All done! Videos downloaded successfully.")
        sys.exit(0)
    else:
        logging.error("Download process failed.")
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
    asyncio.run(main())
