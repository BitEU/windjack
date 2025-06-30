from .constants import *
import curses

class PlayerPartition:
	def __init__(self, x, y, w, h):
		self.x, self.y, self.w, self.h = x, y, w, h

	def get_player_coords(self, player):
		x = self.x + max(round(self.w/8), 1)
		y = self.y + min(self.h - player.avatar_size-2, round(self.h/2) + 2)
		return x,y

	def get_card_coords(self, num_cards):
		ret = []
		if num_cards == 0:
			return []
		card_dim = min(int((self.w - num_cards - 2)/num_cards)-1,int(self.h/2))
		temp_x = self.x
		for i in range(num_cards):
			x = temp_x + 1
			y = self.y + int((self.h/2 - card_dim)/2)
			ret.append((x,y,card_dim, card_dim))
			temp_x += card_dim + 2
		return ret

	def get_money_coords(self):
		x = self.x + max(round(self.w*5/8), 1)
		y = self.y + min(self.h-6, round(self.h/2) + 2)
		return x,y

	def get_bet_coords(self):
		x = self.x + max(round(self.w*5/8), 1)
		y = self.y + min(self.h-4, round(self.h/2) + 5)
		return x,y

	def get_name_coords(self):
		x = self.x + max(round(self.w/8), 1)
		y = self.y + min(self.h - 3, round(self.h*7/8))
		return x,y

	def get_bounds_coords(self):
		return self.x,self.y,self.w,self.h

	def get_coords(self, player):
		return {'bounds': self.get_bounds_coords(),
				'player': self.get_player_coords(player),
				'cards': self.get_card_coords(len(player.cards)),
				'money': self.get_money_coords(),
				'bet': self.get_bet_coords(),
				'name': self.get_name_coords()}
	def resize(self, x,w):
		if x: self.x = x
		if w: self.w = w

class PartitionManager:
	def __init__(self, x, y, w, h, num_parts = 4):
		self.x_min = x
		self.y_min = y
		self.w = w
		self.h = h
		self.num_players = 0
		self.players = {}

		#temp
		self.partitions = []
		temp_x = self.x_min
		width = int(self.w / num_parts) - 1
		for i in range(num_parts):
			p = PlayerPartition(temp_x, self.y_min, width, self.h)
			self.partitions.append(p)
			temp_x += width + 1

	def add_player(self, player_id):
		self.num_players += 1
		new_w = min(int(self.w / self.num_players) - 1, int(self.w/2))
		temp_x = self.x_min
		for partition in self.players.values():
			partition.resize(temp_x, new_w)
			temp_x += new_w + 1
		new_x = round(self.x_min + (new_w+1)*(self.num_players-1))
		self.players[player_id] = PlayerPartition(new_x, self.y_min, new_w, self.h)
		
		# self.players[player_id] = self.partitions. pop(0)

	def remove_player(self, player):
		self.players.remove(player.id)

	def get_coords(self, player):
		partition = self.players[player.id]
		return partition.get_coords(player)

	def restart(self):
		self.num_players = 0
		self.players = {}

