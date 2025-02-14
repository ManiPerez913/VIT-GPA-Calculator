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
        }

    def normalize_course_title(self, title):
        title = str(title).lower()
        return re.sub(r'[^a-z0-9]', '', title)

    def extract_table_data(self, pdf_path):
        try:
            tables = camelot.read_pdf(pdf_path, pages="1-end", flavor="lattice", strip_text="\n")
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
            df = df.iloc[header_row_index + 1 :].reset_index(drop=True)
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

            df["Credits"] = pd.to_numeric(df["Credits"], errors="coerce")
            df = df.dropna(subset=["Credits"])
            df["Credits"] = df["Credits"].astype(int)
            df["Course Code"] = df["Course Code"].str.strip()

            df["display_title"] = df["Course Title"].str.strip()
            df["normalized_title"] = df["Course Title"].apply(self.normalize_course_title)

            if date_col:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
                df = df.dropna(subset=[date_col])
                sort_col = date_col
            else:
                df["Date"] = pd.date_range(end="today", periods=len(df), freq="D")
                sort_col = "Date"

            df = df.sort_values(by=sort_col, ascending=False)
            df = df.drop_duplicates(subset="normalized_title", keep="first")
            df = df[df["Grade"].isin(["S", "A", "B", "C", "D", "E", "F", "P"])]

            rename_map = {
                "Course Code": "course_code",
                "display_title": "course",
                "Credits": "credits",
                "Grade": "grade",
            }
            df = df.rename(columns=rename_map)
            df = df.drop(columns=["normalized_title"])
            return df

        except Exception as e:
            console.print(f"[bold red]Data cleaning error:[/] {e}")
            return None

    def calculate_current_cgpa(self, df):
        df_calc = df[df["grade"] != "P"].copy()  # Exclude courses with grade 'P'
        df_calc["grade_points"] = df_calc["grade"].map(self.grade_points)
        total_credits = df_calc["credits"].sum()
        total_points = (df_calc["credits"] * df_calc["grade_points"]).sum()
        return total_points / total_credits if total_credits > 0 else 0.0

    def get_grade_distribution(self, df):
        distribution = {}
        for grade in self.grade_points:
            credits = df[df["grade"] == grade]["credits"].sum()
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
        for grade in ["S", "A", "B", "C", "D", "E", "F"]:
            credits = distribution.get(grade, 0)
            percent = (credits / total_credits) * 100 if total_credits > 0 else 0
            dist_table.add_row(f"[bold]{grade}[/]", str(credits), f"{percent:.1f}%")
        console.print(Panel.fit(dist_table, border_style="blue"))

        # Courses by Grade
        for grade in ["S", "A", "B", "C", "D", "E", "F"]:
            courses = df[df["grade"] == grade]
            if not courses.empty:
                grade_table = Table(box=box.SIMPLE, show_header=False)
                grade_table.add_column(style="dim", width=12)
                grade_table.add_column(style="bold white")
                grade_table.add_column("Credits", justify="right")
                for _, row in courses.iterrows():
                    grade_table.add_row(row["course_code"], row["course"].title(), str(row["credits"]))
                border_color = "green" if grade in ["S", "A"] else "yellow"
                console.print(Panel.fit(grade_table, title=f"[bold]{grade} Grade Courses[/]", border_style=border_color))
        return current_cgpa, distribution

    def simulate_improvement(self, distribution, changes):
        """
        For each change (from_grade, to_grade, credits), subtract credits from one grade and add them to another.
        """
        new_distribution = distribution.copy()
        for from_grade, to_grade, credits in changes:
            if from_grade not in self.grade_points or to_grade not in self.grade_points:
                raise ValueError(f"Invalid grade(s) provided: {from_grade}, {to_grade}")
            if credits > new_distribution.get(from_grade, 0):
                raise ValueError(f"Not enough credits in grade {from_grade} to convert.")
            new_distribution[from_grade] -= credits
            new_distribution[to_grade] = new_distribution.get(to_grade, 0) + credits
        return new_distribution

    def simulate_and_print(self, original_distribution, simulation_changes, original_cgpa):
        new_distribution = original_distribution.copy()
        for change in simulation_changes:
            new_distribution = self.simulate_improvement(new_distribution, [change])
        new_cgpa = self.calculate_cgpa_from_distribution(new_distribution)

        # Build changes table.
        changes_table = Table(title="Grade Improvement Changes", box=box.SIMPLE)
        changes_table.add_column("From", style="red", justify="center")
        changes_table.add_column("To", style="green", justify="center")
        changes_table.add_column("Credits", justify="center", style="cyan")
        for from_grade, to_grade, credits in simulation_changes:
            changes_table.add_row(from_grade, to_grade, str(credits))
        cgpa_table = Table.grid(padding=1)
        cgpa_table.add_row("Original CGPA:", f"[bold yellow]{original_cgpa:.2f}[/]")
        cgpa_table.add_row("Projected CGPA:", f"[bold green]{new_cgpa:.2f}[/]")

        console.print(
            Panel.fit(
                Group(changes_table, cgpa_table),
                title="[bold blue]After Improvement[/bold blue]",
                border_style="blue",
            )
        )
        return new_cgpa, new_distribution

    def simulate_future_courses(self, distribution, future_changes):
        """
        For each future change (grade, credits), add the credits to that grade.
        """
        new_distribution = distribution.copy()
        for grade, credits in future_changes:
            if grade not in self.grade_points:
                raise ValueError(f"Invalid grade provided: {grade}")
            new_distribution[grade] = new_distribution.get(grade, 0) + credits
        return new_distribution

    def calculate_cgpa_from_distribution(self, distribution):
        total_points = sum(credits * self.grade_points[grade] for grade, credits in distribution.items())
        total_credits = sum(distribution.values())
        return total_points / total_credits if total_credits > 0 else 0

    def visualize_distribution(self, distribution, title="Grade Distribution"):
        """Display a simple bar chart visualization of the grade distribution."""
        if not distribution:
            console.print("[red]No data to visualize.[/red]")
            return
        max_credits = max(distribution.values())
        viz_table = Table(title=title, box=box.SIMPLE_HEAVY, border_style="blue")
        viz_table.add_column("Grade", justify="center", style="bold")
        viz_table.add_column("Bar", justify="left", style="green")
        viz_table.add_column("Credits", justify="right", style="cyan")
        for grade in ["S", "A", "B", "C", "D", "E", "F"]:
            credits = distribution.get(grade, 0)
            bar_length = int((credits / max_credits) * 30) if max_credits > 0 else 0
            bar = "█" * bar_length
            viz_table.add_row(grade, bar, str(credits))
        console.print(viz_table)

    def visualize_grade_history(self, df):
        """Display a grade history showing cumulative CGPA over time."""
        # Determine which date column to use.
        date_col = "Date" if "Date" in df.columns else ("Result Declared On" if "Result Declared On" in df.columns else None)
        if not date_col:
            console.print("[red]No date column available for grade history visualization.[/red]")
            return

        # Consider only courses with a valid grade (excluding 'P').
        df_calc = df[df["grade"] != "P"].copy()
        df_history = df_calc.sort_values(by=date_col, ascending=True).reset_index(drop=True)
        cumulative_points = 0
        cumulative_credits = 0
        history_data = []
        for _, row in df_history.iterrows():
            grade = row["grade"]
            credits = row["credits"]
            grade_point = self.grade_points.get(grade, 0)
            cumulative_points += credits * grade_point
            cumulative_credits += credits
            cgpa = cumulative_points / cumulative_credits if cumulative_credits > 0 else 0
            history_data.append((row[date_col].strftime("%Y-%m-%d"), cgpa))

        # Display the history in a table with a simple bar visualization.
        history_table = Table(title="Grade History (Cumulative CGPA Over Time)", box=box.SIMPLE_HEAVY, border_style="magenta")
        history_table.add_column("Date", style="cyan", justify="center")
        history_table.add_column("Cumulative CGPA", style="bold green", justify="center")
        history_table.add_column("Visualization", style="yellow")
        for date_str, cgpa in history_data:
            bar_length = int((cgpa / 10) * 30)  # assuming max CGPA is 10
            bar = "█" * bar_length
            history_table.add_row(date_str, f"{cgpa:.2f}", bar)
        console.print(history_table)


