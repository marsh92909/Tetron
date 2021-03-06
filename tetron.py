#!/usr/bin/python


import os
import random
import sys
import threading
import time

import numpy as np
import pygame


# Program information.
name_program = 'Tetron'
version_program = '1.3.0'
# Get the path to the temporary folder containing the program.
folder_program = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
folder_sounds = os.path.abspath(os.path.join(folder_program, 'Sounds'))
folder_images = os.path.abspath(os.path.join(folder_program, 'Images'))
# Initialize all pygame modules.
pygame.init()

# =============================================================================
# Game Settings.
# =============================================================================
# Define the scores needed to move to the next stage. The last value is the score needed to win the game.
score_thresholds = [400, 800, 1000]
# Define the numbers of remaining players needed to move to the next stage. The last value is the number needed to win the game.
remaining_thresholds = [50, 10, 1]
# Define the range of block fall speeds (ms) from the start to end of the game.
speeds_fall = [1000, 1000/6]
speeds_fall_classic = [1000, 1000/60]
# Define the block fall speed multiplier for some special effects (values below 1 result in faster speeds).
speed_fall_multiplier = 1/2
# Define the block move speed (ms) and initial delay for key repeats (ms).
speed_move = 25
delay_move = 150
# Define the soft drop speed (ms) and initial delay for key repeats (ms).
speed_softdrop = 50
delay_softdrop = 50
# Define the maximum duration (ms) for a tetrimino to remain landed before locking.
duration_max_landed = 500
# Define the time (ms) between receiving garbage and putting garbage in the matrix on the next hard drop.
time_garbage_warning = 8000

# Define the parameters of a normal distribution for the delay (ms) between deciding and performing a move for AI.
ai_delay_mean = 1500
ai_delay_std = 100

# Define how many blocks to show in the next queue.
next_count = 5
# Define the IDs for classic tetriminos, advanced tetriminos, special effects.
id_classic = [100, 200, 300, 400, 500, 600, 700]
id_advanced = [101, 102, 201, 202, 203, 301, 302, 303, 401, 402, 403, 501, 601, 602, 701, 801, 811, 812, 813, 814, 899]
id_special = ['ghost', 'heavy', 'disoriented', 'blind', 'wind', 'zombie', 'fake']

# Define the range of probabilities (between 0 and 1) of getting an advanced tetrimino.
weights_advanced = [0, 1/3]
# Define the score needed to begin increasing the probability of getting an advanced tetrimino.
score_update_chance_advanced = 100
# Define the range of probabilities (between 0 and 1) of getting a special effect.
weights_special = [0, 1/20]
# Define the score needed to begin increasing the probability of getting a special effect.
score_update_chance_special = score_thresholds[0]
# Define settings for special effects (ms).
duration_disoriented = 10000
duration_blind = 10000
speed_wind = 500

# Create font objects used to create text.
font_normal = pygame.font.SysFont('Segoe UI Semibold', 24)
font_small = pygame.font.SysFont('Segoe UI Semibold', 18)
font_large = pygame.font.SysFont('Segoe UI Black', 30)

# =============================================================================
# Sounds.
# =============================================================================
# Load sound effects.
sound_game_move = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_move.wav'))
sound_game_rotate = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_rotate.wav'))
sound_game_harddrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_harddrop.wav'))
sound_game_softdrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_softdrop.wav'))
sound_game_hold = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_hold.wav'))
sound_game_landing = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_landing.wav'))
sound_game_lock = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_lock.wav'))
sound_game_single = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_single.wav'))
sound_game_double = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_double.wav'))
sound_game_triple = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_triple.wav'))
sound_game_tetris = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_tetris.wav'))
sound_game_special = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_special.wav'))
sound_game_perfect = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_perfect.wav'))
sound_game_garbage_1 = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_garbage_1.wav'))
sound_game_garbage_2 = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_garbage_2.wav'))
sound_game_win = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_win.wav'))
sound_special_ghost = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_ghost.wav'))
sound_special_heavy = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_heavy.wav'))
sound_special_disoriented = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_disoriented.wav'))
sound_special_blind = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_blind.wav'))
sound_special_wind = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_wind.wav'))
sound_special_zombie = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_zombie.wav'))
sound_special_fake = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_fake.wav'))
# Set volume for sound effects.
sound_game_move.set_volume(0.1)
sound_game_rotate.set_volume(0.1)
sound_game_harddrop.set_volume(0.1)
sound_game_softdrop.set_volume(0.1)
sound_game_hold.set_volume(0.1)
sound_game_landing.set_volume(0.1)
sound_game_lock.set_volume(0.1)
sound_game_single.set_volume(0.1)
sound_game_double.set_volume(0.1)
sound_game_triple.set_volume(0.1)
sound_game_tetris.set_volume(0.1)
sound_game_special.set_volume(0.1)
sound_game_perfect.set_volume(0.1)
sound_game_garbage_1.set_volume(0.1)
sound_game_garbage_2.set_volume(0.1)
sound_game_win.set_volume(0.25)
sound_special_ghost.set_volume(0.25)
sound_special_heavy.set_volume(0.25)
sound_special_disoriented.set_volume(0.25)
sound_special_blind.set_volume(0.5)
sound_special_wind.set_volume(0.25)
sound_special_zombie.set_volume(0.5)
sound_special_fake.set_volume(0.25)

# =============================================================================
# Controls.
# =============================================================================
# Main controls.
key_start = pygame.K_RETURN
key_stop = pygame.K_ESCAPE
key_mode_1 = pygame.K_1
key_mode_2 = pygame.K_2
key_mode_3 = pygame.K_3
key_mode_4 = pygame.K_4
key_mode_5 = pygame.K_5
key_mode_6 = pygame.K_6
key_mode_7 = pygame.K_7
key_mode_8 = pygame.K_8
key_mode_9 = pygame.K_9
key_toggle_classic = pygame.K_0
key_move_left = pygame.K_LEFT
key_move_right = pygame.K_RIGHT
key_rotate_clockwise = [pygame.K_UP, pygame.K_x]
key_rotate_counterclockwise = [pygame.K_z]
key_harddrop = pygame.K_SPACE
key_softdrop = pygame.K_DOWN
key_hold = pygame.K_c
# Controls for game modes with multiple player games.
key_left_move_left = pygame.K_a
key_left_move_right = pygame.K_d
key_left_rotate_clockwise = pygame.K_w
key_left_rotate_counterclockwise = pygame.K_e
key_left_softdrop = pygame.K_s
key_left_hold = pygame.K_q
key_right_move_left = pygame.K_j
key_right_move_right = pygame.K_l
key_right_rotate_clockwise = pygame.K_i
key_right_rotate_counterclockwise = pygame.K_u
key_right_softdrop = pygame.K_k
key_right_hold = pygame.K_o


# =============================================================================
# Colors.
# =============================================================================
# Return a 3-tuple with RGB values. For grayscale colors, pass a number between 0 (black) and 1 (white). For block-specific color, pass its corresponding number value.
def rgb(color, tint=0):
    # Set a grayscale color if 'color' is a number between 0 and 1, inclusive.
    if 0 <= color <= 1:
        color = [color*255] * 3
    # Set a predefined color if 'color' is a number greater than 1.
    else:
        if 100 <= color < 200:  # Cyan
            color = [0,175,191]
        elif 200 <= color < 300:  # Blue
            color = [0,149,255]
        elif 300 <= color < 400:  # Orange
            color = [255,128,0]
        elif 400 <= color < 500:  # Yellow
            color = [255,191,0]
        elif 500 <= color < 600:  # Green
            color = [0,191,96]
        elif 600 <= color < 700:  # Purple
            color = [140,102,255]
        elif 700 <= color < 800:  # Red
            color = [255,64,64]
        elif 800 <= color < 900:  # Pink
            color = [255,77,136]
        elif color == 900:  # Gray
            color = [158,158,158]
        elif color == 901:  # White
            color = [255,255,255]
        elif color == 902:  # Black
            color = [0,0,0]
    if tint != 0:
        if tint > 0:
            color = np.array([255,255,255])*abs(tint) + np.array(color)*(1-abs(tint))
        elif tint < 0:
            color = np.array([0,0,0])*abs(tint) + np.array(color)*(1-abs(tint))
    return tuple(color)

# Store 3-tuples of RGB colors in a dictionary.
colors = {
    100: (0,175,191),  # Cyan
    200: (0,149,255),  # Blue
    300: (255,128,0),  # Orange
    400: (255,191,0),  # Yellow
    500: (0,191,96),  # Green
    600: (140,102,255),  # Purple
    700: (255,64,64),  # Red
    800: (255,77,136),  # Pink
    900: rgb(0.618),  # Garbage / AI
    901: rgb(1.00),  # Ghost
    902: rgb(0.00),  # Heavy
    904: rgb(0.28),  # Blind
    906: (106, 128, 96),  # Zombie  (HSB 100, 25%, 50%)

    1001: rgb(1.00),  # White
    1002: rgb(0.00),  # Black
    1003: rgb(0.25),  # Empty blocks
    1004: rgb(0.35),  # Highlighted blocks
    1005: rgb(0.50),  # Gray text
    }


