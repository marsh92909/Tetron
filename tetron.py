#!/usr/bin/python
# -*- coding: latin-1 -*-


import os
import random
import sys
import time

import numpy as np
import pygame


# Program information.
name_program = 'Tetron'
version_program = '1.0.0'
# Get the path to the folder containing the program.
folder_program = os.path.dirname(os.path.realpath(sys.argv[0]))  #getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
folder_sounds = os.path.abspath(os.path.join(folder_program, 'Sounds'))
folder_images = os.path.abspath(os.path.join(folder_program, 'Images'))
# Initialize all pygame modules.
pygame.init()


# =============================================================================
# Helper Functions.
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


# =============================================================================
# Classes.
# =============================================================================
# The main class containing all actions related to the game, such as moving and rotating blocks.
class Tetron:
    # Initialize the attributes of the instance of of this class when it is first created.
    def __init__(self):
        # Define the width, height, and margin of the blocks in pixels.
        self.block_width = 40
        self.block_height = 40
        self.block_margin = 1
        # Define widths of multiple sizes of spacing between elements.
        self.margin_large = 1 * self.block_width
        self.margin_small = int(0.5 * self.block_width)
        # Define the widths of the hold and next columns.
        self.width_hold = 2 * self.block_width
        self.width_next = 2 * self.block_width

        # Define the number of rows and columns of the matrix.
        self.row_count = 20
        self.column_count = 10

        # Create a clock that manages how fast the screen updates.
        self.clock = pygame.time.Clock()
        # Define the frames per second of the game.
        self.fps = 60
        # Initialize the current time (measured from time pygame.init() was called), the start time (when player starts game), and the elapsed duration between these two times.
        self.time_current = 0
        self.time_start = 0
        self.time_elapsed = 0

        # Define the scores needed to move to the next stage. The last value is the score needed to win the game.
        self.score_thresholds = [500, 900, 1000]
        # Define the range of block fall speeds (ms) from the start to end of the game.
        self.speeds_fall = [1000, 500]
        # Define the block fall speed multiplier for some special effects (values below 1 result in faster speeds).
        self.speed_fall_multiplier = 1/3
        # Define the block move speed (ms) and initial delay for key repeats (ms).
        self.speed_move = 25
        self.delay_move = 150
        # Define the soft drop speed (ms) and initial delay for key repeats (ms).
        self.speed_softdrop = 50
        self.delay_softdrop = 50

        # Define the IDs for classic tetriminos, advanced tetriminos, special effects.
        self.id_classic = [100, 200, 300, 400, 500, 600, 700]
        self.id_advanced = [101, 102, 201, 202, 301, 302, 401, 402, 403, 501, 601, 602, 701, 801, 811, 812, 813, 814, 899]
        self.id_special = ['ghost', 'heavy', 'disoriented', 'blind']
        
        # Define the range of probabilities (between 0 and 1) of getting an advanced tetrimino.
        self.weights_advanced = [0, 2/5]
        # Define the score needed to begin increasing the probability of getting an advanced tetrimino.
        self.score_update_chance_advanced = 100
        # Define the range of probabilities (between 0 and 1) of getting a special effect.
        self.weights_special = [0, 1/20]
        # Define the score needed to begin increasing the probability of getting a special effect.
        self.score_update_chance_special = 500
        # Define durations for special effects (ms).
        self.duration_max_disoriented = 20000
        self.duration_max_blind = 20000

        # Create the surface used to display the matrix.
        self.surface_matrix = pygame.Surface((self.column_count*self.block_width+(self.column_count+1)*self.block_margin, self.row_count*self.block_height+(self.row_count+1)*self.block_margin))
        # Create the surface used to display the hold queue.
        self.surface_hold = pygame.Surface((self.width_hold, self.width_hold))
        
        # Load sound effects.
        # self.sound_game_advance = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_advance.wav'))
        self.sound_game_move = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_move.wav'))
        self.sound_game_rotate = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_rotate.wav'))
        self.sound_game_harddrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_harddrop.wav'))
        self.sound_game_softdrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_softdrop.wav'))
        self.sound_game_landing = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_landing.wav'))
        self.sound_game_single = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_single.wav'))
        self.sound_game_double = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_double.wav'))
        self.sound_game_triple = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_triple.wav'))
        self.sound_game_tetris = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_tetris.wav'))
        self.sound_game_special = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_special.wav'))
        self.sound_game_perfect = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_perfect.wav'))
        self.sound_game_win = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_win.wav'))
        self.sound_special_ghost = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_ghost.wav'))
        self.sound_special_disoriented = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_disoriented.wav'))
        self.sound_special_blind = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_blind.wav'))
        # Set volume for some sound effects.
        self.sound_game_move.set_volume(0.1)
        self.sound_game_rotate.set_volume(0.1)
        self.sound_game_harddrop.set_volume(0.1)
        self.sound_game_softdrop.set_volume(0.1)
        self.sound_game_landing.set_volume(0.1)
        self.sound_game_single.set_volume(0.1)
        self.sound_game_double.set_volume(0.1)
        self.sound_game_triple.set_volume(0.1)
        self.sound_game_tetris.set_volume(0.1)
        self.sound_game_special.set_volume(0.1)
        self.sound_game_perfect.set_volume(0.1)

        # Initialize all other attributes.
        self.initialize()

    # Initialize values of attributes that are both modified during the game and reset when starting the game. Called on first startup and subsequent game starts.
    def initialize(self):
        # Initialize flags indicating statuses of the game.
        self.flag_playing = False
        self.flag_paused = False
        self.flag_advancing = True
        self.flag_hold = False
        self.flag_tspin = False
        self.flag_tspin_mini = False
        self.flag_fast_fall = False
        self.flag_softdropping = False
        self.flag_ghost = False
        self.flag_heavy = False
        self.flag_disoriented = False
        self.flag_blind = False

        # Initialize arrays for current tetrimino, dropped blocks, blocks displayed on screen, and highlighted blocks showing where tetriminos will be hard dropped.
        self.array_current = np.zeros([self.row_count, self.column_count])
        self.array_dropped = np.zeros([self.row_count, self.column_count])
        self.array_display = np.zeros([self.row_count, self.column_count])
        self.array_highlight = np.zeros([self.row_count, self.column_count])

        # Initialize lists with Booleans indicating which tetriminos or special effects have been used to prevent duplicates.
        self.used_classic = [False] * len(self.id_classic)
        self.used_advanced = [False] * len(self.id_advanced)
        self.used_special = [False] * len(self.id_special)
        # Initialize the current tetrimino ID.
        self.id_current = 0
        # Initialize the hold list.
        self.queue_hold = []

        # Initialize the stage of the game as a number.
        self.stage = 0
        # Initialize the number of placed tetriminos.
        self.count = 0
        # Initialize the number of successive line clears.
        self.combos = 0
        # Initialize the cleared lines counter.
        self.score = 0

        # Initialize the block fall speed, the probability of getting an advanced tetrimino, and the probability of getting a special effect.
        self.update_speed_fall()
        self.update_chance_advanced()
        self.update_chance_special()

    # Start the game.
    def start_game(self):
        # Reset attributes.
        self.initialize()
        # Save the start time.
        self.time_start = pygame.time.get_ticks()
        self.reset_time_advance()
        # Set flags.
        self.flag_playing = True
        # Create a new tetrimino.
        self.create_new()
        # Unload current music and start playing music indefinitely.
        pygame.mixer.music.unload()
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_{}.ogg'.format(self.stage+1)))
        pygame.mixer.music.play(loops=-1)
    
    # Pause or resume the game.
    def pause_game(self):
        # Resume game.
        if self.flag_paused:
            game.flag_playing = True
            game.flag_paused = False
            pygame.mixer.music.unpause()
        # Pause game.
        else:
            game.flag_playing = False
            game.flag_paused = True
            pygame.mixer.music.pause()
    
    # Stop the game.
    def stop_game(self):
        self.flag_playing = False
        self.flag_paused = False
        self.flag_ghost = False
        self.flag_heavy = False
        self.flag_blind = False
        self.flag_disoriented = False
        self.update()
        # Stop and unload current music.
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

    # Generate a new tetrimino and replace the current arrays.
    def create_new(self, hold_data=None):
        if hold_data is None:
            # Randomly select a category to choose from, then randomly select a tetrimino within the category with each tetrimino having an equal probability.
            if random.choices([True, False], [self.weight_advanced, 1-self.weight_advanced], k=1)[0]:
                id = random.choice([self.id_advanced[i] for i in range(len(self.id_advanced)) if not self.used_advanced[i]])
                self.id_current = id
                self.used_advanced[self.id_advanced.index(id)] = True
                # Reset all values in the list to False.
                if all(self.used_advanced):
                    self.used_advanced = [False] * len(self.used_advanced)
            else:
                id = random.choice([self.id_classic[i] for i in range(len(self.id_classic)) if not self.used_classic[i]])
                self.id_current = id
                self.used_classic[self.id_classic.index(id)] = True
                # Reset all values in the list to False.
                if all(self.used_classic):
                    self.used_classic = [False] * len(self.used_classic)
            
            # Randomly determine if a special property is applied.
            if random.choices([True, False], [self.weight_special, 1-self.weight_special], k=1)[0]:
                effect_special = random.choice([self.id_special[i] for i in range(len(self.id_special)) if not self.used_special[i]])
                self.used_special[self.id_special.index(effect_special)] = True
                # Reset all values in the list to False.
                if all(self.used_special):
                    self.used_special = [False] * len(self.used_special)

                if effect_special == self.id_special[0]:
                    self.flag_ghost = True
                    self.flag_fast_fall = True
                    self.sound_special_ghost.play()
                elif effect_special == self.id_special[1]:
                    self.flag_heavy = True
                    self.flag_fast_fall = True
                    # self.sound_special_heavy.play()
                elif effect_special == self.id_special[2]:
                    # Apply the effect only if it is not currently active.
                    if not self.flag_disoriented:
                        self.flag_disoriented = True
                        self.duration_disoriented = 0
                        self.sound_special_disoriented.play()
                elif effect_special == self.id_special[3]:
                    # Apply the effect only if it is not currently active.
                    if not self.flag_blind:
                        self.flag_blind = True
                        self.duration_blind = 0
                        self.sound_special_blind.play()
            
            # Classic tetriminos.
            if self.id_current == self.id_classic[0]:  # I
                tetrimino = self.id_current * np.ones([4, 4])
                tetrimino[[0,2,3],:] = -1
            elif self.id_current == self.id_classic[1]:  # J
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, 1:] = -1
                tetrimino[2, :] = -1
            elif self.id_current == self.id_classic[2]:  # L
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, 0:2] = -1
                tetrimino[2, :] = -1
            elif self.id_current == self.id_classic[3]:  # O
                tetrimino = self.id_current * np.ones([2, 2])
            elif self.id_current == self.id_classic[4]:  # S
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, 0] = -1
                tetrimino[1, 2] = -1
                tetrimino[2, :] = -1
            elif self.id_current == self.id_classic[5]:  # T
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, [0,2]] = -2
                tetrimino[2, [0,2]] = -3
                tetrimino[2, 1] = -1
            elif self.id_current == self.id_classic[6]:  # Z
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, 2] = -1
                tetrimino[1, 0] = -1
                tetrimino[2, :] = -1
            # Advanced tetriminos.
            elif self.id_current == 101:  # I+
                tetrimino = self.id_current * np.ones([5, 5])
                tetrimino[[0,1,3,4],:] = -1
            elif self.id_current == 102:  # I-
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[[0,2],:] = -1
            elif self.id_current == 201:  # J+
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0:2, 1:3] = -1
            elif self.id_current == 202:  # J-
                tetrimino = self.id_current * np.ones([2, 2])
                tetrimino[0, 1] = -1
            elif self.id_current == 301:  # L+
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0:2, 0:2] = -1
            elif self.id_current == 302:  # L-
                tetrimino = self.id_current * np.ones([2, 2])
                tetrimino[0, 0] = -1
            elif self.id_current == 401:  # O+
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[:, 2] = -1
            elif self.id_current == 402:  # O++
                tetrimino = self.id_current * np.ones([4, 4])
                tetrimino[:, [0,3]] = -1
            elif self.id_current == 403:  # O ring
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[1, 1] = -1
            elif self.id_current == 501:  # S+
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0:2, 0] = -1
                tetrimino[1:3, 2] = -1
            elif self.id_current == 601:  # T+1
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[0, 0] = -1
                tetrimino[0, 2] = -1
                tetrimino[2, 0] = -1
                tetrimino[2, 2] = -1
            elif self.id_current == 602:  # T+2
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[1:3, [0,2]] = -1
            elif self.id_current == 701:  # Z+
                tetrimino = self.id_current * np.ones([3, 3])
                tetrimino[1:3, 0] = -1
                tetrimino[0:2, 2] = -1
            elif self.id_current == 801:  # Random 3x3
                shape = [3, 3]
                tetrimino = -1 * np.ones(shape)
                random_indices = random.sample(range(tetrimino.size), 5)
                tetrimino[np.unravel_index(random_indices, shape)] = self.id_current
            elif self.id_current == 811:  # Period (.)
                tetrimino = self.id_current * np.ones([1, 1])
            elif self.id_current == 812:  # Comma (,)
                tetrimino = self.id_current * np.ones([2, 2])
                tetrimino[[0,1],[0,1]] = -1
            elif self.id_current == 813:  # Colon (:)
                tetrimino = -1 * np.ones([3, 3])
                tetrimino[[0,2], 1] = self.id_current
            elif self.id_current == 814:  # Quotation (")
                tetrimino = -1 * np.ones([3, 3])
                tetrimino[0:2, [0,2]] = self.id_current
            elif self.id_current == 899:  # Freebie
                # Index of highest row containing dropped blocks.
                index_highest = np.argmax(np.any(self.array_dropped > 0, axis=1))
                # Index of lowest row that can fit this tetrimino.
                index_lowest = max(np.argmax(self.array_dropped, axis=0))
                # Get the top rows of the dropped blocks.
                number_rows = index_lowest-index_highest + 1
                array_dropped_top = np.copy(self.array_dropped[index_highest:index_highest+number_rows, :]) > 0
                # Get the row indices of the highest blocks in each column of the dropped blocks array, with values of -1 for empty columns.
                rows_highest = np.argmax(array_dropped_top, axis=0)
                rows_highest[np.all(array_dropped_top == 0, axis=0)] = -1
                # Fill the blocks below the highest blocks in each column.
                for column in range(len(rows_highest)):
                    if rows_highest[column] >= 0:
                        array_dropped_top[rows_highest[column]:, column] = 1
                # Create the tetrimino by inverting the dropped blocks.
                tetrimino = self.id_current * (1 - array_dropped_top)

            # Reset the current rotation value (degrees).
            self.rotation_current = 0
            # Apply special effects to tetrimino, if any.
            if self.flag_ghost:
                tetrimino[tetrimino > 0] = 901
            elif self.flag_heavy:
                tetrimino[tetrimino > 0] = 902
        else:
            tetrimino = np.copy(hold_data[0])
            self.id_current = hold_data[1]
            self.rotation_current = hold_data[2]

        # Set the current tetrimino.
        self.tetrimino = tetrimino
        # Clear the current tetrimino array.
        self.array_current[:] = 0
        # Update the array of the current tetrimino.
        row_left = int(np.floor((self.column_count-tetrimino.shape[1])/2))
        self.array_current[0:tetrimino.shape[0], row_left:row_left+tetrimino.shape[1]] = self.tetrimino

        # Update the displayed array.
        self.update()

    # Advance one line.
    def advance(self):
        # Determine if at the bottom of the matrix.
        is_at_bottom = np.any(self.array_current[-1,:] > 0)
        # Advance the current tetrimino array one line and return a copy.
        array_current = np.roll(self.array_current, shift=1, axis=0)
        # Determine if the advanced copy intersects already placed blocks.
        is_intersecting = np.any(self.array_dropped[array_current > 0] > 0)
        # Apply the advancement if not intersecting and not at the bottom.
        if (self.flag_ghost and not is_at_bottom) or (not self.flag_ghost and (not is_at_bottom and not is_intersecting)):
            self.array_current = np.copy(array_current)
            # Check whether the tetrimino has landed on any already placed block or on the bottom of the matrix.
            is_landed_stack = np.any(self.array_dropped[np.roll(self.array_current, shift=1, axis=0) > 0] > 0)
            is_landed_bottom = np.argmax(np.any(np.flipud(self.array_current) > 0, axis=1)) == 0
            if (self.flag_ghost and is_landed_bottom) or (not self.flag_ghost and (is_landed_stack or is_landed_bottom)):
                # Reset advance timer if landed while soft dropping.
                if self.flag_softdropping:
                    self.stop_softdropping()
                # Play sound effect.
                if not self.flag_ghost:
                    self.sound_game_landing.play()
        else:
            self.harddrop()
        # Update the displayed array.
        self.update()

    # Move left one column.
    def move_left(self):
        # Check if already in leftmost column.
        if self.flag_ghost or not np.any(self.array_current[:, 0] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_dropped[indices_rows, indices_columns-1] > 0):
                self.array_current = np.roll(self.array_current, shift=-1, axis=1)
                # Update the displayed array.
                self.update()
                # Play sound effect.
                self.sound_game_move.play()
    
    # Move right one column.
    def move_right(self):
        # Check if already in rightmost column.
        if self.flag_ghost or not np.any(self.array_current[:, -1] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_dropped[indices_rows, indices_columns+1] > 0):
                self.array_current = np.roll(self.array_current, shift=1, axis=1)
                # Update the displayed array.
                self.update()
                # Play sound effect.
                self.sound_game_move.play()

    # Rotate counterclockwise or clockwise by inputting 1 (default) or -1.
    def rotate(self, direction=1):
        # List of lists of tuples for all translation values (right, down) for each rotation, defined in the order they should be checked.
        translations_all = [
            # J, L, S, T, Z
            [( 0, 0),	(-1, 0),	(-1,-1),	( 0,+2),	(-1,+2),],  # 0->R
            [( 0, 0),	(+1, 0),	(+1,+1),	( 0,-2),	(+1,-2),],  # R->0
            [( 0, 0),	(+1, 0),	(+1,+1),	( 0,-2),	(+1,-2),],  # R->2
            [( 0, 0),	(-1, 0),	(-1,-1),	( 0,+2),	(-1,+2),],  # 2->R
            [( 0, 0),	(+1, 0),	(+1,-1),	( 0,+2),	(+1,+2),],  # 2->L
            [( 0, 0),	(-1, 0),	(-1,+1),	( 0,-2),	(-1,-2),],  # L->2
            [( 0, 0),	(-1, 0),	(-1,+1),	( 0,-2),	(-1,-2),],  # L->0
            [( 0, 0),	(+1, 0),	(+1,-1),	( 0,+2),	(+1,+2),],  # 0->L
            # I
            [( 0, 0),	(-2, 0),	(+1, 0),	(-2,+1),	(+1,-2),],  # 0->R
            [( 0, 0),	(+2, 0),	(-1, 0),	(+2,-1),	(-1,+2),],  # R->0
            [( 0, 0),	(-1, 0),	(+2, 0),	(-1,-2),	(+2,+1),],  # R->2
            [( 0, 0),	(+1, 0),	(-2, 0),	(+1,+2),	(-2,-1),],  # 2->R
            [( 0, 0),	(+2, 0),	(-1, 0),	(+2,-1),	(-1,+2),],  # 2->L
            [( 0, 0),	(-2, 0),	(+1, 0),	(-2,+1),	(+1,-2),],  # L->2
            [( 0, 0),	(+1, 0),	(-2, 0),	(+1,+2),	(-2,-1),],  # L->0
            [( 0, 0),	(-1, 0),	(+2, 0),	(-1,-2),	(+2,+1),],  # 0->L
            # Other
            [( 0, 0),],
            ]
        # Assign the corresponding translation values.
        if self.id_current in np.array(self.id_classic)[[1, 2, 4, 5, 6]]:
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
        elif self.id_current == self.id_classic[0]:
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
        else:
            translations = translations_all[-1]

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
                    available_count = np.argmax(np.any(array_current > 0, axis=1))
                    if abs(translation[1]) > available_count:
                        continue
                elif translation[1] < 0:
                    available_count = np.argmax(np.any(np.flipud(array_current > 0), axis=1))
                    if abs(translation[1]) > available_count:
                        continue

            # Check whether the rotated tetrimino, when translated, intersects already placed blocks.
            is_intersecting = np.any(self.array_dropped[np.roll(array_current, shift=translation, axis=(1,0)) > 0] > 0)
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
                # Update the displayed array.
                self.update()
                # Play sound effect.
                self.sound_game_rotate.play()
                # Set flag if T-spin or mini T-spin.
                if self.id_current == self.id_classic[5]:
                    front_count = np.sum(self.array_dropped[self.array_current == -2] > 0)
                    back_count = np.sum(self.array_dropped[self.array_current == -3] > 0)
                    if front_count == 2 and back_count >= 1:
                        self.flag_tspin = True
                        self.flag_tspin_mini = False
                    elif front_count >= 1 and back_count == 2:
                        self.flag_tspin_mini = True
                        self.flag_tspin = False
                # Exit the for loop.
                break

    # Hard drop.
    def harddrop(self):
        # If a heavy tetrimino, delete placed blocks below the current tetrimino and shift tetrimino to bottom row.
        if self.flag_heavy:
            self.array_dropped[self.array_highlight < 0] = 0
            self.array_current = np.roll(self.array_current, np.argmax(np.any(np.flipud(self.array_current) > 0, axis=1)), axis=0)
        # If not a ghost tetrimino, shift the tetrimino down.
        else:
            if not self.flag_ghost:
                self.array_current = -1 * self.array_highlight
        # Drop the tetrimino.
        self.array_dropped[self.array_current > 0] = self.array_current[self.array_current > 0]
        # Play sound effect.
        self.sound_game_harddrop.play()
        self.update()

        # Increment the placed blocks counter.
        self.count += 1

        # Reset certain flags if needed.
        if self.flag_ghost:
            self.flag_ghost = False
        if self.flag_heavy:
            self.flag_heavy = False
        if self.flag_fast_fall:
            self.flag_fast_fall = False
        self.flag_hold = False
        # Update the values of previously placed ghost blocks.
        self.array_dropped[self.array_dropped == 901] = 900

        # Check for cleared lines and empty them.
        cleared_rows = np.argwhere(np.all(self.array_dropped > 0, axis=1))
        cleared_increment = len(cleared_rows)
        if cleared_increment > 0:
            self.array_dropped = np.concatenate((
                np.zeros([cleared_increment,self.column_count]),
                np.delete(self.array_dropped, obj=cleared_rows, axis=0)
                ), axis=0)
        # Check for a perfect clear.
        cleared_perfect = not np.any(self.array_dropped)
        # Increment the combo counter if a line was cleared.
        if cleared_increment > 0:
            self.combos += 1
        else:
            self.combos = 0
        # Calculate points earned based on the type of line clear.
        score_increment = 5 * cleared_increment
        if cleared_increment >= 4:
            score_increment = 10 * cleared_increment
        # Calculate points for T-spins.
        if self.flag_tspin:
            score_increment = 20 * (cleared_increment + 1)
            print('tspin points ', score_increment)
        elif self.flag_tspin_mini:
            score_increment = 5 * (2 ** cleared_increment)
            print('mini tspin points ', score_increment)
        # Calculate point multipliers.
        multipliers = []
        if self.combos > 1:
            multipliers.append(self.combos)
            print('combo multiplier: ', multipliers[-1])
        if cleared_perfect:
            multipliers.append(cleared_increment)
            print('perfect clear multiplier: ', multipliers[-1])
        # Increment the score.
        score_previous = self.score + 0
        self.score += int(score_increment * np.prod(multipliers))
        # Update the block fall speed, the probability of getting an advanced tetrimino, and the probability of getting a special effect.
        self.update_speed_fall()
        self.update_chance_advanced()
        self.update_chance_special()
        
        # Play a sound corresponding to the number of lines cleared.
        if cleared_increment == 1:
            self.sound_game_single.play()
        elif cleared_increment == 2:
            self.sound_game_double.play()
        elif cleared_increment == 3:
            self.sound_game_triple.play()
        elif cleared_increment >= 4:
            self.sound_game_tetris.play()
        # Play a sound for perfect clears.
        if cleared_perfect:
            self.sound_game_perfect.play()
        # Play a sound for special line clears.
        if self.flag_tspin or self.flag_tspin_mini or cleared_increment >= 4:
            self.sound_game_special.play()
        
        # Advance to the next stage of the game if a score threshold is passed.
        if score_previous < self.score_thresholds[self.stage] <= self.score:
            self.stage_advance()
        
        # Reset the previous advance time.
        self.reset_time_advance()
        
        if self.flag_playing:
            # Stop the game if the top row is occupied.
            if np.any(self.array_dropped[0, :] > 0):
                self.lose_game()
            # Create a new tetrimino otherwise.
            else:
                self.create_new()

    # Start soft dropping.
    def start_softdropping(self):
        self.advance()
        # Set flags.
        self.flag_softdropping = True
        self.flag_advancing = False
        # Reset the previous advance time.
        self.reset_time_advance()
        # Record the current time used later to calculate how long this key is held.
        self.time_start_softdrop = self.time_current + 0
        # Initialize the time at which the previous repeat occured.
        self.time_previous_softdrop = 0
        # Play sound effect.
        self.sound_game_softdrop.play()

    # Stop soft dropping.
    def stop_softdropping(self):
        # Set flags.
        self.flag_softdropping = False
        self.flag_advancing = True
        # Reset the previous advance time.
        self.reset_time_advance()

    # Hold.
    def hold(self):
        # Set the flag to prevent another hold.
        self.flag_hold = True
        # Store the current tetrimino and tetrimino ID in the queue.
        self.queue_hold.append((self.tetrimino, self.id_current, self.rotation_current))
        # Create a new tetrimino if nothing was in the queue.
        if len(self.queue_hold) <= 1:
            self.create_new()
        # Swap the current tetrimino with the one in the queue.
        else:
            self.create_new(self.queue_hold.pop(0))

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
            indices_current = (self.row_count-1) - np.argmax(np.flipud(self.array_current > 0), axis=0)[columns]
            # Get the current columns of the placed blocks array.
            array_dropped_current = self.array_dropped[:, columns]
            # Clear the blocks at or above the current tetrimino.
            for i in range(len(indices_current)):
                array_dropped_current[indices_current[i]::-1, i] = 0
            # List of row indices of highest available positions in current tetrimino's columns.
            if self.flag_heavy:
                indices_available = (self.row_count-1) * np.ones(array_dropped_current.shape[1])
            else:
                indices_available = np.where(
                    np.any(array_dropped_current > 0, axis=0),
                    np.argmax(array_dropped_current > 0, axis=0)-1,
                    (self.row_count-1) * np.ones(array_dropped_current.shape[1])
                    )
            # Mark the blocks where the current tetrimino will fall if hard dropped with negative numbers.
            shift = int(min(indices_available - indices_current))
            if self.flag_heavy:
                for i in range(len(indices_current)):
                    if (indices_current[i]+1) <= self.row_count-1:
                        array_dropped_current[indices_current[i]+1:indices_current[i]+1+shift, i] = -1
                self.array_highlight[:, columns] = array_dropped_current
            else:
                self.array_highlight = -1 * np.roll(self.array_current, shift=shift, axis=0)
        # Remove the current tetrimino if not playing.
        else:
            self.array_current[:] = 0
        # Add the highlighted blocks, dropped blocks, and current tetrimino to the displayed array.
        if not self.flag_ghost and not self.flag_blind:
            self.array_display[self.array_highlight < 0] = self.array_highlight[self.array_highlight < 0]
        self.array_display[self.array_dropped > 0] = self.array_dropped[self.array_dropped > 0]
        self.array_display[self.array_current > 0] = self.array_current[self.array_current > 0]

    # Update the block fall speed.
    def update_speed_fall(self):
        self.speed_fall = np.interp(self.score, [0, self.score_thresholds[-2]], self.speeds_fall)

    # Update the probability of getting an advanced tetrimino.
    def update_chance_advanced(self):
        self.weight_advanced = np.interp(self.score, [self.score_update_chance_advanced, self.score_thresholds[-2]], self.weights_advanced)
    
    # Update the probability of getting a special effect.
    def update_chance_special(self):
        self.weight_special = np.interp(self.score, [self.score_update_chance_special, self.score_thresholds[-2]], self.weights_special)
    
    # Advance to the next stage of the game.
    def stage_advance(self):
        # Advance to the second or third stage.
        if self.stage == 0 or self.stage == 1:
            # Stop and unload current music.
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            # Load transition music.
            pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_transition_{}.ogg'.format(self.stage+1)))
            # Set the music to send an event when done playing.
            pygame.mixer.music.set_endevent(pygame.USEREVENT+1)
            # Play the music once.
            pygame.mixer.music.play(loops=0)
        # Win the game.
        elif self.stage == len(self.score_thresholds)-1:
            self.win_game()
        # Increment the stage value.
        if self.stage < len(self.score_thresholds)-1:
            self.stage += 1
            print('Stage: ', self.stage)
    
    # Stop the game when the player wins.
    def win_game(self):
        self.stop_game()
        # Play music.
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_win.ogg'))
        pygame.mixer.music.play(loops=0)
        # Play sound effect.
        self.sound_game_win.play()

    # Stop the game when the player loses.
    def lose_game(self):
        self.stop_game()
        # Play music.
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_lose.ogg'))
        pygame.mixer.music.play(loops=0)
        # self.sound_game_lose.play()

    # Reset the value of the previous advance time to the current time.
    def reset_time_advance(self):
        self.time_start_advance = self.time_current + 0
        # Reset the T-spin flags.
        self.flag_tspin = False
        self.flag_tspin_mini = False


