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
async def send_gamestate(ret_val, server, winner):
    for i in range(1, len(server.players)):
        
        # Send remaining deck size, discard, and order of play
        await send_message(ret_val[i-1][1], {'deck_size': len(server.deck), 'discard': decompose(server.discard), 'order': server.order, 'id': i, 'winner': winner})
        
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
        print(f'{server.players[i].name} (id={i})')
        print(f'Score: {server.players[i].score}')
        print(f'Cards: {len(server.players[i].hand)}')
        
        # Display melds
        print(f'Melds:')
        for meld in server.players[i].melds:
            meld.sort(key=lambda x: x.suit)
            meld.sort(key=lambda x: Constants().RANKS.index(x.rank))
            print(f'{meld[0].rank.rjust(2)}{meld[0].suit}', end='')
            for j in range(1, len(meld)):
                print(f' {meld[j].rank.rjust(2)}{meld[j].suit}', end='')
            print()
        print()
    
    # Draw self
    print(f'{server.players[0].name} (id=0)')
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
    
    # Display deck and discard
    print(f'Deck: {len(server.deck)}')
    print('Discard:', end='')
    if server.discard:
        for card in server.discard:
            print(f' {card.rank.rjust(2)}{card.suit}', end='')
    print('\n')
    
    # Display hand
    if server.players[0].hand:
        server.players[0].hand.sort(key=lambda x: x.suit)
        server.players[0].hand.sort(key=lambda x: Constants().RANKS.index(x.rank))
        print(f'Hand: {server.players[0].hand[0].rank.rjust(2)}{server.players[0].hand[0].suit}', end='')
        for i in range(1, len(server.players[0].hand)):
            print(f' {server.players[0].hand[i].rank.rjust(2)}{server.players[0].hand[i].suit}', end='')
    print('\n')