# =============================================================================
# Classes.
# =============================================================================
# The main class that controls an instance of a game and contains gameplay actions such as moving and rotating blocks.
class Tetron:
    # Initialize the attributes of the instance of of this class when it is first created.
    def __init__(self, is_player, instance_self, games):
        self.is_player = is_player
        self.instance_self = instance_self
        self.games = games

        # Initialize attributes.
        self.initialize()

        # Create and set the sizes of the surfaces used to display each element of the game.
        self.resize_display()

    # Initialize values of attributes that are both modified during the game and reset when starting the game. Called on first startup and subsequent game starts.
    def initialize(self):
        # Initialize flags indicating statuses of the game.
        self.flag_playing = False
        self.flag_paused = False
        self.flag_lose = False

        self.flag_advancing = True
        self.flag_landed = False
        self.flag_hold = False
        self.flag_tspin = False
        self.flag_tspin_mini = False
        self.flag_fast_fall = False
        self.flag_harddrop = False
        self.flag_softdropping = False
        self.flag_perfect = False
        self.reset_special(reset_all=True)
        
        self.flag_put_garbage = False

        self.ai_flag_positioning = True
        self.ai_flag_positioning_left = True
        self.ai_flag_calculating = True

        # Initialize a list containing effectiveness values of moves.
        self.ai_evaluations = []
        # Initialize the decided move.
        self.ai_decision = None
        # Initialize the decision time.
        self.ai_time_evaluate = 0
        # Initialize the decision duration.
        self.ai_delay = 0

        # Initialize arrays for current tetrimino, dropped blocks, blocks displayed on screen, and highlighted blocks showing where tetriminos will be hard dropped.
        self.array_current = np.zeros([self.games.row_count, self.games.column_count])
        self.array_stack = np.zeros([self.games.row_count, self.games.column_count])
        self.array_display = np.zeros([self.games.row_count, self.games.column_count])
        self.array_highlight = np.zeros([self.games.row_count, self.games.column_count])

        # Initialize lists with Booleans indicating which tetriminos or special effects have been used to prevent duplicates.
        self.used_classic = [False] * len(id_classic)
        self.used_advanced = [False] * len(id_advanced)
        self.used_special = [False] * len(id_special)
        # Initialize the current tetrimino ID.
        self.id_current = 0
        # Initialize the hold queue.
        self.queue_hold = []
        # Initialize the next queue.
        self.queue_next = []
        # Initialize the garbage queue.
        self.queue_garbage = []
        # Initialize time when current garbage was received.
        self.time_receive_garbage = self.games.time_current + 0

        # Initialize the score.
        self.score = 0
        # Initialize the score increment queue.
        self.score_increment = []
        # Initialize the number of placed tetriminos.
        self.count = 0
        # Initialize the number of successive line clears.
        self.combos = 0

        # Initialize the block fall speed, the probability of getting an advanced tetrimino, and the probability of getting a special effect.
        self.update_difficulty()

    # Resize and reposition the surfaces used to display each element of the game.
    def resize_display(self):
        # Define the location (left, top) of the bounding box of the game. Must be after defining the total size.
        position_main = (
            (self.games.size_window[0] - self.games.size_game[0]*len(self.games.all) - (len(self.games.all)-1)*self.games.spacing_large)//2 + self.games.size_game[0]*self.instance_self + self.games.spacing_large*self.instance_self,
            games.height_panel
            )

        # Create the surface and rect object used to display the matrix.
        self.surface_matrix = pygame.Surface(self.games.size_matrix)
        self.rect_matrix = self.surface_matrix.get_rect()
        self.rect_matrix.left = position_main[0] + self.games.width_hold + self.games.spacing_small
        self.rect_matrix.top = position_main[1] + 0
        # Create the text and rect object for the hold queue.
        self.text_hold = font_small.render('HOLD', True, colors[1005])
        self.rect_text_hold = self.text_hold.get_rect()
        self.rect_text_hold.centerx = position_main[0] + self.games.width_hold // 2
        self.rect_text_hold.top = position_main[1] + 0
        # Create the surface and rect object used to display the hold queue.
        self.surface_hold = pygame.Surface((self.games.width_hold, self.games.width_hold))
        self.rect_hold = self.surface_hold.get_rect()
        self.rect_hold.left = position_main[0] + 0
        self.rect_hold.top = position_main[1] + self.rect_text_hold.height
        # Create the text and rect object for the next queue.
        self.text_next = font_small.render('NEXT', True, colors[1005])
        self.rect_text_next = self.text_next.get_rect()
        self.rect_text_next.centerx = position_main[0] + self.games.size_game[0] - self.games.width_next // 2
        self.rect_text_next.top = position_main[1] + 0
        # Create the surface and rect object used to display the next queue.
        self.surface_next = pygame.Surface((self.games.width_next, self.games.size_game[1]))
        self.rect_next = self.surface_next.get_rect()
        self.rect_next.right = position_main[0] + self.games.size_game[0]
        self.rect_next.top = position_main[1] + self.rect_text_next.height
        # Create the surface and rect object used to display the garbage queue.
        self.surface_garbage = pygame.Surface((self.games.width_block, self.games.size_game[1]))
        self.rect_garbage = self.surface_garbage.get_rect()
        self.rect_garbage.right = position_main[0] + self.games.width_hold
        self.rect_garbage.bottom = position_main[1] + self.games.size_game[1]
        # Create the surface and rect object used to display multiplayer information.
        self.surface_information = pygame.Surface((self.games.width_next, self.games.size_game[1]))
        self.rect_information = self.surface_information.get_rect()
        self.rect_information.right = position_main[0] + self.games.size_game[0]
        self.rect_information.bottom = position_main[1] + self.games.size_game[1]

        # Draw the game.
        self.draw_matrix()
        self.draw_hold()
        self.draw_next()
        self.draw_garbage()
        self.draw_information()

    # Start the game.
    def start_game(self):
        # Reset attributes.
        self.initialize()
        self.reset_time_fall()
        # Set flags.
        self.flag_playing = True
        # Select a target.
        self.select_target()
        # Generate the next queue and set the new tetrimino.
        self.add_next(next_count)
        self.set_tetrimino()
    
    # Pause or resume the game.
    def pause_game(self):
        # Resume game.
        if self.flag_paused:
            game.flag_playing = True
            game.flag_paused = False
        # Pause game.
        else:
            game.flag_playing = False
            game.flag_paused = True
    
    # Stop the game.
    def stop_game(self):
        # Set flags.
        self.flag_playing = False
        self.flag_paused = False
        self.reset_special(reset_all=True)
        # Empty queues.
        self.queue_hold = []
        self.queue_next = []
        self.queue_garbage = []
        # Update display.
        self.update()

    # Randomly generate the next tetriminos and add them to the next queue.
    def add_next(self, count=1):
        # Randomly select a category to choose from, then randomly select a tetrimino within the category with each tetrimino having an equal probability.
        for is_advanced in random.choices([True, False], [self.weight_advanced, 1-self.weight_advanced], k=count):
            if is_advanced:
                id_selected = random.choice([id_advanced[i] for i, x in enumerate(id_advanced) if not self.used_advanced[i]])
                self.used_advanced[id_advanced.index(id_selected)] = True
                # Reset all values in the list to False.
                if all(self.used_advanced):
                    self.used_advanced = [False] * len(self.used_advanced)
            else:
                id_selected = random.choice([id_classic[i] for i, x in enumerate(id_classic) if not self.used_classic[i]])
                self.used_classic[id_classic.index(id_selected)] = True
                # Reset all values in the list to False.
                if all(self.used_classic):
                    self.used_classic = [False] * len(self.used_classic)
            
            # Create tetrimino array.
            if id_selected not in [899]:
                tetrimino = self.create_tetrimino(id_selected)
            else:
                tetrimino = None

            # Store the tetrimino array, the ID, and rotation in a tuple and append it to the next queue.
            self.queue_next.append((tetrimino, id_selected, 0))
        # Draw next queue.
        self.draw_next()
    
    # Create and return a tetrimino array.
    def create_tetrimino(self, number):
        # Zombie tetrimino.
        if self.flag_zombie:
            width = random.choice([2, 3])
            height = random.choice([1, 2, 3])
            left = random.choice([column for column in range(self.games.column_count-width+1) if np.any(self.array_stack[:,column])>0])
            right = left + width
            top = np.argmax(np.any(self.array_stack[:, left:right] > 0, axis=1))
            bottom = max(np.argmax(self.array_stack[:, left:right] > 0, axis=0)) + 1
            if bottom - top != height:
                bottom = min([self.games.row_count, top+height])
            tetrimino = np.copy(self.array_stack[top:bottom, left:right])
            tetrimino[tetrimino <= 0] = -1
            tetrimino[tetrimino > 0] = 906
            self.array_stack[top:bottom, left:right] = 0
            # Make the tetrimino square.
            if (bottom-top) != (right-left):
                difference = (bottom-top) - (right-left)
                if difference < 0:
                    if bottom + abs(difference) > self.games.row_count:
                        top -= abs(difference)
                        tetrimino = np.concatenate((-1*np.ones([abs(difference),tetrimino.shape[1]]), tetrimino), axis=0)
                    else:
                        bottom += abs(difference)
                        tetrimino = np.concatenate((tetrimino, -1*np.ones([abs(difference),tetrimino.shape[1]])), axis=0)
                elif difference > 0:
                    if right + abs(difference) > self.games.column_count:
                        left -= abs(difference)
                        tetrimino = np.concatenate((-1*np.ones([tetrimino.shape[0],abs(difference)]), tetrimino), axis=1)
                    else:
                        right += abs(difference)
                        tetrimino = np.concatenate((tetrimino, -1*np.ones([tetrimino.shape[0],abs(difference)])), axis=1)
            # Insert the tetrimino into the current tetrimino array.
            self.array_current[:] = 0
            self.array_current[top:bottom, left:right] = tetrimino
        else:
            # Classic tetriminos.
            if number == id_classic[0]:  # I
                tetrimino = number * np.ones([4, 4])
                tetrimino[[0,2,3], :] = -1
            elif number == id_classic[1]:  # J
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, 1:] = -1
                tetrimino[2, :] = -1
            elif number == id_classic[2]:  # L
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, 0:2] = -1
                tetrimino[2, :] = -1
            elif number == id_classic[3]:  # O
                tetrimino = number * np.ones([2, 2])
            elif number == id_classic[4]:  # S
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, 0] = -1
                tetrimino[1, 2] = -1
                tetrimino[2, :] = -1
            elif number == id_classic[5]:  # T
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, [0,2]] = -2
                tetrimino[2, [0,2]] = -3
                tetrimino[2, 1] = -1
            elif number == id_classic[6]:  # Z
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, 2] = -1
                tetrimino[1, 0] = -1
                tetrimino[2, :] = -1
            # Advanced tetriminos.
            elif number == 101:  # I+ (1x5)
                tetrimino = number * np.ones([5, 5])
                tetrimino[[0,2,3,4], :] = -1
            elif number == 102:  # I- (1x3)
                tetrimino = number * np.ones([3, 3])
                tetrimino[[0,2], :] = -1
            elif number == 201:  # J+ (3x3)
                tetrimino = number * np.ones([3, 3])
                tetrimino[0:2, 1:3] = -1
            elif number == 202:  # J- (2x2)
                tetrimino = number * np.ones([2, 2])
                tetrimino[0, 1] = -1
            elif number == 203:  # J+ (2x4)
                tetrimino = number * np.ones([4, 4])
                tetrimino[[0,3], :] = -1
                tetrimino[1, 1:4] = -1
            elif number == 301:  # L+ (3x3)
                tetrimino = number * np.ones([3, 3])
                tetrimino[0:2, 0:2] = -1
            elif number == 302:  # L- (2x2)
                tetrimino = number * np.ones([2, 2])
                tetrimino[0, 0] = -1
            elif number == 303:  # L+ (2x4)
                tetrimino = number * np.ones([4, 4])
                tetrimino[[0,3], :] = -1
                tetrimino[1, 0:3] = -1
            elif number == 401:  # O+ (2x3)
                tetrimino = number * np.ones([3, 3])
                tetrimino[2, :] = -1
            elif number == 402:  # O+ (2x4)
                tetrimino = number * np.ones([4, 4])
                tetrimino[[0,3], :] = -1
            elif number == 403:  # O+ (Ring)
                tetrimino = number * np.ones([3, 3])
                tetrimino[1, 1] = -1
            elif number == 501:  # S+
                tetrimino = number * np.ones([3, 3])
                tetrimino[0:2, 0] = -1
                tetrimino[1:3, 2] = -1
            elif number == 601:  # T+ (Plus)
                tetrimino = number * np.ones([3, 3])
                tetrimino[0, 0] = -1
                tetrimino[0, 2] = -1
                tetrimino[2, 0] = -1
                tetrimino[2, 2] = -1
            elif number == 602:  # T+ (Capital)
                tetrimino = number * np.ones([3, 3])
                tetrimino[1:3, [0,2]] = -1
            elif number == 701:  # Z+
                tetrimino = number * np.ones([3, 3])
                tetrimino[1:3, 0] = -1
                tetrimino[0:2, 2] = -1
            elif number == 801:  # Random 3x3
                shape = [3, 3]
                count = random.choice([3, 4, 5])
                random_indices = random.sample(range(np.prod(shape)), count)
                tetrimino = -1 * np.ones(shape)
                tetrimino[np.unravel_index(random_indices, shape)] = number
            elif number == 811:  # Period (.)
                tetrimino = number * np.ones([1, 1])
            elif number == 812:  # Comma (,)
                tetrimino = number * np.ones([2, 2])
                tetrimino[[0,1],[0,1]] = -1
            elif number == 813:  # Colon (:)
                tetrimino = -1 * np.ones([3, 3])
                tetrimino[1, [0,2]] = number
            elif number == 814:  # Quotation (")
                tetrimino = -1 * np.ones([3, 3])
                tetrimino[0:2, [0,2]] = number
            elif number == 899:  # Freebie
                # Index of highest row containing dropped blocks.
                index_highest = np.argmax(np.any(self.array_stack > 0, axis=1))
                # Index of lowest row that can fit this tetrimino.
                index_lowest = max(np.argmax(self.array_stack, axis=0))
                # Get the top rows of the dropped blocks.
                tetrimino = np.copy(self.array_stack[index_highest:index_lowest+1, :]) > 0
                # Get the row indices of the highest blocks in each column of the dropped blocks array, with values of -1 for empty columns.
                rows_highest = np.argmax(tetrimino, axis=0)
                rows_highest[np.all(tetrimino == 0, axis=0)] = -1
                # Fill the blocks below the highest blocks in each column.
                for column, row in enumerate(rows_highest):
                    if row >= 0:
                        tetrimino[row:, column] = 1
                # Create the tetrimino by inverting the dropped blocks.
                tetrimino = number * (1 - tetrimino)
                # Replace all values of 0 with -1.
                tetrimino[tetrimino == 0] = -1
        return tetrimino
    
    # Create a padded version of a tetrimino array for display in the queues.
    def create_tetrimino_mini(self, array):
        # Create a placeholder array for tetriminos that must be generated only when taken out of the next queue.
        if array is None:
            array = 800 * np.ones([3, 3])
        # Pad small arrays.
        if array.shape[0] <= 2:
            array = np.pad(array, ((1,1), (0,0)), mode='constant', constant_values=-1)
        if array.shape[1] <= 2:
            array = np.pad(array, ((0,0), (1,1)), mode='constant', constant_values=-1)
        return array
    
    # Get the first tetrimino in the next queue or the hold queue and use it as the current.
    def set_tetrimino(self, hold_data=None):
        # Randomly select a special property after selecting whether to use a special effect.
        if random.choices([True, False], [self.weight_special, 1-self.weight_special], k=1)[0]:
            effect_special = random.choice([id_special[i] for i in range(len(id_special)) if not self.used_special[i]])
            self.used_special[id_special.index(effect_special)] = True
            # Reset all values in the list to False.
            if all(self.used_special):
                self.used_special = [False] * len(self.used_special)
            # Apply the special effect.
            if effect_special == id_special[0]:
                self.flag_ghost = True
                self.flag_fast_fall = True
                if self.is_player:
                    sound_special_ghost.play()
            elif effect_special == id_special[1]:
                self.flag_heavy = True
                self.flag_fast_fall = True
                if self.is_player:
                    sound_special_heavy.play()
            elif effect_special == id_special[2]:
                # Apply the effect only if it is not currently active.
                if not self.flag_disoriented:
                    self.flag_disoriented = True
                    self.time_start_disoriented = self.games.time_current + 0
                    if self.is_player:
                        sound_special_disoriented.play()
            elif effect_special == id_special[3]:
                # Apply the effect only if it is not currently active.
                if not self.flag_blind:
                    self.flag_blind = True
                    self.time_start_blind = self.games.time_current + 0
                    if self.is_player:
                        sound_special_blind.play()
            elif effect_special == id_special[4]:
                self.flag_wind = True
                self.time_start_wind = self.games.time_current + 0
                self.wind_direction = random.choice([1, -1])
                self.wind_position = self.games.width_block // 2
                if self.is_player:
                    sound_special_wind.play()
            elif effect_special == id_special[5]:
                # Apply the effect only if there are placed blocks to use and if not taking a block out of hold.
                if np.any(self.array_stack > 0) and hold_data is None:
                    self.flag_zombie = True
                    if self.is_player:
                        sound_special_zombie.play()
            elif effect_special == id_special[6]:
                self.flag_fake = True
        # Get and remove the first item from the next or hold queue.
        if self.flag_zombie:
            data = [None, None, 0]
        else:
            if hold_data is None:
                data = self.queue_next.pop(0)
                self.add_next()
            else:
                data = hold_data
        tetrimino, number, rotation = data

        # Generate any un-generated tetrimino arrays.
        if tetrimino is None:
            tetrimino = self.create_tetrimino(number)
        # Apply any special effects to tetrimino.
        if self.flag_ghost:
            tetrimino[tetrimino > 0] = 901
        elif self.flag_heavy:
            tetrimino[tetrimino > 0] = 902
        
        # Assign the new data.
        self.tetrimino = tetrimino
        self.id_current = number
        self.rotation_current = rotation

        if not self.flag_zombie:
            # Clear the current tetrimino array.
            self.array_current[:] = 0
            # Insert the new tetrimino in the array.
            column_left = int(np.floor((self.games.column_count-tetrimino.shape[1])/2))
            self.array_current[0:tetrimino.shape[0], column_left:column_left+tetrimino.shape[1]] = self.tetrimino
        # Check for landing.
        self.check_landed()
        # Update display.
        self.update()

        # Record the time for AI.
        self.ai_time_evaluate = self.games.time_current + 0
        # Select a delay for this tetrimino.
        self.ai_delay = random.gauss(ai_delay_mean, ai_delay_std)
    
    # Shift down one line. Return a Boolean indicating whether it was successful.
    def fall(self):
        success = False
        # Determine if at the bottom of the matrix.
        is_at_bottom = np.any(self.array_current[-1*(not self.flag_zombie) + 0*self.flag_zombie,:] > 0)
        # Shift the tetrimino down one line and return a copy.
        array_current = np.roll(self.array_current, shift=1*((-1) ** self.flag_zombie), axis=0)
        # Determine if the shifted copy intersects the stack.
        is_intersecting = np.any(self.array_stack[array_current > 0] > 0)
        # Apply the shift.
        if (self.flag_ghost and not is_at_bottom) or (not self.flag_ghost and (not is_at_bottom and not is_intersecting)):
            self.array_current = np.copy(array_current)
            # Reset the fall timer if the tetrimino has landed.
            self.check_landed()
            # Update display.
            self.update()
            # Update Boolean.
            success = True
        return success
    
    # Lock in place. Input True to play the hard drop sound instead of the lock sound.
    def lock(self, is_harddrop=False):
        # If a heavy tetrimino, delete placed blocks below the current tetrimino and shift tetrimino to bottom row.
        if self.flag_heavy:
            self.array_stack[self.array_highlight < 0] = 0
            self.array_current = np.roll(self.array_current, np.argmax(np.any(np.flipud(self.array_current) > 0, axis=1)), axis=0)
        # Lock tetrimino.
        if not self.flag_fake:
            self.array_stack[self.array_current > 0] = self.array_current[self.array_current > 0]
        # Set flag to hard drop other game instances.
        self.flag_harddrop = True
        # Play sound effect.
        if self.instance_self == 0:
            if self.is_player:
                if not self.flag_fake:
                    if is_harddrop:
                        sound_game_harddrop.play()
                    else:
                        sound_game_lock.play()
                else:
                    sound_special_fake.play()
        self.update()

        # Increment the placed blocks counter.
        self.count += 1

        # Reset certain flags.
        self.reset_special(reset_all=False)
        self.flag_fast_fall = False
        self.flag_landed = False
        self.flag_hold = False
        # Update the values of previously placed special blocks.
        self.array_stack[self.array_stack == 901] = 900
        self.array_stack[self.array_stack == 902] = 900
        self.array_stack[self.array_stack == 906] = 900

        # Check for cleared lines and empty them.
        rows_cleared = np.argwhere(np.all(self.array_stack > 0, axis=1))
        line_count = len(rows_cleared)
        if line_count > 0:
            self.array_stack = np.concatenate((
                np.zeros([line_count,self.games.column_count]),
                np.delete(self.array_stack, obj=rows_cleared, axis=0)
                ), axis=0)
        # Increment the combo counter if a line was cleared.
        if line_count > 0:
            self.combos += 1
            # Check for a perfect clear.
            self.flag_perfect = not np.any(self.array_stack)
        else:
            self.combos = 0

        # Calculate number of garbage lines.
        garbage_count = self.calculate_garbage(line_count)
        # Clear garbage lines if the queue contains any.
        if len(self.queue_garbage) > 0:
            self.subtract_garbage(garbage_count)
        # Send garbage lines if the queue is empty.
        else:
            self.send_garbage(garbage_count)
        # Put garbage in the matrix.
        if self.flag_put_garbage and garbage_count == 0:
            self.put_garbage()

        # Put the score increment in the queue.
        self.score_increment.append(self.calculate_score(line_count))
        
        # Reset the previous block fall time.
        self.reset_time_fall()
        # Reset the T-spin and perfect clear flags. Must be after calculating score.
        self.flag_tspin = False
        self.flag_tspin_mini = False
        self.flag_perfect = False
        # Reset attributes for AI.
        self.ai_evaluations = []
        self.ai_decision = None
        self.ai_time_evaluate = 0
        self.ai_flag_positioning = True
        self.ai_flag_positioning_left = True
        self.ai_flag_calculating = True
        
        # Stop the game or create a new tetrimino.
        if self.flag_playing:
            self.check_lose()
            if not self.flag_lose:
                self.set_tetrimino()

    # Hard drop.
    def harddrop(self):
        if not self.flag_ghost and not self.flag_heavy:
            self.array_current = -1 * self.array_highlight
        self.lock(is_harddrop=True)

    # Move left. Return a Boolean indicating whether it was successful.
    def move_left(self):
        success = False
        # Check if already in leftmost column.
        if self.flag_ghost or not np.any(self.array_current[:, 0] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_stack[indices_rows, indices_columns-1] > 0):
                self.array_current = np.roll(self.array_current, shift=-1, axis=1)
                # Reset the block fall time if the tetrimino has landed.
                self.check_landed()
                # Update display.
                self.update()
                # Play sound effect.
                if self.is_player:
                    sound_game_move.play()
                # Update Boolean.
                success = True
        return success
    
    # Move right. Return a Boolean indicating whether it was successful.
    def move_right(self):
        success = False
        # Check if already in rightmost column.
        if self.flag_ghost or not np.any(self.array_current[:, -1] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_stack[indices_rows, indices_columns+1] > 0):
                self.array_current = np.roll(self.array_current, shift=1, axis=1)
                # Reset the block fall time if the tetrimino has landed.
                self.check_landed()
                # Update display.
                self.update()
                # Play sound effect.
                if self.is_player:
                    sound_game_move.play()
                # Update Boolean.
                success = True
        return success

    # Rotate counterclockwise or clockwise by inputting 1 (default) or -1. Return a Boolean indicating whether it was successful.
    def rotate(self, direction=1):
        success = False
        # List of lists of tuples for all translation values (right, down) for each rotation, defined in the order they should be checked.
        translations_all = [
            # J, L, S, T, Z and their variants
            [( 0, 0),	(-1, 0),	(-1,-1),	( 0,+2),	(-1,+2),],  # 0->R
            [( 0, 0),	(+1, 0),	(+1,+1),	( 0,-2),	(+1,-2),],  # R->0
            [( 0, 0),	(+1, 0),	(+1,+1),	( 0,-2),	(+1,-2),],  # R->2
            [( 0, 0),	(-1, 0),	(-1,-1),	( 0,+2),	(-1,+2),],  # 2->R
            [( 0, 0),	(+1, 0),	(+1,-1),	( 0,+2),	(+1,+2),],  # 2->L
            [( 0, 0),	(-1, 0),	(-1,+1),	( 0,-2),	(-1,-2),],  # L->2
            [( 0, 0),	(-1, 0),	(-1,+1),	( 0,-2),	(-1,-2),],  # L->0
            [( 0, 0),	(+1, 0),	(+1,-1),	( 0,+2),	(+1,+2),],  # 0->L
            # I and its variants
            [( 0, 0),	(-2, 0),	(+1, 0),	(-2,+1),	(+1,-2),],  # 0->R
            [( 0, 0),	(+2, 0),	(-1, 0),	(+2,-1),	(-1,+2),],  # R->0
            [( 0, 0),	(-1, 0),	(+2, 0),	(-1,-2),	(+2,+1),],  # R->2
            [( 0, 0),	(+1, 0),	(-2, 0),	(+1,+2),	(-2,-1),],  # 2->R
            [( 0, 0),	(+2, 0),	(-1, 0),	(+2,-1),	(-1,+2),],  # 2->L
            [( 0, 0),	(-2, 0),	(+1, 0),	(-2,+1),	(+1,-2),],  # L->2
            [( 0, 0),	(+1, 0),	(-2, 0),	(+1,+2),	(-2,-1),],  # L->0
            [( 0, 0),	(-1, 0),	(+2, 0),	(-1,-2),	(+2,+1),],  # 0->L
            # O and its variants
            [( 0, 0),],
            # Others
            [( 0, 0),   (-1, 0),    ( 0,-1),    (-1,-1),    ( 0,-2),    (-1,-2),],  # Clockwise
            [( 0, 0),   (+1, 0),    ( 0,-1),    (+1,-1),    ( 0,-2),    (+1,-2),],  # Counterclockwise
            ]
        # Assign the corresponding translation values.
        if self.id_current is None:
            id_group = None
        else:
            id_group = int(np.floor(self.id_current / 100) * 100)
        if id_group in np.array(id_classic)[[1, 2, 4, 5, 6]]:
            if self.rotation_current == 0 and direction == -1:
                translations = translations_all[0]
            elif self.rotation_current == 0 and direction == 1:
                translations = translations_all[7]
            elif self.rotation_current == 90 and direction == -1:
                translations = translations_all[6]
            elif self.rotation_current == 90 and direction == 1:
                translations = translations_all[5]
            elif self.rotation_current == 180 and direction == -1:
                translations = translations_all[4]
            elif self.rotation_current == 180 and direction == 1:
                translations = translations_all[3]
            elif self.rotation_current == 270 and direction == -1:
                translations = translations_all[2]
            elif self.rotation_current == 270 and direction == 1:
                translations = translations_all[1]
        elif id_group == id_classic[0]:
            if self.rotation_current == 0 and direction == -1:
                translations = translations_all[8]
            elif self.rotation_current == 0 and direction == 1:
                translations = translations_all[15]
            elif self.rotation_current == 90 and direction == -1:
                translations = translations_all[14]
            elif self.rotation_current == 90 and direction == 1:
                translations = translations_all[13]
            elif self.rotation_current == 180 and direction == -1:
                translations = translations_all[12]
            elif self.rotation_current == 180 and direction == 1:
                translations = translations_all[11]
            elif self.rotation_current == 270 and direction == -1:
                translations = translations_all[10]
            elif self.rotation_current == 270 and direction == 1:
                translations = translations_all[9]
        elif id_group == id_classic[3]:
            translations = translations_all[16]
        else:
            if direction == -1:
                translations = translations_all[18]
            else:
                translations = translations_all[17]

        # Calculate how many empty rows at top/bottom and empty columns at left/right within tetrimino before attempting rotation.
        top_empty_before, bottom_empty_before = np.argmax(np.any(self.tetrimino > 0, axis=1)), np.argmax(np.any(np.flipud(self.tetrimino > 0), axis=1))
        left_empty_before, right_empty_before = np.argmax(np.any(self.tetrimino > 0, axis=0)), np.argmax(np.any(np.fliplr(self.tetrimino > 0), axis=0))
        # Create a copy of the current tetrimino array.
        array_current = np.copy(self.array_current)
        # Rotate the tetrimino and return a copy.
        tetrimino_rotated = np.rot90(self.tetrimino, k=direction)
        # Calculate how many empty rows at top/bottom and empty columns at left/right within tetrimino after rotation.
        top_empty_after, bottom_empty_after = np.argmax(np.any(tetrimino_rotated > 0, axis=1)), np.argmax(np.any(np.flipud(tetrimino_rotated > 0), axis=1))
        left_empty_after, right_empty_after = np.argmax(np.any(tetrimino_rotated > 0, axis=0)), np.argmax(np.any(np.fliplr(tetrimino_rotated > 0), axis=0))
        # Shift the copy of the current tetrimino array to prevent it from moving outside the left, right, top, bottom walls.
        if not self.flag_ghost:
            if left_empty_after < left_empty_before:
                shift = left_empty_before - left_empty_after - np.argmax(np.any(array_current > 0, axis=0))
                if shift > 0:
                    array_current = np.roll(array_current, shift=shift, axis=1)
            if right_empty_after < right_empty_before:
                shift = right_empty_before - right_empty_after - np.argmax(np.any(np.fliplr(array_current > 0), axis=0))
                if shift > 0:
                    array_current = np.roll(array_current, shift=-1*shift, axis=1)
        if top_empty_after < top_empty_before:
            shift = top_empty_before - top_empty_after - np.argmax(np.any(array_current > 0, axis=1))
            if shift > 0:
                array_current = np.roll(array_current, shift=shift, axis=0)
        if bottom_empty_after < bottom_empty_before:
            shift = bottom_empty_before - bottom_empty_after - np.argmax(np.any(np.flipud(array_current > 0), axis=1))
            if shift > 0:
                array_current = np.roll(array_current, shift=-1*shift, axis=0)
        # Insert the rotated and shifted tetrimino into the current tetrimino array.
        array_current[array_current != 0] = tetrimino_rotated.flatten()

        # Attempt to rotate for each translation.
        for translation in translations:
            if not self.flag_ghost:
                # Check whether the translation will move the tetrimino outside the right or left walls.
                if translation[0] > 0:
                    available_count = np.argmax(np.any(np.fliplr(array_current > 0), axis=0))
                    if abs(translation[0]) > available_count:
                        continue
                elif translation[0] < 0:
                    available_count = np.argmax(np.any(array_current > 0, axis=0))
                    if abs(translation[0]) > available_count:
                        continue
                # Check whether the desired translation will move the tetrimino outside the top or bottom walls.
                if translation[1] > 0:
                    available_count = np.argmax(np.any(np.flipud(array_current > 0), axis=1))
                    if abs(translation[1]) > available_count:
                        continue
                elif translation[1] < 0:
                    available_count = np.argmax(np.any(array_current > 0, axis=1))
                    if abs(translation[1]) > available_count:
                        continue

            # Check whether the rotated tetrimino, when translated, intersects already placed blocks.
            is_intersecting = np.any(self.array_stack[np.roll(array_current, shift=translation, axis=(1,0)) > 0] > 0)
            # Skip to the next interation of the for loop if intersecting.
            if is_intersecting and not self.flag_ghost:
                continue
            # Apply the translation if not intersecting and ignore the remaining translations.
            else:
                self.array_current = np.roll(array_current, shift=translation, axis=(1,0))
                self.tetrimino = np.copy(tetrimino_rotated)
                # Update the current rotation value.
                if direction == 1:
                    self.rotation_current += 90
                elif direction == -1:
                    self.rotation_current -= 90
                if self.rotation_current < 0 or self.rotation_current >= 360:
                    self.rotation_current = abs(self.rotation_current % 360)
                # Update display.
                self.update()
                # Play sound effect.
                if self.is_player:
                    sound_game_rotate.play()
                # Reset the block fall time if the tetrimino has landed.
                self.check_landed()
                # Reset the T-spin flags.
                self.flag_tspin = False
                self.flag_tspin_mini = False
                # Set flag if T-spin or mini T-spin.
                if self.id_current == id_classic[5]:
                    front_count = np.sum(self.array_stack[self.array_current == -2] > 0)
                    back_count = np.sum(self.array_stack[self.array_current == -3] > 0)
                    if front_count == 2 and back_count >= 1:
                        self.flag_tspin = True
                        self.flag_tspin_mini = False
                    elif front_count >= 1 and back_count == 2:
                        self.flag_tspin_mini = True
                        self.flag_tspin = False
                # Update Boolean.
                success = True
                # Exit the for loop.
                break
        return success

    # Start soft dropping.
    def softdrop_start(self):
        # Shift down one line and check if that caused the block to land.
        if self.fall() and not self.flag_landed and (speed_softdrop <= self.speed_fall):
            # Set flags.
            self.flag_softdropping = True
            self.flag_advancing = False
            # Reset the previous block fall time.
            self.reset_time_fall()
            # Play sound effect.
            if self.is_player:
                sound_game_softdrop.play()

    # Stop soft dropping.
    def softdrop_stop(self):
        # Set flags.
        self.flag_softdropping = False
        self.flag_advancing = True
        # Reset the previous block fall time.
        self.reset_time_fall()

    # Hold.
    def hold(self):
        # Set the flag to prevent another hold.
        self.flag_hold = True
        # Store the current tetrimino array, the current ID, and current rotation in a tuple and store it in the hold queue.
        if self.id_current in [899]:
            self.tetrimino = None
        self.queue_hold.append((self.tetrimino, self.id_current, self.rotation_current))
        # Reset some special effects.
        self.reset_special(reset_all=False)
        # Set the next tetrimino.
        if self.games.game_mode != 2:
            # Create a new tetrimino if nothing was in the queue.
            if len(self.queue_hold) <= 1:
                self.set_tetrimino()
            # Swap the current tetrimino with the one in the queue.
            else:
                self.set_tetrimino(self.queue_hold.pop(0))
        # Play sound effect.
        if self.instance_self == 0:
            if self.is_player:
                sound_game_hold.play()
        # Draw hold queue.
        self.draw_hold()
    
    # Swap.
    def swap(self, game):
        # Swap the current tetrimino with one from another game.
        self.set_tetrimino(game.queue_hold.pop(0))

    # Reset the block fall time if the tetrimino has landed on the stack or on the bottom of the matrix.
    def check_landed(self):
        is_landed_stack = np.any(self.array_stack[np.roll(self.array_current, shift=1*((-1) ** self.flag_zombie), axis=0) > 0] > 0)
        is_landed_bottom = np.any(self.array_current[-1*(not self.flag_zombie) + 0*self.flag_zombie,:] > 0)
        if (self.flag_ghost and is_landed_bottom) or (not self.flag_ghost and (is_landed_stack or is_landed_bottom)):
            self.flag_landed = True
            self.time_landed = self.games.time_current + 0
            # If landed while soft dropping, reset block fall time in addition to resetting specific flags.
            if self.flag_softdropping:
                self.softdrop_stop()
            # If landed normally, reset block fall time only.
            else:
                self.reset_time_fall()
            # Play sound effect.
            if not self.flag_ghost:
                if self.is_player:
                    sound_game_landing.play()
        else:
            self.flag_landed = False
    
    # Set the flag and stop the game if the top row is occupied.
    def check_lose(self):
        if np.any(self.array_stack[0, :] > 0):
            self.flag_lose = True
            if not self.is_player:
                self.stop_game()
    
    # Randomly select a target if playing with AI.
    def select_target(self):
        games = [game for game in self.games.all if not game.flag_lose and game.instance_self != self.instance_self]
        if len(games) > 0 and len(self.games.ai) > 0:
            self.instance_target = games[random.choice(range(len(games)))].instance_self
        else:
            self.instance_target = None
    
    # Calculate the number of garbage lines to send by inputting the number of lines cleared.
    def calculate_garbage(self, lines):
        count = 0
        if lines == 1:
            if self.flag_tspin:
                count = 2
            elif self.flag_tspin_mini:
                count = 0
            else:
                count = 0
        elif lines == 2:
            if self.flag_tspin:
                count = 4
            elif self.flag_tspin_mini:
                count = 1
            else:
                count = 1
        elif lines == 3:
            if self.flag_tspin:
                count = 6
            else:
                count = 2
        elif lines >= 4:
            count = 4
        # Bonus lines.
        if self.id_current != 899:
            # Perfect clear.
            if self.flag_perfect:
                count += 4
            # Combos.
            if self.combos in [2, 3]:
                count += 1
            elif self.combos in [4, 5]:
                count += 2
            elif self.combos in [6, 7]:
                count += 3
            elif self.combos in [8, 9, 10]:
                count += 4
            elif self.combos >= 11:
                count += 5
        return count

    # Add garbage to the queue.
    def add_garbage(self, count):
        total = sum(self.queue_garbage)
        max = 12
        if count > 0:
            if total == 0:
                self.time_receive_garbage = self.games.time_current + 0
            if total + count >= max:
                self.queue_garbage.append(max-total)
            else:
                self.queue_garbage.append(count)
            # Play sound effect.
            if self.is_player:
                if count < 4:
                    sound_game_garbage_1.play()
                else:
                    sound_game_garbage_2.play()
        # Draw garbage queue.
        self.draw_garbage()
    
    # Subtract garbage from the queue.
    def subtract_garbage(self, count):
        total = sum(self.queue_garbage)
        if count > 0:
            if count >= total:
                self.queue_garbage = []
            else:
                while count > 0:
                    if count < self.queue_garbage[0]:
                        self.queue_garbage[0] -= count
                        count = 0
                    else:
                        count -= self.queue_garbage.pop(0)
        # Draw garbage queue.
        self.draw_garbage()

    # Send garbage to another game.    
    def send_garbage(self, count):
        if count > 0:
            if self.instance_target is not None:
                self.games.all[self.instance_target].add_garbage(count)

    # Add garbage lines to the matrix and subtract the corresponding value from the queue.
    def put_garbage(self):
        if len(self.queue_garbage) > 0:
            self.flag_put_garbage = False
            self.time_receive_garbage = self.games.time_current + 0

            count = self.queue_garbage.pop(0)
            array_garbage = 900 * np.ones([count, self.games.column_count])
            array_garbage[:, random.choice(range(self.games.column_count))] = 0
            self.array_stack = np.concatenate((
                self.array_stack[count:, :],
                array_garbage
                ), axis=0)
            self.check_lose()

    # Return the points to add to the score by inputting how many lines were cleared.
    def calculate_score(self, lines):
        # Calculate points earned based on the type of line clear.
        score_increment = 5 * lines
        if lines >= 4:
            score_increment = 10 * lines
        # Calculate points for T-spins.
        if self.flag_tspin:
            score_increment = 20 * (lines + 1)
            print('tspin points: ', score_increment)
        elif self.flag_tspin_mini:
            score_increment = 5 * (2 ** lines)
            print('mini tspin points: ', score_increment)
        
        # Calculate point multipliers.
        multipliers = []
        if self.combos > 1:
            # Combo multiplier.
            if self.id_current != 899:
                multipliers.append(self.combos)
                # print('combo multiplier: ', multipliers[-1])
        if self.flag_perfect:
            # Perfect clear multiplier.
            if self.id_current != 899:
                multipliers.append(lines)
                print('perfect clear multiplier: ', multipliers[-1])
        
        # Play a sound corresponding to the number of lines cleared.
        if self.is_player:
            if lines == 1:
                sound_game_single.play()
            elif lines == 2:
                sound_game_double.play()
            elif lines == 3:
                sound_game_triple.play()
            elif lines >= 4:
                sound_game_tetris.play()
            # Play a sound for perfect clears.
            if self.flag_perfect:
                sound_game_perfect.play()
            # Play a sound for special line clears.
            if self.flag_tspin or self.flag_tspin_mini or lines >= 4:
                sound_game_special.play()
        
        return int(score_increment * np.prod(multipliers))

    # Update the displayed array.
    def update(self):
        # Reset the values of the arrays to 0.
        self.array_display[:] = 0
        self.array_highlight[:] = 0
        # Highlight the area where the current tetrimino will fall if hard dropped.
        if self.flag_playing:
            # List of Booleans indicating which columns of the matrix contain blocks from the current tetrimino.
            columns = np.any(self.array_current > 0, axis=0)
            # List of row indices of the bottommost blocks in each column of the current tetrimino.
            indices_current = (self.games.row_count-1) - np.argmax(np.flipud(self.array_current > 0), axis=0)[columns]
            # Get the current columns of the placed blocks array.
            array_stack_current = self.array_stack[:, columns]
            # Clear the blocks at or above the current tetrimino.
            for i in range(len(indices_current)):
                array_stack_current[indices_current[i]::-1, i] = 0
            # List of row indices of highest available positions in current tetrimino's columns.
            if self.flag_heavy:
                indices_available = (self.games.row_count-1) * np.ones(array_stack_current.shape[1])
            else:
                indices_available = np.where(
                    np.any(array_stack_current > 0, axis=0),
                    np.argmax(array_stack_current > 0, axis=0)-1,
                    (self.games.row_count-1) * np.ones(array_stack_current.shape[1])
                    )
            # Mark the blocks where the current tetrimino will fall if hard dropped with negative numbers.
            shift = int(min(indices_available - indices_current))
            if self.flag_heavy:
                for i in range(len(indices_current)):
                    if (indices_current[i]+1) <= self.games.row_count-1:
                        array_stack_current[indices_current[i]+1:indices_current[i]+1+shift, i] = -1
                self.array_highlight[:, columns] = array_stack_current
            else:
                self.array_highlight = -1 * np.roll(self.array_current, shift=shift, axis=0)
        # Remove the current tetrimino if not playing.
        else:
            self.array_current[:] = 0
        # Add the highlighted blocks, dropped blocks, and current tetrimino to the displayed array.
        if not self.flag_ghost and not self.flag_blind and self.is_player:
            self.array_display[self.array_highlight < 0] = self.array_highlight[self.array_highlight < 0]
        self.array_display[self.array_stack > 0] = self.array_stack[self.array_stack > 0]
        self.array_display[self.array_current > 0] = self.array_current[self.array_current > 0]
        # Draw the matrix.
        self.draw_matrix()

    # Update the game difficulty.
    def update_difficulty(self):
        # Update the block fall speed.
        if self.games.flag_classic:
            self.speed_fall = np.interp(self.score, [0, score_thresholds[-2]], speeds_fall_classic)
        else:
            self.speed_fall = np.interp(self.score, [0, score_thresholds[-2]], speeds_fall)
        # Update the probability of getting an advanced tetrimino.
        if self.games.flag_classic:
            self.weight_advanced = 0
        else:
            self.weight_advanced = np.interp(self.score, [score_update_chance_advanced, score_thresholds[-2]], weights_advanced)
        # Update the probability of getting a special effect.
        if self.games.flag_classic:
            self.weight_special = 0
        else:
            self.weight_special = np.interp(self.score, [score_update_chance_special, score_thresholds[-2]], weights_special)

    # Record the current time to determine when the next block fall occurs.
    def reset_time_fall(self):
        self.time_fall = self.games.time_current + 0
    
    # Reset some or all special effects.
    def reset_special(self, reset_all=False):
        self.flag_ghost = False
        self.flag_heavy = False
        self.flag_wind = False
        self.flag_zombie = False
        self.flag_fake = False
        # Duration-based special effects that should not be reset when hard dropping.
        if reset_all:
            self.flag_disoriented = False
            self.flag_blind = False
    
    # Draw each block in the matrix.
    def draw_matrix(self):
        self.surface_matrix.fill(colors[1003])
        # Draw grid lines.
        for i in range(self.games.row_count+1):
            y = i * (self.games.height_block+self.games.spacing_block)
            pygame.draw.line(surface=self.surface_matrix, color=colors[1002], start_pos=[0, y], end_pos=[self.rect_matrix.width, y], width=self.games.spacing_block)
        for j in range(self.games.column_count+1):
            x = j * (self.games.width_block+self.games.spacing_block)
            pygame.draw.line(surface=self.surface_matrix, color=colors[1002], start_pos=[x, 0], end_pos=[x, self.rect_matrix.height], width=self.games.spacing_block)
        # Draw non-empty blocks.
        for indices in np.argwhere(self.array_display != 0):
            row, column = indices
            number = self.array_display[row, column]
            if self.is_player:
                if self.flag_blind:
                    color = colors[904]  # Color of placed blocks in blind mode
                else:
                    if number < 0:
                        color = colors[1004]  # Color of highlighted blocks
                    else:
                        if number < 900:
                            color = colors[int(np.floor(number/100)*100)]  # Color of placed blocks
                        else:
                            color = colors[number]
            else:
                if number < 0:
                    color = colors[1004]
                else:
                    color = colors[900]
            pygame.draw.rect(surface=self.surface_matrix, color=color, rect=[(self.games.spacing_block+self.games.width_block)*column+self.games.spacing_block, (self.games.spacing_block+self.games.height_block)*row+self.games.spacing_block, self.games.width_block, self.games.height_block])
        # Draw wind.
        if self.flag_wind:
            for i in range(3):
                height_wind = (i+1) * self.games.spacing_block + i * self.games.height_block + self.games.height_block // 2
                # Calculate positions of endpoints of lines.
                start_pos = self.wind_position + 0
                end_pos = start_pos - 3 * self.games.width_block
                width_matrix = self.surface_matrix.get_width()
                if self.wind_direction < 0:
                    start_pos = width_matrix - start_pos
                    end_pos = width_matrix - end_pos
                # Draw lines.
                if self.is_player:
                    color = colors[1001]
                else:
                    color = colors[900]
                pygame.draw.line(surface=self.surface_matrix, color=color, start_pos=[start_pos, height_wind], end_pos=[end_pos, height_wind], width=self.games.spacing_block*4)
        # Rotate the matrix if the disoriented effect is active.
        if self.flag_disoriented:
            self.surface_matrix.blit(pygame.transform.rotate(self.surface_matrix, 180), (0,0))

    # Draw the hold queue.
    def draw_hold(self):
        self.surface_hold.fill(colors[1002])
        if len(self.queue_hold) > 0:
            tetrimino_mini = self.create_tetrimino_mini(self.queue_hold[0][0])
            size = int(min(np.floor([self.games.width_hold/tetrimino_mini.shape[0], self.games.width_hold/tetrimino_mini.shape[1]])))
            for indices in np.argwhere(tetrimino_mini != 0):
                row, column = indices
                number = tetrimino_mini[row, column]
                if number > 0:
                    if self.is_player:
                        if number < 900:
                            color = colors[int(np.floor(number/100)*100)]
                        else:
                            color = colors[number]
                    else:
                        color = colors[900]
                    pygame.draw.rect(surface=self.surface_hold, color=color, rect=[size*column, size*row, size, size])
    
    # Draw the next queue.
    def draw_next(self):
        self.surface_next.fill(colors[1002])
        if len(self.queue_next) > 0:
            # Create the single array containing all blocks in the queue.
            array_next = np.zeros([0, self.games.column_count])
            for data in self.queue_next:
                tetrimino = self.create_tetrimino_mini(data[0])
                if tetrimino.shape[1] < array_next.shape[1]:
                    tetrimino = np.concatenate((
                        tetrimino,
                        np.zeros([tetrimino.shape[0], array_next.shape[1] - tetrimino.shape[1]])
                        ), axis=1)
                    # Add the current tetrimino array and an empty row at the bottom of the existing array.
                    array_next = np.concatenate((array_next, tetrimino, np.zeros([1, array_next.shape[1]])), axis=0)
            # Crop off empty columns at the right.
            array_next = array_next[:, :-np.argmax(np.any(np.fliplr(array_next>0), axis=0))]
            # Draw each block in the array.
            size = int(np.floor(self.games.width_next/array_next.shape[1]))
            for indices in np.argwhere(array_next != 0):
                row, column = indices
                number = array_next[row, column]
                if number > 0:
                    if self.is_player:
                        if number < 900:
                            color = colors[int(np.floor(number/100)*100)]
                        else:
                            color = colors[number]
                    else:
                        color = colors[900]
                    pygame.draw.rect(surface=self.surface_next, color=color, rect=[size*column, size*row, size, size])
    
    # Draw the garbage queue.
    def draw_garbage(self):
        self.surface_garbage.fill(colors[1002])
        if len(self.queue_garbage) > 0:
            for index, count in enumerate(self.queue_garbage):
                if index == 0:
                    if self.flag_put_garbage:
                        # Final warning.
                        if self.is_player:
                            color = colors[700]
                        else:
                            color = colors[900]
                    else:
                        # Initial warning.
                        if self.is_player:
                            color = colors[400]
                        else:
                            color = colors[900]
                else:
                    color = colors[900]
                for block in range(count):
                    position_vertical = (self.games.spacing_block+self.games.height_block)*(sum(self.queue_garbage[:index])+block+1) + self.games.spacing_block + (self.games.spacing_block*4)*index
                    position_vertical = self.rect_garbage.height - position_vertical
                    pygame.draw.rect(surface=self.surface_garbage, color=color, rect=[0, position_vertical, self.games.width_block, self.games.height_block])
    
    # Draw the information text.
    def draw_information(self):
        self.surface_information.fill(colors[1002])  # Delete this, and re-create the surface below
        if self.games.game_mode in [4] and self.is_player and self.flag_playing:
            if self.instance_target == self.instance_self:
                target = 'Self'
            else:
                target = 'AI {}'.format(self.instance_target)
            text_targeting_value = font_normal.render(target, True, colors[1001])
            rect_targeting_value = text_targeting_value.get_rect()
            rect_targeting_value.bottom = self.rect_information.bottom + 0
            rect_targeting_value.right = self.rect_information.width + 0

            text_targeting = font_small.render('Targeting: ', True, colors[1005])
            rect_targeting = text_targeting.get_rect()
            rect_targeting.bottom = rect_targeting_value.top + 0
            rect_targeting.left = 0
            
            text_ko_value = font_normal.render('', True, colors[1001])
            rect_ko_value = text_ko_value.get_rect()
            rect_ko_value.bottom = rect_targeting.top - rect_ko_value.height
            rect_ko_value.right = self.rect_information.width + 0

            text_ko = font_small.render('KOs: ', True, colors[1005])
            rect_ko = text_ko.get_rect()
            rect_ko.bottom = rect_ko_value.top + 0
            rect_ko.left = 0

            self.surface_information.blit(text_targeting_value, rect_targeting_value)
            self.surface_information.blit(text_targeting, rect_targeting)
            self.surface_information.blit(text_ko_value, rect_ko_value)
            self.surface_information.blit(text_ko, rect_ko)

    # Calculate effectiveness of every move, decide on a move, or perform a move.
    def ai_evaluate(self):
        evaluation = []
        if (self.games.time_current - self.ai_time_evaluate) >= self.ai_delay:
            self.ai_flag_calculating = False

        # Calculate.
        if self.ai_flag_calculating:
            # Move left or right to the closest wall.
            if self.ai_flag_positioning:
                if self.ai_flag_positioning_left:
                    if not self.move_left():
                        self.ai_flag_positioning = False
                        self.ai_flag_positioning_left = not self.ai_flag_positioning_left
                else:
                    if not self.move_right():
                        self.ai_flag_positioning = False
                        self.ai_flag_positioning_left = not self.ai_flag_positioning_left
            # Calculate effectiveness value.
            else:
                # Create a copy of the array.
                array = np.copy(self.array_stack)

                # Calculate the number of holes.
                rows_highest = np.where(np.any(array > 0, axis=0), np.argmax(array > 0, axis=0), self.games.row_count * np.ones(self.games.column_count, dtype=int))
                array_holes = np.copy(array)
                for column, row in enumerate(rows_highest):
                    array_holes[:row, column] = 1
                holes_before = np.sum(array_holes == 0)
                # Calculate the number of cleared lines if the current tetrimino is hard dropped.
                array[self.array_highlight < 0] = -self.array_highlight[self.array_highlight < 0]
                line_count = len(np.argwhere(np.all(array > 0, axis=1)))
                # Calculate the number of holes.
                rows_highest = np.where(np.any(array > 0, axis=0), np.argmax(array > 0, axis=0), self.games.row_count * np.ones(self.games.column_count, dtype=int))
                array_holes = np.copy(array)
                for column, row in enumerate(rows_highest):
                    array_holes[:row, column] = 1
                holes_after = np.sum(array_holes == 0)
                
                # Initialize the effectiveness value.
                effectiveness = 0
                # Add points for cleared lines.
                effectiveness += line_count
                # Subtract points for height of placed tetrimino, based on its top square and its lowest square.
                effectiveness -= 1 * abs(self.games.row_count - np.argmax(np.any(self.array_highlight < 0, axis=1)))
                effectiveness -= 1 * np.argmax(np.any(np.flipud(self.array_highlight) < 0, axis=1))
                # Subtract points for occupying the top row.
                if any(array[0, :] > 0):
                    effectiveness -= 100
                # Subtract points for creating holes.
                if holes_after > holes_before:
                    effectiveness -= 5 * abs(holes_after - holes_before)
                
                # Record the effectiveness value with its corresponding position and rotation.
                evaluation = [
                    np.nonzero(np.any(self.array_current > 0, axis=0))[0],
                    self.rotation_current,
                    effectiveness,
                    ]
                self.ai_evaluations.append(evaluation)

                # Move the tetrimino for the next iteration.
                if self.ai_flag_positioning_left:
                    moved = self.move_left()
                else:
                    moved = self.move_right()
                if not moved:
                    self.ai_flag_positioning = True
                    self.rotate(1)
                    # Set the flag to stop calculating if all 4 rotations have been evaluated.
                    if len(np.unique([i[1] for i in self.ai_evaluations])) >= 4:
                        self.ai_flag_calculating = False
        # Decide.
        elif self.ai_decision is None:
            # Delete moves with effectiveness values less than the maximum.
            effectiveness = [i[2] for i in self.ai_evaluations]
            self.ai_evaluations = [i for i in self.ai_evaluations if i[2] == max(effectiveness)]
            # Select a move randomly if multiple options exist.
            if len(self.ai_evaluations) > 1:
                index = random.choice(range(len(self.ai_evaluations)))
                self.ai_evaluations = [self.ai_evaluations[index]]
            # Record the selected move.
            if len(self.ai_evaluations) > 0:
                self.ai_decision = self.ai_evaluations[0]
        # Perform.
        else:
            if self.ai_decision[1] != self.rotation_current:
                self.rotate(1)
            elif any(self.ai_decision[0] != np.nonzero(np.any(self.array_current > 0, axis=0))[0]):
                if np.nonzero(np.any(self.array_current > 0, axis=0))[0][0] > self.ai_decision[0][0]:
                    self.move_left()
                elif np.nonzero(np.any(self.array_current > 0, axis=0))[0][0] < self.ai_decision[0][0]:
                    self.move_right()
            else:
                if (self.games.time_current - self.ai_time_evaluate) >= self.ai_delay:
                    self.harddrop()

