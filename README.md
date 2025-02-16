# VIT-GPA-Calculator

<div align="center">
  <img src="https://github.com/user-attachments/assets/7b0788b6-c50f-40e3-9a17-9715ac0c9d89" width="1000">
</div>
<div align="center">
  <img src="https://github.com/user-attachments/assets/0d58ec90-0c43-40ac-94a0-e54da8882196" width="500">
</div>


[![Build](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yourusername/VIT-GPA-Calculator/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Issues](https://img.shields.io/github/issues/Kaos599/VIT-GPA-Calculator)](https://github.com/Kaos599/VIT-GPA-Calculator/issues)

A Python application that extracts course grade data from a PDF file, calculates your current CGPA, and allows you to simulate grade improvements and plan for future courses.

## Screenshots
<div align="center">
  <img src="https://github.com/user-attachments/assets/ab0666d8-438e-4136-92a7-bded9e8a8a28" width="400">
  <img src="https://github.com/user-attachments/assets/345f3393-04da-46e6-bfab-fec3583b5ddc" width="400">
  <img src="https://github.com/user-attachments/assets/dda54b98-e19c-4272-bf59-4ee19ffd1b28" width="400">
  <img src="https://github.com/user-attachments/assets/83eada9c-400f-4445-826c-e3caf85b8f2d" width="400">
</div>


## Table of Contents!

- [Features](#features)
- [Versions](#versions)
- [Requirements](#requirements)
- [Setup](#setup)
- [Usage](#usage)
- [Screenshots](#screenshots)
- [Contributing](#contributing)
- [License](#license)

VIT-GPA-Calculator is a Python application that extracts course grade data from a PDF file (specifically, your VIT grade history), calculates your current CGPA, and provides powerful simulation and planning tools. It uses the [Camelot](https://camelot-py.readthedocs.io/en/master/) library to parse tables from PDFs and [Pandas](https://pandas.pydata.org/) for data manipulation.  The advanced version leverages the [Rich](https://rich.readthedocs.io/en/stable/) library for a visually appealing and interactive command-line interface.

## Features

- **Data Extraction and Cleaning:**
    - Extracts table data from PDF files using Camelot.
    - Cleans and processes data to extract course codes, course titles, credits, grades, and dates (or result declaration dates).
    - Handles variations in PDF formats and automatically detects the header row.
    - Normalizes course titles for accurate duplicate detection.
    - Removes duplicate course entries, keeping the most recent grade.
    - Filters out invalid grades.

- **CGPA Calculation and Analysis:**
    - Calculates current CGPA.
    - Provides a detailed grade distribution analysis (number of credits for each grade).
    - Presents a summary of total courses and current CGPA.
    - Displays courses grouped by grade.

- **Simulations and Planning:**
    - **Grade Improvement Simulation:**
        - Allows simulating the impact of improving grades in specific courses.
        - Converts credits from a lower grade to a higher grade.
        - Calculates and displays the projected CGPA after improvements.
        - Interactive menu to add, view, reset, and finalize improvement changes.
    - **Future Courses Simulation:**
        - Allows adding planned future courses with predicted grades and credits.
        - Calculates and displays the projected CGPA, including future courses.
        - Interactive menu to add, view, reset, and finalize future course additions.
    - **Target CGPA Planning:**
        - Helps plan to reach a desired target CGPA.
        - Two input modes:
            - **Course-by-Course:**  Enter details for individual future courses.
            - **Aggregate Mode:** Enter groups of courses with total credits and descriptions.
        - Calculates the required average grade points per credit to achieve the target.
        - (Course-by-Course Mode) Simulates predicted grades and shows the projected CGPA.
        - (Aggregate Mode) Displays valid grade combinations across course groups that meet or exceed the target CGPA.

- **Visualization:**
    - **Grade History Visualization:**
        - Displays a table showing the cumulative CGPA progression over time.
        - Includes a simple ASCII line graph visualizing the CGPA trend.
    - **Grade Distribution Visualization:**
        - Displays a bar chart of the grade distribution.
        - Options to visualize the original distribution, the distribution after grade improvement simulation, or the distribution after future courses simulation.
    - **ASCII Line Graph Visualization:**
        -  A general-purpose function to display a simple ASCII line graph for any numeric data.

- **User Interface (main_advanced.py):**
    - Enhanced user interface using the Rich library.
    - Interactive menus and prompts for easy navigation.
    - Clear and visually appealing output with tables, panels, and progress bars.
    - Comprehensive instructions and error handling.
    - ASCII art banner.

## Versions

This project includes two versions of the main application:

1.  **`main.py`**: A basic version of the GPA calculator with console output.
2.  **`main_advanced.py`**: An advanced version with a richer user interface using the Rich library for better visualization and interactive features.

## Requirements

- Python 3.7 or above
- [Camelot](https://camelot-py.readthedocs.io/en/master/) (requires dependencies such as Ghostscript)
- [Pandas](https://pandas.pydata.org/)
- [Rich](https://rich.readthedocs.io/en/stable/)

## Setup

1.  **Clone the repository**

    ```sh
    git clone https://github.com/Kaos599/VIT-GPA-Calculator.git
    cd VIT-GPA-Calculator
    ```
2.  **Install dependencies**

    It's recommended to use a virtual environment. For example, using venv:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Install Ghostscript**

    Camelot requires Ghostscript. Please install it from [Ghostscript Downloads.](https://ghostscript.com/releases/gsdnld.html)

## Usage

-   Download your Grade History PDF from VTOP.

-   Run the application:
    -   For the basic version:

        ```sh
        python main.py
        ```
    -   For the advanced version:

        ```sh
        python main_advanced.py
        ```

-   When prompted, enter the full path to your PDF grade history file.

-   Follow the on-screen instructions to view your current grade analysis, simulate grade improvements, plan future courses, or visualize your data. The advanced version provides a menu-driven interface.

## Contributing

Contributions are welcome! Please fork this repository and submit pull requests.

## License

This project is licensed under the MIT License.
