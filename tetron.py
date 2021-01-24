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
version_program = 'a.0.0'
# Get the path to the folder containing the program.
folder_program = os.path.dirname(os.path.realpath(sys.argv[0]))
folder_sounds = os.path.join(folder_program, 'Sounds')
folder_images = os.path.join(folder_program, 'Images')
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
        elif color == 901:  # White
            color = [255,255,255]
        elif color == 902:  # Gray
            color = [158,158,158]
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
        self.width = 40
        self.height = 40
        self.margin = 1

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

        # Initialize the block fall speed (ms).
        self.speed_fall = 1000
        # Define the maximum block fall speed (lines/second).
        # self.speed_limit_fall = self.fps + 0
        # Define the increment by which the block fall speed is increased (lines/second).
        # self.speed_increment = 0.5
        # Define the block move speed (ms) and initial delay for key repeats (ms).
        self.speed_move = 30
        self.delay_move = 200
        # Define the soft drop speed (ms) and initial delay for key repeats (ms).
        self.speed_drop_soft = 100
        self.delay_drop_soft = 100

        # Define the IDs for classic tetriminos, advanced tetriminos, special effects.
        self.id_classic = [100, 200, 300, 400, 500, 600, 700]
        self.id_advanced = [101, 102, 199, 201, 202, 301, 302, 401, 402, 403, 501, 601, 602, 701, 801, 811, 812, 813, 814]
        self.id_special = ['ghost', 'rotate', 'blind']

        # Define the number of blocks needed to incrementally increase the difficulty.
        self.count_increase_difficulty = 10
        # Define the number of blocks neeeded to begin increasing the chance of getting a special effect.
        self.count_increase_chance_special = 30
        # Define the score needed to win the game.
        self.score_win = 1000

        # Define the maximum probability (between 0 and 1) of getting an advanced tetrimino and the increment by which the probability is increased.
        self.weight_max_advanced = 2/5
        self.weight_increment_advanced = 0.025
        # Define the maximum probability (between 0 and 1) of getting a special effect and the increment by which the probability is increased.
        self.weight_max_special = 1/20
        self.weight_increment_special = 0.005
        # Define durations for special effects (ms).
        self.duration_max_rotate = 20000
        self.duration_max_blind = 20000

        # Create the surface used to display the grid.
        self.grid = pygame.Surface((self.column_count*self.width+(self.column_count+1)*self.margin, self.row_count*self.height+(self.row_count+1)*self.margin))
        
        # Load background music and sound effects.
        pygame.mixer.music.load(os.path.join(folder_sounds, 'tetron.mp3'))
        # self.sound_game_advance = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_advance.wav'))
        self.sound_game_move = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_move.wav'))
        self.sound_game_rotate = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_rotate.wav'))
        self.sound_game_harddrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_harddrop.wav'))
        self.sound_game_softdrop = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_softdrop.wav'))
        self.sound_game_landing = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_landing.wav'))
        self.sound_game_win = pygame.mixer.Sound(os.path.join(folder_sounds, 'game_win.mp3'))
        self.sound_special_ghost = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_ghost.wav'))
        self.sound_special_rotate = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_rotate.wav'))
        self.sound_special_blind = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_blind.wav'))
        # Set volume for some sound effects.
        self.sound_game_move.set_volume(0.1)
        self.sound_game_rotate.set_volume(0.1)
        self.sound_game_harddrop.set_volume(0.1)
        self.sound_game_softdrop.set_volume(0.1)
        self.sound_game_landing.set_volume(0.1)

        # Initialize all other attributes.
        self.initialize()

    # Initialize values of attributes that are both modified during the game and reset when starting the game. Called on first startup and subsequent game starts.
    def initialize(self):
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
        # Initialize the number of placed tetriminos.
        self.count = 0
        # Initialize the number of successive line clears.
        self.combos = 0
        # Initialize the cleared lines counter.
        self.score = 0

        # Initialize the probability (between 0 and 1) of getting an advanced tetrimino.
        self.weight_advanced = 0
        # Initialize the probability (between 0 and 1) of getting a special effect.
        self.weight_special = 0.0

        # Initialize flags indicating statuses of the game.
        self.flag_playing = False
        self.flag_dropping_soft = False
        self.flag_ghost = False
        self.flag_rotate = False
        self.flag_blind = False

    # Start the game.
    def start_game(self):
        # Reset attributes.
        self.initialize()
        # Save the start time.
        self.time_start = pygame.time.get_ticks()
        # Reset the timers.
        pygame.time.set_timer(pygame.USEREVENT+1, self.speed_fall)
        # Start playing music and loop indefinitely.
        pygame.mixer.music.play(loops=-1)
        # Set flags.
        self.flag_playing = True
        # Create a new tetrimino.
        self.create_new()
    
    # Stop the game.
    def stop_game(self):
        pygame.time.set_timer(pygame.USEREVENT+1, 0)
        self.flag_playing = False
        self.flag_ghost = False
        self.flag_blind = False
        self.flag_rotate = False
        self.update()
        # Stop playing music.
        pygame.mixer.music.stop()

    # Generate a new tetrimino and replace the current arrays.
    def create_new(self):
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
                self.sound_special_ghost.play()
            elif effect_special == self.id_special[1]:
                # Apply the effect only if it is not currently active.
                if not self.flag_rotate:
                    self.flag_rotate = True
                    self.duration_rotate = 0
                    self.sound_special_rotate.play()
            elif effect_special == self.id_special[2]:
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
            tetrimino[0, 0] = -1
            tetrimino[0, 2] = -1
            tetrimino[2, :] = -1
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
        elif self.id_current == 199:  # Freebie
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
            tetrimino = self.id_current * np.concatenate((
                np.ones([1, self.column_count]),
                1 - array_dropped_top
                ), axis=0)
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
        # Change the tetrimino to a ghost.
        if self.flag_ghost:
            tetrimino[tetrimino > 0] = 901
        self.tetrimino = tetrimino

        # Clear the current tetrimino array.
        self.array_current[:] = 0
        # Update the array of the current tetrimino.
        row_left = int((self.array_current.shape[1]-tetrimino.shape[1])/2)
        self.array_current[0:tetrimino.shape[0], row_left:row_left+tetrimino.shape[1]] = self.tetrimino

        # Update the displayed array.
        self.update()

    # Advance one line.
    def advance(self):
        # Row and column indices of occupied blocks in current array.
        indices_rows, indices_columns = np.nonzero(self.array_current > 0)
        # Determine if at the bottom of the matrix.
        is_not_at_bottom = not np.any((indices_rows+1) > (self.array_dropped.shape[0]-1))
        # Determine if advancing a line will intersect already placed blocks.
        try:
            no_intersection = not np.any(self.array_dropped[indices_rows+1, indices_columns] > 0)
        except IndexError:
            no_intersection = False
        # Advance one line if not intersecting.
        if (self.flag_ghost and is_not_at_bottom) or (not self.flag_ghost and (is_not_at_bottom and no_intersection)):
            self.array_current = np.roll(self.array_current, shift=1, axis=0)
        # Hard drop if intersecting.
        else:
            self.drop_hard()
            # Play sound effect.
            self.sound_game_landing.play()
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
        # Calculate the indices of the rows and columns currently occupied.
        rows_occupied_before = np.sum(np.any(self.tetrimino > 0, axis=1))
        columns_occupied_before = np.sum(np.any(self.tetrimino > 0, axis=0))
        # Rotate tetrimino.
        self.tetrimino = np.rot90(self.tetrimino, k=direction)
        # Calculate the indices of the rows and columns occupied after rotation.
        rows_occupied_after = np.sum(np.any(self.tetrimino > 0, axis=1))
        columns_occupied_after = np.sum(np.any(self.tetrimino > 0, axis=0))
        # Determine if the rotated tetrimino intersects already placed blocks.
        indices_rows, indices_columns = np.nonzero(self.array_current > 0)
        is_intersecting = np.any(self.array_dropped[self.array_current != 0][self.tetrimino.flatten()>0] > 0)
        if not is_intersecting or self.flag_ghost:
            # Move the tetrimino one block right or left if rotation causes it to exceed the left and right walls.
            if columns_occupied_after > columns_occupied_before:
                if np.any(self.array_current[:, 0] > 0):
                    self.array_current = np.roll(self.array_current, shift=1, axis=1)
                elif np.any(self.array_current[:, -1] > 0):
                    self.array_current = np.roll(self.array_current, shift=-1, axis=1)
            # Move the tetrimino one block up or down if rotation causes it to exceed the top and bottom walls.
            if rows_occupied_after > rows_occupied_before:
                if np.any(self.array_current[0, :] > 0):
                    self.array_current = np.roll(self.array_current, shift=1, axis=0)
                elif np.any(self.array_current[-1, :] > 0):
                    self.array_current = np.roll(self.array_current, shift=-1, axis=0)
            # Insert the rotated tetrimino into the array.
            self.array_current[self.array_current != 0] = self.tetrimino.flatten()
        # Update the displayed array.
        self.update()
        # Play sound effect.
        self.sound_game_rotate.play()

    # Hard drop.
    def drop_hard(self):
        # Reset the timer only if not soft dropping. This prevents double advancing caused by both this timer and the soft drop timer.
        if not self.flag_dropping_soft:
            pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)
            # self.set_timer_advance(True)

        # Shift the tetrimino down only if not a ghost tetrimino.
        if not self.flag_ghost:
            self.array_current = -1 * self.array_highlight
        # Drop the tetrimino.
        self.array_dropped[self.array_current > 0] = self.array_current[self.array_current > 0]
        # Play sound effect.
        self.sound_game_harddrop.play()
        self.update()

        # Increment the placed blocks counter and increase the game difficulty if needed.
        self.count += 1
        if (self.count % self.count_increase_difficulty) == 0:
            self.increase_chance_advanced()
            if self.count >= self.count_increase_chance_special:
                self.increase_chance_special()
        # Reset the ghost flag if needed.
        if self.flag_ghost:
            self.flag_ghost = False
        # Update the values of previously placed ghost blocks.
        self.array_dropped[self.array_dropped == 901] = 902

        # Check for cleared lines and empty them.
        cleared_rows = np.argwhere(np.all(self.array_dropped > 0, axis=1))
        cleared_increment = len(cleared_rows)
        if cleared_increment > 0:
            self.array_dropped = np.concatenate((
                np.zeros([cleared_increment,self.column_count]),
                np.delete(self.array_dropped, obj=cleared_rows, axis=0)
                ), axis=0)
        # Increment the combo counter if a line was cleared.
        if cleared_increment > 0:
            self.combos += 1
        else:
            self.combos = 0
        # Calculate points to add to score.
        score_increment = 10 * cleared_increment
        if cleared_increment >= 4:
            score_increment = 40
        multipliers = []
        if self.combos > 1:
            multipliers.append((self.combos+1)/2)
            print('combo multiplier: ', multipliers[-1])
        self.score += int(score_increment * np.prod(multipliers))
        
        # Stop the game if the top row is occupied.
        if np.any(self.array_dropped[0, :] > 0):
            self.stop_game()
        # Stop the game if the score exceeds the threshold.
        elif self.score >= self.score_win:
            self.win_game()
        # Create a new tetrimino otherwise.
        else:
            self.create_new()

    # Update the displayed array.
    def update(self):
        # Reset the values of the arrays to 0.
        self.array_display[:] = 0
        self.array_highlight[:] = 0
        # Highlight the area where the current tetrimino will fall if hard dropped.
        if self.flag_playing:
            # List of Booleans indicating which columns of the matrix contain blocks from the current tetrimino.
            columns = np.any(self.array_current > 0, axis=0)
            # List of row indices, counting from bottom (0 = bottom row), of the bottommost blocks in each column of the current tetrimino.
            indices_current = (self.array_current.shape[0]-1) - np.argmax(np.flipud(self.array_current > 0), axis=0)[columns]
            # Get the current columns of the placed blocks array.
            array_dropped_current = self.array_dropped[:, columns]
            # Clear the blocks at or above the current tetrimino.
            for i in range(len(indices_current)):
                array_dropped_current[indices_current[i]::-1, i] = 0
            # List of row indices of highest available positions in current tetrimino's columns.
            indices_available = np.where(
                np.any(array_dropped_current > 0, axis=0),
                np.argmax(array_dropped_current > 0, axis=0)-1,
                (self.row_count-1) * np.ones(array_dropped_current.shape[1])
                )
            # Mark the blocks where the current tetrimino will fall if hard dropped with negative numbers.
            shift = np.min(indices_available - indices_current)
            self.array_highlight = -1 * np.roll(self.array_current, shift=int(shift), axis=0)
        # Remove the current tetrimino if not playing.
        else:
            self.array_current[:] = 0
        # Add the current tetrimino and highlighted blocks to the displayed array.
        if not self.flag_ghost and not self.flag_blind:
            self.array_display[self.array_highlight < 0] = self.array_highlight[self.array_highlight < 0]
        self.array_display[self.array_dropped > 0] = self.array_dropped[self.array_dropped > 0]
        self.array_display[self.array_current > 0] = self.array_current[self.array_current > 0]

    # Increase the probability of getting an advanced tetrimino.
    def increase_chance_advanced(self):
        if self.weight_advanced < self.weight_max_advanced:
            self.weight_advanced += self.weight_increment_advanced
            # Prevent the probability from exceeding the maximum value caused by rounding errors.
            self.weight_advanced = min([self.weight_advanced, self.weight_max_advanced])
        print('Probability advanced: ', self.weight_advanced)
    
    # Increase the probability of getting a special effect.
    def increase_chance_special(self):
        if self.weight_special < self.weight_max_special:
            self.weight_special += self.weight_increment_special
            # Prevent the probability from exceeding the maximum value caused by rounding errors.
            self.weight_special = min([self.weight_special, self.weight_max_special])
        print('Probability special: ', self.weight_special)
    
    # Stop the game when the player wins.
    def win_game(self):
        self.stop_game()
        pygame.mixer.music.stop()
        self.sound_game_win.play()

    # Stop the game when the player loses.
    def lose_game(self):
        self.stop_game()
        pygame.mixer.music.stop()
        # self.sound_game_lose.play()

    # # Reset or stop the timer that advances the current tetrimino. If True, reset and start the timer; if False, stop the timer.
    # def set_timer_advance(self, state):
    #     # Stop the timer.
    #     pygame.time.set_timer(pygame.USEREVENT+1, 0)
    #     # Start the timer if input is True.
    #     if state is True:
    #         pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)