# Display function for clients (Draws other players in turn-order first, then self last)
def client_display(gamestate, players):
    # Determine client player draw order (order of drawing aka printing to display)
    draw_order = gamestate['order'][gamestate['order'].index(gamestate['id'])+1:] + gamestate['order'][:gamestate['order'].index(gamestate['id'])]
    for i in draw_order:
        # Display client players's vague info in order
        print(f'{players[i]["name"]} (id={i})')
        print(f'Score: {players[i]["score"]}')
        print(f'Cards: {players[i]["num_cards"]}')
        
        # Display melds
        print(f'Melds:')
        for meld in players[i]['melds']:
            meld.sort(key=lambda x: x[1])
            meld.sort(key=lambda x: Constants().RANKS.index(x[0]))
            print(f'{meld[0][0].rjust(2)}{meld[0][1]}', end='')
            for j in range(1, len(meld)):
                print(f' {meld[j][0].rjust(2)}{meld[j][1]}', end='')
            print()
        print()
    
    # Draw self
    print(f'{players[gamestate["id"]]["name"]} (id={gamestate["id"]})')
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
    
    # Display deck and discard
    print(f'Deck: {gamestate["deck_size"]}')
    print('Discard:', end='')
    if gamestate['discard']:
        for card in gamestate['discard']:
            print(f' {card[0].rjust(2)}{card[1]}', end='')
    print('\n')
    
    # Display hand
    if players[gamestate["id"]]["hand"]:
        players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
        players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
        print(f'Hand: {players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
        for i in range(1, len(players[gamestate['id']]['hand'])):
            print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
    print('\n')


# Meld verifier
def verify_meld(decomposed_cards):
    
    # Meld must be at least 3 cards
    if len(decomposed_cards) < 3:
        return False
    
    # Cards in meld must all be unique
    for i in range(len(decomposed_cards) - 1):
        for j in range(i + 1, len(decomposed_cards)):
            if decomposed_cards[i][0] == decomposed_cards[j][0] and decomposed_cards[i][1] == decomposed_cards[j][1]:
                return False
    
    # All cards in meld must either be of same rank...
    all_same = True
    for card in decomposed_cards[1:]:
        if card[0] != decomposed_cards[0][0]:
            all_same = False
            break
    
    if all_same:
        return True
    
    # ...or cards in meld must be of same suit and sequentially orderable
    decomposed_cards.sort(key=lambda x: x[1])
    decomposed_cards.sort(key=lambda x: Constants().RANKS.index(x[0]))
    
    for i in range(1, len(decomposed_cards)):
        if decomposed_cards[i][1] != decomposed_cards[0][1] or Constants().RANKS.index(decomposed_cards[i][0]) != Constants().RANKS.index(decomposed_cards[i-1][0]) + 1:
            return False
    
    return True


# Find meld
def find_meld(decomposed_cards, required_card=None):
    
    for i in range(len(decomposed_cards) - 2):
        for j in range(i + 1, len(decomposed_cards) - 1):
            for k in range(j + 1, len(decomposed_cards)):
                if verify_meld([decomposed_cards[i], decomposed_cards[j], decomposed_cards[k]]):
                    if required_card == None or required_card in [decomposed_cards[i], decomposed_cards[j], decomposed_cards[k]]:
                        return True
    
    return False


async def main(state_info):
    
    ret_val = await lobby.setState(state_info)
    
    curses.nocbreak()
    curses.echo()
    curses.endwin()
    
    # Host
    if type(ret_val) is list:
        
        # Create Server
        server = Server(ret_val)
        
        while True:
            # Winner player_id
            winner = -1
            
            # Play a turn
            while not server.end:
                
                # Send gamestate
                await send_gamestate(ret_val, server, winner)
                
                # Display game state
                os.system('clear')
                host_display(server)
                
                # Wait until it's your turn
                while server.order[0] != 0 and winner == -1:
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
                        server.players[server.order[0]].melds.append(compose(decompose([server.discard.pop()]) + message['cards']))
                        
                        # Disable player who discarded the card from calling draw
                        server.players[server.order[-1]].can_draw = False
                        
                        # Disable player from calling draw
                        server.players[server.order[0]].can_draw = False
                        
                        # Check if game is over
                        if not server.players[server.order[0]].hand:
                            winner = server.order[0]
                            server.end = True
                            break
                    
                    elif message['command'] == 'draw':
                        winner = -3
                        server.end = True
                        break
                    
                    elif message['command'] == 'expose':
                        # Remove cards from player's hand
                        for meld_card in message['cards']:
                            if meld_card in decompose(server.players[server.order[0]].hand):
                                for card in server.players[server.order[0]].hand:
                                    if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                        server.players[server.order[0]].hand.remove(card)
                                        break
                        
                        # Add meld to player's melds
                        server.players[server.order[0]].melds.append(compose(message['cards']))
                        
                        # Disable player from calling draw
                        server.players[server.order[0]].can_draw = False
                        
                        # Check if game is over
                        if not server.players[server.order[0]].hand:
                            winner = server.order[0]
                            server.end = True
                            break
                    
                    elif message['command'] == 'lay_off':
                        # Remove card from player's hand
                        for card in server.players[server.order[0]].hand:
                            if card.rank == message['card'][0] and card.suit == message['card'][1]:
                                server.players[server.order[0]].hand.remove(card)
                                break
                        
                        # Add card to meld
                        server.players[message['player_id']].melds[message['meld_id']].append(compose([message['card']])[0])
                        
                        # Disable player whose meld got added to from calling draw
                        server.players[message['player_id']].can_draw = False
                        
                        # Disable player from calling draw
                        server.players[server.order[0]].can_draw = False
                        
                        # Check if game is over
                        if not server.players[server.order[0]].hand:
                            winner = server.order[0]
                            server.end = True
                            break
                    
                    elif message['command'] == 'discard':
                        # Remove card from player's hand
                        for card in server.players[server.order[0]].hand:
                            if card.rank == message['card'][0] and card.suit == message['card'][1]:
                                server.players[server.order[0]].hand.remove(card)
                        
                        # Add card to discard
                        server.discard += compose([message['card']])
                        
                        # Enable player to call draw if they have an exposed meld
                        if server.players[server.order[0]].melds:
                            server.players[server.order[0]].can_draw = True
                        
                        # Check if game is over
                        if not server.players[server.order[0]].hand:
                            winner = server.order[0]
                            server.end = True
                            break
                        
                        # Check if deck is exhausted...
                        if not server.deck:
                            winner = -2
                            server.end = True
                            break
                        
                        # End turn, and begin the next player's turn
                        server.order = server.order[1:] + [server.order[0]]
                    
                    # Send gamestate
                    await send_gamestate(ret_val, server, winner)
                    
                    # Redraw display
                    os.system('clear')
                    host_display(server)
                
                if server.end:
                    break
                
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
                    can_pick_discard = find_meld(decompose(server.players[0].hand) + decompose([server.discard[-1]]), decompose([server.discard[-1]])[0])
                    
                    if can_pick_discard:
                        print('1: Pick up a card from the top of the discard to expose a meld')
                
                # Display option to draw if player can
                if server.players[0].can_draw:
                    print('2: Call draw')
                
                # Get player's choice
                choice = input('\n> ')
                while not choice.isnumeric() or int(choice) > 2 or (int(choice) == 1 and not can_pick_discard) or (int(choice) == 2 and not server.players[0].can_draw):
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
                        
                        # Error check input
                        while not all(card.isnumeric() and int(card) < len(server.players[0].hand) for card in choices.split()) or not verify_meld(decompose([server.players[0].hand[int(num)] for num in choices.split()]) + decompose([server.discard[-1]])):
                            print('\nInvalid input')
                            choices = input('\n> ')
                        
                        meld = decompose([server.players[0].hand[int(num)] for num in choices.split()])
                    
                    # Removes melded cards from hand
                    for meld_card in meld:
                        if meld_card in decompose(server.players[0].hand):
                            for card in server.players[0].hand:
                                if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                    server.players[0].hand.remove(card)
                                    break
                    
                    # Pop card from discard and add meld to melds
                    server.players[0].melds.append(compose(decompose([server.discard.pop()]) + meld))
                    
                    # Disable last player from calling draw
                    server.players[server.order[-1]].can_draw = False
                    
                    # Disable self from calling draw
                    server.players[0].can_draw = False
                    
                    # Check if game is over
                    if not server.players[0].hand:
                        winner = 0
                        server.end = True
                        break
                
                elif choice == '2':
                    winner = -3
                    server.end = True
                    break
                
                # Expose/Lay off/Draw loop
                while server.order[0] == 0 and not server.end:
                    # Send gamestate
                    await send_gamestate(ret_val, server, winner)
                    
                    # Redraw display
                    os.system('clear')
                    host_display(server)
                    
                    # Default to false before checking
                    can_expose_meld = False
                    
                    # If a valid meld was found
                    if can_expose_meld := find_meld(decompose(server.players[0].hand)):
                        print('0: Expose a meld')
                    
                    # If can lay off
                    can_lay_off = False
                    for player in server.players:
                        if player.melds:
                            for meld in player.melds:
                                for card in server.players[0].hand:
                                    if find_meld(decompose(meld + [card]), decompose([card])[0]):
                                        can_lay_off = True
                                        break
                                if can_lay_off:
                                    break
                        if can_lay_off:
                            break
                    
                    if can_lay_off:
                        print('l: Lay off a card')
                    
                    print('d: Discard a card')
                    
                    choice = input('\n> ')
                    
                    while (choice != '0' and choice != 'l' and choice != 'd') or (choice == '0' and not can_expose_meld) or (choice == 'l' and not can_lay_off):
                        print('\nInvalid input')
                        choice = input('\n> ')
                    
                    if choice == '0':
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
                        
                        # Error check input
                        while not all(card.isnumeric() and int(card) < len(server.players[0].hand) for card in choices.split()) or not verify_meld(decompose([server.players[0].hand[int(num)] for num in choices.split()])):
                            print('\nInvalid input')
                            choices = input('\n> ')
                        
                        meld = decompose([server.players[0].hand[int(num)] for num in choices.split()])
                        
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
                            winner = 0
                            server.end = True
                            break
                    
                    elif choice == 'l':
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
                        
                        print('\nChoose which card you wish to lay off')
                        
                        choice = input('\n> ')
                        
                        melds = [meld for player in server.players if player.melds for meld in player.melds]
                        
                        valid_input = choice.isnumeric() and int(choice) < len(server.players[0].hand) and not all(not find_meld(decompose(meld + [server.players[0].hand[int(choice)]]), decompose([server.players[0].hand[int(choice)]])[0]) for meld in melds)
                        
                        # Verify input
                        while not valid_input:
                            print('\nInvalid input')
                            choice = input('\n> ')
                            
                            valid_input = choice.isnumeric() and int(choice) < len(server.players[0].hand) and not all(not find_meld(decompose(meld + [server.players[0].hand[int(choice)]]), decompose([server.players[0].hand[int(choice)]])[0]) for meld in melds)
                        
                        # Compile viable melds
                        melds = list()
                        player_ids = list()
                        id_num = 0
                        meld_ids = list()
                        for player in server.players:
                            if player.melds:
                                meld_num = 0
                                for meld in player.melds:
                                    if find_meld(decompose(meld + [server.players[0].hand[int(choice)]]), decompose([server.players[0].hand[int(choice)]])[0]):
                                        melds.append(meld)
                                        player_ids.append(id_num)
                                        meld_ids.append(meld_num)
                                    meld_num += 1
                            id_num += 1
                        
                        meld_choice = None
                        if len(melds) > 1:
                            # Display melds
                            num_meld = 0
                            for meld in melds:
                                meld.sort(key=lambda x: x[1])
                                meld.sort(key=lambda x: Constants().RANKS.index(x[0]))
                                print(f'{num_meld}: {meld[0][0].rjust(2)}{meld[0][1]}', end='')
                                for j in range(1, len(meld)):
                                    print(f'{meld[j][0].rjust(2)}{meld[j][1]}', end='')
                                print()
                                num_meld += 1
                            print()
                            
                            print('Choose which meld you wish to lay off on')
                            meld_choice = input('\n> ')
                            
                            while not meld_choice.isnumeric() or int(meld_choice) >= len(melds) or not verify_meld(decompose(server.players[player_ids[meld_choice]].melds[meld_ids[meld_choice]]) + decompose([server.players[0].hand[int(choice)]])):
                                print('\nInvalid input')
                                meld_choice = input('\n> ')
                            
                            meld_choice = int(meld_choice)
                        
                        else:
                            meld_choice = 0
                        
                        # Lay off card
                        message = {'card': decompose([server.players[0].hand[int(choice)]])[0], 'player_id': player_ids[meld_choice], 'meld_id': meld_ids[meld_choice]}
                        
                        # Remove card from player's hand
                        for card in server.players[server.order[0]].hand:
                            if card.rank == message['card'][0] and card.suit == message['card'][1]:
                                server.players[server.order[0]].hand.remove(card)
                                break
                        
                        # Add card to meld
                        server.players[message['player_id']].melds[message['meld_id']].append(compose([message['card']])[0])
                        
                        # Disable player whose meld got added to from calling draw
                        server.players[message['player_id']].can_draw = False
                        
                        # Disable player from calling draw
                        server.players[server.order[0]].can_draw = False
                        
                        # Check if game is over
                        if not server.players[server.order[0]].hand:
                            winner = 0
                            server.end = True
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
                        while not choice.isnumeric() or int(choice) >= len(server.players[0].hand):
                            print('\nInvalid input')
                            choice = input('\n> ')
                        
                        # Move card from hand to discard
                        server.discard.append(server.players[0].hand.pop(int(choice)))
                        
                        # Enable you to call draw if they have an exposed meld
                        if server.players[0].melds:
                            server.players[0].can_draw = True
                        
                        # Check if game is over
                        if not server.players[0].hand:
                            winner = 0
                            server.end = True
                            break
                        
                        # Check if game is over
                        if not server.deck:
                            winner = -2
                            server.end = True
                            break
                        
                        # End turn, and begin the next player's turn
                        server.order = server.order[1:] + [server.order[0]]
            
            # Server game ended ############################
            
            # If winner == -2, then the deck was exhausted.
            # If winner == -3, then server.order[0] called Draw.
            # Otherwise, winner is the winner.
            
            # Send gamestate
            await send_gamestate(ret_val, server, winner)
            
            # Display game state
            os.system('clear')
            host_display(server)
            
            # Determine how game ended
            if winner == -2:
                # Exhausted deck procedure
                # 
                # 1. Make a list of players with exposed melds.
                candidates = [i for i in range(len(server.players)) if server.players[i].melds]
                
                if not candidates:
                    print('\nNobody exposed a meld; nobody wins.\n')
                
                else:
                    # 2. If host exposed a meld, await their hand after they submit any melds.
                    if server.players[0].melds:
                        choice = ''
                        while choice != 's':
                            print()
                            
                            # If host has any melds to expose
                            if can_expose_meld := find_meld(decompose(server.players[0].hand)):
                                print('0: Expose a meld')
                            else:
                                print('s: Submit your hand')
                            
                            choice = input('\n> ')
                            
                            while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                                print('\nInvalid input')
                                choice = input('\n> ')
                            
                            if choice == '0':
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
                                
                                # Error check input
                                while not all(card.isnumeric() and int(card) < len(server.players[0].hand) for card in choices.split()) or not verify_meld(decompose([server.players[0].hand[int(num)] for num in choices.split()])):
                                    print('\nInvalid input')
                                    choices = input('\n> ')
                                
                                meld = decompose([server.players[0].hand[int(num)] for num in choices.split()])
                                
                                # Removes melded cards from hand
                                for meld_card in meld:
                                    if meld_card in decompose(server.players[0].hand):
                                        for card in server.players[0].hand:
                                            if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                                server.players[0].hand.remove(card)
                                                break
                                
                                # Add meld to melds
                                server.players[0].melds.append(compose(meld))
                                
                                # Refresh display
                                os.system('clear')
                                host_display(server)
                    
                    # 3. Await candidates to submit any melds before submitting their hands.
                    for i in candidates:
                        if i == 0:
                            continue
                        
                        message = await get_message(ret_val[i-1][0])
                        
                        if 'melds' in message:
                            for meld in message['melds']:
                                # Remove cards from player's hand
                                for meld_card in meld:
                                    if meld_card in decompose(server.players[i].hand):
                                        for card in server.players[i].hand:
                                            if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                                server.players[i].hand.remove(card)
                                                break
                                
                                # Add meld to player's melds
                                server.players[i].melds.append(compose(meld))
                    
                    # 4. Tally up the points.
                    results = [(i, sum((card.points for card in server.players[i].hand))) for i in candidates]
                    
                    # 5. Compute the lowest score and filter out players with a higher score.
                    top_score = min((r[1] for r in results))
                    top_candidates = [r for r in results if r[1] == top_score]
                    
                    # 6. Break ties...
                    if len(top_candidates) > 1:
                        if server.last_draw in [candidate[0] for candidate in top_candidates]:
                            winner = server.last_draw
                        else:
                            winner = server.order[1]
                    
                    # ...or simply declare the sole winner!
                    else:
                        winner = top_candidates[0][0]
            
            elif winner == -3:
                # Draw procedure
                # 
                # 1. Check if host called Draw. If so, await their hand, then await any other hands. If not, prompt to challenge or fold.
                challengers = list()
                
                # Host called Draw
                if server.order[0] == 0:
                    
                    # Await their hand.
                    choice = ''
                    while choice != 's':
                        print()
                        
                        # If host has any melds to expose
                        if can_expose_meld := find_meld(decompose(server.players[0].hand)):
                            print('0: Prepare a meld')
                        else:
                            print('s: Submit your hand')
                        
                        choice = input('\n> ')
                        
                        while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                            print('\nInvalid input')
                            choice = input('\n> ')
                        
                        if choice == '0':
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
                            
                            # Error check input
                            while not all(card.isnumeric() and int(card) < len(server.players[0].hand) for card in choices.split()) or not verify_meld(decompose([server.players[0].hand[int(num)] for num in choices.split()])):
                                print('\nInvalid input')
                                choices = input('\n> ')
                            
                            meld = decompose([server.players[0].hand[int(num)] for num in choices.split()])
                            
                            # Removes melded cards from hand
                            for meld_card in meld:
                                if meld_card in decompose(server.players[0].hand):
                                    for card in server.players[0].hand:
                                        if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                            server.players[0].hand.remove(card)
                                            break
                            
                            # Add meld to melds
                            server.players[0].melds.append(compose(meld))
                            
                            # Refresh display
                            os.system('clear')
                            host_display(server)
                    
                    challengers.append(0)
                
                # Client called Draw
                else:
                    # Prompt to challenge or fold.
                    if server.players[0].melds:
                        print('c: Challenge')
                    
                    print('f: Fold')
                    
                    choice = input('\n> ')
                    while (choice != 'c' and choice != 'f') or (choice == 'c' and not server.players[0].melds):
                        print('\nInvalid input')
                        choice = input('\n> ')
                    
                    if choice == 'c':
                        # Challenge: await host's hand
                        choice = ''
                        while choice != 's':
                            print()
                            
                            # If host has any melds to expose
                            if can_expose_meld := find_meld(decompose(server.players[0].hand)):
                                print('0: Prepare a meld')
                            else:
                                print('s: Submit your hand')
                            
                            choice = input('\n> ')
                            
                            while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                                print('\nInvalid input')
                                choice = input('\n> ')
                            
                            if choice == '0':
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
                                
                                # Error check input
                                while not all(card.isnumeric() and int(card) < len(server.players[0].hand) for card in choices.split()) or not verify_meld(decompose([server.players[0].hand[int(num)] for num in choices.split()])):
                                    print('\nInvalid input')
                                    choices = input('\n> ')
                                
                                meld = decompose([server.players[0].hand[int(num)] for num in choices.split()])
                                
                                # Removes melded cards from hand
                                for meld_card in meld:
                                    if meld_card in decompose(server.players[0].hand):
                                        for card in server.players[0].hand:
                                            if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                                server.players[0].hand.remove(card)
                                                break
                                
                                # Add meld to melds
                                server.players[0].melds.append(compose(meld))
                                
                                # Refresh display
                                os.system('clear')
                                host_display(server)
                        
                        challengers.append(0)
                    
                # 2. Await hand(s)
                for i in range(1, len(server.players)):
                    if i == 0:
                        continue
                    
                    message = await get_message(ret_val[i-1][0])
                    
                    if 'draw_response' in message and message['draw_response'] == 'challenge':
                        challengers.append(i)
                        
                        if 'melds' in message:
                            for meld in message['melds']:
                                # Remove cards from player's hand
                                for meld_card in meld:
                                    if meld_card in decompose(server.players[i].hand):
                                        for card in server.players[i].hand:
                                            if card.rank == meld_card[0] and card.suit == meld_card[1]:
                                                server.players[i].hand.remove(card)
                                                break
                                
                                # Add meld to player's melds
                                server.players[i].melds.append(compose(meld))
                
                # 3. Tally up the points.
                results = [(i, sum((card.points for card in server.players[i].hand))) for i in challengers]
                
                # 4. Compute the lowest score and filter out players with a higher score.
                top_score = min((r[1] for r in results))
                top_challengers = [r for r in results if r[1] == top_score]
                
                # 5. Break ties...
                if len(top_challengers) > 1:
                    if (server.last_draw, top_score) in top_challengers:
                        # Remove who called Draw from list of potential winners
                        top_challengers.remove((server.last_draw, top_score))
                        
                        if len(top_challengers) > 1:
                            winner = server.order[1]
                        else:
                            winner = top_challengers[0][0]
                    
                    else:
                        winner = server.order[1]
                
                # ...or simply declare the sole winner!
                else:
                    winner = top_challengers[0][0]
            
            if winner != -2:
                server.players[winner].score += 1
            
            # Send final gamestate
            await send_gamestate(ret_val, server, winner)
            
            # Display final gamestate
            os.system('clear')
            host_display(server)
            
            # Print winner
            if winner != -2:
                print(f'{server.players[winner].name} won (id={winner})!\n')
            else:
                print('Nobody exposed a meld; nobody wins.\n')
            
            # Ask host if they want to host again with same players
            print('Rematch? Enter \'q\' to not rematch.')
            choice = input('\n> ')
            
            if choice == 'q':
                break
            
            print('\nAwaiting player responses...')
            
            # Await rematch response
            all_true = True
            for i in range(1, len(server.players)):
                response = await get_message(ret_val[i-1][0])
                if response['command'] == 'rematch':
                    if response['value'] != 1:
                        all_true = False
                        break
            
            if not all_true:
                break
            
            # Reset server but save score!
            server.reset(ret_val, winner)
    
    
    # Client
    elif type(ret_val) is tuple:
        
        # To verify initial game attendance
        await send_message(ret_val[1], {'command': 'lol'})
        
        # Game lobby loop
        while True:
            
            # Hack to set gamestate winner to -1
            gamestate = {'winner': -1}
            
            # Gameplay loop
            while gamestate['winner'] == -1:
                
                # Await gamestate
                gamestate = await get_message(ret_val[0])
                
                # Get player info
                players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
                
                # Display game state
                os.system('clear')
                client_display(gamestate, players)
                
                # Wait until it's your turn
                while gamestate['order'][0] != gamestate['id'] and gamestate['winner'] == -1:
                    print(f'{players[gamestate["order"][0]]["name"]}\'s turn...')
                    
                    # Await gamestate
                    gamestate = await get_message(ret_val[0])
                    
                    # Get player info
                    players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
                    
                    # Redraw display
                    os.system('clear')
                    client_display(gamestate, players)
                
                if gamestate['winner'] != -1:
                    break
                
                # Client's turn
                # Display option to pick up from deck
                print('0: Pick up a card from the top of the deck')
                
                # Check if player can pick up from discard
                if gamestate['discard']:
                    if can_pick_discard := find_meld(players[gamestate['id']]['hand'] + [gamestate['discard'][-1]], gamestate['discard'][-1]):
                        print('1: Pick up a card from the top of the discard to expose a meld')
                
                # Display option to draw if player can TODO: VERIFY
                if players[gamestate['id']]['can_draw']:
                    print('2: Call draw')
                
                # Get player's choice
                choice = input('\n> ')
                while not choice.isnumeric() or int(choice) > 2 or (int(choice) == 1 and not can_pick_discard) or (int(choice) == 2 and not players[gamestate['id']]['can_draw']):
                    print('\nInvalid input')
                    choice = input('\n> ')
                
                # Process choice
                if choice == '0':
                    # Draw card from deck
                    await send_message(ret_val[1], {'command': 'pick_deck'})
                
                elif choice == '1':
                    # Display hand
                    players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                    players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                    print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                    for i in range(1, len(players[gamestate["id"]]["hand"])):
                        print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                    print()
                    
                    # Display enumeration for card select
                    print('  0', end='')
                    for i in range(1, len(players[gamestate['id']]['hand'])):
                        print(f' {str(i).rjust(3)}', end='')
                    print()
                    
                    print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                    
                    choices = input('\n> ')
                    
                    # Verify input
                    while not all(choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) for choice in choices.split()) or not verify_meld([players[gamestate['id']]['hand'][int(num)] for num in choices.split()] + [gamestate['discard'][-1]]):
                        print('\nInvalid input')
                        choices = input('\n> ')
                    
                    meld = [players[gamestate['id']]['hand'][int(num)] for num in choices.split()]
                    
                    # Expose cards
                    await send_message(ret_val[1], {'command': 'pick_discard', 'cards': meld})
                
                elif choice == '2':
                    await send_message(ret_val[1], {'command': 'draw'})
                
                while gamestate['order'][0] == gamestate['id']:
                    # Await gamestate
                    gamestate = await get_message(ret_val[0])
                    
                    # Get player info
                    players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
                    
                    # Display game state
                    os.system('clear')
                    client_display(gamestate, players)
                    
                    if gamestate['winner'] != -1:
                        break
                    
                    # Check if you have a valid meld to play
                    if can_expose_meld := find_meld(players[gamestate['id']]['hand']):
                        print('0: Expose a meld')
                    
                    # If can lay off
                    can_lay_off = False
                    for player in players:
                        if player['melds']:
                            for meld in player['melds']:
                                for card in players[gamestate['id']]['hand']:
                                    if find_meld(meld + [card], card):
                                        can_lay_off = True
                                        break
                                if can_lay_off:
                                    break
                        if can_lay_off:
                            break
                    
                    if can_lay_off:
                        print('l: Lay off a card')
                    
                    print('d: Discard a card')
                    
                    choice = input('\n> ')
                    
                    while (choice != '0' and choice != 'l' and choice != 'd') or (choice == '0' and not can_expose_meld) or (choice == 'l' and not can_lay_off):
                        print('\nInvalid input')
                        choice = input('\n> ')
                    
                    if choice == '0':
                        # Display hand
                        players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                        players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                        print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                        for i in range(1, len(players[gamestate["id"]]["hand"])):
                            print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                        print()
                        
                        # Display enumeration for card select
                        print('  0', end='')
                        for i in range(1, len(players[gamestate['id']]['hand'])):
                            print(f' {str(i).rjust(3)}', end='')
                        print()
                        
                        print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                        
                        choices = input('\n> ')
                        
                        while not all(choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) for choice in choices.split()) or not verify_meld([players[gamestate['id']]['hand'][int(num)] for num in choices.split()]):
                            print('\nInvalid input')
                            choices = input('\n> ')
                        
                        meld = [players[gamestate['id']]['hand'][int(num)] for num in choices.split()]
                        
                        # Expose cards
                        await send_message(ret_val[1], {'command': 'expose', 'cards': meld})
                    
                    # LAY OFF
                    elif choice == 'l':
                        # Display hand
                        players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                        players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                        print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                        for i in range(1, len(players[gamestate['id']]['hand'])):
                            print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                        print()
                        
                        # Display enumeration for card select
                        print('  0', end='')
                        for i in range(1, len(players[gamestate['id']]['hand'])):
                            print(f' {str(i).rjust(3)}', end='')
                        print()
                        
                        print('\nChoose which card you wish to lay off')
                        
                        choice = input('\n> ')
                        
                        melds = [meld for player in players if player['melds'] for meld in player['melds']]
                        
                        valid_input = choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) and not all(not find_meld(meld + [players[gamestate['id']]['hand'][int(choice)]], players[gamestate['id']]['hand'][int(choice)]) for meld in melds)
                        
                        # Verify input
                        while not valid_input:
                            print('\nInvalid input')
                            choice = input('\n> ')
                            
                            valid_input = choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) and not all(not find_meld(meld + [players[gamestate['id']]['hand'][int(choice)]], players[gamestate['id']]['hand'][int(choice)]) for meld in melds)
                        
                        # Compile viable melds
                        melds = list()
                        player_ids = list()
                        id_num = 0
                        meld_ids = list()
                        for player in players:
                            if player['melds']:
                                meld_num = 0
                                for meld in player['melds']:
                                    if find_meld(meld + [players[gamestate['id']]['hand'][int(choice)]], players[gamestate['id']]['hand'][int(choice)]):
                                        melds.append(meld)
                                        player_ids.append(id_num)
                                        meld_ids.append(meld_num)
                                    meld_num += 1
                            id_num += 1
                        
                        meld_choice = None
                        if len(melds) > 1:
                            # Display melds
                            num_meld = 0
                            for meld in melds:
                                meld.sort(key=lambda x: x[1])
                                meld.sort(key=lambda x: Constants().RANKS.index(x[0]))
                                print(f'{num_meld}: {meld[0][0].rjust(2)}{meld[0][1]}', end='')
                                for j in range(1, len(meld)):
                                    print(f'{meld[j][0].rjust(2)}{meld[j][1]}', end='')
                                print()
                                num_meld += 1
                            print()
                            
                            print('Choose which meld you wish to lay off on')
                            meld_choice = input('\n> ')
                            
                            while not meld_choice.isnumeric() or int(meld_choice) >= len(melds):
                                print('\nInvalid input')
                                meld_choice = input('\n> ')
                            
                            meld_choice = int(meld_choice)
                        
                        else:
                            meld_choice = 0
                        
                        # Lay off card
                        await send_message(ret_val[1], {'command': 'lay_off', 'card': players[gamestate['id']]['hand'][int(choice)], 'player_id': player_ids[meld_choice], 'meld_id': meld_ids[meld_choice]})
                        
                        
                    elif choice == 'd':
                        # Display hand
                        players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                        players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                        print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                        for i in range(1, len(players[gamestate['id']]['hand'])):
                            print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                        print()
                        
                        # Display enumeration for card select
                        print('  0', end='')
                        for i in range(1, len(players[gamestate['id']]['hand'])):
                            print(f' {str(i).rjust(3)}', end='')
                        print()
                        
                        print('\nChoose which card you wish to discard')
                        
                        choice = input('\n> ')
                        
                        while not choice.isnumeric() or int(choice) >= len(players[gamestate['id']]['hand']):
                            print('\nInvalid input')
                            choice = input('\n> ')
                        
                        # Discard card
                        await send_message(ret_val[1], {'command': 'discard', 'card': players[gamestate['id']]['hand'][int(choice)]})
                        
                        # End turn
                        gamestate['order'] = gamestate['order'][1:] + [gamestate['order'][0]]
                        
                        break
            
            # Client game ended ############################
            
            # If winner == -2, then the deck was exhausted.
            # If winner == -3, then server.order[0] called Draw.
            # Otherwise, winner is the winner.
            
            if gamestate['winner'] == -2:
                if players[gamestate['id']]['melds']:
                    melds = list()
                    
                    # Await hand.
                    choice = ''
                    while choice != 's':
                        print()
                        
                        # If you have any melds to expose
                        if can_expose_meld := find_meld(players[gamestate['id']]['hand']):
                            print('0: Prepare a meld')
                        else:
                            print('s: Submit your hand')
                        
                        choice = input('\n> ')
                        
                        while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                            print('\nInvalid input')
                            choice = input('\n> ')
                        
                        if choice == '0':
                            # Display hand
                            players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                            players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                            print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                            for i in range(1, len(players[gamestate["id"]]["hand"])):
                                print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                            print()
                            
                            # Display enumeration for card select
                            print('  0', end='')
                            for i in range(1, len(players[gamestate['id']]['hand'])):
                                print(f' {str(i).rjust(3)}', end='')
                            print()
                            
                            print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                            
                            choices = input('\n> ')
                            
                            while not all(choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) for choice in choices.split()) or not verify_meld([players[gamestate['id']]['hand'][int(num)] for num in choices.split()]):
                                print('\nInvalid input')
                                choices = input('\n> ')
                            
                            meld = [players[gamestate['id']]['hand'][int(num)] for num in choices.split()]
                            
                            melds.append(meld)
                            
                            # Remove cards from player's hand
                            for meld_card in meld:
                                players[gamestate['id']]['hand'].remove(meld_card)
                            
                            # Add meld to player's melds
                            players[gamestate['id']]['melds'].append(meld)
                            
                            # Refresh display
                            os.system('clear')
                            client_display(gamestate, players)
                    
                    # Send melds to host
                    await send_message(ret_val[1], {'melds': melds})
            
            elif gamestate['winner'] == -3:
                # Draw procedure
                # 
                # 1. Check if you called Draw. If so, await your hand. If not, prompt to challenge or fold.
                
                # You called Draw
                if gamestate['order'][0] == gamestate['id']:
                    melds = list()
                    
                    # Await your hand.
                    choice = ''
                    while choice != 's':
                        print()
                        
                        # If you have any melds to expose
                        if can_expose_meld := find_meld(players[gamestate['id']]['hand']):
                            print('0: Prepare a meld')
                        else:
                            print('s: Submit your hand')
                        
                        choice = input('\n> ')
                        
                        while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                            print('\nInvalid input')
                            choice = input('\n> ')
                        
                        if choice == '0':
                            # Display hand
                            players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                            players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                            print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                            for i in range(1, len(players[gamestate["id"]]["hand"])):
                                print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                            print()
                            
                            # Display enumeration for card select
                            print('  0', end='')
                            for i in range(1, len(players[gamestate['id']]['hand'])):
                                print(f' {str(i).rjust(3)}', end='')
                            print()
                            
                            print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                            
                            choices = input('\n> ')
                            
                            while not all(choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) for choice in choices.split()) or not verify_meld([players[gamestate['id']]['hand'][int(num)] for num in choices.split()]):
                                print('\nInvalid input')
                                choices = input('\n> ')
                            
                            meld = [players[gamestate['id']]['hand'][int(num)] for num in choices.split()]
                            
                            melds.append(meld)
                            
                            # Remove cards from player's hand
                            for meld_card in meld:
                                players[gamestate['id']]['hand'].remove(meld_card)
                            
                            # Add meld to player's melds
                            players[gamestate['id']]['melds'].append(meld)
                            
                            # Refresh display
                            os.system('clear')
                            client_display(gamestate, players)
                    
                    # Obv ur not challenging cuz u called the Draw, but host doesn't know that, so this is a little hack
                    await send_message(ret_val[1], {'draw_response': 'challenge', 'melds': melds})
                
                # Someone else called Draw
                else:
                    # Prompt to challenge or fold.
                    if players[gamestate['id']]['melds']:
                        print('c: Challenge')
                    
                    print('f: Fold')
                    
                    choice = input('\n> ')
                    while (choice != 'c' and choice != 'f') or (choice == 'c' and not players[gamestate['id']]['melds']):
                        print('\nInvalid input')
                        choice = input('\n> ')
                    
                    if choice == 'f':
                        await send_message(ret_val[1], {'draw_response': 'fold'})
                    
                    elif choice == 'c':
                        melds = list()
                        
                        # Challenge: await host's hand
                        choice = ''
                        while choice != 's':
                            print()
                            
                            # If you have any melds to expose
                            if can_expose_meld := find_meld(players[gamestate['id']]['hand']):
                                print('0: Prepare a meld')
                            else:
                                print('s: Submit your hand')
                            
                            choice = input('\n> ')
                            
                            while (choice != '0' and choice != 's') or (choice == '0' and not can_expose_meld) or (choice == 's' and can_expose_meld):
                                print('\nInvalid input')
                                choice = input('\n> ')
                            
                            if choice == '0':
                                # Display hand
                                players[gamestate['id']]['hand'].sort(key=lambda x: x[1])
                                players[gamestate['id']]['hand'].sort(key=lambda x: Constants().RANKS.index(x[0]))
                                print(f'{players[gamestate["id"]]["hand"][0][0].rjust(2)}{players[gamestate["id"]]["hand"][0][1]}', end='')
                                for i in range(1, len(players[gamestate["id"]]["hand"])):
                                    print(f' {players[gamestate["id"]]["hand"][i][0].rjust(2)}{players[gamestate["id"]]["hand"][i][1]}', end='')
                                print()
                                
                                # Display enumeration for card select
                                print('  0', end='')
                                for i in range(1, len(players[gamestate['id']]['hand'])):
                                    print(f' {str(i).rjust(3)}', end='')
                                print()
                                
                                print('\nChoose which cards you wish to meld (space-separated list of numbers)')
                                
                                choices = input('\n> ')
                                
                                while not all(choice.isnumeric() and int(choice) < len(players[gamestate['id']]['hand']) for choice in choices.split()) or not verify_meld([players[gamestate['id']]['hand'][int(num)] for num in choices.split()]):
                                    print('\nInvalid input')
                                    choices = input('\n> ')
                                
                                meld = [players[gamestate['id']]['hand'][int(num)] for num in choices.split()]
                                
                                melds.append(meld)
                                
                                # Remove cards from player's hand
                                for meld_card in meld:
                                    players[gamestate['id']]['hand'].remove(meld_card)
                                
                                # Add meld to player's melds
                                players[gamestate['id']]['melds'].append(meld)
                                
                                # Refresh display
                                os.system('clear')
                                client_display(gamestate, players)
                    
                        await send_message(ret_val[1], {'draw_response': 'challenge', 'melds': melds})
            
            # Await final gamestate
            gamestate = await get_message(ret_val[0])
            
            # Get final player info
            players = [await get_message(ret_val[0]) for _ in range(0, len(gamestate['order']))]
            
            # Display game state
            os.system('clear')
            client_display(gamestate, players)
            
            if gamestate['winner'] == -2:
                print('Nobody exposed a meld; nobody wins.\n')
            
            else:
                print(f'{players[gamestate["winner"]]["name"]} won (id={gamestate["winner"]})!\n')
            
            # Send rematch response
            print('Rematch? Enter \'q\' to not rematch.')
            choice = input('\n> ')
            
            # Quit or loop again
            if choice == 'q':
                await send_message(ret_val[1], {'command': 'rematch', 'value': 0})
                break
            
            else:
                await send_message(ret_val[1], {'command': 'rematch', 'value': 1})
                print('\nAwaiting the host\'s response...')


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
