# War Country Simulation
## Overview
This project simulates a territorial conquest game where four countries—USA, Mexico, Spain, and Portugal—compete for control over a grid-based map. The simulation incorporates resource management, battle strategies, and alliances to model dynamic interactions between nations.

## Features
**Grid-Based Map**: The battlefield is represented as a 2D grid where countries compete for territories.

**Resource Management**: Each territory is assigned various resources (air, land, water, cyber) that influence battle outcomes.

**Alliances**: Allied nations cannot attack each other, reflecting diplomatic dynamics.

**Battle Simulation**: Battles are probabilistic, considering troop strength and random factors.

**Visualization**: Real-time grid visualization shows the state of the simulation.

**Data Persistence**: Battle outcomes are stored in a MySQL database and exported as a CSV file.

## Requirements
Python 3.7 or higher

**Libraries**:
numpy
matplotlib
pandas
mysql-connector-python
python-dotenv
A running MySQL server

## Environment variables for database connection:
MYSQL_USER

MYSQL_PASSWORD

MYSQL_HOST

MYSQL_DATABASE

## Setup
Install the required Python libraries using pip install -r requirements.txt.

**Configure your .env file with the following keys:**

MYSQL_USER=<your_mysql_username>

MYSQL_PASSWORD=<your_mysql_password>

MYSQL_HOST=<mysql_host>

MYSQL_DATABASE=<your_database_name>

**Run the script to initialize the database and start the simulation:** 

python war_country_simulation.py

## How It Works
**Initialization:**
Territories are distributed among countries.
Each territory is assigned random resources.

**Simulation:**
Countries take turns attempting to conquer territories.
Battles are resolved using troop strength and strategy.
The simulation ends after 20 successful acquisitions or when only one alliance remains.

**Data Export:**
All battle data is saved to battle_data.csv and a MySQL database.
Visualization
The simulation provides a live visualization of the battlefield with a grid view and a legend for country territories.

## Authors
Jon Ardinast

Zhen Yi Hu Chen
## License
This project is open-source and available under the MIT License.
