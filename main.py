# VIT-GPA-Calculator

# Python

import camelot  # Library to extract tables from PDFs
import pandas as pd  # Library for data manipulation
import re  # Regular expressions for text processing
from datetime import datetime  # For date handling
import os  # For interacting with the operating system

class CGPACalculator:
    def __init__(self):
        # Mapping of grades to their corresponding grade points
        self.grade_points = {
            'S': 10,
            'A': 9,
            'B': 8,
            'C': 7,
            'D': 6,
            'E': 5,
            'F': 0,
        }

    def normalize_course_title(self, title):
        """
        Normalize course title by converting to lowercase and removing special characters.
        """
        title = str(title).lower()
        # Remove characters that are not alphanumeric
        title = re.sub(r'[^a-z0-9]', '', title)
        return title

    def extract_table_data(self, pdf_path):
        """
        Extract table data from the PDF using Camelot.
        Combines dataframes from all detected tables.
        """
        try:
            tables = camelot.read_pdf(pdf_path, pages='1-end', flavor='lattice', strip_text='\n')
            if not tables:
                print("No tables found in the PDF.")
                return None

            combined_df = pd.concat([table.df for table in tables])
            return combined_df

        except Exception as e:
            print(f"Error extracting tables with Camelot: {e}")
            return None

    def clean_table_data(self, df):
        """
        Clean the raw table data and extract relevant columns.
        Identifies header row and converts columns types appropriately.
        """
        try:
            header_row_index = None
            # Locate the header row that contains both "Course Code" and "Grade"
            for i in range(len(df)):
                row_values = [str(val).strip() for val in df.iloc[i].values]
                if "Course Code" in row_values and "Grade" in row_values:
                    header_row_index = i
                    break

            if header_row_index is None:
                raise ValueError("Headers not found")

            # Extract headers and update dataframe
            headers = [str(val).strip() for val in df.iloc[header_row_index].values]
            df = df.iloc[header_row_index + 1:].reset_index(drop=True)
            df.columns = headers

            # Filter to the expected columns if they exist
            columns_to_keep = ["Course Code", "Course Title", "Credits", "Grade", "Date"]
            filtered_columns = [col for col in columns_to_keep if col in df.columns]
            df = df[filtered_columns]

            # Drop rows with missing values and reset the index
            df = df.dropna()
            df = df.reset_index(drop=True)
            # Convert Credits column to numeric and then to integer
            df['Credits'] = pd.to_numeric(df['Credits'], errors='coerce')
            df = df.dropna(subset=['Credits'])
            df['Credits'] = df['Credits'].astype(int)
            df['Course Code'] = df['Course Code'].str.strip()

            # Add a cleaned display title and normalized title columns
            df['display_title'] = df['Course Title'].str.strip()
            df['normalized_title'] = df['Course Title'].apply(self.normalize_course_title)

            # Convert Date column to datetime; if missing, create a date range
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            else:
                df['Date'] = pd.date_range(end='today', periods=len(df), freq='D')

            # Sort by Date descending and remove duplicate courses based on normalized title
            df = df.sort_values('Date', ascending=False)
            df = df.drop_duplicates(subset='normalized_title', keep='first')

            # Filter rows that have valid grades
            df = df[df['Grade'].isin(['S', 'A', 'B', 'C', 'D', 'E', 'F', 'P'])]
            
            # Rename columns to more convenient names
            df = df.rename(columns={
                'Course Code': 'course_code',
                'display_title': 'course',  
                'Credits': 'credits',
                'Grade': 'grade'
            })

            # Drop the normalized_title column as it is no longer needed
            df = df.drop(columns=['normalized_title'])

            return df

        except Exception as e:
            print(f"An error occurred during data cleaning: {e}")
            return None

    def calculate_current_cgpa(self, df):
        """
        Calculate the current CGPA excluding courses with grade 'P'.
        The CGPA is the weighted average of grade points.
        """
        df_calc = df[df['grade'] != 'P'].copy()  
        df_calc['grade_points'] = df_calc['grade'].map(self.grade_points)
        df_calc['weighted_points'] = df_calc['credits'] * df_calc['grade_points']

        total_credits = df_calc['credits'].sum()
        total_weighted_points = df_calc['weighted_points'].sum()
        cgpa = total_weighted_points / total_credits if total_credits > 0 else 0.0

        return cgpa

    def get_grade_distribution(self, df):
        """
        Calculate the total credits associated with each grade.
        """
        distribution = {}
        for grade in self.grade_points:
            credits = df[df['grade'] == grade]['credits'].sum()
            if credits > 0:  # Only include grades with at least one credit
                distribution[grade] = credits
        return distribution

    def print_analysis(self, df):
        """
        Print detailed analysis including total courses, credit distribution,
        current CGPA and list courses by grade.
        """
        current_cgpa = self.calculate_current_cgpa(df)
        distribution = self.get_grade_distribution(df)

        print("\n=== Current Grade Analysis ===")
        print(f"\nTotal Courses: {len(df)}")
        print("\nGrade Distribution (Credits):")
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:
            credits = distribution.get(grade, 0)
            if credits > 0:
                print(f"{grade}: {credits:.1f} credits")

        print(f"\nCurrent CGPA: {current_cgpa:.2f}")

        print("\nCourses by Grade:")
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:
            courses = df[df['grade'] == grade]
            if not courses.empty:
                print(f"\n{grade} Grade Courses:")
                for _, course in courses.iterrows():
                    print(f"- {course['course']} ({course['credits']} credits)")

        return current_cgpa, distribution

    def simulate_improvement(self, distribution, changes):
        """
        Simulate new CGPA based on specified grade improvements.
        It applies changes to the current grade distribution.
        """
        new_distribution = distribution.copy()
        for from_grade, to_grade, credits in changes:
            if from_grade not in self.grade_points or to_grade not in self.grade_points:
                raise ValueError(f"Invalid grade(s) provided: {from_grade}, {to_grade}")
            if not isinstance(credits, (int, float)) or credits <= 0:
                raise ValueError("Credits must be a positive number.")

            if credits > new_distribution.get(from_grade, 0):
                raise ValueError(f"Not enough credits in grade {from_grade} to convert.")

            new_distribution[from_grade] = new_distribution.get(from_grade, 0) - credits
            new_distribution[to_grade] = new_distribution.get(to_grade, 0) + credits

        # Calculate the new CGPA after applying the grade improvements
        total_points = sum(credits * self.grade_points[grade]
                           for grade, credits in new_distribution.items())
        total_credits = sum(credits for credits in new_distribution.values())
        new_cgpa = total_points / total_credits if total_credits > 0 else 0.0

        return new_cgpa

    def simulate_and_print(self, distribution, changes):
        """
        Simulate the effect of a grade improvement scenario and print the results.
        """
        try:
            new_cgpa = self.simulate_improvement(distribution, changes)
            print(f"\n=== After Improvement ===")
            print("Changes made:")
            for from_grade, to_grade, credits in changes:
                print(f"Converted {credits} credits from {from_grade} to {to_grade}")
            print(f"New CGPA would be: {new_cgpa:.2f}")
            return new_cgpa
        except ValueError as e:
            print(f"Error: {e}")
            return None

