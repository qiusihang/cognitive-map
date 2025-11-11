import re
from dotenv import load_dotenv
import os
import sys
import time
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import Agent

class Cell:
    def __init__(self, name, objects=None, npcs=None, interactions=None, movable=True):
        self.name = name
        self.objects = objects or []
        self.npcs = npcs or []
        self.interactions = interactions or {}
        self.visited = False
        self.movable = movable

class NPC:
    def __init__(self, name, description, dialogue, interaction=None):
        self.name = name
        self.description = description
        self.dialogue = dialogue
        self.interaction = interaction

class GameObject:
    def __init__(self, name, description, interactable=True, interaction=None):
        self.name = name
        self.description = description
        self.interactable = interactable
        self.interaction = interaction

class Simulation:
    def __init__(self, player_is_human = True, use_rag = False, knowledge = []):
        self.grid_size = (5, 5)
        self.map = {}
        self.player_is_human = player_is_human
        if not player_is_human:
            load_dotenv()
            OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
            if OPENROUTER_API_KEY is None:
                print("API Key isn't found.")
                exit(0)
            self.agent = Agent(
                openrouter_api_key=OPENROUTER_API_KEY, 
                model="qwen/qwen3-235b-a22b-2507", #"alibaba/tongyi-deepresearch-30b-a3b:free", 
                load_embedding=use_rag
            )
            self.use_rag = use_rag
            if self.use_rag:
                self.agent.add_documents(knowledge)
        self.player_pos = (2, 4)
        self.player_direction = 0  # 0: North, 1: East, 2: South, 3: West
        self.player_inventory = []
        self.barista_inventory = []
        self.pickup_inventory = []
        self.money_to_pay = 0
        self.cash = 10
        self.step = 0
        self.coffee_acquired = False
        self.current_interaction = None
        self.directions = ["North", "East", "South", "West"]
        self.direction_offsets = {
            "North": ( 0, -1),
            "East":  ( 1,  0),
            "South": ( 0,  1),
            "West":  (-1,  0)
        }
        self.barista = NPC("Barista", "A cheerful barista behind the counter",
                        "Barista: 'Welcome!'",
                        self.barista_interaction)
        self.andrea = NPC("Andrea", "Now Andrea really needs coffee",
                        "Andrea: 'Get a cup of Americano for me please.'",
                        self.andrea_interaction)
        self.printed_info = ""
        self.setup_map()
    
    def print_info(self, message):
        print(message)
        self.printed_info += message

    def format_object_list(self, objects):
        if objects:
            return " with " + (", ".join([f"{object.name}" for object in objects]))
        else:
            return ""
    
    def format_npc_list(self, npcs):
        if npcs:
            return " and " + (", ".join([f"{npc.name}" for npc in npcs])) + " there"
        else:
            return ""
    
    def generate_description(self, pos):
        x, y = pos
        description = ""
        for d in self.directions:
            x_offset, y_offset = self.direction_offsets[d]
            new_pos = (x+x_offset, y+y_offset)
            if new_pos in self.map:
                description += f"To your {d.lower()}, it is the {self.map[new_pos].name}"
                description += self.format_object_list(self.map[new_pos].objects)
                description += self.format_npc_list(self.map[new_pos].npcs)
                description += ".\n"
        return description


    def setup_map(self):
        # Create rooms with descriptions, objects, and NPCs
        self.map = {
            (0, 4): Cell("Empty Area"),
            (1, 4): Cell(
                "Sitting Area",
                objects=[
                    GameObject("table", "A small table", interactable=False),
                    GameObject("chair", "A small chair", interactable=True, interaction=self.chair_interaction)
                ]
            ),
            (2, 4): Cell("Empty Area"),
            (3, 4): Cell("Bike Rack"),
            (4, 4): Cell("Road", npcs=[self.andrea]),

            (0, 3): Cell("Wall of the Coffee Shop", movable=False),
            (1, 3): Cell("Wall of the Coffee Shop", movable=False),
            (2, 3): Cell("Entrance of the Coffee Shop"),
            (3, 3): Cell("Wall of the Coffee Shop", movable=False),
            (4, 3): Cell("Road"),

            (0, 2): Cell(
                "Service Area", objects=[
                    GameObject("counter", "The counter table of the coffee shop, where you can see milk and water", interactable=False),
                    GameObject("espresso machine", "An Espresso machine in a very good condition", interactable=True, interaction=self.espresso_machine_interaction),
                    GameObject("pickup point", "The pickup point", interactable=True, interaction=self.pickup_interaction)
                ]
            ),
            (1, 2): Cell(
                "Service Area", objects=[
                    GameObject("counter", "The counter of the coffee shop", interactable=False),
                    GameObject("menu", "A menu listing drinks and pastries", interactable=True, interaction=self.menu_interaction),
                    GameObject("cash register", "A cash register", interactable=True, interaction=self.cash_register_interaction)
                ],
                npcs=[self.barista]
            ),
            (2, 2): Cell("Waiting Area Next to Entrance"),
            (3, 2): Cell("Wall of the Coffee Shop", movable=False),
            (4, 2): Cell("Road"),

            (0, 1): Cell("Service Area", movable=False),
            (1, 1): Cell(
                "Service Area", objects=[
                    GameObject("counter", "The counter of the coffee shop", interactable=False),
                    GameObject("pastry case", "A pastry case where you can see many pastries", interactable=False)
                ]
            ),
            (2, 1): Cell(
                "Sitting Area",
                objects=[
                    GameObject("table", "A small table", interactable=False),
                    GameObject("chair", "A small chair", interactable=True, interaction=self.chair_interaction)
                ]
            ),
            (3, 1): Cell("Wall of the Coffee Shop", movable=False),
            (4, 1): Cell("Road"),

            (0, 0): Cell("Service Area", movable=False),
            (1, 0): Cell(
                "Service Area", objects=[
                    GameObject("counter", "The counter of the coffee shop", interactable=False)
                ]
            ),
            (2, 0): Cell(
                "Sitting Area",
                objects=[
                    GameObject("table", "A small table", interactable=False),
                    GameObject("chair", "A small chair", interactable=True, interaction=self.chair_interaction)
                ]
            ),
            (3, 0): Cell("Wall of the Coffee Shop", movable=False),
            (4, 0): Cell("Road")
        }
        
        # Fill empty spaces with generic descriptions
        for x in range(self.grid_size[0]):
            for y in range(self.grid_size[1]):
                if (x, y) not in self.map:
                    self.map[(x, y)] = Cell("Empty Area")

    def get_current_cell(self):
        return self.map.get(self.player_pos, Cell("Empty Area"))

    def look_around(self):
        cell = self.get_current_cell()
        self.print_info(f"\nYou are currently at {cell.name}.")
        
        if not cell.visited:
            cell.visited = True

        # Describe objects
        if cell.objects:
            self.print_info("\nYou see:")
            for obj in cell.objects:
                self.print_info(f"  - {obj.name}: {obj.description}")

        # Describe NPCs
        if cell.npcs:
            self.print_info("\nPeople here:")
            for npc in cell.npcs:
                self.print_info(f"  - {npc.name}: {npc.description}")

        self.print_info("\n"+self.generate_description(self.player_pos))

        # Describe exits
        self.show_exits()

    def show_exits(self):
        exits = []
        x, y = self.player_pos
        
        for d in self.directions:
            x_offset, y_offset = self.direction_offsets[d]
            new_pos = (x+x_offset, y+y_offset)
            if new_pos in self.map and self.map[new_pos].movable:
                exits.append(d)
        
        if exits:
            self.print_info(f"\nDirections you can go: {', '.join(exits)}")
        else:
            self.print_info("\nYou cannot move.")

    def move_forward(self):
        x, y = self.player_pos
        new_pos = self.player_pos
        
        if self.player_direction == 0:  # North
            new_pos = (x, y-1)
        elif self.player_direction == 1:  # East
            new_pos = (x+1, y)
        elif self.player_direction == 2:  # South
            new_pos = (x, y+1)
        elif self.player_direction == 3:  # West
            new_pos = (x-1, y)
            
        if new_pos in self.map and self.map[new_pos].movable:
            self.player_pos = new_pos
            self.print_info(f"You move {self.directions[self.player_direction].lower()}.")
        else:
            self.print_info("You can't move in that direction!")

    def go_north(self):
        self.player_direction = 0
        self.move_forward()
    
    def go_east(self):
        self.player_direction = 1
        self.move_forward()
    
    def go_south(self):
        self.player_direction = 2
        self.move_forward()
    
    def go_west(self):
        self.player_direction = 3
        self.move_forward()

    def interact(self, target_name):
        cell = self.get_current_cell()
        
        # Check objects first
        for obj in cell.objects:
            if obj.name.lower() == target_name.lower():
                if obj.interactable and obj.interaction:
                    obj.interaction()
                else:
                    self.print_info(f"You look at the {obj.name}, but there's nothing you can do with it right now.")
                return
        
        # Check NPCs
        for npc in cell.npcs:
            if npc.name.lower() == target_name.lower():
                self.print_info(f"\n{npc.dialogue}")
                if npc.interaction:
                    npc.interaction()
                return
        
        for cell in self.map:
            for obj in self.map[cell].objects:
                if obj.name.lower() == target_name.lower():
                    self.print_info(f"Please try to move closer to {obj.name}.")
                    return
            for npc in self.map[cell].npcs:
                if npc.name.lower() == target_name.lower():
                    self.print_info(f"Please try to move closer to {npc.name}.")
                    return

        self.print_info(f"There is no such a thing or person called '{target_name}' here. Please check the given information and try other actions.")


    # Interaction functions
    def menu_interaction(self):
        self.print_info("Barista: 'Hi, what can I get for you?'\n")
        choices = [
            f"Buy Espresso ($2)",
            f"Buy Cappuccino ($3)", 
            f"Buy Americano ($2)",
            f"Buy some pastries ($5)",
            "Leave without buying"
        ]
        coffees = ['', 'Espresso', "Cappuccino", "Americano", "Pastries"]
        prices = [0, 2, 3, 2, 5]
        
        choice = self.single_choice("What would you like to do?", choices) 

        if choice in [1,2,3,4]:
            self.print_info(f"Barista: 'Excellent choice! That'll be ${prices[choice]} for your {coffees[choice]}.'")
            self.money_to_pay += prices[choice]
            self.barista_inventory.append(coffees[choice])
        else:
            self.print_info("Barista: 'No problem, have a great day!'")


    def cash_register_interaction(self):
        if self.money_to_pay > 0:
            if self.cash >= self.money_to_pay:
                for item in self.barista_inventory:
                    self.pickup_inventory.append(item)
                self.barista_inventory = []
                self.cash -= self.money_to_pay
                self.money_to_pay = 0
                self.print_info(f"Barista: 'Thank you. Please wait a moment. I'll make your coffee...'")
                self.print_info(f"Barista: 'OK, it's ready. Take your coffee please!'")
            else:
                self.print_info(f"Barista: 'It looks like you don't have enough cash.'")
        else:
            self.print_info("Barista: 'Hi, how can I help you?'\n")
        

    def pickup_interaction(self):
        if len(self.pickup_inventory) > 0:
            for item in self.pickup_inventory:
                self.player_inventory.append(item)
            self.pickup_inventory = []
            self.print_info("You got what you ordered.")
        else:
            self.print_info("There's nothing in the pick up point.")


    def chair_interaction(self):
        choices = [
            "Sit",
            "Leave"
        ]
        choice = self.single_choice("Choose your action:", choices) 
        if choice == 1:
            self.print_info("You just sat down")
        else:
            self.print_info("You left'")


    def espresso_machine_interaction(self):
        choices = [
            f"Make a single espresso",
            f"Make a double espresso", 
            "It is a beautiful machine!"
        ]
        choice = self.single_choice("Choose your action:", choices) 

        if choice in [1,2]:
            self.print_info("Barista: 'Hey! What are you doing?'")
        else:
            self.print_info("Barista: 'Thank you, have a great day!'")


    def barista_interaction(self):
        if self.money_to_pay > 0:
            self.print_info("\nBarista: 'Did you pay?'")
        elif len(self.pickup_inventory) > 0:
            self.print_info("\nBarista: 'Your coffee is ready. Did you take your coffee?'")
        else:
            self.print_info("\nBarista: 'Morning! What can I do for you?'")


    def andrea_interaction(self):
        self.print_info("\nAndrea: 'Did you get my coffee?'")

        choices = [
            f"Yes, here you are",
            f"No", 
            "Leave without saying anything"
        ]
        choice = self.single_choice("What would you like to do?", choices) 
        if choice == 1:
            if "Americano" in self.player_inventory:
                self.print_info(f"Andrea: 'Thank you! Good job!'")
                self.print_info('=== You have completed the task! ===')
                self.coffee_acquired = True
            else:
                self.print_info(f"Andrea: 'I don't see my Americano. Can you help me get one?'")
        else:
            self.print_info("Andrea: 'No problem, take your time.'")


    def single_choice(self, prompt, options):
        while True:
            self.print_info(f"\n{prompt}")
            for i, option in enumerate(options, 1):
                self.print_info(f"{i}. {option}")
            try:
                choice = int(self.command_input("Enter your command (number): "))
                if 1 <= choice <= len(options):
                    return choice
                else:
                    self.print_info(f"Please enter a number between 1 and {len(options)}")
                    self.llm_input_hint()
            except ValueError:
                self.print_info(f"Please enter a number between 1 and {len(options)}")
                self.llm_input_hint()


    def show_help(self):
        self.print_info("\nCOMMANDS:  n -- Go north   e -- Go east   s -- Go south   w -- Go west   l - Look around   interact [thing] - Interact with an object or person")


    def llm_input_hint(self):
        if not self.player_is_human:
            self.print_info(r"You can input only one command each time. Use the following format {input: command}.")


    def command_input(self, message):
        if self.player_is_human:
            command = input("\n"+message+" ")
        else:
            # Generate response
            self.print_info("\n"+message+" ")
            self.llm_input_hint()
            response = self.agent.generate_response(self.printed_info, use_rag=self.use_rag)
            print(f"\nAssistant: {response}")
            command = self.extract_command(response)
            print(f"Assistant Command: {command}")
        self.printed_info = "" # clear printing history after each input
        return command


    def extract_command(self, text):
        text = text.replace('[','')
        text = text.replace(']','')
        pattern = re.compile(
            r'(?s)(?i)\{.*?["\']?input["\']?\s*:\s*(?:"([^"]*?)"|\'([^\']*?)\'|([^}]+?))\s*\}'
        )
        matches = pattern.findall(text)
        if not matches:
            return "/"
        last_match_tuple = matches[0] # get the first match
        for command_group in last_match_tuple:
            if command_group:
                return command_group.strip()
        return "/"


    def play(self, mission):
        self.print_info("\nYou're a robotic assistant of Andrea. Andrea woke up feeling extremely tired, and desperately needs coffee.")
        self.print_info("You're now standing in front of a coffee shop. Andrea tells you your mission:\n")
        self.print_info(f"*** {mission} ***")
        self.print_info("Andrea is waiting for you on the road (near the bike rack)!")
        
        self.step = 0
        rounds = 0
        while True:
            self.step += 1
            rounds += 1
            if self.step > 30:
                self.print_info("Too many steps! Thank you.")
                break
            if rounds > 100:
                self.print_info("Problematic.")
                exit(0)
            if self.current_interaction:
                # Handle ongoing interaction
                pass
            else:
                # Normal movement mode
                self.look_around()
                self.show_help()
                command = self.command_input("What would you like to do? ").lower().strip()

                self.print_info("\n"+"-"*20)
                if command in ['quit', 'exit']:
                    self.print_info("Thanks for playing! Better luck next time getting that coffee!")
                    break
                elif command in ['n']:
                    self.go_north()
                elif command in ['e']:
                    self.go_east()
                elif command in ['s']:
                    self.go_south()
                elif command in ['w']:
                    self.go_west()
                elif command in ['look', 'l']:
                    self.look_around()
                elif command.startswith('interact '):
                    target = command[9:]
                    self.interact(target)
                elif command == 'help':
                    self.show_help()
                else:
                    self.step -= 1
                    self.print_info("Unknown command.")
                    if not self.player_is_human:
                        self.print_info(r"You can input only one command each time. Use the following format {input: command}.")
                
            if self.coffee_acquired:
                self.print_info("Thanks for playing! Enjoy your coffee!")
                break
            time.sleep(5) # avoid too frequent requests


