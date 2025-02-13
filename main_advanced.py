import camelot
import pandas as pd
import re
import os
from datetime import datetime
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

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
        # Lowercase and remove all non-alphanumeric characters.
        title = str(title).lower()
        return re.sub(r'[^a-z0-9]', '', title)

    def extract_table_data(self, pdf_path):
        try:
            # Use lattice flavor; if your PDF structure suits stream better, switch flavor.
            tables = camelot.read_pdf(pdf_path, pages='1-end', flavor='lattice', strip_text='\n')
            if not tables:
                console.print("[bold red]No tables found in the PDF.[/]")
                return None
            combined_df = pd.concat([table.df for table in tables], ignore_index=True)
            return combined_df
        except Exception as e:
            console.print(f"[bold red]Error extracting tables:[/] {e}")
            return None

    def clean_table_data(self, df):
        try:
            # Locate header row by finding a row that contains both "Course Code" and "Grade"
            header_row_index = None
            for i in range(len(df)):
                row_values = [str(val).strip() for val in df.iloc[i].values]
                if "Course Code" in row_values and "Grade" in row_values:
                    header_row_index = i
                    break
            if header_row_index is None:
                raise ValueError("Headers not found")
            
            headers = [str(val).strip() for val in df.iloc[header_row_index].values]
            df = df.iloc[header_row_index + 1:].reset_index(drop=True)
            df.columns = headers

            # Determine which date column to use (either "Date" or "Result Declared On")
            columns_to_keep = ["Course Code", "Course Title", "Credits", "Grade"]
            if "Date" in df.columns:
                columns_to_keep.append("Date")
                date_col = "Date"
            elif "Result Declared On" in df.columns:
                columns_to_keep.append("Result Declared On")
                date_col = "Result Declared On"
            else:
                date_col = None

            df = df[columns_to_keep]
            df = df.dropna().reset_index(drop=True)

            # Convert Credits to numeric, drop rows where conversion fails, then cast to int.
            df['Credits'] = pd.to_numeric(df['Credits'], errors='coerce')
            df = df.dropna(subset=['Credits'])
            df['Credits'] = df['Credits'].astype(int)
            df['Course Code'] = df['Course Code'].str.strip()

            # Create cleaned display title and a normalized title for deduplication.
            df['display_title'] = df['Course Title'].str.strip()
            df['normalized_title'] = df['Course Title'].apply(self.normalize_course_title)

            # Process date: if available, convert it; if not, create a dummy date range.
            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                df = df.dropna(subset=[date_col])
                sort_col = date_col
            else:
                df['Date'] = pd.date_range(end='today', periods=len(df), freq='D')
                sort_col = 'Date'

            # Sort by date descending so that the most recent entry comes first.
            df = df.sort_values(by=sort_col, ascending=False)
            # Drop duplicates based on the normalized title.
            df = df.drop_duplicates(subset='normalized_title', keep='first')

            # Filter rows with valid grades.
            df = df[df['Grade'].isin(['S', 'A', 'B', 'C', 'D', 'E', 'F', 'P'])]

            # Rename columns for consistency.
            rename_map = {
                'Course Code': 'course_code',
                'display_title': 'course',
                'Credits': 'credits',
                'Grade': 'grade'
            }
            df = df.rename(columns=rename_map)
            df = df.drop(columns=['normalized_title'])
            return df

        except Exception as e:
            console.print(f"[bold red]Data cleaning error:[/] {e}")
            return None

    def calculate_current_cgpa(self, df):
        df_calc = df[df['grade'] != 'P'].copy()  # Exclude courses with grade 'P'
        df_calc['grade_points'] = df_calc['grade'].map(self.grade_points)
        total_credits = df_calc['credits'].sum()
        total_points = (df_calc['credits'] * df_calc['grade_points']).sum()
        return total_points / total_credits if total_credits > 0 else 0.0

    def get_grade_distribution(self, df):
        distribution = {}
        for grade in self.grade_points:
            credits = df[df['grade'] == grade]['credits'].sum()
            if credits > 0:
                distribution[grade] = credits
        return distribution

    def print_analysis(self, df):
        current_cgpa = self.calculate_current_cgpa(df)
        distribution = self.get_grade_distribution(df)

        # Academic Summary Panel
        summary_table = Table.grid(padding=1)
        summary_table.add_column(style="cyan", justify="right")
        summary_table.add_column(style="bold magenta")
        summary_table.add_row("Total Courses", str(len(df)))
        summary_table.add_row("Current CGPA", f"[bold]{current_cgpa:.2f}[/]")
        console.print(Panel.fit(summary_table, title="[bold yellow]Academic Summary[/]", border_style="yellow"))

        # Grade Distribution Table
        dist_table = Table(title="Grade Distribution", box=box.ROUNDED, header_style="bold cyan")
        dist_table.add_column("Grade", width=8)
        dist_table.add_column("Credits", justify="right")
        dist_table.add_column("Percentage", justify="right")
        total_credits = sum(distribution.values())
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:
            credits = distribution.get(grade, 0)
            percent = (credits / total_credits) * 100 if total_credits > 0 else 0
            dist_table.add_row(f"[bold]{grade}[/]", str(credits), f"{percent:.1f}%")
        console.print(Panel.fit(dist_table, border_style="blue"))

        # Courses by Grade
        for grade in ['S', 'A', 'B', 'C', 'D', 'E', 'F']:
            courses = df[df['grade'] == grade]
            if not courses.empty:
                grade_table = Table(box=box.SIMPLE, show_header=False)
                grade_table.add_column(style="dim", width=12)
                grade_table.add_column(style="bold white")
                grade_table.add_column("Credits", justify="right")
                for _, row in courses.iterrows():
                    grade_table.add_row(row['course_code'], row['course'].title(), str(row['credits']))
                border_color = "green" if grade in ['S', 'A'] else "yellow"
                console.print(Panel.fit(grade_table, title=f"[bold]{grade} Grade Courses[/]", border_style=border_color))
        return current_cgpa, distribution

    def simulate_improvement(self, distribution, changes):
        new_distribution = distribution.copy()
        for from_grade, to_grade, credits in changes:
            if from_grade not in self.grade_points or to_grade not in self.grade_points:
                raise ValueError(f"Invalid grade(s) provided: {from_grade}, {to_grade}")
            if credits > new_distribution.get(from_grade, 0):
                raise ValueError(f"Not enough credits in grade {from_grade} to convert.")
            new_distribution[from_grade] -= credits
            new_distribution[to_grade] = new_distribution.get(to_grade, 0) + credits
        return new_distribution

    def calculate_cgpa_from_distribution(self, distribution):
        total_points = sum(credits * self.grade_points[grade] for grade, credits in distribution.items())
        total_credits = sum(distribution.values())
        return total_points / total_credits if total_credits > 0 else 0

    def simulate_and_print(self, original_distribution, simulation_changes):
        # Apply all simulation changes on top of the original distribution.
        new_distribution = original_distribution.copy()
        for change in simulation_changes:
            new_distribution = self.simulate_improvement(new_distribution, [change])
        new_cgpa = self.calculate_cgpa_from_distribution(new_distribution)
        
        # Build changes table.
        changes_table = Table(title="Proposed Changes", box=box.SIMPLE)
        changes_table.add_column("From", style="red")
        changes_table.add_column("To", style="green")
        changes_table.add_column("Credits", justify="right")
        for from_grade, to_grade, credits in simulation_changes:
            changes_table.add_row(from_grade, to_grade, str(credits))
            
        # CGPA comparison table.
        original_cgpa = self.calculate_cgpa_from_distribution(original_distribution)
        cgpa_table = Table.grid()
        cgpa_table.add_row("Original CGPA:", f"[bold yellow]{original_cgpa:.2f}[/]")
        cgpa_table.add_row("Projected CGPA:", f"[bold green]{new_cgpa:.2f}[/]")
        
        console.print(Panel.fit(Group(changes_table, cgpa_table), title="[bold blue]Simulation Results[/]", border_style="blue"))
        return new_cgpa, new_distribution

