# Sphero-Control-Gui
A GUI written in Python and Tkinter to control Sphero robot toys with your keyboard or controller.

This is mostly AI-Generated code, but it works pretty well.

This is developed mainly for the Steam Deck, so the 16:10 aspect ratio fits the screen well.

## Modes

Normal Mode - Uses speed and heading APIs to provide a smooth and stable experience comparible to Sphero Edu App.

FPV Mode - Uses raw motor commands directly from your inputs - You're in control.

# Installation
## Clone the repo
```bash
git clone https://github.com/AeEn123/Sphero-Control-Gui
```

## Activate Python venv (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate # Linux, check documentation for other operating systems
```

## Install requirements (Required)
```bash
pip install -r requirements.txt
```

# Running
```bash
python3 main.py
```

## You can also use start.sh to automatically run it inside the venv
```bash
./start.sh
```
On steam deck you can right-click start.sh and add it to steam. This makes it easy to launch within gaming mode.
