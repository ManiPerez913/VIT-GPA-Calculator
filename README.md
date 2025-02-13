# VIT-GPA-Calculator


###########################################################################
#                                                                         #
#                                                                         #
#   ___      ___ ___  _________        ________  ________  ________       #
#  |\  \    /  /|\  \|\___   ___\     |\   ____\|\   __  \|\   __  \      #
#  \ \  \  /  / | \  \|___ \  \_|     \ \  \___|\ \  \|\  \ \  \|\  \     #
#   \ \  \/  / / \ \  \   \ \  \       \ \  \  __\ \   ____\ \   __  \    #
#    \ \    / /   \ \  \   \ \  \       \ \  \|\  \ \  \___|\ \  \ \  \   #
#     \ \__/ /     \ \__\   \ \__\       \ \_______\ \__\    \ \__\ \__\  #
#      \|__|/       \|__|    \|__|        \|_______|\|__|     \|__|\|__|  #
#                                                                         #
#                                                                         #
###########################################################################


[![Build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/VIT-GPA-Calculator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/Kaos599/VIT-GPA-Calculator)](https://github.com/Kaos599/VIT-GPA-Calculator/issues)

A Python application that extracts course grade data from a PDF file, calculates your current CGPA, and allows you to simulate grade improvements.

## Table of Contents

- [Features](#features)
- [Versions](#versions)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

VIT-GPA-Calculator is a Python application that extracts course grade data from a PDF file, calculates your current CGPA, and allows you to simulate grade improvements. It uses the [Camelot](https://camelot-py.readthedocs.io/en/master/) library to parse tables from PDFs and [Pandas](https://pandas.pydata.org/) for data manipulation.

## Features

- Extracts table data from PDF files using Camelot.
- Cleans and processes data to extract course codes, course titles, credits, grades, and dates.
- Calculates current CGPA excluding courses with grade 'P'.
- Displays a detailed analysis of grade distribution and courses by grade.
- Simulates grade improvements and calculates potential new CGPA.
- Enhanced user interface with Rich library for better visualization (in `main_advanced.py`).

## Versions

This project includes two versions of the main application:

1. **`main.py`**: A basic version of the GPA calculator with console output.
2. **`main_advanced.py`**: An advanced version with a richer user interface using the Rich library for better visualization.

## Requirements

- Python 3.7 or above
- [Camelot](https://camelot-py.readthedocs.io/en/master/) (requires dependencies such as Ghostscript)
- [Pandas](https://pandas.pydata.org/)
- [Rich](https://rich.readthedocs.io/en/stable/)

## Setup

1. **Clone the repository**

   ```sh
   git clone https://github.com/Kaos599/VIT-GPA-Calculator.git
   cd VIT-GPA-Calculator
   ```
2. **Install dependencies**

It's recommended to use a virtual environment. For example, using venv:
 ```sh
 python -m venv venv
 source venv/bin/activate   # On Windows use: venv\Scripts\activate
 pip install -r requirements.txt
```
3. **Install Ghostscript**

Camelot requires Ghostscript. Please install it from [Ghostscript Downloads.](https://ghostscript.com/releases/gsdnld.html)

## Usage

- Download your Grade History PDF from VTOP.

- Run the application:
  - For the basic version:
    ```sh
    python main.py
    ```
  - For the advanced version:
    ```sh
    python main_advanced.py
    ```

- When prompted, enter the full path to your PDF grade history file.

- Follow the on-screen instructions to view your current grade analysis or simulate grade improvements.


## Contributing
Contributions are welcome! Please fork this repository and submit pull requests.

## License
This project is licensed under the MIT License.
 
