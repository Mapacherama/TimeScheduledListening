import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

token_store = {}
TOKEN_FILE_PATH = "token_info.json"

def save_token_info(token_info):
    logging.info("Attempting to save token information.")
    token_store['token_info'] = token_info
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_info, f)
    logging.info("Token information saved successfully.")

def load_token_info():
    logging.info("Attempting to load token information.")
    if 'token_info' in token_store:
        logging.info("Token information found in memory.")
        return token_store['token_info']
    if os.path.exists(TOKEN_FILE_PATH):
        try:
            with open(TOKEN_FILE_PATH, 'r') as f:
                token_info = json.load(f)
                token_store['token_info'] = token_info
                logging.info("Token information loaded from file.")
                return token_info
        except json.JSONDecodeError:
            logging.error("Invalid token file format. Re-authentication is required.")
            return None
    logging.warning("No token information found.")
    return None