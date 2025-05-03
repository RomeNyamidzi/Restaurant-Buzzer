# Restaurant Buzzer System

A fully functional software simulation of a restaurant buzzer system that includes dimming functionality and a rechargeable battery feature.

## 🚀 Features

- **Dimming Functionality**: Buzzers gradually dim when inactive to simulate real-world behavior and save battery
- **Rechargeable Battery**: Complete simulation of battery charging and discharging mechanics
- **User Interface**: Comprehensive CLI interface for restaurant staff to manage buzzers
- **Multi-threaded Architecture**: Real-time simulation of buzzer behavior using background threads
- **Data Persistence**: All buzzer and user data is saved between program runs
- **Security Features**: Basic user authentication and role-based access control

## 📋 System Requirements

- Python 3.7 or higher
- No external dependencies required (uses only Python standard library)

## 🔧 Installation

1. Clone this repository:
   ```
   git clone https://github.com/RomeNyamidzi/restaurant-buzzer-system.git
   cd restaurant-buzzer-system
   ```

2. Make sure you have Python 3.7+ installed:
   ```
   python --version
   ```

3. Run the application:
   ```
   python buzzer_system.py
   ```

## 💡 Usage

### Default Login
- Username: `admin`
- Password: `admin123`

### Main Menu Options
1. **Manage Buzzers** - Add, remove, and view buzzers
2. **Activate/Deactivate Buzzers** - Assign buzzers to customers and manage active states
3. **Charging Management** - Control buzzer charging and monitor battery levels
4. **User Management** - Add new staff users (admin only)
5. **Exit** - Log out and exit the system

### Using the Buzzer System

#### Adding a New Buzzer
1. Select "Manage Buzzers" from the main menu
2. Choose "Add New Buzzer"
3. Enter a name for the buzzer

#### Activating a Buzzer for a Customer
1. Select "Activate/Deactivate Buzzers" from the main menu
2. Choose "Activate Buzzer"
3. Select an available buzzer from the list
4. Enter customer name and estimated wait time

#### Managing Charging
1. Select "Charging Management" from the main menu
2. Choose "Start Charging Buzzer" or "Stop Charging Buzzer"
3. Select the appropriate buzzer from the list

## 🏗️ Technical Implementation

### Core Components

#### Buzzer Class
- Represents each individual buzzer with properties like:
  - Battery level
  - Brightness
  - Active state
  - Charging state
  - Customer assignment

#### BuzzerSystem Class
- Core logic for managing all buzzers
- Implements multithreaded simulation for:
  - Dimming functionality
  - Battery simulation
  - Charging mechanics
- Handles data persistence

#### BuzzerCLI Class
- Command Line Interface for interacting with the system
- Menu-based user interface
- Formatted display of buzzer information

#### BuzzerSimulator Class
- Adds realistic behavior to the simulation
- Introduces random events like occasional faster battery drain

### Data Storage
- All data is stored in JSON format in the `buzzer_data` directory:
  - `buzzers.json` - Stores buzzer information
  - `users.json` - Stores user credentials

## 🔍 Simulation Details

### Dimming Logic
- Buzzers start at maximum brightness (100%)
- When inactive, brightness gradually decreases to minimum level (10%)
- When activated, brightness returns to maximum
- Dimming occurs in small steps to create a smooth transition

### Battery Simulation
- Battery drains at different rates based on buzzer state:
  - Active buzzers drain faster
  - Inactive buzzers drain slower
- When charging, battery level increases at a constant rate
- Buzzers automatically turn off when battery level is critically low (5%)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👏 Acknowledgements

- Created for the Restaurant Buzzer System Coding Challenge
- Developed to demonstrate software simulation capabilities for real-world systems

+447471321040

Rome Nyamidzi - romenyamidzi89@gmail.com

Project Link: https://github.com/romenyamidzi/restaurant-buzzer-system
