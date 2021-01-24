#!/usr/bin/python
# -*- coding: latin-1 -*-


import getopt  # Needed to parse command line arguments.
import os
import random
import sys
import time

import numpy as np
import pygame

# Resources.
# Template started with: http://programarcadegames.com/index.php?lang=en&chapter=array_backed_grids
# Keyboard codes: https://www.pygame.org/docs/ref/key.html#pygame.key.key_code


# Get the path to the folder containing the program.
folder_program = os.path.dirname(os.path.realpath(sys.argv[0]))
folder_sounds = os.path.join(folder_program, 'Sounds')

# Initialize pygame modules.
pygame.init()
try:
    pygame.mixer.init()
except pygame.error:
    print('An audio output device may not be connected.')


# =============================================================================
# Helper Functions.
# =============================================================================
# Return a string with RGB values used for setting colors. Pass a number between 0 and 1 for grayscale colors, or pass a string corresponding to a specific color.
def rgb(color=None, tint=0):
    # Select the default blank color if 'color' is None.
    if color is None:
        color = 0.25
    
    # Set a predefined color if 'color' is a string.
    if isinstance(color, str):
        if color == 'I' or color == 'I+' or color == 'freebie':  # Cyan
            color = [0,175,191]
        elif color == 'J' or color == 'J+':  # Blue
            color = [0,149,255]
        elif color == 'L' or color == 'L+':  # Orange
            color = [255,128,0]
        elif color == 'O' or color == 'O+':  # Yellow
            color = [255,191,0]
        elif color == 'S' or color == 'S+':  # Green
            color = [0,191,96]
        elif color == 'T' or color == 'T+':  # Purple
            color = [140,102,255]
        elif color == 'Z' or color == 'Z+':  # Red
            color = [255,64,64]
        elif color == 'ghost':  # White
            color = [255,255,255]
        else:  # Pink
            color = [255,77,136]
    # Set a grayscale color if 'color' is a number.
    else:
        color = tuple([color * 255] * 3)
    
    if tint != 0:
        if tint > 0:
            color = [255,255,255]*tint + color*(1-tint)
        elif tint < 0:
            color = [0,0,0]*tint + color*(1-tint)
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

        # Initialize arrays for current tetrimino's position, dropped blocks, and displayed blocks.
        self.array_current = np.zeros([self.row_count, self.column_count])
        self.array_dropped = np.zeros([self.row_count, self.column_count])
        self.array_display = np.zeros([self.row_count, self.column_count])

        # Initialize the block fall speed (ms).
        self.speed_fall = 1000
        # Define the maximum block fall speed (lines/second).
        # self.speed_limit_fall = self.fps + 0
        # Define the increment by which the block fall speed is increased (lines/second).
        # self.speed_increment = 0.5
        # Define the block shift speed (ms) and initial delay for key repeats (ms).
        self.speed_shift = 30
        self.delay_shift = 200
        # Define the soft drop speed (ms) and initial delay for key repeats (ms).
        self.speed_drop_soft = 100
        self.delay_drop_soft = 100
        # Define the duration of time before each difficulty increase (ms).
        self.time_increase_difficulty = 20000

        # Initialize the current and previous tetrimino IDs.
        self.id_current = 0
        self.id_previous = 0
        # Initialize the cleared lines counter.
        self.cleared_count = 0

        # Initialize the probabilities (between 0 and 1) of getting an advanced or classic.
        self.weight_advanced = 0
        self.weight_classic = 1 - self.weight_advanced
        self.weight_max_advanced = 1/4
        self.weight_increment_advanced = 0.01
        # Initialize the probability (between 0 and 1) of getting a special effect.
        self.weight_special = 1/2 #0.0
        self.weight_max_special = 1/20
        self.weight_increment_special = 0.0025
        # Define the initial duration (ms) during which the probability of getting a special effect cannot increase.
        self.delay_increment_special = 60000
        # Define parameters for special effects.
        self.duration_max_rotate = 20000
        self.duration_max_blind = 20000

        # Initialize flags indicating statuses of the game.
        self.flag_playing = False
        self.flag_dropping_soft = False
        self.flag_ghost = False
        self.flag_rotate = False
        self.flag_blind = False

        # Initialize sounds and music.
        # self.music = pygame.mixer.Sound('tetris.mp3')
        self.sound_special_ghost = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_ghost.wav'))
        self.sound_special_rotate = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_rotate.wav'))
        self.sound_special_blind = pygame.mixer.Sound(os.path.join(folder_sounds, 'special_blind.wav'))
    
    # Convert a tetrimino ID from its number to its string, or vice versa.
    def convert_tetrimino_id(self, number_or_str):
        id_pairs = [
            (1, 'I'), (2, 'J'), (3, 'L'), (4, 'O'), (5, 'S'), (6, 'T'), (7, 'Z'),
            (10, 'I+'), (20, 'J+'), (30, 'L+'), (40, 'O+'), (50, 'S+'), (60, 'T+'), (70, 'Z+'), (100, 'freebie'), (101, '.'), (102, ':'), (103, '*'), (104, 'ghost')]
        if isinstance(number_or_str, str):
            output = [pair[0] for pair in id_pairs if pair[-1] == number_or_str]
        else:
            output = [pair[-1] for pair in id_pairs if pair[0] == number_or_str]
        return output[0]

    # Generate a new tetrimino and replace the current arrays.
    def create_new(self):
        # Define the IDs for classic and advanced tetriminos.
        id_classic = [1, 2, 3, 4, 5, 6, 7]
        id_advanced = [10, 20, 30, 40, 50, 60, 70, 100, 101, 102, 103]
        # Randomly select which category to choose from.
        category = random.choices(['classic', 'advanced'], [self.weight_classic, self.weight_advanced], k=1)[0]
        # Randomly select a tetrimino within the chosen category, with each tetrimino having an equal probability.
        if category == 'classic':
            self.id_current = random.choice([id for id in id_classic if id != self.id_previous])
        elif category == 'advanced':
            self.id_current = random.choice([id for id in id_advanced if id != self.id_previous])
        # Apply special properties.
        if random.choices([True, False], [self.weight_special, 1-self.weight_special])[0]:
            id_special = ['ghost', 'rotate', 'blind']
            weight_special = [2, 1, 1]
            effect_special = random.choices(id_special, weight_special, k=1)[0]
            if effect_special == 'ghost':
                self.flag_ghost = True
                self.sound_special_ghost.play()
            elif effect_special == 'rotate':
                # Apply the effect only if it is not currently active.
                if not self.flag_rotate:
                    self.flag_rotate = True
                    self.duration_rotate = 0
                    self.sound_special_rotate.play()
            elif effect_special == 'blind':
                # Apply the effect only if it is not currently active.
                if not self.flag_blind:
                    self.flag_blind = True
                    self.duration_blind = 0
                    self.sound_special_blind.play()
        
        # Classic tetriminos.
        if self.id_current == 1:  # I
            tetrimino = self.id_current * np.ones([4, 4])
            tetrimino[[0,2,3],:] = -1
        elif self.id_current == 2:  # J
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0, 1:] = -1
            tetrimino[2, :] = -1
        elif self.id_current == 3:  # L
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0, 0:2] = -1
            tetrimino[2, :] = -1
        elif self.id_current == 4:  # O
            tetrimino = self.id_current * np.ones([2, 2])
        elif self.id_current == 5:  # S
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0, 0] = -1
            tetrimino[1, 2] = -1
            tetrimino[2, :] = -1
        elif self.id_current == 6:  # T
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0, 0] = -1
            tetrimino[0, 2] = -1
            tetrimino[2, :] = -1
        elif self.id_current == 7:  # Z
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[1, 0] = -1
            tetrimino[0, 2] = -1
            tetrimino[2, :] = -1
        # Advanced tetriminos.
        elif self.id_current == 10:  # I+
            tetrimino = self.id_current * np.ones([4, 4])
            tetrimino[[0,3], :] = -1
        elif self.id_current == 20:  # J+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0:2, 1:3] = -1
        elif self.id_current == 30:  # L+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0:2, 0:2] = -1
        elif self.id_current == 40:  # O+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[1, 1] = -1
        elif self.id_current == 50:  # S+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0:2, 0] = -1
            tetrimino[1:3, 2] = -1
        elif self.id_current == 60:  # T+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[0, 0] = -1
            tetrimino[0, 2] = -1
            tetrimino[2, 0] = -1
            tetrimino[2, 2] = -1
        elif self.id_current == 70:  # Z+
            tetrimino = self.id_current * np.ones([3, 3])
            tetrimino[1:3, 0] = -1
            tetrimino[0:2, 2] = -1
        elif self.id_current == 100:  # freebie
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
        elif self.id_current == 101:  # .
            tetrimino = self.id_current * np.ones([1, 1])
        elif self.id_current == 102:  # :
            tetrimino = -1 * np.ones([3, 3])
            tetrimino[[0,2], 1] = self.id_current
        elif self.id_current == 103:  # Random 3x3
            shape = [3, 3]
            tetrimino = -1 * np.ones(shape)
            random_indices = random.sample(range(tetrimino.size), 5)
            tetrimino[np.unravel_index(random_indices, shape)] = self.id_current
        # Change the tetrimino to a ghost.
        if self.flag_ghost:
            tetrimino[tetrimino > 0] = 104
        self.tetrimino = tetrimino

        # Clear the current tetrimino array.
        self.array_current[:] = 0
        # Update the array of the current tetrimino.
        row_left = int((self.array_current.shape[1]-tetrimino.shape[1])/2)
        self.array_current[0:tetrimino.shape[0], row_left:row_left+tetrimino.shape[1]] = self.tetrimino

        # Update the displayed array.
        self.update()

    # Advance the current tetrimino.
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
            # End the game if the top row is occupied.
            if np.any(self.array_dropped[0, :] > 0):
                self.flag_playing = False
            # Create a new tetrimino.
            if self.flag_playing:
                self.create_new()
        # Update the displayed array.
        self.update()

    # Shift current tetrimino left one column.
    def shift_left(self):
        # Check if already in leftmost column.
        if self.flag_ghost or not np.any(self.array_current[:, 0] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_dropped[indices_rows, indices_columns-1] > 0):
                self.array_current = np.roll(self.array_current, shift=-1, axis=1)
                # Update the displayed array.
                self.update()
    
    # Shift current tetrimino right one column.
    def shift_right(self):
        # Check if already in rightmost column.
        if self.flag_ghost or not np.any(self.array_current[:, -1] > 0):
            # Check if placed blocks are in the way.
            indices_rows, indices_columns = np.nonzero(self.array_current > 0)
            if self.flag_ghost or not np.any(self.array_dropped[indices_rows, indices_columns+1] > 0):
                self.array_current = np.roll(self.array_current, shift=1, axis=1)
                # Update the displayed array.
                self.update()

    # Hard drop the current tetrimino.
    def drop_hard(self):
        if not self.flag_dropping_soft:
            # Reset the timer only if not soft dropping. This prevents double advancing caused by both this timer and the soft drop timer.
            pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)
            # self.set_timer_advance(True)

        # Shift the current tetrimino completely down only if not a ghost tetrimino.
        if not self.flag_ghost:
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
            # Shift the current tetrimino down.
            shift = np.min(indices_available - indices_current)
            if shift > 0:
                self.array_current = np.roll(self.array_current, shift=int(shift), axis=0)
        self.array_dropped[self.array_current > 0] = self.array_current[self.array_current > 0]
        self.update()

        # Create a list of indices of the cleared rows.
        cleared_rows = np.argwhere(np.all(self.array_dropped > 0, axis=1))
        cleared_increment = len(cleared_rows)
        if cleared_increment > 0:
            # Clear lines and add the same number of empty rows at the top.
            self.array_dropped = np.concatenate((
                np.zeros([cleared_increment,self.column_count]),
                np.delete(self.array_dropped, obj=cleared_rows, axis=0)
                ), axis=0)
        self.cleared_count += cleared_increment

        # Reset the ghost flag if needed.
        if self.flag_ghost:
            self.flag_ghost = False

    # Update the displayed array.
    def update(self):
        self.array_display = np.maximum(self.array_current, self.array_dropped)

    # Increase the probability of getting an advanced tetrimino.
    def increase_chance_advanced(self):
        if self.weight_advanced < self.weight_max_advanced:
            self.weight_advanced = round(self.weight_advanced + self.weight_increment_advanced, 3)
            self.weight_classic = round(1 - self.weight_advanced, 3)
        # Increase the block fall speed.
        pass
        print('increased chance advanced: ', self.weight_advanced)
    
    # Increase the probability of getting a special effect.
    def increase_chance_special(self):
        if self.weight_special < self.weight_max_special:
            self.weight_special = round(self.weight_special + self.weight_increment_special, 3)
        print('increased chance special: ', self.weight_special)
    
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

