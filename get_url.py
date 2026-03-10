import undetected_chromedriver as uc
import sys
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    patcher = uc.patcher.Patcher(version_main=145)
    url = patcher.download_url
    print("Download URL:", url)
except Exception as e:
    print("Error:", e)