# A class that stores and manages different game instances.
class Games:
    def __init__(self):
        self.player = []
        self.ai = []
        self.all = []

        # Define the frames per second of the game.
        self.fps = 60
        # Create a clock that manages how fast the screen updates.
        self.clock = pygame.time.Clock()

        # Initialize time-related attributes.
        self.time_current = 0
        self.time_start = 0
        self.time_elapsed = 0

        # Initialize the game mode number and classic flag.
        self.game_mode = 1
        self.flag_classic = False

        # Define the numbers of rows and columns.
        self.row_count = 20
        self.column_count = 10
        # Define the size of the space between blocks in pixels.
        self.spacing_block = 1
        # Define the height and width of the blocks in pixels.
        self.height_block = round(((0.8 * pygame.display.Info().current_h) - ((self.row_count+1) * self.spacing_block)) / (self.row_count+1))
        self.width_block = self.height_block + 0
        # Define the height of the panel above the matrix in pixels.
        self.height_panel = self.height_block + 0
        # Define the widths of the hold and next columns.
        self.width_hold = 2 * self.width_block
        self.width_next = 2 * self.width_block
        # Define the width of spacing between elements.
        self.spacing_large = self.width_block + 0
        self.spacing_small = self.width_block // 2
        # Initialize the window size (width, height) in pixels.
        self.size_window = (
            self.column_count*self.width_block + (self.column_count+1)*self.spacing_block + (self.width_hold+self.spacing_small) + (self.width_next+self.spacing_small),
            self.height_panel + self.row_count*self.height_block + (self.row_count+1)*self.spacing_block
            )
        # Size of matrix.
        self.size_matrix = (
            self.column_count*self.width_block + (self.column_count+1)*self.spacing_block,
            self.row_count*self.height_block + (self.row_count+1)*self.spacing_block
            )
        # Size of the combined elements of one game.
        self.size_game = (
            self.width_hold + self.spacing_small + self.size_matrix[0] + self.spacing_small + self.width_next,
            self.size_matrix[1]
            )

        # # Define the names of the game modes.
        # self.name_default = name_program + ''
        # self.name_classic = 'Tetris'
        # self.names_game_modes = [
        #     ['', ''],
        #     ['Twin ', ''],
        #     ['', ' 1v1'],
        #     ['', ' 99'],
        #     ]
        # # Create the menu.
        # self.draw_menu()

        # Initialize game-related attributes.
        self.reset_game()
    
    # Redefine the sizes of elements.
    def resize(self):
        # Get the new size of the window.
        self.size_window = pygame.display.get_window_size()
        
        # Size of one square in the matrix.
        self.width_block = int(np.floor((self.size_window[1] - ((self.row_count+1)*self.spacing_block)) / (self.row_count+1)))
        self.height_block = self.width_block + 0
        # Height of the space above the matrix.
        self.height_panel = self.height_block + 0
        # Widths of the hold and next queues.
        self.width_hold = 2 * self.width_block
        self.width_next = 2 * self.width_block
        # Widths of spacing between games and between elements within a game.
        self.spacing_large = self.width_block + 0
        self.spacing_small = self.width_block // 2
        # Size of matrix.
        self.size_matrix = (
            self.column_count*self.width_block + (self.column_count+1)*self.spacing_block,
            self.row_count*self.height_block + (self.row_count+1)*self.spacing_block
            )
        # Size of the combined elements of one game.
        self.size_game = (
            self.width_hold + self.spacing_small + self.size_matrix[0] + self.spacing_small + self.width_next,
            self.size_matrix[1]
            )

    # Reposition all games.
    def reposition_games(self):
        for game in self.all:
            game.resize_display()

    # Create the surface used to display the game modes.
    def draw_menu(self):
        height_button = self.height_block * 2
        height_spacing = self.height_block // 2
        images = []
        texts = []
        if self.flag_classic:
            name = self.name_classic
        else:
            name = self.name_default
        # Load images and create text.
        for index in range(len(self.names_game_modes)):
            image = pygame.image.load(os.path.join(folder_program, 'icon.png'))
            images.append(
                pygame.transform.smoothscale(image, [int(height_button*(image.get_width()/image.get_height())), height_button])
                )
            string = self.names_game_modes[index][0] + name + self.names_game_modes[index][1]
            texts.append(
                font_large.render(string.upper(), True, colors[1001])
                )
        # Create the buttons.
        self.surface_menu = pygame.Surface((
            max([image.get_width() for image in images]) + max([text.get_width() for text in texts]),
            sum([image.get_height() for image in images]) + (len(self.names_game_modes)-1) * height_spacing
            ))
        for index in range(len(self.names_game_modes)):
            self.surface_menu.blit(
                images[index],
                (0, sum([image.get_height() for image in images[:index]]) + index * height_spacing)
                )
            self.surface_menu.blit(
                texts[index],
                (images[index].get_width(), sum([image.get_height() for image in images[:index]]) + index * height_spacing)
                )

    # Reset parameters when starting a new game.
    def reset_game(self):
        self.score = 0
        self.score_previous = 0
        self.remaining = 0
        self.remaining_previous = 0
        self.stage = 0

    # Switch game modes.
    def set_mode(self, mode):
        if mode != self.game_mode:
            self.game_mode = mode
            if mode == 1:
                games.remove_games_player()
                games.remove_games_ai()
            elif mode == 2:
                games.remove_games_player()
                games.remove_games_ai()
                games.add_game(Tetron(True, len(games.player), games))
            elif mode == 3:
                games.remove_games_player()
                games.add_game(Tetron(False, len(games.all), games))
            elif mode == 4:
                pass
    
    # Invert the classic flag.
    def toggle_classic(self):
        self.flag_classic = not self.flag_classic
    
    # Add a game to the corresponding list.
    def add_game(self, game):
        if game.is_player:
            self.player.append(game)
        else:
            self.ai.append(game)
        self.all.append(game)
    
    # Delete all player games except the first game.
    def remove_games_player(self):
        self.player = [self.player[0]]
        self.all = [game for game in self.all if game.is_player and game.instance_self == 0]
    
    # Delete all AI games.
    def remove_games_ai(self):
        self.ai = []
        self.all = [game for game in self.all if game.is_player]

