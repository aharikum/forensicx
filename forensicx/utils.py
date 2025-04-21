#!/usr/bin/env python3
"""
Utility functions for ForensicX
"""

import logging
import json
import datetime

def setup_logging(log_file=None):
    """
    Sets up logging configuration
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers = []

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def write_json_file(file_path, data):
    """
    Writes a dictionary to a JSON file
    """
    # https://pynative.com/python-serialize-datetime-into-json/ 
    def json_serial(obj):
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=json_serial)
    except Exception as e:
        raise IOError(f"Error writing to file {file_path}: {e}")