# =============================================================================
# Main Program Loop.
# =============================================================================
# Create an instance of the game class.
game = Tetron()

# Set up the panel above the grid.
height_panel = 1 * game.height
# Set the window title and window icon.
pygame.display.set_caption(name_program + ' - ' + version_program)
icon = pygame.image.load('icon.png')
pygame.display.set_icon(icon)
# Set the window size [width, height] in pixels.
size_window = [game.column_count*game.width+(game.column_count+1)*game.margin, height_panel + game.row_count*game.height+(game.row_count+1)*game.margin]
screen = pygame.display.set_mode(size_window, pygame.RESIZABLE)

# Load the logo.
logo = pygame.image.load('logo.png')
logo = pygame.transform.scale(logo, [int(height_panel*(logo.get_width()/logo.get_height())), height_panel])

# Create a font object that is used to create text.
font = pygame.font.SysFont('Segoe UI Semibold', 24)

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
        # Key presses.
        elif event.type == pygame.KEYDOWN:
            # Start the game.
            if event.key == pygame.K_SPACE and game.flag_playing is False:
                game.start_game()
            # Stop the game.
            elif event.key == pygame.K_ESCAPE and game.flag_playing is True:
                game.stop_game()
            
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
                    game.rotate(direction)
                # Hard drop.
                elif event.key == pygame.K_w:
                    game.drop_hard()
                # Start soft dropping.
                elif event.key == pygame.K_s:
                    game.advance()
                    # Play sound effect.
                    game.sound_game_softdrop.play()
                    # Set flags.
                    game.flag_dropping_soft = True
                    # Record the current time used later to calculate how long this key is held.
                    game.time_start_drop_soft = game.time_current + 0
                    # Initialize the time at which the previous repeat occured.
                    game.time_previous_drop_soft = 0
                    # Stop the advance timer.
                    pygame.time.set_timer(pygame.USEREVENT+1, 0)
                    # game.set_timer_advance(False)
        # Key releases.
        elif event.type == pygame.KEYUP:
            if game.flag_playing:
                # Stop soft dropping.
                if event.key == pygame.K_s:
                    # Set flags.
                    game.flag_dropping_soft = False
                    # Start the advance timer.
                    pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)
                    # game.set_timer_advance(True)
        # Custom event for advancing one line.
        elif event.type == pygame.USEREVENT+1 and game.flag_playing:
            game.advance()
    
    # =============================================================================
    # Keys Held Continuously.
    # =============================================================================
    # Get a list of the keys currently being held down.
    keys_pressed = pygame.key.get_pressed()
    # Soft drop.
    if keys_pressed[pygame.K_s] and game.flag_playing:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_drop_soft) > game.delay_drop_soft:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_drop_soft) > game.speed_drop_soft:
                game.advance()
                game.time_previous_drop_soft = game.time_current + 0
                # Play sound effect.
                game.sound_game_softdrop.play()
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
    # Draw Screen.
    # =============================================================================
    # Fill the screen.
    screen.fill(rgb(0))
    # Display the logo if not playing.
    if not game.flag_playing:
        rect_logo = logo.get_rect()
        rect_logo.top = 0
        rect_logo.centerx = size_window[0]//2
        screen.blit(logo, rect_logo)
    # Draw each block inside the grid.
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
            pygame.draw.rect(surface=game.grid, color=rgb(color, tint=tint), rect=[(game.margin+game.width)*column+game.margin, (game.margin+game.height)*row+game.margin, game.width, game.height])
    # Add elapsed time text to the screen.
    text_time_elapsed = font.render('{:02d}:{:02d}'.format(game.time_elapsed//60000, int((game.time_elapsed/1000)%60)), True, rgb(1))
    rect_text_time_elapsed = text_time_elapsed.get_rect()
    rect_text_time_elapsed.right = size_window[0]
    rect_text_time_elapsed.bottom = height_panel
    screen.blit(text_time_elapsed, rect_text_time_elapsed)
    # Add cleared lines text to the screen.
    text_cleared = font.render('{}'.format(game.score), True, rgb(1))
    rect_text_cleared = text_cleared.get_rect()
    rect_text_cleared.left = 0
    rect_text_cleared.bottom = height_panel
    screen.blit(text_cleared, rect_text_cleared)
    # Stop the rotation effect if it has lasted longer than the maximum duration.
    if game.flag_rotate:
        if game.duration_rotate > game.duration_max_rotate:
            game.flag_rotate = False
            game.duration_rotate = 0
        else:
            game.duration_rotate += 1000/game.fps
        # Rotate the grid.
        game.grid.blit(pygame.transform.rotate(game.grid, 180), (0,0))
    # Stop the blind effect if it has lasted longer than the maximum duration.
    if game.flag_blind:
        if game.duration_blind > game.duration_max_blind:
            game.flag_blind = False
            game.duration_blind = 0
        else:
            game.duration_blind += 1000/game.fps
    # Display the grid inside the window.
    screen.blit(game.grid, [0, height_panel])
    
    # Update the screen.
    pygame.display.flip()

    # Limit the game to 60 frames per second by delaying every iteration of this loop.
    game.clock.tick(game.fps)
 
# Close the window and quit.
pygame.quit()
