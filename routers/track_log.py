import functools
import logging
import os

# Ensure log directory exists
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_function(func):
    module_name = func.__module__.split('.')[-1]  # Get the module name

    # Configure logging for the module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=f'{LOG_DIR}/{module_name}.log',  # Log file named after the module
    )

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Executing function {func.__name__} in module {module_name} with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"Function {func.__name__} executed successfully")
            return result
        except Exception as e:
            logging.error(f"Error in function {func.__name__}: {str(e)}")
            raise
    return wrapper
