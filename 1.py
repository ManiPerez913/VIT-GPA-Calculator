import camelot
import pandas as pd
import re
from datetime import datetime
import os

class CGPACalculator:
    def __init__(self):
        self.grade_points = {
            'S': 10,
            'A': 9,
            'B': 8,
            'C': 7,
            'D': 6,
            'E': 5,
            'F': 0,
            'P': 0  # Not counted in CGPA
        }

    def normalize_course_title(self, title):
        """Normalize course title by removing special characters and extra spaces."""
        # Convert to lowercase
        title = str(title).lower()
        # Remove special characters and extra spaces
        title = re.sub(r'[^a-z0-9]', '', title)
        return title

    def extract_table_data(self, pdf_path):
        """Extracts table data from the PDF using Camelot."""
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
        """Cleans the raw table data and extracts relevant columns."""
        try:
            # Find header row
            header_row_index = None
            for i in range(len(df)):
                row_values = [str(val).strip() for val in df.iloc[i].values]
                if "Course Code" in row_values and "Grade" in row_values:
                    header_row_index = i
                    break

            if header_row_index is None:
                raise ValueError("Headers not found")

            # Extract headers and data
            headers = [str(val).strip() for val in df.iloc[header_row_index].values]
            df = df.iloc[header_row_index + 1:].reset_index(drop=True)
            df.columns = headers

            # Filter necessary columns
            columns_to_keep = ["Course Code", "Course Title", "Credits", "Grade", "Date"]
            filtered_columns = [col for col in columns_to_keep if col in df.columns]
            df = df[filtered_columns]

            # Basic cleaning
            df = df.dropna()
            df = df.reset_index(drop=True)
            df['Credits'] = pd.to_numeric(df['Credits'], errors='coerce')
            df = df.dropna(subset=['Credits'])
            df['Credits'] = df['Credits'].astype(int)
            df['Course Code'] = df['Course Code'].str.strip()
            
            # Store original course titles for display
            df['display_title'] = df['Course Title'].str.strip()
            
            # Create normalized course titles for comparison
            df['normalized_title'] = df['Course Title'].apply(self.normalize_course_title)
            
            # Handle dates
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            else:
                df['Date'] = pd.date_range(end='today', periods=len(df), freq='D')

            # Sort by date (descending) and remove duplicates based on normalized title
            df = df.sort_values('Date', ascending=False)
            df = df.drop_duplicates(subset='normalized_title', keep='first')
            
            # Filter valid grades
            df = df[df['Grade'].isin(['S', 'A', 'B', 'C', 'D', 'E', 'F', 'P'])]

            # Rename columns for consistency
            df = df.rename(columns={
                'Course Code': 'course_code',
                'display_title': 'course',  # Use display_title for course column
                'Credits': 'credits',
                'Grade': 'grade'
            })

            # Drop the normalized_title column as it's no longer needed
            df = df.drop(columns=['normalized_title'])

            return df

        except Exception as e:
            print(f"An error occurred during data cleaning: {e}")
            return None

    def calculate_current_cgpa(self, df):
        """Calculate the CGPA from the current grades."""
        df_calc = df[df['grade'] != 'P'].copy()  # Exclude 'P' grades
        df_calc['grade_points'] = df_calc['grade'].map(self.grade_points)
        df_calc['weighted_points'] = df_calc['credits'] * df_calc['grade_points']

        total_credits = df_calc['credits'].sum()
        total_weighted_points = df_calc['weighted_points'].sum()
        cgpa = total_weighted_points / total_credits if total_credits > 0 else 0.0

        return cgpa

    def get_grade_distribution(self, df):
        """Get the credit distribution across grades."""
        distribution = {}
        for grade in self.grade_points:
            credits = df[df['grade'] == grade]['credits'].sum()
            if credits > 0:  # Only include grades with credits
                distribution[grade] = credits
        return distribution

    def print_analysis(self, df):
        """Print a comprehensive grade analysis."""
        current_cgpa = self.calculate_current_cgpa(df)
        distribution = self.get_grade_distribution(df)

        print("\n=== Current Grade Analysis ===")
        print(f"\nTotal Courses: {len(df)}")
        print("\nGrade Distribution (Credits):")
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:  # Print in order
            credits = distribution.get(grade, 0)
            if credits > 0:
                print(f"{grade}: {credits:.1f} credits")

        print(f"\nCurrent CGPA: {current_cgpa:.2f}")

        # Print courses by grade
        print("\nCourses by Grade:")
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:
            courses = df[df['grade'] == grade]
            if not courses.empty:
                print(f"\n{grade} Grade Courses:")
                for _, course in courses.iterrows():
                    print(f"- {course['course']} ({course['credits']} credits)")

        return current_cgpa, distribution

    def simulate_improvement(self, distribution, changes):
        """Simulate the CGPA with specified grade improvements."""
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

        total_points = sum(credits * self.grade_points[grade]
                           for grade, credits in new_distribution.items())
        total_credits = sum(credits for credits in new_distribution.values())
        new_cgpa = total_points / total_credits if total_credits > 0 else 0.0

        return new_cgpa

    def simulate_and_print(self, distribution, changes):
        """Simulate and print grade improvement scenarios."""
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