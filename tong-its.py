#!/usr/bin/env python3
# tong-its.py

# To read stdin and write stdout without blocking 
import curses

# Import lobby.py
import lobby

# os.system('clear') to clear screen
import os

# To enable use of send_message and get_message
import asyncio

# To send lists of cards as messages
from server import decompose, compose, Server

# To simplify message sending and receiving
from config import send_message, get_message, Constants


# Send game state to players other than host
async def send_gamestate(ret_val, server):
    for i in range(1, len(server.players)):
        
        # Send remaining deck size, discard, and order of play
        await send_message(ret_val[i-1][1], {'deck_size': len(server.deck), 'discard': decompose(server.discard), 'order': server.order, 'id': i})
        
        # Send each players' information to each player
        for j in range(0, len(server.players)):
            
            # Send detailed info if it's the player's own info
            if i == j:
                await send_message(ret_val[i-1][1], {'score': server.players[j].score, 'name': server.players[j].name, 'hand': decompose(server.players[j].hand), 'melds': [decompose(meld) for meld in server.players[j].melds], 'can_draw': server.players[j].can_draw})
            
            # Send vague info if it's not the player's own info
            else:
                await send_message(ret_val[i-1][1], {'score': server.players[j].score, 'name': server.players[j].name, 'num_cards': len(server.players[j].hand), 'melds': [decompose(meld) if meld else None for meld in server.players[j].melds], 'can_draw': server.players[j].can_draw})


# Display function for host (Draws other clients in turn order first, then self last)
def host_display(server):
    # Determine client player draw order
    draw_order = server.order[server.order.index(0)+1:] + server.order[:server.order.index(0)]
    for i in draw_order:
        # Display client players's vague info in order
        print(f'{server.players[i].name}')
        print(f'Score: {server.players[i].score}')
        print(f'Cards: {len(server.players[i].hand)}')
        
        # Display melds
        print(f'Melds:')
        for meld in server.players[i].melds:
            meld.sort(key=lambda x: x.suit)
            meld.sort(key=lambda x: Constants().RANKS.index(x.rank))
            print(f'{meld[0].rank.rjust(2)}{meld[0].suit}', end='')
            for j in range(1, len(meld)):
                print(f'{meld[j].rank.rjust(2)}{meld[j].suit}', end='')
            print()
        print()
    
    # Draw self
    print(f'{server.players[0].name}')
    print(f'Score: {server.players[0].score}')
    print(f'Cards: {len(server.players[0].hand)}')
    
    # Display melds
    print(f'Melds:')
    for meld in server.players[0].melds:
        meld.sort(key=lambda x: x.suit)
        meld.sort(key=lambda x: Constants().RANKS.index(x.rank))
        print(f'{meld[0].rank.rjust(2)}{meld[0].suit}', end='')
        for j in range(1, len(meld)):
            print(f' {meld[j].rank.rjust(2)}{meld[j].suit}', end='')
        print()
    print()
    
    # Display hand
    server.players[0].hand.sort(key=lambda x: x.suit)
    server.players[0].hand.sort(key=lambda x: Constants().RANKS.index(x.rank))
    print(f'{server.players[0].hand[0].rank.rjust(2)}{server.players[0].hand[0].suit}', end='')
    for i in range(1, len(server.players[0].hand)):
        print(f' {server.players[0].hand[i].rank.rjust(2)}{server.players[0].hand[i].suit}', end='')
    print()
    
    # Display deck and discard
    print(f'Deck: {len(server.deck)}')
    print('Discard:', end='')
    if server.discard:
        for card in server.discard:
            print(f' {card.rank.rjust(2)}{card.suit}', end='')
    print('\n')