def simulate_grade_improvement(calculator, original_distribution, original_cgpa):
    improvement_changes = []
    while True:
        sim_menu = Table(title="Grade Improvement Simulator", box=box.HEAVY_EDGE, border_style="bright_blue")
        sim_menu.add_column("Option", justify="center", style="bold white")
        sim_menu.add_column("Action", justify="left", style="cyan")
        sim_menu.add_row("1", "Add a new grade improvement")
        sim_menu.add_row("2", "View current improvement chain")
        sim_menu.add_row("3", "Reset improvement simulation")
        sim_menu.add_row("4", "Finalize improvement simulation and return")
        console.print(sim_menu)

        choice = console.input("[bold cyan]Enter your choice (1-4): [/bold cyan]").strip()
        if choice == "1":
            try:
                from_grade = console.input("[bold]From Grade (e.g., B): [/bold]").upper().strip()
                to_grade = console.input("[bold]To Grade (e.g., S): [/bold]").upper().strip()
                credits = float(console.input("[bold]Credits to convert: [/bold]"))
                improvement_changes.append((from_grade, to_grade, credits))
                final_cgpa_improve, new_distribution = calculator.simulate_and_print(original_distribution, improvement_changes, original_cgpa)
                console.print("[green]Grade improvement added successfully![/green]")
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
        elif choice == "2":
            if improvement_changes:
                chain_table = Table(title="Current Improvement Chain", box=box.SIMPLE_HEAVY)
                chain_table.add_column("Step", justify="center", style="bold white")
                chain_table.add_column("From", justify="center", style="red")
                chain_table.add_column("To", justify="center", style="green")
                chain_table.add_column("Credits", justify="center", style="cyan")
                for i, change in enumerate(improvement_changes, start=1):
                    chain_table.add_row(str(i), change[0], change[1], str(change[2]))
                console.print(chain_table)
            else:
                console.print("[yellow]No improvement changes added yet.[/yellow]")
        elif choice == "3":
            improvement_changes.clear()
            console.print("[green]Improvement simulation chain reset successfully.[/green]")
        elif choice == "4":
            if improvement_changes:
                final_cgpa_improve, new_distribution = calculator.simulate_and_print(original_distribution, improvement_changes, original_cgpa)
                console.rule("[bold green]Improvement Simulation Finalized[/bold green]")
                console.print(
                    Panel.fit(
                        f"[bold green]New Projected CGPA after Improvements: {final_cgpa_improve:.2f}[/bold green]",
                        title="Improvement Results",
                        border_style="green",
                    )
                )
                return new_distribution, final_cgpa_improve
            else:
                console.print("[yellow]No improvement changes applied. Returning original distribution.[/yellow]")
                return original_distribution, original_cgpa
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")


