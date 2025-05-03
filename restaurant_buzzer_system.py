"""
Restaurant Buzzer System Simulation
-----------------------------------
A fully functional software simulation of a restaurant buzzer system with
dimming functionality and rechargeable features.

Author: Rome Nyamidzi
Date: May 2nd, 2025
"""

import time
import threading
import os
import random
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_BATTERY_LEVEL = 100
MIN_BATTERY_LEVEL = 0
MAX_BRIGHTNESS = 100
MIN_BRIGHTNESS = 10
DIMMING_INTERVAL = 0.5  # seconds between brightness adjustments
DIMMING_STEP = 5  # brightness reduction per step
BATTERY_DRAIN_ACTIVE = 0.05  # battery drain per second when active
BATTERY_DRAIN_INACTIVE = 0.01  # battery drain per second when inactive
CHARGING_RATE = 0.5  # battery charge increase per second

# File paths
DATA_DIR = "buzzer_data"
BUZZERS_FILE = os.path.join(DATA_DIR, "buzzers.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


@dataclass
class Buzzer:
    """Representation of a restaurant buzzer with all its properties."""
    id: int
    name: str
    battery_level: float = MAX_BATTERY_LEVEL
    brightness: int = MAX_BRIGHTNESS
    is_active: bool = False
    is_charging: bool = False
    assigned_to: Optional[str] = None
    wait_time: Optional[int] = None
    last_updated: float = time.time()
    
    def to_dict(self) -> Dict:
        """Convert the buzzer to a dictionary for serialization."""
        return asdict(self)


class BuzzerSystem:
    """Main class to manage the restaurant buzzer system."""
    
    def __init__(self):
        """Initialize the buzzer system."""
        self.buzzers: Dict[int, Buzzer] = {}
        self.users: Dict[str, str] = {}  # username: password
        self.current_user: Optional[str] = None
        self.load_data()
        self.dimming_threads: Dict[int, threading.Thread] = {}
        self.battery_threads: Dict[int, threading.Thread] = {}
        self.charging_threads: Dict[int, threading.Thread] = {}
        self.running = True
        
        # Create necessary directories
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Start background thread for all existing buzzers
        for buzzer_id, buzzer in self.buzzers.items():
            self._start_buzzer_threads(buzzer_id)
    
    def load_data(self) -> None:
        """Load buzzer and user data from files."""
        # Load buzzers
        if os.path.exists(BUZZERS_FILE):
            try:
                with open(BUZZERS_FILE, 'r') as f:
                    buzzer_dicts = json.load(f)
                    for buzzer_dict in buzzer_dicts:
                        buzzer = Buzzer(**buzzer_dict)
                        self.buzzers[buzzer.id] = buzzer
                logger.info(f"Loaded {len(self.buzzers)} buzzers from {BUZZERS_FILE}")
            except Exception as e:
                logger.error(f"Error loading buzzers: {e}")
        
        # Load users
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    self.users = json.load(f)
                logger.info(f"Loaded {len(self.users)} users from {USERS_FILE}")
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        
        # If no users exist, create a default admin user
        if not self.users:
            self.users = {"admin": "admin123"}
            self.save_data()
    
    def save_data(self) -> None:
        """Save buzzer and user data to files."""
        # Save buzzers
        try:
            buzzer_dicts = [buzzer.to_dict() for buzzer in self.buzzers.values()]
            with open(BUZZERS_FILE, 'w') as f:
                json.dump(buzzer_dicts, f, indent=2)
            logger.info(f"Saved {len(buzzer_dicts)} buzzers to {BUZZERS_FILE}")
        except Exception as e:
            logger.error(f"Error saving buzzers: {e}")
        
        # Save users
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(self.users, f, indent=2)
            logger.info(f"Saved {len(self.users)} users to {USERS_FILE}")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def login(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        if username in self.users and self.users[username] == password:
            self.current_user = username
            logger.info(f"User {username} logged in successfully")
            return True
        logger.warning(f"Failed login attempt for user {username}")
        return False
    
    def logout(self) -> None:
        """Log out the current user."""
        if self.current_user:
            logger.info(f"User {self.current_user} logged out")
            self.current_user = None
    
    def add_user(self, username: str, password: str) -> bool:
        """Add a new user."""
        if self.current_user != "admin":
            logger.warning(f"Non-admin user {self.current_user} attempted to add a new user")
            return False
        
        if username in self.users:
            logger.warning(f"User {username} already exists")
            return False
        
        self.users[username] = password
        self.save_data()
        logger.info(f"New user {username} added by admin")
        return True
    
    def add_buzzer(self, name: str) -> int:
        """Add a new buzzer to the system."""
        buzzer_id = max(self.buzzers.keys(), default=0) + 1
        self.buzzers[buzzer_id] = Buzzer(id=buzzer_id, name=name)
        self._start_buzzer_threads(buzzer_id)
        self.save_data()
        logger.info(f"New buzzer added: {buzzer_id} - {name}")
        return buzzer_id
    
    def remove_buzzer(self, buzzer_id: int) -> bool:
        """Remove a buzzer from the system."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to remove non-existent buzzer {buzzer_id}")
            return False
        
        # Stop all threads for this buzzer
        self._stop_buzzer_threads(buzzer_id)
        
        # Remove the buzzer
        del self.buzzers[buzzer_id]
        self.save_data()
        logger.info(f"Buzzer {buzzer_id} removed")
        return True
    
    def _start_buzzer_threads(self, buzzer_id: int) -> None:
        """Start background threads for a buzzer."""
        # Start dimming thread
        dimming_thread = threading.Thread(
            target=self._dimming_thread,
            args=(buzzer_id,),
            daemon=True
        )
        self.dimming_threads[buzzer_id] = dimming_thread
        dimming_thread.start()
        
        # Start battery drain thread
        battery_thread = threading.Thread(
            target=self._battery_thread,
            args=(buzzer_id,),
            daemon=True
        )
        self.battery_threads[buzzer_id] = battery_thread
        battery_thread.start()
    
    def _stop_buzzer_threads(self, buzzer_id: int) -> None:
        """Stop all threads associated with a buzzer."""
        # We don't actually stop threads (they're daemon threads),
        # but we remove them from our dictionaries
        if buzzer_id in self.dimming_threads:
            del self.dimming_threads[buzzer_id]
        if buzzer_id in self.battery_threads:
            del self.battery_threads[buzzer_id]
        if buzzer_id in self.charging_threads:
            del self.charging_threads[buzzer_id]
    
    def _dimming_thread(self, buzzer_id: int) -> None:
        """Background thread to handle buzzer dimming."""
        while self.running and buzzer_id in self.buzzers:
            try:
                buzzer = self.buzzers[buzzer_id]
                
                # If the buzzer is inactive, gradually dim it
                if not buzzer.is_active and buzzer.brightness > MIN_BRIGHTNESS:
                    buzzer.brightness = max(MIN_BRIGHTNESS, buzzer.brightness - DIMMING_STEP)
                    logger.debug(f"Buzzer {buzzer_id} dimmed to {buzzer.brightness}%")
                
                # If the buzzer is active, gradually restore brightness
                elif buzzer.is_active and buzzer.brightness < MAX_BRIGHTNESS:
                    buzzer.brightness = min(MAX_BRIGHTNESS, buzzer.brightness + DIMMING_STEP * 2)
                    logger.debug(f"Buzzer {buzzer_id} brightness increased to {buzzer.brightness}%")
                
                time.sleep(DIMMING_INTERVAL)
            except Exception as e:
                logger.error(f"Error in dimming thread for buzzer {buzzer_id}: {e}")
                time.sleep(DIMMING_INTERVAL)
    
    def _battery_thread(self, buzzer_id: int) -> None:
        """Background thread to handle battery drain."""
        while self.running and buzzer_id in self.buzzers:
            try:
                buzzer = self.buzzers[buzzer_id]
                now = time.time()
                elapsed = now - buzzer.last_updated
                buzzer.last_updated = now
                
                # If charging, handle in the charging thread
                if buzzer.is_charging:
                    time.sleep(1)
                    continue
                
                # Drain battery based on active state
                drain_rate = BATTERY_DRAIN_ACTIVE if buzzer.is_active else BATTERY_DRAIN_INACTIVE
                drain_amount = drain_rate * elapsed
                
                # Apply battery drain
                old_level = buzzer.battery_level
                buzzer.battery_level = max(MIN_BATTERY_LEVEL, buzzer.battery_level - drain_amount)
                
                # Log significant changes
                if int(old_level) != int(buzzer.battery_level):
                    logger.debug(f"Buzzer {buzzer_id} battery level: {buzzer.battery_level:.1f}%")
                
                # If battery is critically low, automatically turn off
                if buzzer.battery_level <= 5 and buzzer.is_active:
                    logger.warning(f"Buzzer {buzzer_id} turned off due to low battery")
                    buzzer.is_active = False
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in battery thread for buzzer {buzzer_id}: {e}")
                time.sleep(1)
    
    def _charging_thread(self, buzzer_id: int) -> None:
        """Background thread to handle buzzer charging."""
        while self.running and buzzer_id in self.buzzers and self.buzzers[buzzer_id].is_charging:
            try:
                buzzer = self.buzzers[buzzer_id]
                now = time.time()
                elapsed = now - buzzer.last_updated
                buzzer.last_updated = now
                
                # Increase battery level
                old_level = buzzer.battery_level
                buzzer.battery_level = min(MAX_BATTERY_LEVEL, buzzer.battery_level + CHARGING_RATE * elapsed)
                
                # Log significant changes
                if int(old_level) != int(buzzer.battery_level):
                    logger.debug(f"Buzzer {buzzer_id} charging: {buzzer.battery_level:.1f}%")
                
                # If fully charged, stop charging
                if buzzer.battery_level >= MAX_BATTERY_LEVEL:
                    logger.info(f"Buzzer {buzzer_id} fully charged")
                    self.stop_charging(buzzer_id)
                    break
                
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error in charging thread for buzzer {buzzer_id}: {e}")
                time.sleep(1)
    
    def start_charging(self, buzzer_id: int) -> bool:
        """Start charging a buzzer."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to charge non-existent buzzer {buzzer_id}")
            return False
        
        buzzer = self.buzzers[buzzer_id]
        if buzzer.is_charging:
            logger.info(f"Buzzer {buzzer_id} is already charging")
            return True
        
        # Start charging
        buzzer.is_charging = True
        buzzer.last_updated = time.time()
        
        # Start charging thread if not already running
        if buzzer_id not in self.charging_threads or not self.charging_threads[buzzer_id].is_alive():
            charging_thread = threading.Thread(
                target=self._charging_thread,
                args=(buzzer_id,),
                daemon=True
            )
            self.charging_threads[buzzer_id] = charging_thread
            charging_thread.start()
        
        logger.info(f"Started charging buzzer {buzzer_id}")
        return True
    
    def stop_charging(self, buzzer_id: int) -> bool:
        """Stop charging a buzzer."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to stop charging non-existent buzzer {buzzer_id}")
            return False
        
        buzzer = self.buzzers[buzzer_id]
        if not buzzer.is_charging:
            logger.info(f"Buzzer {buzzer_id} is not charging")
            return True
        
        # Stop charging
        buzzer.is_charging = False
        buzzer.last_updated = time.time()
        logger.info(f"Stopped charging buzzer {buzzer_id}")
        return True
    
    def activate_buzzer(self, buzzer_id: int, customer_name: str, wait_time: int) -> bool:
        """Activate a buzzer and assign it to a customer."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to activate non-existent buzzer {buzzer_id}")
            return False
        
        buzzer = self.buzzers[buzzer_id]
        if buzzer.battery_level <= 5:
            logger.warning(f"Cannot activate buzzer {buzzer_id} due to low battery ({buzzer.battery_level:.1f}%)")
            return False
        
        if buzzer.is_active:
            logger.warning(f"Buzzer {buzzer_id} is already active")
            return False
        
        # Activate the buzzer
        buzzer.is_active = True
        buzzer.assigned_to = customer_name
        buzzer.wait_time = wait_time
        buzzer.brightness = MAX_BRIGHTNESS
        buzzer.last_updated = time.time()
        
        # Stop charging if the buzzer was charging
        if buzzer.is_charging:
            self.stop_charging(buzzer_id)
        
        logger.info(f"Activated buzzer {buzzer_id} for customer {customer_name}, wait time: {wait_time} minutes")
        self.save_data()
        return True
    
    def deactivate_buzzer(self, buzzer_id: int) -> bool:
        """Deactivate a buzzer."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to deactivate non-existent buzzer {buzzer_id}")
            return False
        
        buzzer = self.buzzers[buzzer_id]
        if not buzzer.is_active:
            logger.warning(f"Buzzer {buzzer_id} is not active")
            return False
        
        # Deactivate the buzzer
        buzzer.is_active = False
        buzzer.assigned_to = None
        buzzer.wait_time = None
        buzzer.last_updated = time.time()
        
        logger.info(f"Deactivated buzzer {buzzer_id}")
        self.save_data()
        return True
    
    def get_buzzer_status(self, buzzer_id: int) -> Optional[Dict]:
        """Get the status of a buzzer."""
        if buzzer_id not in self.buzzers:
            logger.warning(f"Attempt to get status of non-existent buzzer {buzzer_id}")
            return None
        
        return self.buzzers[buzzer_id].to_dict()
    
    def get_all_buzzers(self) -> List[Dict]:
        """Get the status of all buzzers."""
        return [buzzer.to_dict() for buzzer in self.buzzers.values()]
    
    def stop(self) -> None:
        """Stop all background threads and save data."""
        self.running = False
        self.save_data()
        logger.info("Buzzer system stopped")


class BuzzerCLI:
    """Command Line Interface for the Buzzer System."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.system = BuzzerSystem()
        self.running = True
    
    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self, title: str) -> None:
        """Print a formatted header."""
        self.clear_screen()
        print("=" * 60)
        print(f"{title:^60}")
        print("=" * 60)
        print()
    
    def get_input(self, prompt: str, options: List[str] = None) -> str:
        """Get user input with optional validation."""
        while True:
            value = input(prompt).strip()
            if options is None or value in options:
                return value
            print(f"Invalid input. Please choose from: {', '.join(options)}")
    
    def login_menu(self) -> None:
        """Display the login menu."""
        self.print_header("Restaurant Buzzer System - Login")
        
        while not self.system.current_user:
            username = input("Username: ")
            password = input("Password: ")
            
            if self.system.login(username, password):
                print(f"Welcome, {username}!")
                time.sleep(1)
                break
            else:
                print("Invalid username or password. Please try again.")
                time.sleep(1)
                self.print_header("Restaurant Buzzer System - Login")
    
    def main_menu(self) -> None:
        """Display the main menu."""
        while self.running and self.system.current_user:
            self.print_header(f"Restaurant Buzzer System - Main Menu [{self.system.current_user}]")
            
            menu_options = [
                "1. Manage Buzzers",
                "2. Activate/Deactivate Buzzers",
                "3. Charging Management",
                "4. User Management",
                "5. Exit"
            ]
            
            for option in menu_options:
                print(option)
            
            choice = self.get_input("\nSelect an option: ", ["1", "2", "3", "4", "5"])
            
            if choice == "1":
                self.manage_buzzers_menu()
            elif choice == "2":
                self.activate_deactivate_menu()
            elif choice == "3":
                self.charging_menu()
            elif choice == "4":
                self.user_management_menu()
            elif choice == "5":
                self.logout()
    
    def manage_buzzers_menu(self) -> None:
        """Display the buzzer management menu."""
        while True:
            self.print_header("Buzzer Management")
            
            menu_options = [
                "1. View All Buzzers",
                "2. Add New Buzzer",
                "3. Remove Buzzer",
                "4. Back to Main Menu"
            ]
            
            for option in menu_options:
                print(option)
            
            choice = self.get_input("\nSelect an option: ", ["1", "2", "3", "4"])
            
            if choice == "1":
                self.view_all_buzzers()
            elif choice == "2":
                self.add_buzzer()
            elif choice == "3":
                self.remove_buzzer()
            elif choice == "4":
                break
    
    def view_all_buzzers(self) -> None:
        """Display all buzzers."""
        self.print_header("All Buzzers")
        
        buzzers = self.system.get_all_buzzers()
        if not buzzers:
            print("No buzzers in the system.")
            input("\nPress Enter to continue...")
            return
        
        print(f"{'ID':^5} | {'Name':^15} | {'Battery':^10} | {'Status':^10} | {'Customer':^15} | {'Wait Time':^10}")
        print("-" * 75)
        
        for buzzer in buzzers:
            status = "Active" if buzzer['is_active'] else "Inactive"
            if buzzer['is_charging']:
                status += " (⚡)"
            
            customer = buzzer['assigned_to'] if buzzer['assigned_to'] else "-"
            wait_time = f"{buzzer['wait_time']} min" if buzzer['wait_time'] else "-"
            
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15} | {buzzer['battery_level']:^8.1f}% | {status:^10} | {customer:^15} | {wait_time:^10}")
        
        input("\nPress Enter to continue...")
    
    def add_buzzer(self) -> None:
        """Add a new buzzer."""
        self.print_header("Add New Buzzer")
        
        name = input("Enter buzzer name: ")
        if name:
            buzzer_id = self.system.add_buzzer(name)
            print(f"Buzzer added successfully. ID: {buzzer_id}")
        else:
            print("Buzzer name cannot be empty.")
        
        input("\nPress Enter to continue...")
    
    def remove_buzzer(self) -> None:
        """Remove a buzzer."""
        self.print_header("Remove Buzzer")
        
        # Display all buzzers first
        buzzers = self.system.get_all_buzzers()
        if not buzzers:
            print("No buzzers in the system.")
            input("\nPress Enter to continue...")
            return
        
        print(f"{'ID':^5} | {'Name':^15}")
        print("-" * 23)
        
        for buzzer in buzzers:
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15}")
        
        try:
            buzzer_id = int(input("\nEnter buzzer ID to remove (or 0 to cancel): "))
            if buzzer_id == 0:
                return
            
            if self.system.remove_buzzer(buzzer_id):
                print(f"Buzzer {buzzer_id} removed successfully.")
            else:
                print(f"Failed to remove buzzer {buzzer_id}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        
        input("\nPress Enter to continue...")
    
    def activate_deactivate_menu(self) -> None:
        """Display the activate/deactivate menu."""
        while True:
            self.print_header("Activate/Deactivate Buzzers")
            
            menu_options = [
                "1. Activate Buzzer",
                "2. Deactivate Buzzer",
                "3. Back to Main Menu"
            ]
            
            for option in menu_options:
                print(option)
            
            choice = self.get_input("\nSelect an option: ", ["1", "2", "3"])
            
            if choice == "1":
                self.activate_buzzer()
            elif choice == "2":
                self.deactivate_buzzer()
            elif choice == "3":
                break
    
    def activate_buzzer(self) -> None:
        """Activate a buzzer and assign it to a customer."""
        self.print_header("Activate Buzzer")
        
        # Display available buzzers
        buzzers = [b for b in self.system.get_all_buzzers() if not b['is_active']]
        if not buzzers:
            print("No inactive buzzers available.")
            input("\nPress Enter to continue...")
            return
        
        print("Available Buzzers:")
        print(f"{'ID':^5} | {'Name':^15} | {'Battery':^10}")
        print("-" * 35)
        
        for buzzer in buzzers:
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15} | {buzzer['battery_level']:^8.1f}%")
        
        try:
            buzzer_id = int(input("\nEnter buzzer ID to activate (or 0 to cancel): "))
            if buzzer_id == 0:
                return
            
            customer_name = input("Enter customer name: ")
            if not customer_name:
                print("Customer name cannot be empty.")
                input("\nPress Enter to continue...")
                return
            
            wait_time = int(input("Enter estimated wait time (minutes): "))
            if wait_time <= 0:
                print("Wait time must be positive.")
                input("\nPress Enter to continue...")
                return
            
            if self.system.activate_buzzer(buzzer_id, customer_name, wait_time):
                print(f"Buzzer {buzzer_id} activated for {customer_name}.")
            else:
                print(f"Failed to activate buzzer {buzzer_id}.")
        except ValueError:
            print("Invalid input. Please enter valid numbers.")
        
        input("\nPress Enter to continue...")
    
    def deactivate_buzzer(self) -> None:
        """Deactivate a buzzer."""
        self.print_header("Deactivate Buzzer")
        
        # Display active buzzers
        buzzers = [b for b in self.system.get_all_buzzers() if b['is_active']]
        if not buzzers:
            print("No active buzzers.")
            input("\nPress Enter to continue...")
            return
        
        print("Active Buzzers:")
        print(f"{'ID':^5} | {'Name':^15} | {'Customer':^15} | {'Wait Time':^10}")
        print("-" * 60)
        
        for buzzer in buzzers:
            wait_time = f"{buzzer['wait_time']} min" if buzzer['wait_time'] else "-"
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15} | {buzzer['assigned_to']:^15} | {wait_time:^10}")
        
        try:
            buzzer_id = int(input("\nEnter buzzer ID to deactivate (or 0 to cancel): "))
            if buzzer_id == 0:
                return
            
            if self.system.deactivate_buzzer(buzzer_id):
                print(f"Buzzer {buzzer_id} deactivated.")
            else:
                print(f"Failed to deactivate buzzer {buzzer_id}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        
        input("\nPress Enter to continue...")
    
    def charging_menu(self) -> None:
        """Display the charging management menu."""
        while True:
            self.print_header("Charging Management")
            
            menu_options = [
                "1. Start Charging Buzzer",
                "2. Stop Charging Buzzer",
                "3. View Charging Status",
                "4. Back to Main Menu"
            ]
            
            for option in menu_options:
                print(option)
            
            choice = self.get_input("\nSelect an option: ", ["1", "2", "3", "4"])
            
            if choice == "1":
                self.start_charging()
            elif choice == "2":
                self.stop_charging()
            elif choice == "3":
                self.view_charging_status()
            elif choice == "4":
                break
    
    def start_charging(self) -> None:
        """Start charging a buzzer."""
        self.print_header("Start Charging")
        
        # Display all buzzers with their charging status
        buzzers = self.system.get_all_buzzers()
        if not buzzers:
            print("No buzzers in the system.")
            input("\nPress Enter to continue...")
            return
        
        print(f"{'ID':^5} | {'Name':^15} | {'Battery':^10} | {'Charging':^10}")
        print("-" * 50)
        
        for buzzer in buzzers:
            charging = "Yes" if buzzer['is_charging'] else "No"
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15} | {buzzer['battery_level']:^8.1f}% | {charging:^10}")
        
        try:
            buzzer_id = int(input("\nEnter buzzer ID to start charging (or 0 to cancel): "))
            if buzzer_id == 0:
                return
            
            if self.system.start_charging(buzzer_id):
                print(f"Started charging buzzer {buzzer_id}.")
            else:
                print(f"Failed to start charging buzzer {buzzer_id}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        
        input("\nPress Enter to continue...")
    
    def stop_charging(self) -> None:
        """Stop charging a buzzer."""
        self.print_header("Stop Charging")
        
        # Display charging buzzers
        buzzers = [b for b in self.system.get_all_buzzers() if b['is_charging']]
        if not buzzers:
            print("No buzzers are currently charging.")
            input("\nPress Enter to continue...")
            return
        
        print(f"{'ID':^5} | {'Name':^15} | {'Battery':^10}")
        print("-" * 35)
        
        for buzzer in buzzers:
            print(f"{buzzer['id']:^5} | {buzzer['name']:^15} | {buzzer['battery_level']:^8.1f}%")
        
        try:
            buzzer_id = int(input("\nEnter buzzer ID to stop charging (or 0 to cancel): "))
            if buzzer_id == 0:
                return
            
            if self.system.stop_charging(buzzer_id):