# Display function for clients (Draws other players in turn-order first, then self last)
def client_display(gamestate, players):
    # Determine client player draw order (order of drawing aka printing to display)
    draw_order = gamestate['order'][gamestate['order'].index(gamestate['id'])+1:] + gamestate['order'][:gamestate['order'].index(gamestate['id'])]
    for i in draw_order:
        # Display client players's vague info in order
        print(f'{players[i]["name"]}')
        print(f'Score: {players[i]["score"]}')
        print(f'Cards: {players[i]["num_cards"]}')
        
        # Display melds
        print(f'Melds:')
        for meld in players[i]['melds']:
            meld.sort(key=lambda x: x[1])
            meld.sort(key=lambda x: Constants().RANKS.index(x[0]))
            print(f'{meld[0][0].rjust(2)}{meld[0][1]}', end='')
            for j in range(1, len(meld)):
                print(f'{meld[j][0].rjust(2)}{meld[j][1]}', end='')
            print()
        print()
    
    # Draw self
    print(f'{players[gamestate["id"]]["name"]}')
    print(f'Score: {players[gamestate["id"]]["score"]}')
    print(f'Cards: {len(players[gamestate["id"]]["hand"])}')
    
    # Display melds
    print(f'Melds:')
    for meld in players[gamestate['id']]['melds']:
        meld.sort(key=lambda x: x[1])
        meld.sort(key=lambda x: Constants().RANKS.index(x[0]))
        print(f'{meld[0][0].rjust(2)}{meld[0][1]}', end='')
        for j in range(1, len(meld)):
            print(f' {meld[j][0].rjust(2)}{meld[j][1]}', end='')
        print()
    print()
    
    # Display hand
    players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
    players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
    print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
    for i in range(1, len(players[gamestate['id']]['hand'])):
        print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
    print()
    
    # Display deck and discard
    print(f'Deck: {gamestate["deck_size"]}')
    print('Discard:', end='')
    if gamestate['discard']:
        for card in gamestate['discard']:
            print(f' {card[0].rjust(2)}{card[1]}', end='')
    print('\n')