def simulate_future_courses(calculator, current_distribution):
    future_changes = []
    while True:
        future_menu = Table(title="Future Courses Simulator", box=box.HEAVY_EDGE, border_style="bright_blue")
        future_menu.add_column("Option", justify="center", style="bold white")
        future_menu.add_column("Action", justify="left", style="cyan")
        future_menu.add_row("1", "Add a future course")
        future_menu.add_row("2", "View current future courses chain")
        future_menu.add_row("3", "Reset future courses simulation")
        future_menu.add_row("4", "Finalize future courses simulation and return")
        console.print(future_menu)

        choice = console.input("[bold cyan]Enter your choice (1-4): [/bold cyan]").strip()
        if choice == "1":
            try:
                future_grade = console.input("[bold]Grade Achieved (e.g., A): [/bold]").upper().strip()
                future_credits = float(console.input("[bold]Credits Earned: [/bold]"))
                future_changes.append((future_grade, future_credits))
                temp_distribution = calculator.simulate_future_courses(current_distribution, future_changes)
                new_cgpa = calculator.calculate_cgpa_from_distribution(temp_distribution)
                console.print(
                    Panel.fit(
                        f"[bold green]New Projected CGPA including future courses: {new_cgpa:.2f}[/bold green]",
                        title="After Adding Future Courses",
                        border_style="blue",
                    )
                )
            except ValueError as e:
                console.print(f"[red]Error: {e}[/red]")
        elif choice == "2":
            if future_changes:
                future_chain = Table(title="Current Future Courses Chain", box=box.SIMPLE_HEAVY)
                future_chain.add_column("Step", justify="center", style="bold white")
                future_chain.add_column("Grade Achieved", justify="center", style="green")
                future_chain.add_column("Credits Earned", justify="center", style="cyan")
                for i, change in enumerate(future_changes, start=1):
                    future_chain.add_row(str(i), change[0], str(change[1]))
                console.print(future_chain)
            else:
                console.print("[yellow]No future courses added yet.[/yellow]")
        elif choice == "3":
            future_changes.clear()
            console.print("[green]Future courses simulation chain reset successfully.[/green]")
        elif choice == "4":
            if future_changes:
                final_distribution = calculator.simulate_future_courses(current_distribution, future_changes)
                final_cgpa_future = calculator.calculate_cgpa_from_distribution(final_distribution)
                console.rule("[bold green]Future Courses Simulation Finalized[/bold green]")
                console.print(
                    Panel.fit(
                        f"[bold green]Final Projected CGPA including future courses: {final_cgpa_future:.2f}[/bold green]",
                        title="Final Future Courses Results",
                        border_style="green",
                    )
                )
                return final_distribution
            else:
                console.print("[yellow]No future courses applied. Returning current distribution.[/yellow]")
                return current_distribution
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")


