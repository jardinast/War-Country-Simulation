import time
import numpy as np
import threading
import random
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import os
from dotenv import load_dotenv
import mysql.connector
import uuid #package to create simulation ids
import csv
from matplotlib.patches import Patch
matplotlib.use('TkAgg')

# Retrieve the credentials from the environment
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# Establish a connection to the MySQL server
cnx = mysql.connector.connect(
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    host=MYSQL_HOST,
    database=MYSQL_DATABASE
)

if cnx.is_connected():
    print('Connected')

# Create a cursor object to execute SQL queries
cursor = cnx.cursor() 

# Define the SQL query to create a new table
create_table_query = '''
CREATE TABLE IF NOT EXISTS territory_conquest_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    simulation_id VARCHAR(255) NOT NULL,
    battle_id INT NOT NULL,
    coordinate VARCHAR(255) NOT NULL,
    strategy VARCHAR(255) NOT NULL,
    attacker VARCHAR(255) NOT NULL,
    defender VARCHAR(255) NOT NULL,
    winner VARCHAR(255) NOT NULL,
    resources_lost_attacker INT NOT NULL,
    resources_lost_defender INT NOT NULL,
    coordinate_count_us INT NOT NULL,
    coordinate_count_mexico INT NOT NULL, 
    coordinate_count_spain INT NOT NULL,
    coordinate_count_portugal INT NOT NULL
)
'''
# Execute the query to create the new table
cursor.execute(create_table_query)

# Commit the changes and close the cursor and connection
cnx.commit()


# Define the columns for the DataFrame
columns = ['simulation_id', 'battle_id', 'coordinate', 'strategy', 'attacker',
           'defender', 'winner', 'resources_lost_attacker', 'resources_lost_defender',
           'coordinate_count_us', 'coordinate_count_mexico', "coordinate_count_spain", "coordinate_count_portugal"]

battle_data_path = '/Users/fani/Desktop/1st Semester/OPERATING SYSTEMS & PARALLEL COMPUTING/Op.Systems files/battle_data.csv'
if os.path.exists(battle_data_path):
    os.remove(battle_data_path) #remove it if it already exists
battle_data = pd.DataFrame(columns=columns)

