# f360-plategen
Keyboard plate generator for Fusion 360

Disclaimer: This tool is mainly made for my personal use, so doublecheck measurements (especially stabilizer related) before ordering a plate.

## TO-DO
* Flipped stabilizers  (_rs:180)
* Outline
  * Box currently only supports layouts without rotated keys
  * Around clusters does nothing for now, but should in the future wrap separate key cluster with individual outlines 

## Installation
### Windows
Save files from repository to: `C:\Users\[username]\AppData\Roaming\Autodesk\Autodesk Fusion 360\API\AddIns\PlateGen`.

Appdata\Roaming folder can be accessed with command `%appdata%`.

[How to install an add-in or script in Fusion 360](https://knowledge.autodesk.com/support/fusion-360/troubleshooting/caas/sfdcarticles/sfdcarticles/How-to-install-an-ADD-IN-and-Script-in-Fusion-360.html)

## Changes
* [2021-11-12]
  * Add option for custom switch spacing
  * Add option for custom switch cutout sizes
* [2021-05-29]
  * Removed smaller mx stabilizer cutout
  * Changed width of large mx stabilizer cutout from 7mm to 7.5mm for better clearance with durock stabilizers