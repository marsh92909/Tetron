# Tetron
Tetris with a twist.

## Gameplay
Tetron has the same blocks in Tetris but also features advanced blocks and special effects, which occur more frequently as the game progresses.

### Advanced blocks
* I block variations: I+, I-
* J block variations: J+, J-
* L block variations: L+, L-
* O block variations: O+, O++, O ring
* S block variations: S+
* T block variations: T+1, T+2
* Z block variations: Z+
* Random block
* Period block
* Comma block
* Colon block
* Quotation block
* Freebie block

### Special effects
* Ghost block: The current block passes through other blocks and through the walls. Locks in-place instead of dropping down.
* Heavy block: The current block drops to the very bottom and destroys other blocks in the way instead of stacking.
* Disoriented: The entire matrix is rotated temporarily.
* Blind: Blocks are harder to distinguish from the background temporarily.

### Game modes
* Tetron (press 1): Reach a score of 1,000 to win.
* Twin Tetron (press 2): Play two Tetron games at once.

Toggle classic Tetris (press 0) to disable advanced blocks and special effects.


## Controls
| Action | Key |
| :-- | --: |
| Move Left | ← |
| Move Right | → |
| Rotate Clockwise | ↑ or X |
| Rotate Counterclockwise | Z |
| Hard Drop | Space |
| Soft Drop | ↓ |
| Hold | C |
| Start / Pause Game | Enter |
| Stop Game | Escape |

### Twin Tetron
| Action | Key (Left) | Key (Right) |
| :-- | --: | --: |
| Move Left | A | J |
| Move Right | D | L |
| Rotate Clockwise | W | I |
| Hard Drop (Both) | Space | Space |
| Soft Drop | S | K |
| Swap (Both) | C (or E or U) | C (or E or U) |


## Installation
1. Open the [latest release](https://github.com/marsh92909/Tetron/releases/latest).
2. Click on the `Tetron.exe` file to download it, and place it anywhere.


## Compilation
Using PyInstaller 4.2 and Python 3.9.1 on Windows 10. PyInstaller can compile either a single .exe file or a folder containing an .exe file along with other files. The instructions below are for compiling a single .exe file.

### Set up a .spec file
1. Open Command Prompt and set the current directory to the folder where the main .py file is: `cd Desktop\Tetron`.
2. Create a .spec file by entering in Command Prompt: `pyi-makespec --onefile --windowed --name Tetron --icon icon.ico tetron.py`. The .spec file will appear in the current directory.
   1. To compile a folder instead, change `--onefile` to `--onedir`.
3. Open the .spec file to add additional information:
   1. Delete the path in the list in the `pathex` argument to `Analysis`.
   2. Specify all the files (images, audio, etc.) to be included in the program in the `datas` argument to `Analysis`. This argument is a list of tuples in which each tuple contains two strings. ([Source](https://pyinstaller.readthedocs.io/en/stable/spec-files.html#adding-data-files))
      > 1. The first string specifies the file or files as they are in this system now.
      
      This string can be a relative path relative to the current directory used during compilation. To specify all of a type of file within a folder, use an asterisk in place of the file name: `'<folder name>\\*.wav'`.

      > 2. The second specifies the name of the folder to contain the files at run-time.

      To place a file in the same directory used by the program at run-time, use `'.'`. To place a file in a folder within that directory, use `'.\\<folder name>'`. 

Note: If compiling a folder, the generated .spec file will contain an instance of COLLECT.

### Compile the program with the .spec file
1. Open Command Prompt and set the current directory to the folder where the main .py file is: `cd Desktop\Tetron`.
2. Enter `pyinstaller tetron.spec` to compile the program. PyInstaller will create a `build` and `dist` folder if they do not already exist.
3. Open the `dist` folder to find the compiled program.

Note: A .spec file is not required to compile a program, but it makes compilation easier by shortening the command that is typed in Command Prompt.


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