def main():
    # Display ASCII Banner
    ascii_art = Text(
        """
     ██╗   ██╗██╗████████╗  ██████╗ ██████╗  █████╗ 
     ██║   ██║██║╚══██╔══╝ ██╔════╝ ██╔══██╗██╔══██╗
     ██║   ██║██║   ██║    ██║  ███╗██████╔╝███████║
     ╚██╗ ██╔╝██║   ██║    ██║   ██║██╔═══╝ ██╔══██║
      ╚████╔╝ ██║   ██║    ╚██████╔╝██║     ██║  ██║
       ╚═══╝  ╚═╝   ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝
        """,
        justify="center",
        style="bold cyan",
    )
    console.print(Panel.fit(ascii_art, title="[bold blue]VIT GPA ANALYZER[/]", subtitle="by Academic Insights"))

    # Prompt for PDF path.
    while True:
        pdf_path = console.input("[bold cyan]📁 Enter PDF path (or 'q' to quit): [/]").strip()
        if pdf_path.lower() == "q":
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

    calculator = CGPACalculator()
    current_cgpa, original_dist = calculator.print_analysis(clean_df)

    # Initialize simulation distributions.
    improved_distribution = original_dist.copy()  # for grade improvement simulation
    future_distribution = original_dist.copy()    # for future courses simulation

    # Main simulation menu
    while True:
        menu_table = Table(title="Main Menu", box=box.DOUBLE_EDGE, border_style="bright_blue")
        menu_table.add_column("Option", justify="center", style="bold white")
        menu_table.add_column("Description", style="cyan")
        menu_table.add_row("1", "Simulate Grade Improvement")
        menu_table.add_row("2", "Simulate Future Courses")
        menu_table.add_row("3", "Visualize Grade History")
        menu_table.add_row("4", "Visualize Final Grade Distribution")
        menu_table.add_row("5", "Exit")
        console.print(menu_table)

        choice = console.input("[bold cyan]Enter your choice (1-5): [/bold cyan]").strip()
        if choice == "1":
            improved_distribution, current_cgpa = simulate_grade_improvement(calculator, original_dist, current_cgpa)
        elif choice == "2":
            # Start future simulation from the improved distribution if grade improvements were applied.
            future_distribution = simulate_future_courses(calculator, improved_distribution)
        elif choice == "3":
            calculator.visualize_grade_history(clean_df)
        elif choice == "4":
            # Let the user choose which distribution to visualize.
            viz_menu = Table(title="Visualization Options", box=box.SIMPLE_HEAVY, border_style="cyan")
            viz_menu.add_column("Option", justify="center", style="bold white")
            viz_menu.add_column("Description", style="cyan")
            viz_menu.add_row("1", "Original Grade Distribution")
            viz_menu.add_row("2", "After Grade Improvement")
            viz_menu.add_row("3", "After Future Courses Simulation")
            console.print(viz_menu)
            sub_choice = console.input("[bold cyan]Choose distribution to visualize (1-3): [/bold cyan]").strip()
            if sub_choice == "1":
                calculator.visualize_distribution(original_dist, title="Original Grade Distribution")
            elif sub_choice == "2":
                calculator.visualize_distribution(improved_distribution, title="After Grade Improvement")
            elif sub_choice == "3":
                calculator.visualize_distribution(future_distribution, title="After Future Courses Simulation")
            else:
                console.print("[red]Invalid choice.[/red]")
        elif choice == "5":
            console.print("[bold magenta]Exiting simulation. Thank you![/bold magenta]")
            break
        else:
            console.print("[red]Invalid option, please try again.[/red]")


if __name__ == "__main__":
    main()