# Set the width and height of the window.
size_window = [game.column_count*game.width+(game.column_count+1)*game.margin, game.row_count*game.height+(game.row_count+1)*game.margin]
screen = pygame.display.set_mode(size_window)
pygame.display.set_caption('Tetron')

# Loop until the window is closed.
done = False
while not done:
    # Calculate the current time and elapsed time.
    game.time_current = pygame.time.get_ticks()
    if game.flag_playing:
        game.time_elasped = pygame.time.get_ticks() - game.time_start

    # =============================================================================
    # Key Presses/Releases And Other Events.
    # =============================================================================
    for event in pygame.event.get():
        game.id_previous = game.id_current + 0
        # Window is exited.
        if event.type == pygame.QUIT:
            done = True
        # Key presses.
        elif event.type == pygame.KEYDOWN:
            # Start the game.
            if event.key == pygame.K_SPACE and game.flag_playing is False:
                # Save the start time.
                game.time_start = pygame.time.get_ticks()
                # Reset the timers.
                pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)
                pygame.time.set_timer(pygame.USEREVENT+2, game.time_increase_difficulty)
                # Reset the arrays.
                game.array_current[:] = 0
                game.array_dropped[:] = 0
                game.array_display[:] = 0
                # Set flags.
                game.flag_playing = True
                game.flag_dropping_soft = False
                game.flag_ghost = False
                # Create a new tetrimino.
                game.create_new()
                # Start playing music.
                # self.music.play()
            # Shift current tetrimino left one column.
            elif event.key == pygame.K_a and game.flag_playing is True:
                game.shift_left()
                # Record the current time used later to calculate how long this key is held.
                game.time_start_shift_left = game.time_current + 0
                # Initialize the time at which the previous repeat occured.
                game.time_previous_shift_left = 0
            # Shift current tetrimino right one column.
            elif event.key == pygame.K_d and game.flag_playing is True:
                game.shift_right()
                # Record the current time used later to calculate how long this key is held.
                game.time_start_shift_right = game.time_current + 0
                # Initialize the time at which the previous repeat occured.
                game.time_previous_shift_right = 0
            # Rotate current tetrimino clockwise or counterclockwise.
            elif (event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT) and game.flag_playing is True:
                rows_occupied_before = np.sum(np.any(game.tetrimino > 0, axis=1))
                columns_occupied_before = np.sum(np.any(game.tetrimino > 0, axis=0))
                if event.key == pygame.K_RIGHT:
                    game.tetrimino = np.rot90(game.tetrimino, k=-1)
                elif event.key == pygame.K_LEFT:
                    game.tetrimino = np.rot90(game.tetrimino, k=1)
                rows_occupied_after = np.sum(np.any(game.tetrimino > 0, axis=1))
                columns_occupied_after = np.sum(np.any(game.tetrimino > 0, axis=0))
                # Determine if the rotated tetrimino intersects already placed blocks.
                indices_rows, indices_columns = np.nonzero(game.array_current > 0)
                is_intersecting = np.any(game.array_dropped[game.array_current != 0][game.tetrimino.flatten()>0] > 0)
                if not is_intersecting:
                    # Shift the tetrimino one block right or left if rotation causes it to exceed the left and right walls.
                    if columns_occupied_after > columns_occupied_before:
                        if np.any(game.array_current[:, 0] > 0):
                            game.array_current = np.roll(game.array_current, shift=1, axis=1)
                        elif np.any(game.array_current[:, -1] > 0):
                            game.array_current = np.roll(game.array_current, shift=-1, axis=1)
                    # Shift the tetrimino one block up or down if rotation causes it to exceed the top and bottom walls.
                    if rows_occupied_after > rows_occupied_before:
                        if np.any(game.array_current[0, :] > 0):
                            game.array_current = np.roll(game.array_current, shift=1, axis=0)
                        elif np.any(game.array_current[-1, :] > 0):
                            game.array_current = np.roll(game.array_current, shift=-1, axis=0)
                    # Insert the rotated tetrimino into the array.
                    game.array_current[game.array_current != 0] = game.tetrimino.flatten()
                # Update the displayed array.
                game.update()
            # Hard drop.
            elif event.key == pygame.K_w and game.flag_playing is True:
                game.drop_hard()
                # End the game if the top row is occupied.
                if np.any(game.array_dropped[0, :] > 0):
                    game.flag_playing = False
                # Create a new tetrimino otherwise.
                else:
                    game.create_new()
            # Start soft dropping.
            elif event.key == pygame.K_s and game.flag_playing is True:
                game.advance()
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
            # Stop soft dropping.
            if event.key == pygame.K_s and game.flag_playing is True:
                # Set flags.
                game.flag_dropping_soft = False
                # Start the advance timer.
                pygame.time.set_timer(pygame.USEREVENT+1, game.speed_fall)
                # game.set_timer_advance(True)
        # Custom event for advancing one line.
        elif event.type == pygame.USEREVENT+1 and game.flag_playing:
            game.advance()
        # Custom event for increasing the difficulty of the game.
        elif event.type == pygame.USEREVENT+2 and game.flag_playing:
            game.increase_chance_advanced()
            if game.time_elapsed > game.delay_increment_special:
                game.increase_chance_special()
    
    # =============================================================================
    # Keys Held Continuously.
    # =============================================================================
    # Get a list of the keys currently being held down.
    keys_pressed = pygame.key.get_pressed()
    # Soft drop.
    if keys_pressed[pygame.K_s]:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_drop_soft) > game.delay_drop_soft:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_drop_soft) > game.speed_drop_soft:
                game.advance()
                game.time_previous_drop_soft = game.time_current + 0
    # Shift left.
    if keys_pressed[pygame.K_a]:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_shift_left) > game.delay_shift:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_shift_left) > game.speed_shift:
                game.shift_left()
                game.time_previous_shift_left = game.time_current + 0
    # Shift right.
    if keys_pressed[pygame.K_d]:
        # Check if the key has been held longer than the required initial delay.
        if (game.time_current - game.time_start_shift_right) > game.delay_shift:
            # Check if the key has been held longer than the key repeat interval.
            if (game.time_current - game.time_previous_shift_right) > game.speed_shift:
                game.shift_right()
                game.time_previous_shift_right = game.time_current + 0
    
    # =============================================================================
    # Draw Screen.
    # =============================================================================
    # Set the background color before drawing the blocks.
    screen.fill(rgb(0))
    # Draw the screen.
    for row in range(game.row_count):
        for column in range(game.column_count):
            number = game.array_display[row, column]
            if number != 0:
                if game.flag_blind:
                    color = 0.3
                else:
                    color = game.convert_tetrimino_id(number)
            else:
                color = 0.25
            pygame.draw.rect(surface=screen, color=rgb(color), rect=[(game.margin+game.width)*column+game.margin, (game.margin+game.height)*row+game.margin, game.width, game.height])
    # Stop the rotation effect if it has lasted longer than the maximum duration.
    if game.flag_rotate:
        if game.duration_rotate > game.duration_max_rotate:
            game.flag_rotate = False
            game.duration_rotate = 0
        else:
            game.duration_rotate += 1000/game.fps
        # Rotate the screen.
        screen.blit(pygame.transform.rotate(screen, 180), (0,0))
    # Stop the blind effect if it has lasted longer than the maximum duration.
    if game.flag_blind:
        if game.duration_blind > game.duration_max_blind:
            game.flag_blind = False
            game.duration_blind = 0
        else:
            game.duration_blind += 1000/game.fps
    # Update the screen.
    pygame.display.flip()

    # Limit the game to 60 frames per second by delaying every iteration of this loop.
    game.clock.tick(game.fps)
 
# Close the window and quit.
pygame.quit()