def main():
    """
    Main function to run the GPA Calculator:
    1. Prompt the user for the PDF path.
    2. Extract and clean data.
    3. Display analysis.
    4. Allow grade improvement simulation.
    """
    calculator = CGPACalculator()

    while True:
        file_path = input("\nEnter the path to your grade history PDF file: ")
        if os.path.exists(file_path):
            break
        print("File not found. Please enter a valid file path.")

    raw_df = calculator.extract_table_data(file_path)
    if raw_df is None:
        return

    df = calculator.clean_table_data(raw_df)
    if df is None:
        return

    current_cgpa, distribution = calculator.print_analysis(df)

    while True:
        print("\n=== Grade Improvement Simulator ===")
        print("1. Simulate grade improvement")
        print("2. View current grade distribution")
        print("3. Exit")

        choice = input("\nEnter your choice (1-3): ")

        if choice == '1':
            print("\nEnter grade improvement details:")
            try:
                from_grade = input("From Grade (e.g., B): ").upper()
                to_grade = input("To Grade (e.g., A): ").upper()
                credits = float(input("Credits to convert: "))

                changes = [(from_grade, to_grade, credits)]
                calculator.simulate_and_print(distribution, changes)
            except ValueError:
                print("Invalid input. Please enter valid grades and credits.")

        elif choice == '2':
            calculator.print_analysis(df)

        elif choice == '3':
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()