async def main(state_info):
    
    ret_val = await lobby.setState(state_info)
    
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    
    # Host
    if type(ret_val) is list:
        
        # Create Server
        server = Server(ret_val)
        
        # Play a turn
        while not server.end:
            
            # Send gamestate
            await send_gamestate(ret_val, server)
            
            # Display game state
            os.system('clear')
            host_display(server)
            
            # Wait until it's your turn
            while server.order[0] != 0:
                print(f'{server.players[server.order[0]].name}\'s turn...')
                
                # Wait for client player to send action
                message = await get_message(ret_val[server.order[0]-1][0])
                
                # Parse action message
                if message['command'] == 'pick_deck':
                    # Pop card from deck and add it to player's hand
                    server.players[server.order[0]].hand.append(server.deck.pop())
                    
                    # Save the player id who drew the last card
                    server.last_draw = server.order[0]
                    
                    # Disable player from calling draw
                    server.players[server.order[0]].can_draw = False
                
                elif message['command'] == 'pick_discard':
                    # Removes melded cards from player's hand
                    for meld_card in message['cards']:
                        if meld_card in decompose(server.players[server.order[0]].hand):
                            for card in server.players[server.order[0]].hand:
                                if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                    server.players[server.order[0]].hand.remove(card)
                                    break
                    
                    # Pop card from discard and add meld to player's melds
                    server.players[server.order[0]].melds.append(compose([decompose(server.discard.pop())] + message['cards']))
                    
                    # Disable player who discarded the card from calling draw
                    server.players[server.order[-1]].can_draw = False
                    
                    # Disable player from calling draw
                    server.players[server.order[0]].can_draw = False
                    
                    # Check if game is over
                    if not server.players[server.order[0]].hand:
                        # TODO: Implement TONGITS win!
                        break
                
                elif message['command'] == 'draw':
                    # TODO: Implement Draw
                    pass
                
                elif message['command'] == 'expose':
                    # Remove cards from player's hand
                    for meld_card in message['cards']:
                        if meld_card in decompose(server.players[server.order[0]].hand):
                            for card in server.players[server.order[0]].hand:
                                if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                    server.players[server.order[0]].hand.remove(card)
                                    break
                    
                    # Pop card from discard and add meld to player's melds
                    server.players[server.order[0]].melds.append(compose(message['cards']))
                    
                    # Disable player from calling draw
                    server.players[server.order[0]].can_draw = False
                    
                    # Check if game is over
                    if not server.players[server.order[0]].hand:
                        # TODO: Implement TONGITS win!
                        break
                
                elif message['command'] == 'lay_off':
                    # Remove card from player's hand
                    for card in server.players[server.order[0]].hand:
                        if card.rank == message['card'][0] and card.suit == message['card'][1]:
                            server.players[server.order[0]].hand.remove(card)
                    
                    # Add card to meld
                    server.players[message['player_id']].melds[message['meld_id']].append(compose(message['card']))
                    
                    # Disable player whose meld got added to from calling draw
                    server.players[message['player_id']].can_draw = False
                    
                    # Disable player from calling draw
                    server.players[server.order[0]].can_draw = False
                    
                    # Check if game is over
                    if not server.players[server.order[0]].hand:
                        # TODO: Implement TONGITS win!
                        break
                
                elif message['command'] == 'discard':
                    # Remove card from player's hand
                    for card in server.players[server.order[0]].hand:
                        if card.rank == message['card'][0] and card.suit == message['card'][1]:
                            server.players[server.order[0]].hand.remove(card)
                    
                    # Add card to discard
                    server.discard.append(compose(message['card']))
                    
                    # Enable player to call draw if they have an exposed meld
                    if server.players[server.order[0]].melds:
                        server.players[server.order[0]].can_draw = True
                    
                    # Check if game is over
                    if not server.deck:
                        # TODO: Implement exhausted deck procedure
                        break
                    
                    # Check if game is over
                    if not server.players[server.order[0]].hand:
                        # TODO: Implement TONGITS win!
                        break
                    
                    # End turn, and begin the next player's turn
                    server.order = server.order[1:] + [server.order[0]]
                
                # Send gamestate
                await send_gamestate(ret_val, server)
                
                # Redraw display
                os.system('clear')
                host_display(server)
            
            # Rules (https://www.pagat.com/rummy/tong-its.html)
            # 1) Draw
            #    - You must have exposed at least one meld
            #    - Your exposed meld(s) must be unchanged since the end of your last turn
            #    - The card you discarded on your previous turn must not have been melded by another player
            #    - Others may fold or challenge a draw
            #    - Others must have at least one exposed meld to challenge a draw
            #    - The player whose hand is worth the least number of points wins
            #    - You lose if you tie with any challengers
            #    - If two challengers tie, the challenger whose turn it would have been after your's wins
            # 
            # 2) Pick
            #    - You may either pick from the deck or the discard
            #    - You can only pick from the discard if you can expose a meld with the card and if you do so
            # 
            # 3) Expose
            #    - The following melds can be exposed:
            #      3 or 4 cards of the same rank
            #      3 to 13 cards of sequential rank in the same suit
            #    - You may expose as many melds as you like on your turn
            #    - You may also lay off as many cards to exposed melds as you like on your turn
            # 
            # 4) Discard
            #    - Once you discard a card from your hand, your turn ends
            #    - You must discard a card from your hand before the next player's turn can begin
            
            # Bool to remember whether pick discard is valid
            can_pick_discard = False
            
            # Display option to pick up from deck
            print('0: Pick up a card from the top of the deck')
            
            # Check if player can pick up from discard
            if server.discard:
                valid_meld = 0
                
                # Check for a 3-of-a-kind
                for card in server.players[0].hand:
                    if card.rank == server.discard[-1].rank:
                        valid_meld += 1
                        if valid_meld == 2:
                            break
                
                if valid_meld != 2:
                    valid_meld = 1
                    
                    # Check for a straight flush (discard is lowest rank)
                    for card in server.players[0].hand:
                        if card.suit == server.discard[-1].suit:
                            if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.discard[-1].rank) + valid_meld:
                                valid_meld += 1
                                if valid_meld == 3:
                                    break
                    
                    if valid_meld != 3:
                        valid_meld = -1
                        
                        # Check for a straight flush (discard is middle rank)
                        for card in server.players[0].hand:
                            if card.suit == server.discard[-1].suit:
                                if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.discard[-1].rank) + valid_meld:
                                    valid_meld += 2
                                    if valid_meld == 3:
                                        break
                        
                        if valid_meld != 3:
                            valid_meld = -2
                            
                            # Check for a straight flush (discard is lowest rank)
                            for card in server.players[0].hand:
                                if card.suit == server.discard[-1].suit:
                                    if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.discard[-1].rank) + valid_meld:
                                        valid_meld += 1
                                        if valid_meld == 0:
                                            break
                
                # If a valid meld was found
                if valid_meld >= 0:
                    can_pick_discard = True
                    print('1: Pick up a card from the top of the discard to expose a meld')
            
            # Display option to draw if player can
            if server.players[0].can_draw:
                print('2: Call draw')
            
            # Get player's choice
            choice = input('\n> ')
            while not choice.isnumeric() or int(choice) > 2 or (int(choice) == 1 and not can_pick_discard):
                print('\nInvalid input')
                choice = input('\n> ')
            
            # Process choice
            if choice == '0':
                # Pop card from deck and add it to hand
                server.players[server.order[0]].hand.append(server.deck.pop())
                
                # Save your id as the last player who drew a card
                server.last_draw = server.order[0]
                
                # Disable self from calling draw
                server.players[server.order[0]].can_draw = False
            
            elif choice == '1':
                # Get desired melded cards
                meld = list()
                
                while not meld:
                    # Display hand
                    server.players[0].hand.sort(key=lambda x: x.suit)
                    server.players[0].hand.sort(key=lambda x: Constants().RANKS.index(x.rank))
                    print(f'{server.players[0].hand[0].rank.rjust(2)}{server.players[0].hand[0].suit}', end='')
                    for i in range(1, len(server.players[0].hand)):
                        print(f' {server.players[0].hand[i].rank.rjust(2)}{server.players[0].hand[i].suit}', end='')
                    print()
                    
                    # Display enumeration for card select
                    print('  0', end='')
                    for i in range(1, len(server.players[0].hand)):
                        print(f' {str(i).rjust(3)}', end='')
                    print()
                    
                    print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                    
                    choices = input('\n> ')
                    
                    # TODO: Error check input
                    #
                    
                    for num in choices.split():
                        meld.append(server.players[0].hand[int(num)])
                    meld = decompose(meld)
                    
                    # TODO: Check if meld + discard_card is valid
                    #
                
                # Removes melded cards from hand
                for meld_card in meld:
                    if meld_card in decompose(server.players[0].hand):
                        for card in server.players[0].hand:
                            if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                server.players[0].hand.remove(card)
                                break
                
                # Pop card from discard and add meld to melds
                server.players[0].melds.append(compose([decompose(server.discard.pop())] + meld))
                
                # Disable last player from calling draw
                server.players[server.order[-1]].can_draw = False
                
                # Disable self from calling draw
                server.players[0].can_draw = False
                
                # Check if game is over
                if not server.players[0].hand:
                    # TODO: Implement TONGITS win!
                    break
            
            elif choice == '2':
                # TODO: Implement draw
                pass
            
            while server.order[0] == 0:
                # Send gamestate
                await send_gamestate(ret_val, server)
                
                # Redraw display
                os.system('clear')
                host_display(server)
                
                # Default to false before checking
                can_expose_meld = False
                
                # Check if you have a valid meld to play
                for i in range(len(server.players[0].hand)):
                    valid_meld = 0
                    
                    # Check for a 3-of-a-kind
                    for card in server.players[0].hand:
                        if card != server.players[0].hand[i]:
                            if card.rank == server.players[0].hand[i].rank:
                                valid_meld += 1
                                if valid_meld == 2:
                                    break
                    
                    if valid_meld != 2:
                        valid_meld = 1
                        
                        # Check for a straight flush (i card is lowest rank)
                        for card in server.players[0].hand:
                            if card != server.players[0].hand[i]:
                                if card.suit == server.players[0].hand[i].suit:
                                    if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.players[0].hand[i].rank) + valid_meld:
                                        valid_meld += 1
                                        if valid_meld == 3:
                                            break
                        
                        if valid_meld != 3:
                            valid_meld = -1
                            
                            # Check for a straight flush (i card is middle rank)
                            for card in server.players[0].hand:
                                if card != server.players[0].hand[i]:
                                    if card.suit == server.players[0].hand[i].suit:
                                        if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.players[0].hand[i].rank) + valid_meld:
                                            valid_meld += 2
                                            if valid_meld == 3:
                                                break
                            
                            if valid_meld != 3:
                                valid_meld = -2
                                
                                # Check for a straight flush (i card is lowest rank)
                                for card in server.players[0].hand:
                                    if card != server.players[0].hand[i]:
                                        if card.suit == server.players[0].hand[i].suit:
                                            if Constants().RANKS.index(card.rank) == Constants().RANKS.index(server.players[0].hand[i].rank) + valid_meld:
                                                valid_meld += 1
                                                if valid_meld == 0:
                                                    break
                    
                # If a valid meld was found
                if valid_meld >= 0:
                    can_expose_meld = True
                    print('0: Expose a meld')
                
                print('d: Discard a card')
                
                choice = input('\n> ')
                
                while (choice == '0' and not can_expose_meld) or (choice != '0' and choice != 'd'):
                    print('\nInvalid input')
                    choice = input('\n> ')
                
                if choice == '0':
                    # Get desired melded cards
                    meld = list()
                    
                    while not meld:
                        # Display hand
                        server.players[0].hand.sort(key=lambda x: x.suit)
                        server.players[0].hand.sort(key=lambda x: Constants().RANKS.index(x.rank))
                        print(f'{server.players[0].hand[0].rank.rjust(2)}{server.players[0].hand[0].suit}', end='')
                        for i in range(1, len(server.players[0].hand)):
                            print(f' {server.players[0].hand[i].rank.rjust(2)}{server.players[0].hand[i].suit}', end='')
                        print()
                        
                        # Display enumeration for card select
                        print('  0', end='')
                        for i in range(len(server.players[0].hand)):
                            print(f' {str(i).rjust(3)}', end='')
                        print()
                        
                        print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                        
                        choices = input('\n> ')
                        
                        # TODO: Error check input
                        #
                        
                        for num in choices.split():
                            meld.append(server.players[0].hand[int(num)])
                        meld = decompose(meld)
                        
                        # TODO: Check if meld + discard_card is valid
                        #
                    
                    # Removes melded cards from hand
                    for meld_card in meld:
                        if meld_card in decompose(server.players[0].hand):
                            for card in server.players[0].hand:
                                if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                    server.players[0].hand.remove(card)
                                    break
                    
                    # Add meld to melds
                    server.players[0].melds.append(compose(meld))
                    
                    # Check if game is over
                    if not server.players[0].hand:
                        # TODO: Implement TONGITS win!
                        break
                
                elif choice == 'd':
                    # Display hand
                    server.players[0].hand.sort(key=lambda x: x.suit)
                    server.players[0].hand.sort(key=lambda x: Constants().RANKS.index(x.rank))
                    print(f'{server.players[0].hand[0].rank.rjust(2)}{server.players[0].hand[0].suit}', end='')
                    for i in range(1, len(server.players[0].hand)):
                        print(f' {server.players[0].hand[i].rank.rjust(2)}{server.players[0].hand[i].suit}', end='')
                    print()
                    
                    # Display enumeration for card select
                    print('  0', end='')
                    for i in range(1, len(server.players[0].hand)):
                        print(f' {str(i).rjust(3)}', end='')
                    print()
                    
                    print('\nChoose which card you wish to discard')
                    
                    choice = input('\n> ')
                    
                    # TODO: Error check input
                    #
                    
                    # Move card from hand to discard
                    server.discard.append(server.players[0].hand.pop(int(choice)))
                    
                    # Enable you to call draw if they have an exposed meld
                    if server.players[0].melds:
                        server.players[0].can_draw = True
                    
                    # Check if game is over
                    if not server.deck:
                        # TODO: Implement exhausted deck procedure
                        break
                    
                    # Check if game is over
                    if not server.players[0].hand:
                        # TODO: Implement TONGITS win!
                        break
                    
                    # End turn, and begin the next player's turn
                    server.order = server.order[1:] + [server.order[0]]
        
        # Server game ended
    
    
    # Client
    elif type(ret_val) is tuple:
        
        while True:
            # Await gamestate
            gamestate = await get_message(ret_val[0])
            
            # Get player info
            players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
            
            # Display game state
            os.system('clear')
            client_display(gamestate, players)
            
            # Wait until it's your turn
            while gamestate['order'][0] != gamestate['id']:
                print(f'{players[gamestate["order"][0]]["name"]}\'s turn...')
                
                # Await gamestate
                gamestate = await get_message(ret_val[0])
                
                # Get player info
                players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
                
                # Redraw display
                os.system('clear')
                client_display(gamestate, players)
            
            # Client's turn
            print("WAHOO")


def start_game(stdscr):
    # Force curses not to do dumb stuff
    curses.use_default_colors()
    
    # Set to non-blocking
    stdscr.nodelay(True)
    
    # Enable normal reading of backspace
    stdscr.keypad(False)
    
    # Initialize state
    state_info = lobby.StateInfo(stdscr)
    
    # Run program
    return asyncio.run(main(state_info))


if __name__ == '__main__':
    stdscr = curses.initscr()
    curses.wrapper(start_game)
