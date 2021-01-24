#!/usr/bin/python
# -*- coding: latin-1 -*-


import getopt  # Needed to parse command line arguments.
import os
import random
import sys
import time

import numpy as np
import pygame
pygame.init()


# Resources.
# Template started with: http://programarcadegames.com/index.php?lang=en&chapter=array_backed_grids
# Keyboard codes: https://www.pygame.org/docs/ref/key.html#pygame.key.key_code


# =============================================================================
# Functions
# =============================================================================
# Return a string with RGB values used for setting colors. Pass a number between 0 and 1 for grayscale colors, or pass a string corresponding to a specific color.
def rgb(color=None, tint=0):
    # Select the default blank color if 'color' is None.
    if color is None:
        color = 0.25
    
    # Set a predefined color if 'color' is a string.
    if isinstance(color, str):
        if color == 'I' or color == 'I+':  # Cyan
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

def convert_tetrimino_id(number_or_str):
    id_pairs = [
        (1, 'I'), (2, 'J'), (3, 'L'), (4, 'O'), (5, 'S'), (6, 'T'), (7, 'Z'),
        (10, 'I+'), (20, 'J+'), (30, 'L+'), (40, 'O+'), (50, 'S+'), (60, 'T+'), (70, 'Z+'), (101, '.'), (102, ':'), (103, '*')]
    if isinstance(number_or_str, str):
        output = [pair[0] for pair in id_pairs if pair[-1] == number_or_str]
    else:
        output = [pair[-1] for pair in id_pairs if pair[0] == number_or_str]
    return output[0]

# Return a randomly generated tetrimino by inputting probabilities for the categories.
def random_tetrimino(weight_classic, weight_advanced, id_previous):
    # Randomly select which category to choose from.
    category = random.choice([1]*weight_classic + [2]*weight_advanced)
    if category == 1:
        category = 'classic'
    elif category == 2:
        category = 'advanced'
    # category = random.choices(['classic', 'advanced'], [weight_classic, weight_advanced])  # Available in Python 3 only

    # Define the IDs for classic and advanced tetriminos.
    id_classic = [1, 2, 3, 4, 5, 6, 7]
    id_advanced = [10, 20, 30, 40, 50, 60, 70, 101, 102, 103]
    if category == 'classic':
        id = random.choice([id for id in id_classic if id != id_previous])
    elif category == 'advanced':
        id = random.choice([id for id in id_advanced if id != id_previous])
    return id

# Replace the current tetrimino array with a new tetrimino.
def create_new(id, current):
    # # If no input given, generate a random tetrimino.
    # if id is None:
    #     id = random.randint(1, 7)
    
    # Classic tetriminos.
    if id == 1:  # 'I'
        tetrimino = id * np.ones([4, 4])
        tetrimino[[0,2,3],:] = -1
    elif id == 2:  # 'J'
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 1:] = -1
        tetrimino[2, :] = -1
    elif id == 3:  # 'L'
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 0:2] = -1
        tetrimino[2, :] = -1
    elif id == 4:  # 'O'
        tetrimino = id * np.ones([2, 2])
    elif id == 5:  # 'S'
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 0] = -1
        tetrimino[1, 2] = -1
        tetrimino[2, :] = -1
    elif id == 6:  # 'T'
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 0] = -1
        tetrimino[0, 2] = -1
        tetrimino[2, :] = -1
    elif id == 7:  # 'Z'
        tetrimino = id * np.ones([3, 3])
        tetrimino[1, 0] = -1
        tetrimino[0, 2] = -1
        tetrimino[2, :] = -1
    # Advanced tetriminos.
    elif id == 10:
        tetrimino = id * np.ones([4, 4])
        tetrimino[[0,3], :] = -1
    elif id == 20:
        tetrimino = id * np.ones([3, 3])
        tetrimino[0:2, 0:2] = -1
    elif id == 30:
        tetrimino = id * np.ones([3, 3])
        tetrimino[1:, 1:] = -1
    elif id == 40:
        tetrimino = id * np.ones([3, 3])
        tetrimino[1, 1] = -1
    elif id == 50:
        tetrimino = id * np.ones([3, 3])
        tetrimino[:2, 0] = -1
        tetrimino[1:, 2] = -1
    elif id == 60:
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 0] = -1
        tetrimino[0, 2] = -1
        tetrimino[2, 0] = -1
        tetrimino[2, 2] = -1
    elif id == 70:
        tetrimino = id * np.ones([3, 3])
        tetrimino[0, 1:] = -1
        tetrimino[2, :2] = -1
    elif id == 101:  # .
        tetrimino = id * np.ones([1, 1])
    elif id == 102:  # :
        tetrimino = -1 * np.ones([3, 3])
        tetrimino[[0,2], 1] = id
    elif id == 103:  # Random 3x3
        shape = [3, 3]
        tetrimino = -1 * np.ones(shape)
        random_indices = random.sample(range(tetrimino.size), 5)
        tetrimino[np.unravel_index(random_indices, shape)] = id

    # Clear the current tetrimino array.
    current[:] = 0
    # Update the array of the current tetrimino.
    row_left = int((current.shape[1]-tetrimino.shape[1])/2)
    current[0:tetrimino.shape[0], row_left:row_left+tetrimino.shape[1]] = tetrimino
    return current, tetrimino