class DisplayTable:
	def __init__(self, stdscr):
		self.screen = stdscr
		self.items = []
		self.H = curses.LINES - 1
		self.W = curses.COLS - 1
		
		# Windows compatibility: ensure dimensions are positive
		dealer_h = max(1, int(self.H/2-1))
		player_h = max(1, int(self.H/2))
		player_y = max(1, int(self.H/2+1))
		
		self.dealer_wind = stdscr.derwin(dealer_h, self.W, 0, 0)
		self.dealer_wind.box()
		self.player_wind = stdscr.derwin(player_h, self.W, player_y, 0)	
		self.players = set()
		self.partitions = PartitionManager(0, 0, self.W-1, player_h)
		self.dealer = None
		self.dealer_partition = None
		self.state = None
		self.turn = None
		self.printed_msg = None
		self.max_players = None

	def refresh(self):
		try:
			self.dealer_wind.clear()
			self.dealer_wind.box()
			self.draw_dealer()
			if self.state == "starting":
				self.draw_starting_screen()			
			if self.state == "betting":
				self.draw_betting_screen()
			if self.state == "betting_error":
				self.draw_betting_screen("Error: Bet too large or not an integer")
			if self.state == "dealing":
				self.draw_dealing_screen()
			if self.state == "turn":
				self.draw_turn_screen()
			if self.state == "end":
				self.draw_end_screen()
			if self.printed_msg is not None:
				self.draw_printed_msg()

			self.player_wind.clear()
			self.player_wind.box()
			if self.turn:
				self.draw_turn_marker(self.turn)
			for player in self.players:
				self.draw_player(player, self.player_wind)
			self.player_wind.refresh()
			self.dealer_wind.refresh()
		except curses.error:
			# Handle potential Windows terminal resize issues
			pass
	
	def print(self, msg):
		self.printed_msg = msg
		self.refresh()

	def draw_printed_msg(self):
		try:
			y = int(self.H*3/8)
			x = max(int(self.W/2),int(self.W*3/4-len(self.printed_msg)/2))
			# Ensure coordinates are within bounds
			if y >= 0 and y < self.H and x >= 0 and x < self.W:
				self.dealer_wind.addstr(y, x, self.printed_msg)
		except curses.error:
			pass
		self.printed_msg = None

	def add_player(self, player):
		self.partitions.add_player(player.id)
		self.players.add(player)
		self.refresh()

	def remove_player(self, player):
		self.players.remove(player)
		self.refresh()

	def set_dealer(self, dealer):
		self.dealer = dealer
		dealer_w = max(1, int(self.W/2)-1)
		dealer_h = max(1, int(self.H/2)-1)
		self.dealer_partition = PlayerPartition(0, 0, dealer_w, dealer_h)

	def draw_player(self, player, window, coords=None):
		coords = self.partitions.get_coords(player) if not coords else coords
		self.draw_avatar(player, window, coords['player'])
		self.draw_name(player.name, window, coords['name'])
		self.draw_money(player.money, window, coords['money'])
		self.draw_bet(player.bet, window, coords['bet'])
		for i in range(len(player.cards)):
			self.draw_card(player.cards[i], window, coords['cards'][i])
		self.draw_boundary(window, coords['bounds'])

	def draw_dealer(self):
		if not self.dealer:
			return False
		self.draw_player(self.dealer, self.dealer_wind, self.dealer_partition.get_coords(self.dealer))

	def draw_card(self, card, window, loc):
		x, y, w, h = loc
		try:
			# Fill card background
			for j in range(y,min(y+h, self.H-1)):
				for i in range(x, min(x+w+1, self.W-1)):
					window.addstr(j,i," ", curses.color_pair(1))
			
			if card.facedown:
				# Draw card back
				for j in range(y,min(y+h, self.H-1)):
					for i in range(x, min(x+w+1, self.W-1)):
						window.addstr(j,i,"@", curses.color_pair(COLOR.CARD_BLACK.value))
			else:
				# Draw card face
				if y >= 0 and x >= 0:
					window.addstr(y, x, card.symbol, curses.color_pair(card.color.value))
				if y + h-1 < self.H and x + w-1 < self.W:
					window.addstr(y + h-1, x + w-1, card.symbol, curses.color_pair(card.color.value))
				if y + int(h/2) < self.H and x + int(w/2) < self.W:
					window.addstr(y + int(h/2), x + int(w/2), card.num, curses.color_pair(card.color.value))
		except curses.error:
			# Handle drawing outside window bounds
			pass

	def draw_boundary(self, window, loc):
		x,y,w,h = loc
		try:
			for j in range(y,min(y+h-2, self.H-1)):
				if j >= 0 and x >= 0 and x < self.W:
					window.addstr(j,x,"|")
				if j >= 0 and x+w-1 >= 0 and x+w-1 < self.W:
					window.addstr(j,x+w-1,"|")
		except curses.error:
			pass

	def safe_addstr(self, window, y, x, text, *args):
		"""Safely add string to window, handling boundary issues"""
		try:
			if y >= 0 and x >= 0:
				if args:
					window.addstr(y, x, text, *args)
				else:
					window.addstr(y, x, text)
		except curses.error:
			pass

	def draw_money(self, money, window, loc):
		x,y = loc
		self.safe_addstr(window, y, x, "Money")
		self.safe_addstr(window, y+1, x, f"{money}")

	def draw_bet(self, bet, window, loc):
		x,y = loc
		self.safe_addstr(window, y, x, "Bet")
		self.safe_addstr(window, y+1, x, f"{bet}")

	def draw_name(self, name, window, loc):
		x,y = loc
		self.safe_addstr(window, y, x, name)

	def draw_avatar(self, player, window, loc):
		x,y = loc
		avatar = player.avatar
		for i,j in avatar:
			try:
				if y + j >= 0 and x + i >= 0:
					window.addstr(y + j, x + i, player.symbol, curses.color_pair(player.color.value))
			except curses.error:
				pass

	def draw_starting_screen(self):
		msg1 = "Press 'n' to add more players"
		msg2 = "Press 's' to start"
		msg3 = f"(MAX PLAYERS: {self.max_players})"
		y1 = round(self.H/4)
		self.safe_addstr(self.dealer_wind, y1, int(self.W*3/4-len(msg1)/2), msg1)
		self.safe_addstr(self.dealer_wind, y1+1, int(self.W*3/4-len(msg2)/2), msg2)
		self.safe_addstr(self.dealer_wind, y1+3, int(self.W*3/4-len(msg2)/2), msg3)

	def draw_betting_screen(self, msg2 = None):
		msg1 = f"Type your bet ({BET_MIN} - {BET_MAX}) and hit [Enter]"
		y = int(self.H/4)
		x = max(int(self.W/2),int(self.W*3/4-len(msg1)/2))
		self.safe_addstr(self.dealer_wind, y, x, msg1)
		if msg2:
			self.safe_addstr(self.dealer_wind, y+1, max(int(self.W/2),int(self.W*3/4-len(msg2)/2)), msg2)
		try:
			self.screen.move(int(self.H/4) + 2, int(self.W*3/4))
		except curses.error:
			pass

	def draw_turn_marker(self, player):
		msg1 = "[Your Turn]"
		coords = self.partitions.get_coords(player)
		x,y,w,h = coords["bounds"]
		self.safe_addstr(self.player_wind, y+h-2, x + max(0,int(w/2 - len(msg1)/2)), msg1)

	def draw_dealing_screen(self):
		msg1 = f"Dealing ..."
		self.safe_addstr(self.dealer_wind, int(self.H/4), max(int(self.W/2),int(self.W*3/4-len(msg1)/2)), msg1)

	def draw_turn_screen(self):
		if self.turn:
			for i in range(len(self.turn.options)):
				option = self.turn.options[i]
				msg = f"[{option.value}] - {option.name} "
				self.safe_addstr(self.dealer_wind, 2*i + int(self.H/8), max(int(self.W/2),int(self.W*5/8)), msg)
	
	def draw_end_screen(self):
		msg1 = f"Round over! Would you like to keep playing? (y/n)"
		self.safe_addstr(self.dealer_wind, int(self.H/4), max(int(self.W/2),int(self.W*3/4-len(msg1)/2)), msg1)

	def set_state(self, state):
		# if self.state != state:
		self.state = state
		self.refresh()

	def set_turn(self, player):
		self.turn = player
		self.refresh()

	def restart(self):
		self.items = []
		self.players = set()
		self.state = "starting"
		self.turn = None
		self.printed_msg = None
		self.partitions.restart()


def wait(stdscr):
	while(stdscr.getch() != ord('q')):
		pass