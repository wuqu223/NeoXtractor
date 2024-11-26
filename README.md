# NeoXtractor
 NeoX NXPK / EXPK (.npk) extraction and viewer tool GUI - NeoX engine made by NetEase

THIS TOOL IS IN ITS EARLY STAGES, ANY HELP IS WELCOME! FEEL FREE TO OPEN A PULL REQUEST OR FORK THE REPOSITORY IF YOU WISH TO ADD SOMETHING OR FIX ANY ISSUE YOU SPOT

## Setup
```
pip install -r requirements.txt
```

## Usage

### Steps before use
1. Make sure you have installed the correct requirements with the command above
2. Open the program with the command
```
python main.py
```
3. Set the XOR Key (if necessary) by pressing File -> Decryption Key
    - If you dont know which key to use, check in the official Discord for the tool! (Only some games need this key)
 
### Basic Usage
To start using the tool, open it by using the command above, once its open, you will see two screens, the "Main" window and the "Mesh" window.

This is the main Window:
![Main Window](https://github.com/user-attachments/assets/02b85303-6ebe-4016-9a6b-cc789ba90987)

To open a file, press File -> Open File and select your NPK. Make sure to have input the correct Decryption Key as explained in step 3!

Once the file opens, you will see a list of files which are inside of this NPK, these files are just representations, the files have not been loaded yet! 

![Unloaded files](https://github.com/user-attachments/assets/8eaf3272-a859-47a9-9b1f-726b8ae15085)

To load them, you have to select them by clicking them, they will turn from red to green after being selected, indicating that they have loaded correctly.

![Loaded files](https://github.com/user-attachments/assets/e47e91a7-23b7-4f5b-a865-c770a972b245)

You can also use the "Read all files" button to speed up the process, but be warned, this can take a very long time depending on how many files there are inside the NPK file!

After having been loaded, the files will be added an extension if they already didnt have one, which helps to identify what type of file they are (If they are NXFN this extension is already added).

Use your left-click to open the context menu on a file, and you will be presented with options you can choose from.

**Show Data**<br>
Shows you all of the properties from the file selected, such as its starting offset in the NPK file as well as its current length and its original pre-compressed length, its compiled CRC hash and its FILESIGN property.

![Show Data example](https://github.com/user-attachments/assets/5cb63480-d35e-40d5-b5f8-4f10f78c67ff)

**Export File**<br>
Exports the selected file into the folder `/out/NPKNAME.npk/FILE.EXTENSION` as raw directly extracted from the NPK (it won't do any conversion *yet*), you can use this to export PNGs, TGAs, plaintext files or anything else.

**Hex Viewer**<br>
Opens a *(very basic for now)* hexadecimal viewer where you can check for strings or read binary data straight from the file, useful if youre searching for a specific model or browsing through PYC files.

![Hex Viewer in action](https://github.com/user-attachments/assets/34b53d1e-b379-4b5d-b58a-e14c7ffbbf80)

**Plaintext Viewer**<br>
Opens a text viewer to see files that contain text, such as NeoXML files or CSV files, its very rudimentary for now but its capable of loading the files from memory and displaying them which makes it very efficient.

![Plaintext Viewer in action](https://github.com/user-attachments/assets/ef9f15dd-1c4f-4683-b826-0a4aa4237f1d)

**Texture Viewer**<br>
Converts KTX, DDS and PVR files into PNGs (output.png) that later get loaded into the Texture Viewer, it currently just displays textures!

![Texture Viewer in action](https://github.com/user-attachments/assets/733a33ce-dd9c-42c6-80a3-38cc15a6981f)

**Mesh Viewer**<br>
Capable of opening `.mesh` with and without bones, it has an OpenGL viewer that loads the model directly. In the "View" tab, you can change how you see the mesh (Show Bones, Wireframe Mode and Show Normals), in the "Save" tab, you can select with what format you want to save your mesh, available options are: OBJ, SMD, ASCII, PMX and IQE (glTF is coming soon). 

![Mesh Viewer in action](https://github.com/user-attachments/assets/dba83f60-cf73-4ede-81a2-e0584d6d8402)

## Roadmap

- [x] Search bar (coming in the next update)
- [] UI Improvements (WIP)
- [] glTF conversion
- [x] Whole NPK extraction
- [] Editing NPK files
- [] Implementing repacking
- [] Standardized / Persistent configuration
- [] Parsing RAWANIM files
- More things to come...

## Extra information

Please join the [Discord](https://discord.gg/eedXVqzmfn) server if you wish to contribute or learn about the tool!<br>
UI designed mostly by KingJulz
