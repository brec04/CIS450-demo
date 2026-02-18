# CIS450-demo

## Introduction
This repo illustrates best practice README file generation.

## Projects
Open-CV image processing demos.

## Resources

<img src="./assets/opencv-logo-black.png" alt="OpenCV Logo" width="100"/>

[Open-CV](https://opencv.org/)

## Edge Detection
Edge detection works on an image by detecting pixel intensity changes with specific algorithms. Image blending combines more than one image and allows for a smooth transition.

## Using Github Copilot Chat
### Call Sequence: plt.plot -> gca().plot -> Axes.plot -> add_line

- `plt.plot` - calls for gca().plot and returns a list of Line2D objects
- `gca().plot` - gets current axes, and if there is none, it creates one automatically
- `Axes.plot` - this step processes keyword args and packages everything into a Line2D object
- `add_line` - after the Line2D object is made, the lines are registered so they will render