def main():
    ascii_art = Text("""
     ██╗   ██╗██╗████████╗  ██████╗ ██████╗  █████╗ 
     ██║   ██║██║╚══██╔══╝ ██╔════╝ ██╔══██╗██╔══██╗
     ██║   ██║██║   ██║    ██║  ███╗██████╔╝███████║
     ╚██╗ ██╔╝██║   ██║    ██║   ██║██╔═══╝ ██╔══██║
      ╚████╔╝ ██║   ██║    ╚██████╔╝██║     ██║  ██║
       ╚═══╝  ╚═╝   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝
    """, justify="center", style="bold cyan")
    console.print(Panel.fit(ascii_art, title="[bold blue]VIT GPA ANALYZER[/]", subtitle="by Academic Insights"))

    calculator = CGPACalculator()
    while True:
        pdf_path = console.input("[bold cyan]📁 Enter PDF path (or 'q' to quit): [/]")
        if pdf_path.lower() == 'q':
            return
        if os.path.exists(pdf_path):
            break
        console.print("[red]File not found. Please try again.[/]")

    with console.status("[bold green]Processing PDF...[/]", spinner="bouncingBall"):
        raw_df = calculator.extract_table_data(pdf_path)
        if raw_df is None:
            return
        clean_df = calculator.clean_table_data(raw_df)
    if clean_df is None:
        return

    current_cgpa, distribution = calculator.print_analysis(clean_df)
    original_dist = distribution.copy()
    current_dist = distribution.copy()
    simulation_changes = []

    while True:
        sim_panel = Panel.fit(
            "[bold]\n1. Simulate grade improvement\n2. View original grades\n3. Reset simulation\n4. Finalize & Exit\n[/bold]",
            title="[yellow]Grade Simulator[/]", border_style="yellow"
        )
        console.print(sim_panel)
        choice = console.input("\nEnter your choice (1-4): ")

        if choice == '1':
            console.print("\n[bold]Enter grade improvement details:[/bold]")
            try:
                from_grade = console.input("From Grade (e.g., B): ").upper()
                to_grade = console.input("To Grade (e.g., A): ").upper()
                credits = float(console.input("Credits to convert: "))
                simulation_changes.append((from_grade, to_grade, credits))
                # Reapply all accumulated simulation changes.
                final_cgpa, current_dist = calculator.simulate_and_print(original_dist, simulation_changes)
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == '2':
            calculator.print_analysis(clean_df)

        elif choice == '3':
            current_dist = original_dist.copy()
            simulation_changes = []
            console.print("[green]Simulation reset.[/green]")

        elif choice == '4':
            if simulation_changes:
                final_cgpa = calculator.calculate_cgpa_from_distribution(current_dist)
                console.print(Panel.fit(f"[bold green]Final Projected CGPA: {final_cgpa:.2f}[/bold green]",
                                        title="[yellow]Final Results[/yellow]"))
            break

        else:
            console.print("[red]Invalid choice. Please try again.[/red]")

if __name__ == "__main__":
    main()
