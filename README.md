## Terminal BlackJack Design Doc

### Overview

This goal is to create a BlackJack game that operates solely in the Windows terminal. This game supports multiplayer and most of the standard rules and strategies of Blackjack.

### Tools Used

This game is written in Python. It uses Python's built-in libraries and the `windows-curses` package for Windows compatibility. The `windows-curses` package provides pdcurses functionality for Windows terminals.

### Windows-Specific Changes

1. **Curses Library**: Uses `windows-curses` package which provides pdcurses for Windows
2. **Character Encoding**: Handles Windows string encoding properly (UTF-8 decode for getstr())
3. **Card Symbols**: Uses Windows-compatible Unicode characters (♦♠♥♣)
4. **Avatar Characters**: Limited to A-Z for better Windows terminal compatibility
5. **Error Handling**: Added try-except blocks for curses operations to handle Windows terminal quirks
6. **Color Initialization**: Added color support check and use_default_colors() for better terminal compatibility
7. **Window Dimensions**: Added validation to ensure positive dimensions for derwin()
8. **Safe Drawing**: Implemented safe_addstr() method to prevent boundary errors

### Design Considerations

- There must be a separation between gameplay and displaying graphics. Displaying graphics in terminal can be annoying and have some unforeseen effects, it's better if all display functionality is abstracted away
- A dealer in this game is similar to a player but with special game mechanics. Dealers can just be a subclass of Player.
- The terminal window size is crucial because this could introduce a lot of potential bugs.
  - _PDCurses_ works by drawing strings at specific coordinates in the terminal. If the coordinate is outside the bounds, _PDCurses_ will throw an exception
  - The size of the board and tables must be adaptable to the size of the terminal window so that objects are not either too small or get cut off and throw the aforementioned exception.
  - The solution to this was to divide up player areas into "Partitions", and have a separate "PartitionsManager" class to handle resizing of Partitions
- Cards may be hard to represent given the space constraints described above, because there is a potentially large number of cards each player can be dealt (bounded at 12 cards). Therefore, Cards must be displayed in a way that can be resized based on available space.

### Structure

#### Game:

- Main control loop of program, will manage operation of the game and interaction with user inputs
- Methods
  - `sleep(x)`
    - Sleep for given period of time
  - `run()`
    - Runs main control loop
  - `start()`
  - `gameplay()`
    - Runs the gameplay past the start screen and before end screen
    - States: "betting", "dealing", "turn", "scoring"
  - `end()` -> "Keep Playing?" [Bool]

#### Card:

- Representation of cards in the game, initialized with a suit, a number, and whether or not the card is face down
  - Methods:
    - `flip()`
      - Flips the card from face up to face down

#### Player:

- The Player object keeps track of the score of each player, the current bet amount, the cards in that players hand, and their name/symbol/id etc.
- Each Player object corresponds to a PlayerPartition object in the DisplayTable
- Methods:
  - `add_card(card)`
    - Adds card to the player's hand
  - `make_bet (amount)`
    - "Makes the bet" by modifying bet and score variables
  - `win(), lose(), standoff()`
    - Used to handle each of the three cases that describe a player when comparing their decks to the dealer.
  - `sums()`
    - Calculate all the possible sums of cards that exist
    - For each 'A', double the list of possibilities with half being "A"=1 or "A"=11.

#### Dealer (Player):

- Subclass of Player, with extra dealer functionality
- Methods:
  - `init_deck()`:
    - Initialize a deck with a certain number of decks worth of cards
  - `deal(facedown=False)`
    - Dealer will deal out a random card from the deck and remove it from the deck
  - `reveal()`:
    - Flips over any unflipped cards

#### PlayerPartition:

- Grid space on the terminal is divided into "partitions", one for each player. Each partition consists of the player's name, avatar, a score, a bet, and the cards that player holds.
- Methods:
  - `get_coords()`:
    - Returns the relative coordinates of each element in the partition based on the initial base coordinates of the partition.

#### PartitionManager:

- The primary function of PartitionManager is to keep track of each partition, its relative positions, and resize partitions as necessary based on the screen width and the number of players in the game.
  - Methods:
    - `add_player(self, player_id)`
      - Adds player partition to partition manager
      - Also resize all other player partitions to fit the new partition
    - `remove_player(self, player_id)`
      - Removes player with player.id = player_id
    - 

#### DisplayTable:

- Displayer for Game, takes in abstracted objects and transfers them to the interface. The goal is, Game only needs to change properties of objects without worrying about display, and DisplayTable will automatically update these changes on the interface
- Methods:
  - `refresh()`
    - Refreshes interface and updates all components
  - `print()`
    - Helper function to print text directly into text window, helpful so that there doesn't need to be a separate state for these messages
  - `add_player()`
    - Adds player to internal representation of display
  - `remove_player()`
    - Removes player from internal representation
  - `set_dealer()`
    - Sets the dealer object in display
  - `draw_player(player)`
    - Draws the partition corresponding to "player", according to the coordinates given by Partition and PartitionManager
  - `draw_dealer()`
    - Draws dealer partition
  - `draw_game_menus()`
    - Draws items related to the game progression depending on the state of the game
  - `safe_addstr()`
    - Windows-specific method to safely add strings without boundary errors