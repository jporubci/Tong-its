##Dependencies:
The easiest way to play is to install on the student machines with ssh.

If you want to install it elsewhere, you'll need to make sure you have all the necessary programs and modules.

* Python 3.11 (tested on 3.11.2)
* Some Python modules


##How to Install:
###On macOS with SSH:
1. ssh into a student machine.
1. Navigate to a desirable directory to clone this repository.
1. Enter `git clone git@github.com:jporubci/Tong-its.git`.


###On macOS with ZIP:
Note, this has not been tested. Furthermore, the shebang and corresponding python3 path might not be correct if installed this way.

1. Download this repository's ZIP.
1. Extract the ZIP to a desirable destination.
1. Optional: The extracted ZIP will be a folder that holds this respository's contents in a folder with the same name as this repository. Since you only need one top-level folder to hold this repository's contents, you can move the repository's folder to the directory where you extracted the ZIP. This should replace the repository folder being nested in the extracted ZIP folder with just the repository folder, leaving you with one top-level folder holding the precious contents. Clean.
1. Move the ZIP to the trash.


###On Windows:
This game was not designed for Windows and it won't display properly because I only use `os.system('clear')`, not `os.system('cls')`, and I don't check for the operating system type, but it should still be theoretically playable. That said, i forgor how to even ssh on windows, i'd prob use PuTTY and try to generally follow the installation instructions for macOS, remembering that slashes are sometimes backwards on windows. if installing with the ZIP, then it should be p much the same as with macOS.


##How to Run:
1. Change your working directory to this repository's directory, wherever you installed it.
1. Enter `python3 tong-its.py`.


##What is Tong-its?
Tong-its is a turn-based 3-player card game that uses the standard 52-card deck of French-suited playing cards. Aces are low cards worth 1 point. Jacks, Queens, and Kings are worth 10 points. All other cards are worth the same number of points as their rank. Tong-its is about creating completed sets or runs of cards, and making strategic decisions that favor the odds.


##How to Play:
First, some definitions.

A `set` of cards (in this game) is 3 or 4 cards of the same rank; in other words, 3 or 4 of a kind. Rank is distinct from point value. 10s, Jacks, Queens, and Kings all share the same point value (10) but are not considered the same rank.

A `run` of cards (in this game) is 3 to 13 cards of the same suit and consecutive ranks. The order of ranks is Ace, 2, 3, 4, 5, 6, 7, 8, 9, 10, Jack, Queen, and King.

A `meld` is a set or run of cards, as defined for this game.

`Expose` is an action that a player can perform on a meld in their hand. Exposing a meld means placing the meld face-up. You must have at least one exposed meld by the end of the game in order to win.

`Draw` is an action that a player may perform. This is not to be confused with drawing a card. This term will typically be used in the phrase `call a draw` so as to avoid confusion. You should call a draw if you believe that the unmelded cards in your hand sum up to the least number of points among the players with at least one exposed meld.

`Challenge` and `fold` are actions that a player may perform in response to a draw.

1. The game starts with a shuffled face-down deck. Each player gets 12 random cards. The turn-order is randomly determined.
1. At the beginning of your turn, you may perform one of up to three actions.
   - Draw a card from the top of the deck
     - You may always draw from the deck.
   - Draw a card from the top of the discard pile
     - You may only draw from the discard pile to expose a meld with it using the cards in your hand.
   - Call a draw
     - You may only call a draw if you have at least one exposed meld, it would be the first action you perform during your turn, and nobody has layed off any cards on any of your exposed melds since the end of your previous turn.
1. If you call a draw, the game ends. See the last numbered entry in this list for details on draws. If you draw from the discard and empty your hand by exposing meld, you win. Otherwise, if you draw a card and still have cards in your hand, you may perform one of up to three actions.
   - Expose a meld
   - Lay off a card
   - Discard a card
1. If you empty your hand by exposing a meld, laying off a card, or discarding a card you win. Your turn ends when you discard a card.
1. If the deck is exhausted, the game ends. Players without any exposed melds automatically lose. The rest of the players with at least one exposed meld sums the number of points that the unmeldable cards in their hand are worth. The player whose hand is the lowest value wins. In the case of a tie, the player who drew the last card from the deck wins. If the tie is between the other two players, then the player whose turn it would have been next wins. If the deck is not exhausted, the next player's turn begins.
1. When a draw is called, players may choose to either challenge or fold. You must have exposed at least one meld in order to challenge a draw. If you fold, you lose. If you challenge, the procedure is similar to when the deck is exhausted. Determine the value of your hand and compare it. The player that called the draw wins if their hand is worth the fewest points. In the case of a tie, the player that called the draw loses. If there is a tie between two challengers, the player whose turn it would have been next wins.


##How to Play Tips:
* Try to expose at least one meld. You cannot win without exposing at least one meld unless you manage to lay off your entire hand onto other players' melds, but good luck doing that.
* You can lay off a card on another player's meld to prevent them from calling a draw during their upcoming turn.
* Don't always expose a meld if you have one. If someone calls a draw or the deck is exhausted, you can always meld cards in your hand at the end to lower the value of your hand. Exposing a meld allows other players to lay off cards from their hand. Expose a meld if you can get rid if all the cards from your hand or if you would greatly benefit from someone laying off a card onto your meld. For example, if you have an 8, 9, 10, Queen, and King of the same suit, but not the Jack, you could expose the 8, 9, and 10 in hopes of someone laying off the Jack to enable you to lay off your Queen and King. Beware however that this could allow someone to lay off a 7 or more onto your meld. Ideally, the 7 would be in the discard, and not on the top of it.
* Be careful what you discard. Discarding high-value cards will reduce the value of your hand more, but it could enable the next player to expose a meld with the card you discarded, and a high-value card means a meld with high-value cards.
* Call a draw if you believe your hand is worth the fewest number of points among the players with at least one exposed meld. If you can call a draw and nobody else has exposed a meld, you can automatically win.
* Have fun!


##TODO:

* Implement message authentication so that users may only receive messages from other users that are logged-in to the student machines.
* Implement the scoring mechanism with betting and a pot so there is a reason to fold.
* Add more information to the Dependencies section of the README.
* ~~Write installation instructions for Windows users lol.~~


##Potential Ideas:

* Give users the option to create custom color themes for displayed text.
* Add a sound notification to inform host when a client player joins the lobby.
* Add a sound notification to inform all players when a game starts.
* Add a text and/or sound notification to inform client players when a player is kicked from the lobby.
* Add a text and/or sound notification to inform a kicked player when they are kicked.
* Block players from rejoining lobbies that they were kicked from for either a certain amount of time or indefinitely.
* Display the most recent action so game events are more clear for all players.
* Log game history for in-game and/or post-game review.


##Rejected Ideas:

* Implement any chat.
* Record any user's statistics such as their number of wins and losses.