def agent_game():
    for use_rag in [True, False]:
        stats = {"steps":[], "coffee_acquired":[], "coffee_picked":[], "coffee_bought":[], "coffee_ordered":[]}
        mission = "Please get me an Americano. Buy it from the coffee shop and give it to me." # mission 1
        mission = "Please get me an Americano. Here's what to do: go in through the entrance, check the menu for Americanos, order and pay at the cash register, wait for it to be made, then bring it to me from the pickup point." # mission 2
        if use_rag:
            stats_file = 'output/stat_rag_mission2.csv'
        else:
            stats_file = 'output/stat_no_rag_mission2.csv'

        # Read file and store each line in a list
        with open('output/knowledge.txt', 'r') as file: knowledge = file.readlines()
        # Remove newline characters from each line
        knowledge = [line.strip() for line in knowledge]

        for i in range(50):
            game = Simulation(player_is_human=False, use_rag=use_rag, knowledge=knowledge)
            if use_rag:
                similar_docs = game.agent.search_similar_documents(mission, 5)
                if similar_docs:
                    context = ""
                    for i, doc in enumerate(similar_docs, 1):
                        context += f"{doc['content']}\n"
                print(context)
                game.agent.context = context
            game.play(mission)
            stats["coffee_ordered"].append( 1 if "Americano" in game.barista_inventory or "Americano" in game.pickup_inventory or "Americano" in game.player_inventory else 0 )
            stats["coffee_bought"].append( 1 if "Americano" in game.pickup_inventory  or "Americano" in game.player_inventory else 0 )
            stats["coffee_picked"].append( 1 if "Americano" in game.player_inventory else 0 )
            stats["coffee_acquired"].append( 1 if game.coffee_acquired else 0 )
            stats["steps"].append( game.step )
            df = pd.DataFrame(stats)
            df.to_csv(stats_file, index=False)

def human_game():
    mission = "I want a cup of Americano, buy it from the coffee shop and give it to me." # mission 1
    game = Simulation(player_is_human=True)
    game.play(mission)

# Run the game
if __name__ == "__main__":
    human_game()
