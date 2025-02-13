# VIT-GPA-Calculator
[![Build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/VIT-GPA-Calculator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/yourusername/VIT-GPA-Calculator)](https://github.com/yourusername/VIT-GPA-Calculator/issues)

A Python application that extracts course grade data from a PDF file, calculates your current CGPA, and allows you to simulate grade improvements.

## Table of Contents

- [Features](#features)
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

## Requirements

- Python 3.7 or above
- [Camelot](https://camelot-py.readthedocs.io/en/master/) (requires dependencies such as Ghostscript)
- [Pandas](https://pandas.pydata.org/)

## Setup

1. **Clone the repository**

   ```sh
   git clone https://github.com/yourusername/VIT-GPA-Calculator.git
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

Camelot requires Ghostscript. Please install it from Ghostscript Downloads.

## Usage
- Run the application:

- When prompted, enter the full path to your PDF grade history file.

- Follow the on-screen instructions to view your current grade analysis or simulate grade improvements.


## Contributing
Contributions are welcome! Please fork this repository and submit pull requests.

## License
This project is licensed under the MIT License.
 