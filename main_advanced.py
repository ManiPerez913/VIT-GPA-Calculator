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
        title = str(title).lower()
        return re.sub(r'[^a-z0-9]', '', title)

    def extract_table_data(self, pdf_path):
        try:
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

            df['Credits'] = pd.to_numeric(df['Credits'], errors='coerce')
            df = df.dropna(subset=['Credits'])
            df['Credits'] = df['Credits'].astype(int)
            df['Course Code'] = df['Course Code'].str.strip()

            df['display_title'] = df['Course Title'].str.strip()
            df['normalized_title'] = df['Course Title'].apply(self.normalize_course_title)

            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                df = df.dropna(subset=[date_col])
                sort_col = date_col
            else:
                df['Date'] = pd.date_range(end='today', periods=len(df), freq='D')
                sort_col = 'Date'

            df = df.sort_values(by=sort_col, ascending=False)
            df = df.drop_duplicates(subset='normalized_title', keep='first')
            df = df[df['Grade'].isin(['S', 'A', 'B', 'C', 'D', 'E', 'F', 'P'])]
            
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

    def simulate_and_print(self, original_distribution, simulation_changes, original_cgpa):
        new_distribution = original_distribution.copy()
        for change in simulation_changes:
            new_distribution = self.simulate_improvement(new_distribution, [change])
        new_cgpa = self.calculate_cgpa_from_distribution(new_distribution)
        
        # Build changes table.
        changes_table = Table(title="Changes Made", box=box.SIMPLE)
        changes_table.add_column("From", style="red", justify="center")
        changes_table.add_column("To", style="green", justify="center")
        changes_table.add_column("Credits", justify="center", style="cyan")
        for from_grade, to_grade, credits in simulation_changes:
            changes_table.add_row(from_grade, to_grade, str(credits))
            
        # CGPA comparison table.
        cgpa_table = Table.grid(padding=1)
        cgpa_table.add_row("Original CGPA:", f"[bold yellow]{original_cgpa:.2f}[/]")
        cgpa_table.add_row("Projected CGPA:", f"[bold green]{new_cgpa:.2f}[/]")
        
        console.print(Panel.fit(Group(changes_table, cgpa_table),
                                title="[bold blue]After Improvement[/bold blue]",
                                border_style="blue"))
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
    
    # Prompt for PDF path.
    while True:
        pdf_path = console.input("[bold cyan]📁 Enter PDF path (or 'q' to quit): [/]").strip()
        if pdf_path.lower() == 'q':
            return
        if os.path.exists(pdf_path):
            break
        console.print("[red]File not found. Please try again.[/red]")

    with console.status("[bold green]Processing PDF...[/]", spinner="bouncingBall"):
        raw_df = CGPACalculator().extract_table_data(pdf_path)
        if raw_df is None:
            return
        clean_df = CGPACalculator().clean_table_data(raw_df)
    if clean_df is None:
        return

    # Display academic analysis.
    calculator = CGPACalculator()
    current_cgpa, distribution = calculator.print_analysis(clean_df)
    original_dist = distribution.copy()
    simulation_changes = []
    
    # Display an instruction box for the simulation workflow.
    instructions = Panel.fit(
        "[bold]Instructions:[/bold]\n"
        "1. When adding a grade improvement, you will be asked for:\n"
        "   • [bold]From Grade[/bold]: The current grade (e.g., B).\n"
        "   • [bold]To Grade[/bold]: The target grade (e.g., S).\n"
        "   • [bold]Credits to convert[/bold]: The number of credits to convert (e.g., 16).\n\n"
        "2. You can chain multiple improvements. Use option 2 to view your current simulation chain.\n"
        "3. Option 3 resets the chain, and Option 4 finalizes the simulation.\n",
        title="[bold blue]Simulation Instructions[/bold blue]",
        border_style="cyan"
    )
    console.print(instructions)

    # Refined simulation loop with enhanced CLI menu and instruction boxes.
    while True:
        sim_menu = Table(title="[yellow]Grade Improvement Simulator[/yellow]", box=box.HEAVY_EDGE, border_style="bright_blue")
        sim_menu.add_column("Option", justify="center", style="bold white")
        sim_menu.add_column("Action", justify="left", style="cyan")
        sim_menu.add_row("1", "Add a new grade improvement")
        sim_menu.add_row("2", "View current simulation chain")
        sim_menu.add_row("3", "Reset simulation")
        sim_menu.add_row("4", "Finalize simulation")
        console.print(sim_menu)
        
        choice = console.input("\n[bold cyan]Enter your choice (1-4): [/bold cyan]").strip()

        if choice == '1':
            # Display instructions for entering grade improvement details.
            input_instructions = Panel.fit(
                "[bold]How to enter grade improvement details:[/bold]\n"
                "- [bold]From Grade[/bold]: Current grade (e.g., B)\n"
                "- [bold]To Grade[/bold]: Target grade (e.g., S)\n"
                "- [bold]Credits to convert[/bold]: Numeric value (e.g., 16)\n"
                "Press enter after each input.",
                title="[bold magenta]Grade Improvement Input Instructions[/bold magenta]",
                border_style="magenta"
            )
            console.print(input_instructions)
            try:
                from_grade = console.input("[bold]From Grade (e.g., B): [/bold]").upper().strip()
                to_grade = console.input("[bold]To Grade (e.g., S): [/bold]").upper().strip()
                credits = float(console.input("[bold]Credits to convert: [/bold]"))
                simulation_changes.append((from_grade, to_grade, credits))
                final_cgpa, new_distribution = calculator.simulate_and_print(original_dist, simulation_changes, current_cgpa)
                console.print("[green]Grade improvement added successfully![/green]")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")

        elif choice == '2':
            if simulation_changes:
                chain_table = Table(title="[bold magenta]Current Simulation Chain[/bold magenta]", box=box.SIMPLE_HEAVY)
                chain_table.add_column("Step", justify="center", style="bold white")
                chain_table.add_column("From", justify="center", style="red")
                chain_table.add_column("To", justify="center", style="green")
                chain_table.add_column("Credits", justify="center", style="cyan")
                for i, change in enumerate(simulation_changes, start=1):
                    chain_table.add_row(str(i), change[0], change[1], str(change[2]))
                console.print(chain_table)
            else:
                console.print("[yellow]No simulation changes added yet.[/yellow]")

        elif choice == '3':
            simulation_changes.clear()
            new_distribution = original_dist.copy()
            console.print("[green]Simulation chain reset successfully.[/green]")

        elif choice == '4':
            if simulation_changes:
                final_cgpa, new_distribution = calculator.simulate_and_print(original_dist, simulation_changes, current_cgpa)
                console.rule("[bold green]Final Simulation Results[/bold green]")
                console.print(Panel.fit(f"[bold green]Final Projected CGPA: {final_cgpa:.2f}[/bold green]",
                                        title="[yellow]Final Results[/yellow]",
                                        border_style="green"))
            else:
                console.print("[yellow]No simulation changes applied. Exiting simulation...[/yellow]")
            break

        else:
            console.print("[red]Invalid choice. Please try again.[/red]")

if __name__ == "__main__":
    main()