# A thread that controls AI games.
# class AIThread(threading.Thread):
#     # Override __init__ method.
#     def __init__(self, games):
#         super().__init__()
#         self.games = games
    
#     # Override run method.
#     def run(self):
#         print('Starting thread {}'.format(self.name))
#         pass
#         print('Stopping thread {}'.format(self.name))


# =============================================================================
# Main Program Loop.
# =============================================================================
# Create an object to contain lists of player/AI games and general game information.
games = Games()
# Create a player instance of the game.
games.add_game(Tetron(True, len(games.player), games))
# Reposition the game.
games.reposition_games()

# Set the window title and window icon.
pygame.display.set_caption(name_program + ' ' + version_program)
icon = pygame.image.load(os.path.join(folder_program, 'icon.png'))
pygame.display.set_icon(icon)
# Create the window.
screen = pygame.display.set_mode(games.size_window, pygame.RESIZABLE)

# Load the logo.
logo_full = pygame.image.load(os.path.join(folder_program, 'logo.png'))
logo = pygame.transform.smoothscale(logo_full, [int(games.height_panel*(logo_full.get_width()/logo_full.get_height())), games.height_panel])
# Create text for classic Tetris.
text_classic = font_normal.render('Tetris', True, colors[1001])
# Define names [prefix, suffix] for each game mode.
game_mode_names = [
    ['', ''],
    ['Twin ', ''],
    ['', ' 1v1'],
    ['', ' 99'],
    ]