class Grid:
    def __init__(self, max_x, max_y,simulation_id ):
        # Initialize a dictionary to hold locks for each grid position
        self.grid_locks = {(x, y): threading.Lock() for x in range(max_x) for y in range(max_y)}
        # Optionally, you can keep track of which country owns which territory and their troops
        troop_types = ['air', 'land', 'water', 'cyber']
        self.territory_owners = {(x, y): None for x in range(max_x) for y in range(max_y)}
        self.succesfull_acquisitions = 0
        # Initialize troops with a dictionary for each territory
        self.territory_resources = {(x, y): {troop_type: 0 for troop_type in troop_types} for x in range(max_x) for y in
                                    range(max_y)}
        self.simulation_id = simulation_id
        self.battle_id = 1
        self.max_x = max_x
        self.max_y = max_y
        self.battle_data = battle_data
        self.usa_count = 0
        self.mexico_count = 0
        self.spain_count = 0
        self.portugal_count = 0
        self.max_count = self.max_x * self.max_y
        self.allies = {
            "USA": ["Mexico"],
            "Mexico": ["USA"],
            "Spain": ["Portugal"],
            "Portugal": ["Spain"]
        }

    def are_allies(self, country1, country2):
        return country2 in self.allies.get(country1, [])

    def get_territory_owner(self, x, y):
        return self.territory_owners.get((x, y))

    def count_territories(self):
        # Count territories owned by each country
        self.usa_count = sum(1 for owner in self.territory_owners.values() if owner == 'USA')
        self.mexico_count = sum(1 for owner in self.territory_owners.values() if owner == 'Mexico')
        self.spain_count = sum(1 for owner in self.territory_owners.values() if owner == 'Spain')
        self.portugal_count = sum(1 for owner in self.territory_owners.values() if owner == 'Portugal')

    def attempt_acquire(self, location, country):
        """
        Attempt to acquire the lock for the given location. If the lock is already acquired,
        a battle ensues.
        """
        lock = self.grid_locks[location]
        owner = self.territory_owners[location]

        # If the country already owns this territory, we do not need to acquire the lock.
        if owner == country.name:
            return True

        # Try to acquire the lock
        if lock.acquire(blocking=False):
            # Since all territories are owned from the start, we don't need to check for None
            print(f"{country.name} is attempting to conquer territory {location} owned by {owner}")
            battle_won = self.battle_for_territory(location, country)
            if battle_won:
                self.succesfull_acquisitions += 1
                print(f"{country.name} has acquired territory {location} after a battle")
            else:
                print(f"{country.name} has lost the fight for {location} against {owner}")
            lock.release()
            return battle_won if owner is not None else True

        else:
            # If the lock cannot be acquired, it means another process/thread is currently engaging in a battle.
            if owner != country.name:
                return False

    def get_adjacent_locations(self, location):
        x, y = location
        adjacent = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]  # Left, right, bottom, top
        valid_adjacent = [(ax, ay) for ax, ay in adjacent if 0 <= ax < self.max_x and 0 <= ay < self.max_y]
        return valid_adjacent

    def choose_strategy_for_battle(self, dictionary):
        strategy = random.choice(list(dictionary.keys()))
        return strategy

    def battle_for_territory(self, location, attacker_country):
        defender_country_name = self.territory_owners[location]

        # Check if attacker and defender are allies
        if self.are_allies(attacker_country.name, defender_country_name):
            print(f"{attacker_country.name} and {defender_country_name} are allies. They cannot battle.")
            return False

        defender_resources = self.territory_resources[location]
        # Identify adjacent locations owned by the attacker
        adjacent_locations = self.get_adjacent_locations(location)
        attacker_adjacent_resources = {"land": 0, "air": 0, "water": 0, "cyber": 0}

        attacker_adjacent_locations = []
        defender_adjacent_locations = []

        for adj_location in adjacent_locations:
            if self.territory_owners[adj_location] == attacker_country.name:
                attacker_adjacent_locations.append(adj_location)
                for resource_type in attacker_adjacent_resources.keys():
                    attacker_adjacent_resources[resource_type] += self.territory_resources[adj_location][resource_type]
            else:
                defender_adjacent_locations.append(adj_location)
        # Let the attacker choose resources from these adjacent locations
        # This is a placeholder - you'll need to implement the logic for choosing resources
        attacker_strategy = self.choose_strategy_for_battle(attacker_adjacent_resources)
        print(f"{attacker_country.name} is attacking {location} with {attacker_strategy} strategy")

        defender_troops = defender_resources[attacker_strategy]
        attacker_troops = attacker_adjacent_resources[attacker_strategy]

        # The chance of winning is proportional to the number of troops, but random
        total_troops = defender_troops + attacker_troops
        if total_troops <= 0:
            return False  # No battle if there are no troops

        # Calculate probabilities based on troop counts
        defender_win_probability = defender_troops / total_troops
        attacker_win_probability = attacker_troops / total_troops

        current_battle_id = self.battle_id
        self.battle_id += 1

        # Decide the winner based on the probabilities
        battle_outcome = random.choices(
            ['defender', 'attacker'],
            weights=[defender_win_probability, attacker_win_probability],
            k=1
        )[0]
        lost_resources_attacker, lost_resources_defender = self.adjust_troops(battle_outcome, attacker_adjacent_locations, defender_adjacent_locations, attacker_strategy,
                           location)

        if attacker_country.name == "USA":
            attacker_counter = self.usa_count
        elif attacker_country.name == "Mexico":
            attacker_counter = self.mexico_count
        elif attacker_country.name == "Spain":
            attacker_counter = self.spain_count
        else:
            attacker_counter = self.portugal_count

        if defender_country_name == "USA":
            defender_counter = self.usa_count
        elif defender_country_name == "Mexico":
            defender_counter = self.mexico_count
        elif defender_country_name == "Spain":
            defender_counter = self.spain_count
        else:
            defender_counter = self.portugal_count

        #We need to make that two allies cannot battle for a territory since they are allies

        if battle_outcome == 'attacker':
            self.territory_owners[location] = attacker_country.name
            # self.territory_troops[location] = attacker_troops - random.randint(0, defender_troops)
            print(f"{attacker_country.name} has won the battle for {location} against {defender_country_name}")
            self.count_territories()
            print(f"{attacker_country.name} Territory Count: {attacker_counter}, {defender_country_name} Territory Count: {defender_counter}")  
            self.insert_data(simulation_id = self.simulation_id, battle_id = current_battle_id,coordinate=location, strategy=attacker_strategy, attacker=attacker_country.name,
                             defender=defender_country_name, winner=battle_outcome,
                             coordinate_count_us=self.usa_count, coordinate_count_mexico=self.mexico_count, coordinate_count_spain=self.spain_count,coordinate_count_portugal=self.portugal_count, lost_resources_att = lost_resources_attacker,lost_resources_def = lost_resources_defender)
            return True
        else:
            # self.territory_troops[location] = defender_troops - random.randint(0, attacker_troops)
            print(f"{defender_country_name} has defended {location} against {attacker_country.name}")
            self.count_territories()
            print(f"{attacker_country.name} Territory Count: {attacker_counter}, {defender_country_name} Territory Count: {defender_counter}") 
            self.insert_data(simulation_id = self.simulation_id, battle_id = current_battle_id,coordinate=location, strategy=attacker_strategy, attacker=attacker_country.name,
                             defender=defender_country_name, winner=battle_outcome,
                             coordinate_count_us=self.usa_count, coordinate_count_mexico=self.mexico_count, coordinate_count_spain=self.spain_count,coordinate_count_portugal=self.portugal_count, lost_resources_att = lost_resources_attacker,lost_resources_def = lost_resources_defender)
            return False



    def adjust_troops(self, battle_outcome, attacker_adjacent_locations, defender_adjacent_locations, attacker_strategy,
                      location):
        # SCENARIO 1
        # if the attacker wins, deduct some % of the adjacent troops that have helped in the battle, but it would also help gaining more troops from the enemy (85 %) that would start fighting for you.
        # if the defender loses the battle, it will lose some of the resources of that strategy (ex: all land resources), but a 15% of the remaining 3 types of resources stays loyal to the defender country and are allocated to other adjacent coordinates.
        lost_resources_attacker = 0
        if battle_outcome == "attacker":
            for coordinate in attacker_adjacent_locations:
                lost_resources_adjacent = (random.randint(0, self.territory_resources[coordinate][attacker_strategy] // 5))
                self.territory_resources[coordinate][attacker_strategy] = (self.territory_resources[coordinate][attacker_strategy]) - lost_resources_attacker 
                lost_resources_attacker += lost_resources_adjacent
            #First deduct 10% from the resources of the location where the battle happened (all battles will have some loss of resources)
            overall_location_loss = (random.randint(0, self.territory_resources[location][attacker_strategy] // 10))
            self.territory_resources[location][attacker_strategy] = (self.territory_resources[location][attacker_strategy]) - overall_location_loss
            time.sleep(0.03)
            
            #Second, allocation of the remaining resources
            defender_allocated = 0
            for key in self.territory_resources[location]:
                defender_proportion = int(self.territory_resources[location][key] * 0.15)
                defender_allocated += defender_proportion
                self.territory_resources[location][key] = (self.territory_resources[location][key]) - defender_proportion  # 85% betrays and convert to the attacker, 15% loyal to defenderr
                for coordinate in defender_adjacent_locations:
                    self.territory_resources[coordinate][key] = (self.territory_resources[coordinate][key]) + int(defender_proportion / len(defender_adjacent_locations))
            lost_resources_defender = overall_location_loss + defender_allocated
        # SCENARIO 2
        # if the attacker loses, it will decrease by x% the resource type for each of its adjacent coordinates
        # if defender wins, decrease that resoruce by 5% (you always lose sth, even if you win)
        # UP TO 5% !!!!!!!!
        
        else:
            for coordinate in attacker_adjacent_locations:
                lost_resources_adjacent = (random.randint(0, self.territory_resources[coordinate][attacker_strategy] // 20))
                self.territory_resources[coordinate][attacker_strategy] = (self.territory_resources[coordinate][attacker_strategy]) - lost_resources_adjacent
                lost_resources_attacker += lost_resources_adjacent
            lost_resources_defender = (random.randint(0, self.territory_resources[location][attacker_strategy] // 5))
            self.territory_resources[location][attacker_strategy] = (self.territory_resources[location][attacker_strategy]) - lost_resources_defender

        return lost_resources_attacker, lost_resources_defender

    def insert_data(self,simulation_id ,attacker, defender, winner, strategy, coordinate, coordinate_count_us, coordinate_count_mexico, coordinate_count_spain, coordinate_count_portugal, battle_id, lost_resources_att, lost_resources_def): 
        dic = {
            "simulation_id": simulation_id,
            "battle_id": battle_id,
            "coordinate": coordinate,
            "strategy": strategy,
            "attacker": attacker,
            "defender": defender,
            "winner": winner,
            "resources_lost_attacker": lost_resources_att, 
            "resources_lost_defender": lost_resources_def, 
            "coordinate_count_us": coordinate_count_us,
            "coordinate_count_mexico": coordinate_count_mexico, 
            "coordinate_count_spain": coordinate_count_spain, 
            "coordinate_count_portugal": coordinate_count_portugal
        }

        battle_data.loc[len(battle_data)] = dic

    def release(self, location, country):
        """
        Release the lock for a given location if the calling country is the owner.
        """
        lock = self.grid_locks[location]
        current_owner = self.territory_owners[location]
        if current_owner == country.name and lock.locked():
            lock.release()
            self.territory_owners[location] = None
            self.territory_troops[location] = 0
            print(f"{country.name} has released territory {location}")


class Country(threading.Thread):
    def __init__(self, name, grid):
        super().__init__()
        self.name = name
        self.grid = grid
        self.territories = set()  # A set to keep track of the territories this country owns
        self.alive = True  # A flag to keep the thread running

    def run(self):
        while self.alive:
            # Country's action logic goes here
            self.try_acquire_territory()
            # Wait a bit before the next action
            time.sleep(random.uniform(0.5, 2.0))


    def try_acquire_territory(self):
        # Country tries to acquire a random territory on the grid
        x = random.randint(0, self.grid.max_x - 1)
        y = random.randint(0, self.grid.max_y - 1)
        acquired = self.grid.attempt_acquire((x, y), self)
        if acquired:
            self.territories.add((x, y)) #PROBLEM: are we removing this coordinate for the losing country??

    def stop_country(self):
        self.alive = False
       

country_colors = {
    "USA": "darkseagreen",
    "Portugal": "sandybrown",
    "Spain": "moccasin", 
    "Mexico": "darkslategray"
   
}


def update_visualization(grid, ax, fig, max_x, max_y, country_colors):
    ax.clear()  # Clear the previous drawing
    ax.set_xlim(0, max_x)  # Set the x-axis limits
    ax.set_ylim(0, max_y)  # Set the y-axis limits
    ax.set_xticks(np.arange(0, max_x, 1))
    ax.set_yticks(np.arange(0, max_y, 1))

    # Iterate through the grid and draw the squares
    for x in range(max_x):
        for y in range(max_y):
            owner = grid.get_territory_owner(x, y)
            # Use a default color (e.g., "white") if territory is not owned by anyone
            color = country_colors.get(owner, "white") if owner else "white"
            ax.add_patch(plt.Rectangle((x, y), 1, 1, color=color))

    # Draw grid lines
    ax.grid(which='both', color='k', linestyle='-', linewidth=1)
    ax.set_aspect('equal')  # Set aspect ratio to ensure squares remain square-shaped

    # Create a legend for the countries
    legend_handles = [Patch(facecolor=color, edgecolor='black', label=country) for country, color in
                      country_colors.items()]
    # Place the legend outside of the grid to the right
    ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))

    # Update the figure canvas
    fig.canvas.draw()
    plt.pause(0.01)


class Environment:
    def __init__(self, max_x, max_y , country_names, troop_mean, troop_sd, simulation_id):
        self.simulation_id = simulation_id
        self.grid = Grid(max_x, max_y, self.simulation_id)  # Unpack grid_size tuple to max_x and max_y
        self.max_x = max_x
        self.max_y = max_y
        self.troop_mean = troop_mean
        self.troop_sd = troop_sd
        self.country_colors = country_colors
        self.countries = {name: Country(name, self.grid) for name in country_names}
        self.initialize_territories()

        self.fig, self.ax = plt.subplots()
        plt.ion()  # Turn on interactive mode for live updates
        update_visualization(self.grid, self.ax, self.fig,  max_x, max_y , self.country_colors)

    def initialize_territories(self):
        print("Initializing territories...")
        for x in range(self.max_x):
            for y in range(self.max_y):
                if x < self.max_x / 2:
                    # Left side of the grid
                    if y < self.max_y / 2:
                        country_name = 'Mexico'
                    else:
                        country_name = 'USA'
                else:
                    # Right side of the grid
                    if y < self.max_y / 2:
                        country_name = 'Portugal'
                    else:
                        country_name = 'Spain'

                # Generate a random number of resources
                print(f"Territory at ({x}, {y}) initialized to {country_name}")
                print("\nRESOURCES:")
                for key in self.grid.territory_resources[(x, y)]:
                    self.grid.territory_resources[(x, y)][key] = max(1, int(np.random.normal(self.troop_mean, self.troop_sd)))
                    print(f"{key} resources: {self.grid.territory_resources[(x, y)][key]}")

                # Add territory to country and update territory owners in the grid
                self.countries[country_name].territories.add((x, y))
                self.grid.territory_owners[(x, y)] = country_name

        print("Initialization complete.")

    def run_simulation(self):
        # Start all country threads
        for country in self.countries.values():
            country.start()

        while any(country.is_alive() for country in self.countries.values()):
            update_visualization(self.grid, self.ax, self.fig, self.grid.max_x, self.grid.max_y, self.country_colors)
            for country in list(self.countries.values()):
                if not country.territories:
                    print(f"{country.name} has no territories left and is out of the simulation.")
                    country.stop_country()
                    self.countries.pop(country.name)

        # End the simulation after x runs
            if self.grid.succesfull_acquisitions >= 20:
                print("20 successful acquisitions have been made. Ending simulation.")
                for country in self.countries.values():
                    country.stop_country()
                total_usa_mex = self.grid.usa_count + self.grid.mexico_count
                total_sp_port = self.grid.spain_count + self.grid.portugal_count
                if total_usa_mex == total_sp_port:
                    print("There was not a clear winner, they ended in a tie")
                elif total_usa_mex > total_sp_port:
                    percentage_dominated = (total_usa_mex / self.grid.max_count)*100
                    print(f"USA & MEXICO WON THE CONQUEST dominating {percentage_dominated:.2f}% of the territory!")
                else: 
                    percentage_dominated = (total_sp_port / self.grid.max_count)*100
                    print(f"SPAIN & PORTUGAL WON THE CONQUEST dominating {percentage_dominated:.2f}% of the territory!")
                break
            time.sleep(1)

        # Wait for all threads to finish
        for country in self.countries.values():
            country.join()

        # After the simulation ends, export the collected battle data
        print("Simulation has ended. Exporting collected battle data.")
        battle_data.to_csv('/Users/fani/Desktop/1st Semester/OPERATING SYSTEMS & PARALLEL COMPUTING/Op.Systems files/battle_data.csv', index=False)
        print("Data exported to 'battle_data.csv'.")

max_x = 6
max_y = 6
country_names = ['USA', 'Mexico', "Spain", "Portugal"]  # Names of the two countries
troop_mean = 100  # Mean for normal distribution of troops
troop_sd = 10  # Standard deviation for normal distribution of troops

#Create simulation_id for this run
simulation_id = uuid.uuid4()
print("Simulation ID:", simulation_id)

# Create the simulation environment
simulation_env = Environment(max_x, max_y, country_names, troop_mean, troop_sd, simulation_id)

# Run the simulation
simulation_env.run_simulation()


# Define the path to your CSV file
csv_file_path = '/Users/fani/Desktop/1st Semester/OPERATING SYSTEMS & PARALLEL COMPUTING/Op.Systems files/battle_data.csv'

with open(csv_file_path, "r") as csvfile:
    # Create a CSV reader object
    csv_reader = csv.reader(csvfile)

    # Skip the header row if it exists
    header = next(csv_reader, None)

    for row in csv_reader:
        # Extract values from the row
        simulation_id, battle_id, coordinate, strategy, attacker, defender, winner, resources_lost_attacker, \
        resources_lost_defender, coordinate_count_us, coordinate_count_mexico, coordinate_count_spain, \
        coordinate_count_portugal = row

        # Define the SQL query to insert data into the MySQL table
        insert_query = f'''
        INSERT INTO territory_conquest_data  (simulation_id,
                battle_id,
                coordinate,
                strategy,
                attacker,
                defender,
                winner,
                resources_lost_attacker,
                resources_lost_defender,
                coordinate_count_us,
                coordinate_count_mexico,
                coordinate_count_spain,
                coordinate_count_portugal)
        VALUES ('{simulation_id}',"{battle_id}", "{coordinate}", "{strategy}", "{attacker}", "{defender}", "{winner}", {resources_lost_attacker}, {resources_lost_defender}, {coordinate_count_us}, {coordinate_count_mexico}, {coordinate_count_spain}, {coordinate_count_portugal})
        '''
        cursor.execute(insert_query)          


# Commit the changes and close the cursor and connection
cnx.commit()
cursor.close()
cnx.close()
