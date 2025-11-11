class Cell {
    constructor(name, objects = null, npcs = null, interactions = null, movable = true) {
        this.name = name;
        this.objects = objects || [];
        this.npcs = npcs || [];
        this.interactions = interactions || {};
        this.visited = false;
        this.movable = movable;
    }
}

class NPC {
    constructor(name, description, dialogue, interaction = null) {
        this.name = name;
        this.description = description;
        this.dialogue = dialogue;
        this.interaction = interaction;
    }
}

class GameObject {
    constructor(name, description, interactable = true, interaction = null) {
        this.name = name;
        this.description = description;
        this.interactable = interactable;
        this.interaction = interaction;
    }
}

class Simulation {
    constructor() {
        this.grid_size = [5, 5];
        this.map = {};
        this.player_pos = [2, 4];
        this.player_direction = 0; // 0: North, 1: East, 2: South, 3: West
        this.player_inventory = [];
        this.barista_inventory = [];
        this.pickup_inventory = [];
        this.money_to_pay = 0;
        this.cash = 10;
        this.step = 0;
        this.coffee_acquired = false;
        this.current_interaction = false;
        this.directions = ["North", "East", "South", "West"];
        this.direction_offsets = {
            "North": [0, -1],
            "East": [1, 0],
            "South": [0, 1],
            "West": [-1, 0]
        };
        this.barista = new NPC("Barista", "A cheerful barista behind the counter",
            "Barista: 'Welcome!'",
            () => this.barista_interaction());
        this.andrea = new NPC("Andrea", "Now Andrea really needs coffee",
            "Andrea: 'Get a cup of Americano for me please.'",
            () => this.andrea_interaction());
        this.setup_map();
        this.outputElement = document.getElementById('output');
        this.inputElement = document.getElementById('command-input');
        this.submitButton = document.getElementById('submit-button');
        
        // Set up event listeners
        this.submitButton.addEventListener('click', () => this.handleCommand());
        this.inputElement.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleCommand();
            }
        });
        
        // Set up keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (document.activeElement !== this.inputElement) {
                switch(e.key) {
                    case 'n': this.go_north(); break;
                    case 'e': this.go_east(); break;
                    case 's': this.go_south(); break;
                    case 'w': this.go_west(); break;
                    case 'l': this.look_around(); break;
                }
            }
        });
    }

    printInfo(message) {
        this.outputElement.textContent += message + '\n';
        this.outputElement.scrollTop = this.outputElement.scrollHeight;
    }

    formatObjectList(objects) {
        if (objects && objects.length > 0) {
            return " with " + objects.map(obj => `${obj.name}`).join(", ");
        } else {
            return "";
        }
    }

    formatNpcList(npcs) {
        if (npcs && npcs.length > 0) {
            return " and " + npcs.map(npc => `${npc.name}`).join(", ") + " there";
        } else {
            return "";
        }
    }

    generateDescription(pos) {
        const [x, y] = pos;
        let description = "";
        for (const d of this.directions) {
            const [x_offset, y_offset] = this.direction_offsets[d];
            const new_pos = [x + x_offset, y + y_offset];
            const key = new_pos.join(',');
            if (this.map[key]) {
                description += `To your ${d.toLowerCase()}, it is the ${this.map[key].name}`;
                description += this.formatObjectList(this.map[key].objects);
                description += this.formatNpcList(this.map[key].npcs);
                description += ".\n";
            }
        }
        return description;
    }

    setup_map() {
        // Create rooms with descriptions, objects, and NPCs
        this.map = {
            "0,4": new Cell("Empty Area"),
            "1,4": new Cell(
                "Sitting Area",
                [
                    new GameObject("table", "A small table", false),
                    new GameObject("chair", "A small chair", true, () => this.chair_interaction())
                ]
            ),
            "2,4": new Cell("Empty Area"),
            "3,4": new Cell("Bike Rack"),
            "4,4": new Cell("Road", null, [this.andrea]),

            "0,3": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "1,3": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "2,3": new Cell("Entrance of the Coffee Shop"),
            "3,3": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "4,3": new Cell("Road"),

            "0,2": new Cell(
                "Service Area", [
                    new GameObject("counter", "The counter table of the coffee shop, where you can see milk and water", false),
                    new GameObject("espresso machine", "An Espresso machine in a very good condition", true, () => this.espresso_machine_interaction()),
                    new GameObject("pickup point", "The pickup point", true, () => this.pickup_interaction())
                ]
            ),
            "1,2": new Cell(
                "Service Area", [
                    new GameObject("counter", "The counter of the coffee shop", false),
                    new GameObject("menu", "A menu listing drinks and pastries", true, () => this.menu_interaction()),
                    new GameObject("cash register", "A cash register", true, () => this.cash_register_interaction())
                ],
                [this.barista]
            ),
            "2,2": new Cell("Waiting Area Next to Entrance"),
            "3,2": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "4,2": new Cell("Road"),

            "0,1": new Cell("Service Area", null, null, null, false),
            "1,1": new Cell(
                "Service Area", [
                    new GameObject("counter", "The counter of the coffee shop", false),
                    new GameObject("pastry case", "A pastry case where you can see many pastries", false)
                ]
            ),
            "2,1": new Cell(
                "Sitting Area",
                [
                    new GameObject("table", "A small table", false),
                    new GameObject("chair", "A small chair", true, () => this.chair_interaction())
                ]
            ),
            "3,1": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "4,1": new Cell("Road"),

            "0,0": new Cell("Service Area", null, null, null, false),
            "1,0": new Cell(
                "Service Area", [
                    new GameObject("counter", "The counter of the coffee shop", false)
                ]
            ),
            "2,0": new Cell(
                "Sitting Area",
                [
                    new GameObject("table", "A small table", false),
                    new GameObject("chair", "A small chair", true, () => this.chair_interaction())
                ]
            ),
            "3,0": new Cell("Wall of the Coffee Shop", null, null, null, false),
            "4,0": new Cell("Road")
        };

        // Fill empty spaces with generic descriptions
        for (let x = 0; x < this.grid_size[0]; x++) {
            for (let y = 0; y < this.grid_size[1]; y++) {
                const key = `${x},${y}`;
                if (!this.map[key]) {
                    this.map[key] = new Cell("Empty Area");
                }
            }
        }
    }

    getCurrentCell() {
        const key = this.player_pos.join(',');
        return this.map[key] || new Cell("Empty Area");
    }

    look_around() {
        const cell = this.getCurrentCell();
        this.printInfo(`\nYou are currently at ${cell.name}.`);

        if (!cell.visited) {
            cell.visited = true;
        }

        // Describe objects
        if (cell.objects && cell.objects.length > 0) {
            this.printInfo("\nYou see:");
            for (const obj of cell.objects) {
                this.printInfo(`  - ${obj.name}: ${obj.description}`);
            }
        }

        // Describe NPCs
        if (cell.npcs && cell.npcs.length > 0) {
            this.printInfo("\nPeople here:");
            for (const npc of cell.npcs) {
                this.printInfo(`  - ${npc.name}: ${npc.description}`);
            }
        }

        this.printInfo("\n" + this.generateDescription(this.player_pos));

        // Describe exits
        this.show_exits();
    }

    show_exits() {
        const exits = [];
        const [x, y] = this.player_pos;

        for (const d of this.directions) {
            const [x_offset, y_offset] = this.direction_offsets[d];
            const new_pos = [x + x_offset, y + y_offset];
            const key = new_pos.join(',');
            if (this.map[key] && this.map[key].movable) {
                exits.push(d);
            }
        }

        if (exits.length > 0) {
            this.printInfo(`\nDirections you can go: ${exits.join(', ')}`);
        } else {
            this.printInfo("\nYou cannot move.");
        }
    }

    move_forward() {
        const [x, y] = this.player_pos;
        let new_pos = [...this.player_pos];

        if (this.player_direction === 0) { // North
            new_pos = [x, y - 1];
        } else if (this.player_direction === 1) { // East
            new_pos = [x + 1, y];
        } else if (this.player_direction === 2) { // South
            new_pos = [x, y + 1];
        } else if (this.player_direction === 3) { // West
            new_pos = [x - 1, y];
        }

        const key = new_pos.join(',');
        if (this.map[key] && this.map[key].movable) {
            this.player_pos = new_pos;
            this.printInfo(`You move ${this.directions[this.player_direction].toLowerCase()}.`);
        } else {
            this.printInfo("You can't move in that direction!");
        }

        this.look_around();
    }

    go_north() {
        this.player_direction = 0;
        this.move_forward();
    }

    go_east() {
        this.player_direction = 1;
        this.move_forward();
    }

    go_south() {
        this.player_direction = 2;
        this.move_forward();
    }

    go_west() {
        this.player_direction = 3;
        this.move_forward();
    }

    interact(target_name) {
        const cell = this.getCurrentCell();

        // Check objects first
        if (cell.objects) {
            for (const obj of cell.objects) {
                if (obj.name.toLowerCase() === target_name.toLowerCase()) {
                    if (obj.interactable && obj.interaction) {
                        obj.interaction();
                    } else {
                        this.printInfo(`You look at the ${obj.name}, but there's nothing you can do with it right now.`);
                    }
                    return;
                }
            }
        }

        // Check NPCs
        if (cell.npcs) {
            for (const npc of cell.npcs) {
                if (npc.name.toLowerCase() === target_name.toLowerCase()) {
                    this.printInfo(`\n${npc.dialogue}`);
                    if (npc.interaction) {
                        npc.interaction();
                    }
                    return;
                }
            }
        }

        // Check if target exists elsewhere in the map
        for (const key in this.map) {
            const cell = this.map[key];
            if (cell.objects) {
                for (const obj of cell.objects) {
                    if (obj.name.toLowerCase() === target_name.toLowerCase()) {
                        this.printInfo(`Please try to move closer to ${obj.name}.`);
                        return;
                    }
                }
            }
            if (cell.npcs) {
                for (const npc of cell.npcs) {
                    if (npc.name.toLowerCase() === target_name.toLowerCase()) {
                        this.printInfo(`Please try to move closer to ${npc.name}.`);
                        return;
                    }
                }
            }
        }

        this.printInfo(`There is no such a thing or person called '${target_name}' here. Please check the given information and try other actions.`);
    }

    // Interaction functions
    menu_interaction() {
        this.printInfo("Barista: 'Hi, what can I get for you?'\n");
        const choices = [
            "Buy Espresso ($2)",
            "Buy Cappuccino ($3)",
            "Buy Americano ($2)",
            "Buy some pastries ($5)",
            "Leave without buying"
        ];
        const coffees = ['', 'Espresso', "Cappuccino", "Americano", "Pastries"];
        const prices = [0, 2, 3, 2, 5];

        this.single_choice("What would you like to do?", choices)
            .then(choice => {
                if (choice >= 1 && choice <= 4) {
                    this.printInfo(`Barista: 'Excellent choice! That'll be $${prices[choice]} for your ${coffees[choice]}.'`);
                    this.money_to_pay += prices[choice];
                    this.barista_inventory.push(coffees[choice]);
                } else {
                    this.printInfo("Barista: 'No problem, have a great day!'");
                }
            });
    }

    cash_register_interaction() {
        if (this.money_to_pay > 0) {
            if (this.cash >= this.money_to_pay) {
                for (const item of this.barista_inventory) {
                    this.pickup_inventory.push(item);
                }
                this.barista_inventory = [];
                this.cash -= this.money_to_pay;
                this.money_to_pay = 0;
                this.printInfo("Barista: 'Thank you. Please wait a moment. I'll make your coffee...'");
                setTimeout(() => {this.printInfo("Barista: 'OK, it's ready. Take your coffee please!'")}, 5000);
            } else {
                this.printInfo("Barista: 'It looks like you don't have enough cash.'");
            }
        } else {
            this.printInfo("Barista: 'Hi, how can I help you?'\n");
        }
    }

    pickup_interaction() {
        if (this.pickup_inventory.length > 0) {
            for (const item of this.pickup_inventory) {
                this.player_inventory.push(item);
            }
            this.pickup_inventory = [];
            this.printInfo("You got what you ordered.");
        } else {
            this.printInfo("There's nothing in the pick up point.");
        }
    }

    chair_interaction() {
        const choices = [
            "Sit",
            "Leave"
        ];
        this.single_choice("Choose your action:", choices)
            .then(choice => {
                if (choice === 1) {
                    this.printInfo("You just sat down");
                } else {
                    this.printInfo("You left");
                }
            });
    }

    espresso_machine_interaction() {
        const choices = [
            "Make a single espresso",
            "Make a double espresso",
            "It is a beautiful machine!"
        ];
        this.single_choice("Choose your action:", choices)
            .then(choice => {
                if (choice === 1 || choice === 2) {
                    this.printInfo("Barista: 'Hey! What are you doing?'");
                } else {
                    this.printInfo("Barista: 'Thank you, have a great day!'");
                }
            });
    }

    barista_interaction() {
        if (this.money_to_pay > 0) {
            this.printInfo("\nBarista: 'Did you pay?'");
        } else if (this.pickup_inventory.length > 0) {
            this.printInfo("\nBarista: 'Your coffee is ready. Did you take your coffee?'");
        } else {
            this.printInfo("\nBarista: 'Morning! What can I do for you?'");
        }
    }

    andrea_interaction() {
        this.printInfo("\nAndrea: 'Did you get my coffee?'");

        const choices = [
            "Yes, here you are",
            "No",
            "Leave without saying anything"
        ];
        this.single_choice("What would you like to do?", choices)
            .then(choice => {
                if (choice === 1) {
                    if (this.player_inventory.includes("Americano")) {
                        this.printInfo("Andrea: 'Thank you! Good job!'");
                        this.printInfo('=== You have completed the task! ===');
                        this.coffee_acquired = true;
                    } else {
                        this.printInfo("Andrea: 'I don't see my Americano. Can you help me get one?'");
                    }
                } else {
                    this.printInfo("Andrea: 'No problem, take your time.'");
                }
            });
    }

    single_choice(prompt, options) {
        return new Promise((resolve) => {
            this.printInfo(`\n${prompt}`);
            for (let i = 0; i < options.length; i++) {
                this.printInfo(`${i + 1}. ${options[i]}`);
            }

            // Create a temporary input handler for this choice
            const tempHandler = (command) => {
                try {
                    const choice = parseInt(command.detail);
                    if (choice >= 1 && choice <= options.length) {
                        // Remove the temporary handler
                        document.removeEventListener('choiceEntered', tempHandler);
                        resolve(choice);
                    } else {
                        this.printInfo(`Please enter a number between 1 and ${options.length}`);
                    }
                } catch (e) {
                    this.printInfo(`Please enter a number between 1 and ${options.length}`);
                }
            };

            // Use a custom event to handle the choice
            document.addEventListener('choiceEntered', tempHandler);
        });
    }

    show_help() {
        this.printInfo("\nCOMMANDS:  n -- Go north   e -- Go east   s -- Go south   w -- Go west   l - Look around   interact [thing] - Interact with an object or person");
    }

    handleCommand() {
        const command = this.inputElement.value.toLowerCase().trim();
        this.inputElement.value = '';
        
        this.printInfo("\n" + "-".repeat(20));
        
        // Check if we need to trigger a choice event
        if (command.match(/^\d+$/)) {
            const event = new CustomEvent('choiceEntered', { detail: command });
            document.dispatchEvent(event);
        } else if (command === 'quit' || command === 'exit') {
            this.printInfo("Thanks for playing! Better luck next time getting that coffee!");
            return;
        } else if (command === 'n') {
            this.go_north();
        } else if (command === 'e') {
            this.go_east();
        } else if (command === 's') {
            this.go_south();
        } else if (command === 'w') {
            this.go_west();
        } else if (command === 'look' || command === 'l') {
            this.look_around();
        } else if (command.startsWith('interact ')) {
            const target = command.substring(9);
            this.interact(target);
        } else if (command === 'help') {
            this.show_help();
        } else {
            this.printInfo("Unknown command.");
        }
        
        // Check win condition
        if (this.coffee_acquired) {
            this.printInfo("Thanks for playing! Enjoy your coffee!");
        }
        
    }

    play(mission) {
        this.printInfo("\nYou're a robotic assistant of Andrea. Andrea woke up feeling extremely tired, and desperately needs coffee.");
        this.printInfo("You're now standing in front of a coffee shop. Andrea tells you your mission:\n");
        this.printInfo(`*** ${mission} ***`);
        this.printInfo("Andrea is waiting for you on the road (near the bike rack)!");
        
        this.step = 0;
        this.look_around();
        this.show_help();
    }
}

// Start the game when the page loads
window.onload = function() {
    const mission = "Please get me an Americano. Buy it from the coffee shop and give it to me.";
    const game = new Simulation();
    game.play(mission);
};