# Return arrays after hard dropping the current tetrimino.
def drop_hard(current, dropped, display):
    # Reset the timer.
    pygame.time.set_timer(pygame.USEREVENT, 0)
    pygame.time.set_timer(pygame.USEREVENT, int(1000 / speed_fall))

    # List of Booleans indicating which columns of the matrix contain blocks from the current tetrimino.
    columns = np.any(current > 0, axis=0)
    rows = np.any(current > 0, axis=1)
    
    # List of indices, counting from bottom (0 = bottom row), of the bottommost blocks of the current tetrimino.
    indices_current = (current.shape[0]-1) - np.argmax(np.flipud(current > 0), axis=0)[columns]
    # List of indices of highest available positions in current tetrimino's columns.
    indices_placed = np.where(np.any(dropped > 0, axis=0), np.argmax(dropped > 0, axis=0)-1, (dropped.shape[0]-1)*np.ones(dropped.shape[1]))
    indices_placed = indices_placed[columns]

    # Shift the current tetrimino down.
    shift = np.min(indices_placed - indices_current)
    if shift > 0:
        current = np.roll(current, shift=int(shift), axis=0)
    dropped[current > 0] = current[current > 0]
    display = dropped + 0
    
    # Create a list of indices of the cleared rows.
    cleared_rows = np.argwhere(np.all(dropped > 0, axis=1))
    cleared_count = len(cleared_rows)
    if cleared_count > 0:
        # Clear lines and add the same number of empty rows at the top.
        dropped = np.concatenate((
            np.zeros([cleared_count,column_count]),
            np.delete(dropped, obj=cleared_rows, axis=0)
            ), axis=0)

    return current, dropped, display, cleared_count



# =============================================================================
# Settings.
# =============================================================================
# Set the width, height, and margin of the blocks.
width = 20
height = 20
margin = 1

# Define the number of rows and columns of the matrix.
row_count = 20
column_count = 10

# Set the width and height of the window.
size_window = (column_count*width+(column_count+1)*margin, row_count*height+(row_count+1)*margin)
screen = pygame.display.set_mode(size_window)
pygame.display.set_caption('Tetron')

# Create a clock that manages how fast the screen updates.
clock = pygame.time.Clock()
# Define the frames per second of the game.
fps = 60


# =============================================================================
# Main Program Loop
# =============================================================================
# Initialize arrays for current tetrimino's position, dropped blocks, and displayed blocks.
array_current = np.zeros([row_count, column_count])
array_dropped = np.zeros([row_count, column_count])
array_display = np.zeros([row_count, column_count])

