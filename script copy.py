import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import os

class QuizApp:
    def __init__(self, root, quiz_data, time_limit):
        self.root = root
        self.root.title("Quiz Application")
        self.quiz_data = quiz_data
        self.time_limit = time_limit  # Time limit in seconds
        self.time_remaining = time_limit
        self.selected_subject = tk.StringVar(value=list(quiz_data.keys())[0])
        self.answers = {subject: [None] * len(questions) for subject, questions in quiz_data.items()}
        self.selected_answers = {subject: [None] * len(questions) for subject, questions in quiz_data.items()}
        self.submitted = False  # Track if the test has been submitted

        self.create_widgets()
        self.load_questions()
        self.update_timer()

    def create_widgets(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(sticky="nsew")

        self.main_frame.grid_rowconfigure(0, weight=0)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.subject_menu = ttk.Combobox(self.header_frame, textvariable=self.selected_subject, values=list(self.quiz_data.keys()), state="readonly")
        self.subject_menu.pack(side=tk.LEFT, pady=10, padx=10)
        self.subject_menu.bind("<<ComboboxSelected>>", self.change_subject)

        self.timer_label = ttk.Label(self.header_frame, text="", font=('Helvetica', 14))
        self.timer_label.pack(side=tk.RIGHT, pady=10, padx=10)

        self.question_frame = ttk.Frame(self.main_frame)
        self.question_frame.grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky="nsew")

        self.question_frame.grid_rowconfigure(0, weight=1)
        self.question_frame.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.question_frame)
        self.scrollbar = ttk.Scrollbar(self.question_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Bind the mouse wheel event to the canvas for both Windows and macOS
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Shift-MouseWheel>", self._on_shiftmouse)

        self.footer_frame = ttk.Frame(self.main_frame)
        self.footer_frame.grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky="ew")

        self.submit_button = ttk.Button(self.footer_frame, text="Submit", command=self.submit_test)
        self.submit_button.pack(fill=tk.X, padx=20, pady=10)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_shiftmouse(self, event):
        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")

    def load_questions(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        subject = self.selected_subject.get()
        questions = self.quiz_data[subject]

        question_container = ttk.Frame(self.scrollable_frame)
        question_container.pack(fill="both", expand=True)

        for i, question_data in enumerate(questions):
            question_frame = ttk.Frame(question_container, padding="10")
            question_frame.pack(fill="both", expand=True, pady=10)

            question_label = ttk.Label(question_frame, text=f"{i + 1}. {question_data['question']}", wraplength=1000, justify="left")
            question_label.pack(anchor="w", pady=(10, 0))

            var = tk.StringVar(value=self.selected_answers[subject][i])  # Restore selected answer if available
            for j, (key, option) in enumerate(question_data['options'].items()):
                rb = tk.Radiobutton(question_frame, text=f"{key}. {option}", variable=var, value=key, wraplength=1000, justify="left", command=lambda i=i, var=var: self.save_answer(i, var))
                rb.pack(anchor="w", padx=20)  # Added padding for better spacing

            self.answers[subject][i] = var

    def change_subject(self, event=None):
        if not self.submitted:
            self.load_questions()

    def save_answer(self, index, var):
        subject = self.selected_subject.get()
        self.selected_answers[subject][index] = var.get()

    def submit_test(self):
        if self.submitted:
            messagebox.showinfo("Info", "You have already submitted the test.")
            return

        # Check if all questions are attempted
        for subject, answers in self.selected_answers.items():
            for answer in answers:
                if answer is None:
                    messagebox.showwarning("Warning", "Please attempt all questions before submitting.")
                    return

        self.submitted = True
        self.submit_button.config(state=tk.DISABLED)
        self.show_results()

    def show_results(self):
        total_score = 0
        total_questions = 0
        results = []

        for subject, questions in self.quiz_data.items():
            subject_score = 0
            subject_total = len(questions)
            for index, question_data in enumerate(questions):
                correct_answer = question_data['answer']
                user_answer = self.selected_answers[subject][index]
                if user_answer == correct_answer:
                    subject_score += 1
                    results.append((f"Question {index + 1}", "Correct", user_answer, correct_answer))
                else:
                    results.append((f"Question {index + 1}", "Incorrect", user_answer, correct_answer))
            results.append((f"{subject} Total", f"{subject_score}/{subject_total}", "", ""))
            total_score += subject_score
            total_questions += subject_total

        results.append(("Overall Total Score", f"{total_score}/{total_questions}", "", ""))
        
        self.display_results(results)

    def display_results(self, results):
        result_window = tk.Toplevel(self.root)
        result_window.title("Quiz Results")

        result_frame = ttk.Frame(result_window, padding="10")
        result_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        columns = ("Question", "Result", "Your Answer", "Correct Answer")
        tree = ttk.Treeview(result_frame, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center")

        for row in results:
            tree.insert("", tk.END, values=row)

        tree.pack(fill=tk.BOTH, expand=True)

        close_button = ttk.Button(result_window, text="Close", command=result_window.destroy)
        close_button.pack(pady=10)

    def update_timer(self):
        if self.submitted:  # Stop the timer if the test has been submitted
            return
        if self.time_remaining > 0:
            mins, secs = divmod(self.time_remaining, 60)
            time_format = '{:02d}:{:02d}'.format(mins, secs)
            self.timer_label.config(text=f"Time Remaining: {time_format}")
            self.time_remaining -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="Time's up!")
            self.submit_test()

if __name__ == "__main__":
    # Ensure the data file is included in the executable package
    if getattr(sys, 'frozen', False):
        # If the application is run from a bundle
        application_path = sys._MEIPASS
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(application_path, 'quiz_data.json')

    with open(file_path, 'r') as file:
        quiz_data = json.load(file)

    time_limit = 240 * 60  # Set time limit in seconds (e.g., 4 hours)

    root = tk.Tk()
    root.attributes('-fullscreen', True)  # Make the window full screen
    app = QuizApp(root, quiz_data, time_limit)
    root.mainloop()