# =============================================================================
# Main Program Loop.
# =============================================================================
# Create an instance of the game.
game = Tetron()
# Create lists to store multiple instances of the game.
games_player = [game]
games_ai = []

# Define the height of the panel above the matrix.
height_panel = 1 * game.block_height

# Set the window title and window icon.
pygame.display.set_caption(name_program + ' - ' + version_program)
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)
# Set the window size [width, height] in pixels.
size_window = [
    game.column_count*game.block_width + (game.column_count+1)*game.block_margin + (game.width_hold+game.margin_small) + (game.width_next+game.margin_small),
    height_panel + game.row_count*game.block_height+(game.row_count+1)*game.block_margin
    ]
screen = pygame.display.set_mode(size_window, pygame.RESIZABLE)
# Define and position a rect object representing the matrix.
rect_matrix = game.surface_matrix.get_rect()
rect_matrix.top = height_panel + 0
rect_matrix.left = game.width_hold + game.margin_small
# Define and position a rect object representing the hold queue.
rect_hold = game.surface_hold.get_rect()
rect_hold.top = height_panel + 0
rect_hold.left = rect_matrix.left - game.width_hold - game.margin_small

# Load the logo.
logo = pygame.image.load('logo.png')
logo = pygame.transform.scale(logo, [int(height_panel*(logo.get_width()/logo.get_height())), height_panel])

