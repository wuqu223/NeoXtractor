import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logfile.txt", mode="a"),  # Write logs to a file
        logging.StreamHandler()  # Optional: Print logs to the console
    ]
)

# Get the logger instance
logger = logging.getLogger("PyQtAppLogger")
