helptext  = '''
Running this command will generate a subfolder containing 64 .aiff files, 
each one of them relating to one of the main colors found in the image you 
supplied as argument. In addition, there will be one .ck file to be used 
with ChucK and freely modified, as well as the .csv files used to generate 
sound synthesis parameters and one .html document containing reference to 
colors, their occurences in the image and RGB code associations with .aiff 
filenames.

The duration of each sound sample is based upon how many times a color 
occurs in the image. Each sound consists of three partials, each one with 
its frequency controlled by X (red/high wavelength), Y (green/medium 
wavelength) and Z (blue/low wavelength) components of the referred color. 
Amplitude of each of these partial waves is controled by x, y and z 
proportional energies for each wavelength group.

This software is free and opensource, and is alive thanks to Linux, Python, 
ImageMagick and ChucK.
'''

cleanup = '''
Cleaning up temporary files and moving things to their right places...
'''

creaiff = '''
Creating .aiff files. It can take a while...
'''

crechuck = '''
Creating a .ck file for good ol' ChucK...
'''

crehtml = '''
Generating html reference for color data and corresponding sound files...
'''

crexyz = '''
Generating XYZ and xyz color data for image...
'''

welcome = '''
Welcome to Pictophon 1.0 beta!

- * - * -

Software created by Jean Menezes da Rocha (jean.rudess AT gmail DOT com)
This version was released May 4th, 2011

- * - * -
'''