# Create font objects used to create text.
font_normal = pygame.font.SysFont('Segoe UI Semibold', 24)
font_small = pygame.font.SysFont('Segoe UI Semibold', 18)

# Loop until the window is closed.
done = False
while not done:
    # Calculate the current time and elapsed time.
    game.time_current = pygame.time.get_ticks()
    if game.flag_playing:
        game.time_elapsed = pygame.time.get_ticks() - game.time_start

    # =============================================================================
    # Key Presses/Releases And Other Events.
    # =============================================================================
    for event in pygame.event.get():
        # Window is exited.
        if event.type == pygame.QUIT:
            done = True
        # Window is resized.
        elif event.type == pygame.VIDEORESIZE:
            # Redefine the size of the window.
            size_window = pygame.display.get_window_size()  # screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            # Adjust the positions of the elements.
            rect_matrix.centerx = size_window[0]//2
            rect_hold.left = rect_matrix.left - game.width_hold - game.margin_small
            
            # # Redefine the width and height of the blocks in the matrix.
            # game.block_width = int(np.floor((size_window[1] - ((game.row_count+1)*game.block_margin)) / (game.row_count+1)))
            # game.block_height = game.block_width + 0
            # # Redefine the height of the panel above the matrix.
            # height_panel = 1 * game.block_height
        # Key presses.
        elif event.type == pygame.KEYDOWN:
            if game.flag_playing:
                # Move left one column.
                if event.key == pygame.K_a:
                    game.move_left()
                    # Record the current time used later to calculate how long this key is held.
                    game.time_start_move_left = game.time_current + 0
                    # Initialize the time at which the previous repeat occured.
                    game.time_previous_move_left = 0
                # Move right one column.
                elif event.key == pygame.K_d:
                    game.move_right()
                    # Record the current time used later to calculate how long this key is held.
                    game.time_start_move_right = game.time_current + 0
                    # Initialize the time at which the previous repeat occured.
                    game.time_previous_move_right = 0
                # Rotate counterclockwise or clockwise.
                elif event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                    if event.key == pygame.K_LEFT:
                        direction = 1
                    elif event.key == pygame.K_RIGHT:
                        direction = -1
                    # Only rotate if not freebie.
                    if not game.id_current == 899:
                        game.rotate(direction)
                # Hard drop.
                elif event.key == pygame.K_w:
                    game.harddrop()
                # Start soft dropping.
                elif event.key == pygame.K_s:
                    game.start_softdropping()
                # Hold.
                elif event.key == pygame.K_q:
                    if not game.flag_hold and not game.flag_ghost and not game.flag_heavy:
                        game.hold()
        # Key releases.
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if not game.flag_playing:
                    # Resume game.
                    if game.flag_paused:
                        game.pause_game()
                    # Start game.
                    else:
                        game.start_game()
                # Pause game.
                else:
                    game.pause_game()
            # Stop game.
            elif event.key == pygame.K_ESCAPE:
                if game.flag_playing or game.flag_paused:
                    game.stop_game()

            if game.flag_playing:
                # Stop soft dropping.
                if event.key == pygame.K_s:
                    game.stop_softdropping()
        # Transition music ends.
        elif event.type == pygame.USEREVENT+1:
            if game.flag_playing:
                # Stop and unload current music.
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                # Load music for current stage.
                pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron_{}.ogg'.format(game.stage+1)))
                # Disable the event sent when music ends, and play indefinitely.
                pygame.mixer.music.set_endevent()
                pygame.mixer.music.play(loops=-1)
    
    # =============================================================================
    # Keys Held Continuously.
    # =============================================================================
    # Get a list of the keys currently being held down.
    keys_pressed = pygame.key.get_pressed()
    # Soft drop.
    if keys_pressed[pygame.K_s] and game.flag_playing:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_softdrop) > game.delay_softdrop:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_softdrop) > game.speed_softdrop:
                if game.flag_softdropping:  # Check whether soft dropping to prevent advancing line immediately after landing
                    game.advance()
                    # Play sound effect.
                    game.sound_game_softdrop.play()
                game.time_previous_softdrop = game.time_current + 0
    # Move left.
    if keys_pressed[pygame.K_a] and game.flag_playing:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_move_left) > game.delay_move:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_move_left) > game.speed_move:
                game.move_left()
                game.time_previous_move_left = game.time_current + 0
    # Move right.
    if keys_pressed[pygame.K_d] and game.flag_playing:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_move_right) > game.delay_move:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_move_right) > game.speed_move:
                game.move_right()
                game.time_previous_move_right = game.time_current + 0
    
    # =============================================================================
    # Time-Based Actions.
    # =============================================================================
    if game.flag_playing:
        # Advance current tetrimino.
        if game.flag_advancing:
            if (game.time_current - game.time_start_advance) >= (game.speed_fall * (game.speed_fall_multiplier ** game.flag_fast_fall)):
                game.advance()
                game.reset_time_advance()
        else:
            game.reset_time_advance()
    
    # =============================================================================
    # Draw Screen.
    # =============================================================================
    # Erase the screen.
    screen.fill(rgb(0))
    # Display the logo if not playing.
    if not game.flag_playing:
        rect_logo = logo.get_rect()
        rect_logo.bottom = height_panel
        rect_logo.centerx = rect_matrix.centerx + 0
        screen.blit(logo, rect_logo)
    # Draw each block inside the matrix.
    for row in range(game.row_count):
        for column in range(game.column_count):
            number = game.array_display[row, column]
            tint = 0
            if number != 0:
                if game.flag_blind:
                    color = 0.28  # Color of placed blocks in blind mode
                else:
                    if number < 0:
                        color = 0.35  # Color of highlighted blocks
                    else:
                        color = number + 0  # Color of placed blocks
            else:
                color = 0.25  # Color of blank blocks
            pygame.draw.rect(surface=game.surface_matrix, color=rgb(color, tint=tint), rect=[(game.block_margin+game.block_width)*column+game.block_margin, (game.block_margin+game.block_height)*row+game.block_margin, game.block_width, game.block_height])
    # Erase the displayed hold queue.
    game.surface_hold.fill(rgb(0))
    # Draw tetrimino in hold queue.
    if len(game.queue_hold) > 0:
        size = int(min(np.floor([game.width_hold/game.queue_hold[0][0].shape[0], game.width_hold/game.queue_hold[0][0].shape[1]])))
        for row in range(game.queue_hold[0][0].shape[0]):
            for column in range(game.queue_hold[0][0].shape[1]):
                color = game.queue_hold[0][0][row, column]
                if color > 0:
                    pygame.draw.rect(surface=game.surface_hold, color=rgb(color), rect=[size*column, size*row, size, size])
        # Display hold queue label text.
        text_hold = font_small.render('HOLD', True, rgb(0.5))
        rect_text_hold = text_hold.get_rect()
        rect_text_hold.left = rect_hold.left + 0
        rect_text_hold.bottom = height_panel + 0
        screen.blit(text_hold, rect_text_hold)
    # Display elapsed time text.
    text_time_elapsed = font_normal.render('{:02d}:{:02d}'.format(game.time_elapsed//60000, int((game.time_elapsed/1000)%60)), True, rgb(1))
    rect_text_time_elapsed = text_time_elapsed.get_rect()
    rect_text_time_elapsed.right = rect_matrix.right + 0
    rect_text_time_elapsed.bottom = height_panel + 0
    screen.blit(text_time_elapsed, rect_text_time_elapsed)
    # Display cleared lines text.
    text_cleared = font_normal.render('{}'.format(game.score), True, rgb(1))
    rect_text_cleared = text_cleared.get_rect()
    rect_text_cleared.left = rect_matrix.left + 0
    rect_text_cleared.bottom = height_panel + 0
    screen.blit(text_cleared, rect_text_cleared)
    # Stop the disoriented effect if it has lasted longer than the maximum duration.
    if game.flag_disoriented:
        if game.duration_disoriented > game.duration_max_disoriented:
            game.flag_disoriented = False
            game.duration_disoriented = 0
        else:
            game.duration_disoriented += 1000/game.fps
        # Rotate the matrix.
        game.surface_matrix.blit(pygame.transform.rotate(game.surface_matrix, 180), (0,0))
    # Stop the blind effect if it has lasted longer than the maximum duration.
    if game.flag_blind:
        if game.duration_blind > game.duration_max_blind:
            game.flag_blind = False
            game.duration_blind = 0
        else:
            game.duration_blind += 1000/game.fps
    # Display the matrix in the window.
    screen.blit(game.surface_matrix, rect_matrix)
    # Display the hold queue in the window.
    screen.blit(game.surface_hold, rect_hold)
    
    # Update the screen.
    pygame.display.flip()

    # Limit the game to 60 frames per second by delaying every iteration of this loop.
    game.clock.tick(game.fps)
 
# Close the window and quit.
pygame.quit()
