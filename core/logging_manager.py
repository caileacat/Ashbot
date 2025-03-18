import logging

# ✅ Set up logging (default to INFO)
logging.basicConfig(level=logging.WARNING)

def set_logging_level(level):
    """Changes the logging level dynamically, including discord.py loggers."""
    level_map = {
        "1": logging.DEBUG,
        "2": logging.INFO,
        "3": logging.WARNING,
        "4": logging.ERROR,
        "5": logging.CRITICAL
    }
    
    if level in level_map:
        new_level = level_map[level]
        logging.getLogger().setLevel(new_level)
        logging.getLogger("discord").setLevel(new_level)
        logging.getLogger("discord.gateway").setLevel(new_level)
        logging.getLogger("discord.client").setLevel(new_level)

        print(f"✅ Logging level set to {logging.getLevelName(new_level)}")
    else:
        print("❌ Invalid selection. Please choose a number between 1 and 5.")

def show_logging_menu():
    """Displays the logging configuration menu."""
    while True:
        print("\n=== Logging Configuration Menu ===")
        print("[1] Set Logging Level to DEBUG")
        print("[2] Set Logging Level to INFO")
        print("[3] Set Logging Level to WARNING")
        print("[4] Set Logging Level to ERROR")
        print("[5] Set Logging Level to CRITICAL")
        print("[X] Back")

        choice = input("Select an option: ").strip().upper()

        if choice == "X":
            break
        else:
            set_logging_level(choice)
            break
