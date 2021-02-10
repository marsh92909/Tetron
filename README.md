# Tetron
Tetris with a twist.

## Gameplay
Tetron features advanced blocks and special effects in addition to the seven blocks in Tetris. Win the game by reaching a score of 1,000.

### Controls
| Action | Key |
| :-- | --: |
| Move Left | ← |
| Move Right | → |
| Rotate Clockwise | ↑ or X |
| Rotate Counterclockwise | Z |
| Hard Drop | Space |
| Soft Drop | ↓ |
| Hold | C |
| Start Game | Enter |
| Stop Game | Escape |

### Advanced blocks
* Variations of the I block: I+, I-
* Variations of the J block: J+, J-
* Variations of the L block: L+, L-
* Variations of the O block: O+, O++, O ring
* Variations of the S block: S+
* Variations of the T block: T+1, T+2
* Variations of the Z block: Z+
* Freebie block
* Randomly generated block with 5 blocks
* Period block
* Comma block
* Colon block
* Quotation block

### Special effects
* Ghost block: A block that passes through other blocks and through the walls. If hard dropped, a ghost block is locked in-place instead of dropping down.
* Heavy block: A block that drops to the very bottom instead of stacking on top of other blocks.
* Disoriented: The entire matrix is rotated.
* Blind: The colors of all blocks become almost identical to the background, making them harder to see.

### Game modes
| Mode | Press to Start |
| :-- | --: |
| Tetron | Enter |

## Installation
1. Click on the most recent release found [here](https://github.com/marsh92909/Tetron/releases).
2. Click on the `Tetron.zip` file to download it.
3. Unzip the file and place the Tetron folder anywhere. Do not move, modify, or delete any file in this folder, including the `.exe` file, or the program may not open.
4. Open the Tetron folder and create a shortcut of the `.exe` file. Move the shortcut to the desktop for convenience.

## Compilation
Using PyInstaller 4.2 and Python 3.9.1 on Windows 10.

### Compile a folder with existing `.spec` file
If a `.spec` file already exists and has the correct information:
1. Open Command Prompt and set the current directory to the folder where the `.py` file is: `cd Desktop\Tetron`.
2. Enter `pyinstaller tetron.spec` to compile the folder.
3. Open the `dist` folder to find the compiled folder containing the `.exe` file and other files.
4. Zip the folder and distribute.

### Create a `.spec` file
If a `.spec` file does not exist, create it first:
1. Open Command Prompt and set the current directory to the folder where the `.py` file is: `cd Desktop\Tetron`.
2. Create a `.spec` file by entering `pyi-makespec --windowed --name Tetron tetron.py`. The file will appear in the current directory.
3. Open the `.spec` file to add additional information:
   1. The `datas` argument to `Analysis` contains the files to be included in the compiled folder. It is a list of tuples in which each tuple represents a file and contains two strings. The first string is the path to the file to be included. To include all of a type of file, use an asterisk in place of the file name: `'C:\\Users\\...\\Tetron\\*.mp3'`. The second string is the path to the folder, relative to the compiled folder, in which the file will be placed during compilation. To place a file directly in the compiled folder, use `'.'`. To place a file in a folder within the compiled folder, use `'.\\<folder name>'`.
   2. The `icon` argument to `EXE` is a string of the file name of the icon file: `'icon.ico'`.

## Credits
### Programming
* [Script template](http://programarcadegames.com/index.php?lang=en&chapter=array_backed_grids)
* [Tetris scoring guidlines](https://tetris.wiki/Scoring#Recent_guideline_compatible_games)
### Sound Effects
* [All Tetris 99 sound effects](https://www.sounds-resource.com/nintendo_switch/tetris99/sound/19376/)
* [https://wiki.teamfortress.com/w/images/4/46/Spy_taunts05.wav](https://wiki.teamfortress.com/w/images/4/46/Spy_taunts05.wav)
* [https://www.youtube.com/watch?v=40qZmV_1E6c&ab_channel=BestGamingSoundEffects](https://www.youtube.com/watch?v=40qZmV_1E6c&ab_channel=BestGamingSoundEffects)
* [http://www.soundgator.com/audios/571/man-saying-hmm-03-sound-effect](http://www.soundgator.com/audios/571/man-saying-hmm-03-sound-effect)
* [https://www.mediafire.com/file/lqow4b8y6rw894b](https://www.mediafire.com/file/lqow4b8y6rw894b)
* [https://www.audioatrocities.com/games/michigan/clip20.mp3](https://www.audioatrocities.com/games/michigan/clip20.mp3), found on [https://www.audioatrocities.com/games/michigan/index.html](https://www.audioatrocities.com/games/michigan/index.html)