# Initialize the game mode text.
text_prefix = font_normal.render(game_mode_names[0][0], True, colors[1001])
text_suffix = font_normal.render(game_mode_names[0][1], True, colors[1001])
# Initialize the game mode surface.
surface_mode = pygame.Surface((0,0))

ms = []  # Debug

# Loop until the window is closed.
done = False
while not done:
    # START = time.time()  # Debug

    flag_playing = any([game.flag_playing for game in games.all])
    flag_paused = all([game.flag_paused for game in games.all])
    
    # Calculate current time and elapsed time.
    if flag_playing:
        games.time_elapsed += pygame.time.get_ticks() - games.time_current
    games.time_current = pygame.time.get_ticks()

    # =============================================================================
    # Key Presses/Releases And Other Events.
    # =============================================================================
    for event in pygame.event.get():
        # Window is exited.
        if event.type == pygame.QUIT:
            done = True
        # Window is resized.
        elif event.type == pygame.VIDEORESIZE:
            # Resize the elements of each game.
            games.resize()
            # Reposition the elements of each game.
            games.reposition_games()
            # Resize the logo.
            logo = pygame.transform.smoothscale(logo_full, [int(games.height_panel*(logo_full.get_width()/logo_full.get_height())), games.height_panel])
        # Key presses.
        elif event.type == pygame.KEYDOWN:
            if flag_playing:
                # Move left.
                if event.key in [key_move_left, key_left_move_left, key_right_move_left]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key == key_move_left:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        if event.key == key_left_move_left:
                            indices.append(0)
                        if event.key == key_right_move_left:
                            indices.append(1)
                    for index in indices:
                        games.player[index].move_left()
                        # Record the current time used later to calculate how long this key is held.
                        games.player[index].time_start_move_left = games.time_current + 0
                        # Initialize the time at which the previous repeat occurred.
                        games.player[index].time_previous_move_left = 0
                # Move right.
                elif event.key in [key_move_right, key_left_move_right, key_right_move_right]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key == key_move_right:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        if event.key == key_left_move_right:
                            indices.append(0)
                        if event.key == key_right_move_right:
                            indices.append(1)
                    for index in indices:
                        games.player[index].move_right()
                        # Record the current time used later to calculate how long this key is held.
                        games.player[index].time_start_move_right = games.time_current + 0
                        # Initialize the time at which the previous repeat occurred.
                        games.player[index].time_previous_move_right = 0
                # Rotate counterclockwise or clockwise.
                elif event.key in key_rotate_clockwise+[key_left_rotate_clockwise,key_right_rotate_clockwise] or \
                event.key in key_rotate_counterclockwise+[key_left_rotate_counterclockwise,key_right_rotate_counterclockwise]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key in key_rotate_clockwise + key_rotate_counterclockwise:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        if event.key in [key_left_rotate_clockwise,key_left_rotate_counterclockwise]:
                            indices.append(0)
                        if event.key in [key_right_rotate_clockwise,key_right_rotate_counterclockwise]:
                            indices.append(1)
                    if event.key in key_rotate_clockwise+[key_left_rotate_clockwise,key_right_rotate_clockwise]:
                        direction = -1
                    elif event.key in key_rotate_counterclockwise+[key_left_rotate_counterclockwise,key_right_rotate_counterclockwise]:
                        direction = 1
                    for index in indices:
                        games.player[index].rotate(direction)
                # Hard drop.
                elif event.key == key_harddrop:
                    for game in games.player:
                        game.harddrop()
                # Start soft dropping.
                elif event.key in [key_softdrop, key_left_softdrop, key_right_softdrop]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key == key_softdrop:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        if event.key == key_left_softdrop:
                            indices.append(0)
                        elif event.key == key_right_softdrop:
                            indices.append(1)
                    for index in indices:
                        games.player[index].softdrop_start()
                        # Record the current time used later to calculate how long this key is held.
                        games.player[index].time_start_softdrop = games.time_current + 0
                        # Initialize the time at which the previous repeat occurred.
                        games.player[index].time_previous_softdrop = 0
                # Hold / Swap.
                elif event.key in [key_hold, key_left_hold, key_right_hold]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key == key_hold:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        indices = [0, 1]
                    # Check that no games currently holding, no games have a ghost block, and no games have a heavy block.
                    if not any([any([game.flag_hold, game.flag_ghost, game.flag_heavy, game.flag_zombie]) for game in games.player]):
                        # Hold.
                        for index in indices:
                            games.player[index].hold()
                        # Swap.
                        if len(games.player) >= 2:
                            for index in indices:
                                index_swap = np.roll(range(0,len(games.player)), 1)[index]
                                games.player[index].swap(games.player[index_swap])
            else:
                if not flag_paused:
                    # Switch game modes.
                    if event.key == key_mode_1:
                        games.set_mode(1)
                    elif event.key == key_mode_2:
                        games.set_mode(2)
                    elif event.key == key_mode_3:
                        games.set_mode(3)
                    elif False: #event.key == key_mode_4:
                        games.set_mode(4)
                    # Toggle classic Tetris.
                    elif event.key == key_toggle_classic:
                        games.toggle_classic()
                    # Reposition all games.
                    games.reposition_games()
                    # Update game mode text.
                    text_prefix = font_normal.render(game_mode_names[games.game_mode-1][0], True, colors[1001])
                    text_suffix = font_normal.render(game_mode_names[games.game_mode-1][1], True, colors[1001])
        # Key releases.
        elif event.type == pygame.KEYUP:
            if event.key == key_start:
                if not flag_playing:
                    # Resume game.
                    if flag_paused:
                        pygame.mixer.music.unpause()
                        for game in games.all:
                            game.pause_game()
                    # Start game.
                    else:
                        games.reset_game()
                        # Unload current music and start playing music indefinitely.
                        pygame.mixer.music.unload()
                        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_{}.ogg'.format(games.stage+1)))
                        pygame.mixer.music.play(loops=-1)
                        # Start each game.
                        games.time_start = games.time_current + 0
                        games.time_elapsed = 0
                        for game in games.all:
                            game.start_game()
                # Pause game.
                else:
                    pygame.mixer.music.pause()
                    # Pause each game.
                    for game in games.all:
                        game.pause_game()
            # Stop game.
            elif event.key == key_stop:
                if flag_playing or flag_paused:
                    # Stop and unload current music.
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    # Stop each game.
                    for game in games.all:
                        game.stop_game()

            if flag_playing:
                # Stop soft dropping.
                if event.key in [key_softdrop, key_left_softdrop, key_right_softdrop]:
                    indices = []
                    if len(games.player) == 1:
                        if event.key == key_softdrop:
                            indices.append(0)
                    elif len(games.player) >= 2:
                        if event.key == key_left_softdrop:
                            indices.append(0)
                        elif event.key == key_right_softdrop:
                            indices.append(1)
                    for index in indices:
                        # Only stop if currently soft dropping.
                        if games.player[index].flag_softdropping:
                            games.player[index].softdrop_stop()
        # Transition music ends.
        elif event.type == pygame.USEREVENT+1:
            if flag_playing:
                # Stop and unload current music.
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                # Load music for current stage.
                pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_{}.ogg'.format(games.stage+1)))
                # Disable the event sent when music ends, and play indefinitely.
                pygame.mixer.music.set_endevent()
                pygame.mixer.music.play(loops=-1)
    
    # =============================================================================
    # Keys Held Continuously.
    # =============================================================================
    # Get a list of the keys currently being held down.
    keys_pressed = pygame.key.get_pressed()
    if flag_playing:
        # Soft drop.
        if keys_pressed[key_softdrop] or keys_pressed[key_left_softdrop] or keys_pressed[key_right_softdrop]:
            indices = []
            if len(games.player) == 1:
                if keys_pressed[key_softdrop]:
                    indices.append(0)
            elif len(games.player) >= 2:
                if keys_pressed[key_left_softdrop]:
                    indices.append(0)
                if keys_pressed[key_right_softdrop]:
                    indices.append(1)
            # Check if the key has been held longer than the required initial delay.
            for index in indices:
                if (games.time_current - games.player[index].time_start_softdrop) > delay_softdrop:
                    # Check if the key has been held longer than the key repeat interval.
                    if (games.time_current - games.player[index].time_previous_softdrop) > speed_softdrop:
                        if games.player[index].flag_softdropping:  # Check whether soft dropping to prevent advancing line immediately after landing
                            games.player[index].fall()
                            # Play sound effect.
                            sound_game_softdrop.play()
                        games.player[index].time_previous_softdrop = games.time_current + 0
        # Move left.
        if keys_pressed[key_move_left] or keys_pressed[key_left_move_left] or keys_pressed[key_right_move_left]:
            indices = []
            if len(games.player) == 1:
                if keys_pressed[key_move_left]:
                    indices.append(0)
            elif len(games.player) >= 2:
                if keys_pressed[key_left_move_left]:
                    indices.append(0)
                if keys_pressed[key_right_move_left]:
                    indices.append(1)
            # Check if the key has been held longer than the required initial delay.
            for index in indices:
                if (games.time_current - games.player[index].time_start_move_left) > delay_move:
                    # Check if the key has been held longer than the key repeat interval.
                    if (games.time_current - games.player[index].time_previous_move_left) > speed_move:
                        games.player[index].move_left()
                        games.player[index].time_previous_move_left = games.time_current + 0
        # Move right.
        if keys_pressed[key_move_right] or keys_pressed[key_left_move_right] or keys_pressed[key_right_move_right]:
            indices = []
            if len(games.player) == 1:
                if keys_pressed[key_move_right]:
                    indices.append(0)
            elif len(games.player) >= 2:
                if keys_pressed[key_left_move_right]:
                    indices.append(0)
                if keys_pressed[key_right_move_right]:
                    indices.append(1)
            # Check if the key has been held longer than the required initial delay.
            for index in indices:
                if (games.time_current - games.player[index].time_start_move_right) > delay_move:
                    # Check if the key has been held longer than the key repeat interval.
                    if (games.time_current - games.player[index].time_previous_move_right) > speed_move:
                        games.player[index].move_right()
                        games.player[index].time_previous_move_right = games.time_current + 0
    

    # =============================================================================
    # Game Progress.
    # =============================================================================
    # Calculate score.
    games.score_previous = games.score + 0
    if games.game_mode in [1]:
        games.score += sum([game.score_increment.pop(0) for game in games.player if len(game.score_increment) > 0])
    elif games.game_mode in [2]:
        scores = [game.score_increment.pop(0) for game in games.player if len(game.score_increment) > 0]
        # Apply a point multiplier if both games earned points.
        if len([score for score in scores if score > 0]) > 1:
            scores = sum(scores) * 3
        else:
            scores = sum(scores)
        games.score += scores
    elif games.game_mode in [3]:
        games.score += max([0] + [game.score_increment.pop(0) for game in games.all if len(game.score_increment) > 0])
    # Calculate number of players left.
    games.remaining_previous = games.remaining + 0
    games.remaining = sum([not game.flag_lose for game in games.all])
    # Update scores and difficulty for all games.
    for game in games.all:
        game.score = games.score + 0
        game.update_difficulty()
    
    # Win the game.
    if games.game_mode in [1, 2] and games.score_previous < score_thresholds[-1] <= games.score or \
        games.game_mode in [3, 4] and games.remaining <= remaining_thresholds[-1] < games.remaining_previous:
        # Play music and sound effect only if the player won.
        if all([game.flag_lose for game in games.ai]):
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_win.ogg'))
            pygame.mixer.music.play(loops=0)
            # Play sound effect.
            sound_game_win.play()
        # Stop all games.
        for game in games.all:
            game.stop_game()
    # Stop the game if the player has lost.
    elif any([game.flag_lose for game in games.player]):
        # Play music.
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_lose.ogg'))
        pygame.mixer.music.play(loops=0)
        # Stop player games.
        for game in games.player:
            game.flag_lose = False
            game.stop_game()
    # Advance to the next stage of the game.
    elif games.game_mode in [1, 2, 3] and games.score_previous < score_thresholds[games.stage] <= games.score and games.stage < 2 or \
        games.game_mode in [4] and games.remaining <= remaining_thresholds[games.stage] < games.remaining_previous:
        # Calculate the stage value.
        if games.game_mode in [1, 2, 3]:
            games.stage = sum([games.score >= i for i in score_thresholds])
        elif games.game_mode in [4]:
            games.stage = sum([games.remaining <= i for i in remaining_thresholds])
        print('Stage: ', games.stage)
        # Stop and unload current music.
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        # Load transition music.
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_transition_{}.ogg'.format(games.stage)))
        # Set the music to send an event when done playing.
        pygame.mixer.music.set_endevent(pygame.USEREVENT+1)
        # Play the music once.
        pygame.mixer.music.play(loops=0)

    # =============================================================================
    # Game Actions.
    # =============================================================================
    # Hard drop all player games if one game has hard dropped.
    if any([game.flag_harddrop for game in games.player]):
        for game in games.player:
            if not game.flag_harddrop:
                game.harddrop()
            game.flag_harddrop = False
    
    for game in games.all:
        if game.flag_playing:
            # Let block fall.
            if game.flag_advancing:
                if (
                    # Check if the required time for automatic advancing has elapsed.
                    (not game.flag_landed and (games.time_current - game.time_fall) >= (game.speed_fall * (speed_fall_multiplier ** game.flag_fast_fall))) or
                    # If tetrimino is landed, check if the maximum time has elapsed.
                    (game.flag_landed and (games.time_current - game.time_landed >= duration_max_landed))
                    ):
                        if not game.fall():
                            game.lock()
                        game.reset_time_fall()
            else:
                game.reset_time_fall()
            
            # Apply wind special effect.
            if game.flag_wind:
                if games.time_current - game.time_start_wind >= speed_wind:
                    game.time_start_wind = games.time_current + 0
                    game.wind_position += games.width_block
                    if game.wind_direction > 0:
                        game.move_right()
                    elif game.wind_direction < 0:
                        game.move_left()
                    if game.is_player:
                        game.draw_matrix()

            # Garbage queue.
            if games.time_current - game.time_receive_garbage >= time_garbage_warning:
                game.flag_put_garbage = True
            else:
                game.flag_put_garbage = False
            
            # Process AI games.
            if not game.is_player:
                game.ai_evaluate()
    
    # =============================================================================
    # Draw Screen.
    # =============================================================================
    # Erase all surfaces.
    screen.fill(colors[1002])
    # surface_mode.fill(colors[1002])   # Delete if not needed (recreated every loop)

    # Draw the game mode if not playing.
    if not flag_playing:
        # Get the width of the logo or text.
        if games.flag_classic:
            width_name = text_classic.get_width()
        else:
            width_name = logo.get_width()
        # Create the game mode surface and insert the prefix.
        width_prefix = text_prefix.get_width()
        width_suffix = text_suffix.get_width()
        surface_mode = pygame.Surface((width_prefix+width_name+width_suffix, games.height_panel))
        surface_mode.blit(text_prefix, (0,surface_mode.get_height()-text_prefix.get_height()))
        # Insert the logo or text.
        if games.flag_classic:
            surface_mode.blit(text_classic, (width_prefix,surface_mode.get_height()-text_classic.get_height()))
        else:
            surface_mode.blit(logo, (width_prefix,0))
        # Insert the suffix.
        surface_mode.blit(text_suffix, (surface_mode.get_width()-width_suffix,surface_mode.get_height()-text_suffix.get_height()))

        # Insert the game mode surface in the screen.
        rect_mode = surface_mode.get_rect()
        rect_mode.bottom = games.height_panel + 0
        rect_mode.centerx = games.size_window[0]//2
        screen.blit(surface_mode, rect_mode)
    # Display score text.
    text_score = font_normal.render('{}'.format(games.score), True, colors[1001])
    rect_text_score = text_score.get_rect()
    rect_text_score.left = (
        games.size_window[0] - games.size_game[0]*len(games.all) - games.spacing_large*(len(games.all)-1)
        )//2 + games.width_hold + games.spacing_small
    rect_text_score.bottom = games.height_panel + 0
    screen.blit(text_score, rect_text_score)
    # Display elapsed time text.
    text_time_elapsed = font_normal.render('{:02d}:{:02d}'.format(games.time_elapsed//60000, int((games.time_elapsed/1000)%60)), True, colors[1001])
    rect_text_time_elapsed = text_time_elapsed.get_rect()
    rect_text_time_elapsed.right = games.size_window[0] - (
        games.size_window[0] - games.size_game[0]*len(games.all) - games.spacing_large*(len(games.all)-1)
        )//2 - games.width_next - games.spacing_small
    rect_text_time_elapsed.bottom = games.height_panel + 0
    screen.blit(text_time_elapsed, rect_text_time_elapsed)

    # Draw each game.
    for index, game in enumerate(games.all):
        # Stop the disoriented effect if it has lasted longer than the maximum duration.
        if game.flag_disoriented:
            if games.time_current - game.time_start_disoriented > duration_disoriented:
                game.flag_disoriented = False
                game.draw_matrix()
        # Stop the blind effect if it has lasted longer than the maximum duration.
        if game.flag_blind:
            if games.time_current - game.time_start_blind > duration_blind:
                game.flag_blind = False
                game.draw_matrix()

        # Draw the elements of each game in order from back to front.
        if len(game.queue_garbage) > 0:
            game.draw_garbage()
            screen.blit(game.surface_garbage, game.rect_garbage)
        if len(game.queue_hold) > 0:
            screen.blit(game.surface_hold, game.rect_hold)
            screen.blit(game.text_hold, game.rect_text_hold)
        if len(game.queue_next) > 0:
            screen.blit(game.surface_next, game.rect_next)
            screen.blit(game.text_next, game.rect_text_next)
        # game.draw_information()
        # screen.blit(game.surface_information, game.rect_information)
        screen.blit(game.surface_matrix, game.rect_matrix)
    
    # END = time.time()  # Debug
    # ms.append((END-START)*1000)  # Debug

    # Update the screen.
    pygame.display.flip()
    # Limit the game to the desired frames per second by delaying every iteration of this loop.
    games.clock.tick(games.fps)

# Close the window and quit.
pygame.quit()

# import matplotlib.pyplot as plot
# plot.plot(ms)
# plot.show()
# print('Median: {:.2f},   Average: {:.2f},   Max: {:.2f},   Percent over: {:.2f}%'.format(
#     np.median(ms),
#     np.mean(ms),
#     np.max(ms),
#     100 * len([i for i in ms if i > 1000/games.fps])/len(ms)
#     ))