# Initialize the block fall speed, in lines/second.
speed_fall = 1
# Define the maximum block fall speed, in lines/second.
speed_limit_fall = fps + 0
# Define the increment by which the block fall speed is increased, in lines/second.
speed_increment = 0.5
# Define the duraction of time before each difficulty increase, in seconds.
time_increase_difficulty = 30

# Initialize the cleared lines counter.
cleared_count = 0
# Initialize the relative probabilities for tetrimino categories.
weight_classic, weight_advanced = 10, 0
# Initialize the previous tetrimino ID.
id_current = 0
id_previous = 0

# Initialize flags indicating statuses of the game.
flag_playing = False

# Create a timer that causes advances the current tetrimino down one line.
pygame.time.set_timer(pygame.USEREVENT, int(1000 / speed_fall))
# Create a timer that increases the difficulty of the game.
pygame.time.set_timer(pygame.USEREVENT+1, time_increase_difficulty*1000)

# Loop until the window is closed.
done = False

while not done:
    # Main event loop.
    for event in pygame.event.get():
        id_previous = id_current + 0
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.KEYDOWN:
            # Begin the game.
            if event.key == pygame.K_RETURN and flag_playing is False:
                # Reset the arrays.
                array_current[:] = 0
                array_dropped[:] = 0
                array_display[:] = 0
                # Set the playing flag.
                flag_playing = True
                # Create the array for the tetrimino.
                id_current = random_tetrimino(weight_classic, weight_advanced, id_previous)
                array_current, tetrimino = create_new(id=id_current, current=array_current)
                # Update the displayed array.
                array_display = np.maximum(array_current, array_dropped)
            # Move current tetrimino left one column.
            elif event.key == pygame.K_a and flag_playing is True:
                # Check if already in leftmost column.
                if not np.any(array_current[:, 0] > 0):
                    # Check if placed blocks are in the way.
                    indices_rows, indices_columns = np.nonzero(array_current > 0)
                    if not np.any(array_dropped[indices_rows, indices_columns-1] > 0):
                        array_current = np.roll(array_current, shift=-1, axis=1)
                        array_display = np.maximum(array_current, array_dropped)
            # Move current tetrimino right one column.
            elif event.key == pygame.K_d and flag_playing is True:
                # Check if already in rightmost column.
                if not np.any(array_current[:, -1] > 0):
                    # Check if placed blocks are in the way.
                    indices_rows, indices_columns = np.nonzero(array_current > 0)
                    if not np.any(array_dropped[indices_rows, indices_columns+1] > 0):
                        array_current = np.roll(array_current, shift=1, axis=1)
                        array_display = np.maximum(array_current, array_dropped)
            # Rotate current tetrimino clockwise or counterclockwise.
            elif (event.key == pygame.K_RIGHT or event.key == pygame.K_LEFT) and flag_playing is True:
                rows_occupied_before = np.sum(np.any(tetrimino > 0, axis=1))
                columns_occupied_before = np.sum(np.any(tetrimino > 0, axis=0))
                if event.key == pygame.K_RIGHT:
                    tetrimino = np.rot90(tetrimino, k=-1)
                elif event.key == pygame.K_LEFT:
                    tetrimino = np.rot90(tetrimino, k=1)
                rows_occupied_after = np.sum(np.any(tetrimino > 0, axis=1))
                columns_occupied_after = np.sum(np.any(tetrimino > 0, axis=0))
                # Determine if the rotated tetrimino intersects already placed blocks.
                indices_rows, indices_columns = np.nonzero(array_current > 0)
                has_intersection = np.any(array_dropped[array_current != 0][tetrimino.flatten()>0] > 0)
                if not has_intersection:
                    # Shift the tetrimino one block right or left if rotation causes it to exceed the left and right walls.
                    if columns_occupied_after > columns_occupied_before:
                        if np.any(array_current[:, 0] > 0):
                            array_current = np.roll(array_current, shift=1, axis=1)
                        elif np.any(array_current[:, -1] > 0):
                            array_current = np.roll(array_current, shift=-1, axis=1)
                    # Shift the tetrimino one block up or down if rotation causes it to exceed the top and bottom walls.
                    if rows_occupied_after > rows_occupied_before:
                        if np.any(array_current[0, :] > 0):
                            array_current = np.roll(array_current, shift=1, axis=0)
                        elif np.any(array_current[-1, :] > 0):
                            array_current = np.roll(array_current, shift=-1, axis=0)
                    # Insert the rotated tetrimino into the array.
                    array_current[array_current != 0] = tetrimino.flatten()
                # Update the displayed array.
                array_display = np.maximum(array_current, array_dropped)
            # Hard drop the current tetrimino.
            elif event.key == pygame.K_w and flag_playing is True:
                array_current, array_dropped, array_display, cleared_increment = drop_hard(current=array_current, dropped=array_dropped, display=array_display)
                cleared_count += cleared_increment
                # End the game if the top row is occupied.
                if np.any(array_dropped[0, :] > 0):
                    flag_playing = False
                # Create a new tetrimino.
                id_current = random_tetrimino(weight_classic, weight_advanced, id_previous)
                array_current, tetrimino = create_new(id=id_current, current=array_current)
                # Update the displayed array.
                array_display = np.maximum(array_current, array_dropped)
        # Advance the current tetrimino by one line.
        elif event.type == pygame.USEREVENT and flag_playing:
            # Row and column indices of occupied blocks in current array.
            indices_rows, indices_columns = np.nonzero(array_current > 0)
            # Determine if at the bottom of the matrix.
            is_not_at_bottom = not np.any((indices_rows+1) > (array_dropped.shape[0]-1))
            # Determine if advancing a line will intersect already placed blocks.
            try:
                no_intersection = not np.any(array_dropped[indices_rows+1, indices_columns] > 0)
            except IndexError:
                no_intersection = False
            # If not intersecting, advance one line.
            if is_not_at_bottom and no_intersection:
                array_current = np.roll(array_current, shift=1, axis=0)
                array_display = np.maximum(array_current, array_dropped)
            # If intersecting, hard drop the current tetrimino.
            else:
                array_current, array_dropped, array_display, cleared_increment = drop_hard(current=array_current, dropped=array_dropped, display=array_display)
                cleared_count += cleared_increment
                # End the game if the top row is occupied.
                if np.any(array_dropped[0, :] > 0):
                    flag_playing = False
                # Create a new tetrimino.
                if flag_playing:
                    id_current = random_tetrimino(weight_classic, weight_advanced, id_previous)
                    array_current, tetrimino = create_new(id=id_current, current=array_current)
                    # Update the displayed array.
                    array_display = np.maximum(array_current, array_dropped)
        # Increase the difficulty of the game.
        elif event.type == pygame.USEREVENT+1 and flag_playing:
            # Increase the block fall speed.
            # speed_fall += speed_increment

            # Increase the probability of getting an advanced tetrimino.
            weight_advanced += 1
            if weight_classic > 0:
                weight_classic -= 0
    
    # Set the background color. Put this before drawing commands to avoid deleting them.
    screen.fill(rgb(0))
    # Draw the screen.
    for row in range(row_count):
        for column in range(column_count):
            number = array_display[row, column]
            if number != 0:
                color = convert_tetrimino_id(number)
            else:
                color = 0.25
            pygame.draw.rect(surface=screen, color=rgb(color), rect=[(margin+width)*column+margin, (margin+height)*row+margin, width, height])
    # Update the screen.
    pygame.display.flip()

    # Limit the game to 60 frames per second by delaying every iteration of the loop.
    clock.tick(fps)
 
# Close the window and quit.
pygame.quit()