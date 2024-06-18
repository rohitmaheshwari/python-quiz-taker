import sys
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox,
                             QComboBox, QScrollArea, QGroupBox, QRadioButton, QButtonGroup, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class QuizApp(QMainWindow):
    def __init__(self, quiz_data, time_limit):
        super().__init__()
        self.quiz_data = quiz_data
        self.time_limit = time_limit  # Time limit in seconds
        self.time_remaining = time_limit
        self.selected_subject = list(quiz_data.keys())[0]
        self.answers = {subject: [None] * len(questions) for subject, questions in quiz_data.items()}
        self.selected_answers = {subject: [None] * len(questions) for subject, questions in quiz_data.items()}
        self.submitted = False  # Track if the test has been submitted

        self.init_ui()
        self.load_questions()
        self.update_timer()

    def init_ui(self):
        self.setWindowTitle("Quiz Application")

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_layout = QVBoxLayout(self.main_widget)

        self.header_layout = QHBoxLayout()
        self.main_layout.addLayout(self.header_layout)

        self.subject_combo = QComboBox()
        self.subject_combo.addItems(self.quiz_data.keys())
        self.subject_combo.setFixedSize(300, 40)  # Set bigger size
        self.subject_combo.setFont(QFont('Arial', 18))  # Increase font size
        self.subject_combo.currentIndexChanged.connect(self.change_subject)
        self.header_layout.addWidget(self.subject_combo, alignment=Qt.AlignLeft)

        self.timer_label = QLabel()
        self.timer_label.setFont(QFont('Arial', 18))  # Increase font size
        self.header_layout.addWidget(self.timer_label, alignment=Qt.AlignCenter)

        self.submit_button = QPushButton("Submit")
        self.submit_button.setFixedSize(200, 40)  # Set bigger size
        self.submit_button.setFont(QFont('Arial', 18))  # Increase font size
        self.submit_button.clicked.connect(self.submit_test)
        self.submit_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.header_layout.addWidget(self.submit_button, alignment=Qt.AlignRight)  # Align right

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(self.scroll_area)

        self.questions_widget = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_widget)
        self.scroll_area.setWidget(self.questions_widget)

        self.showFullScreen()  # Enter true full-screen mode

    def load_questions(self):
        for i in reversed(range(self.questions_layout.count())):
            widget = self.questions_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        subject = self.selected_subject
        questions = self.quiz_data[subject]

        for i, question_data in enumerate(questions):
            question_group = QGroupBox(f"Question {i + 1}")
            question_layout = QVBoxLayout()

            question_label = QLabel(question_data['question'])
            question_label.setFont(QFont('Arial', 16))  # Increase font size
            question_layout.addWidget(question_label)

            button_group = QButtonGroup(self)
            for key, option in question_data['options'].items():
                radio_button = QRadioButton(f"{key}. {option.encode('utf-8').decode('unicode_escape')}")
                radio_button.setFont(QFont('Arial', 14))  # Increase font size
                button_group.addButton(radio_button, id=ord(key))
                question_layout.addWidget(radio_button)
                if self.selected_answers[subject][i] == key:
                    radio_button.setChecked(True)

                radio_button.toggled.connect(lambda checked, i=i, key=key: self.save_answer(i, key, checked))

            self.answers[subject][i] = button_group
            question_group.setLayout(question_layout)
            self.questions_layout.addWidget(question_group)
            question_group.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.questions_layout.addStretch()

    def change_subject(self):
        if not self.submitted:
            self.selected_subject = self.subject_combo.currentText()
            self.load_questions()

    def save_answer(self, index, key, checked):
        if checked:
            subject = self.selected_subject
            self.selected_answers[subject][index] = key

    def submit_test(self):
        if self.submitted:
            QMessageBox.information(self, "Info", "You have already submitted the test.")
            return

        # Check if all questions are attempted
        for subject, answers in self.selected_answers.items():
            for answer in answers:
                if answer is None:
                    QMessageBox.warning(self, "Warning", "Please attempt all questions before submitting.")
                    return

        self.submitted = True
        self.submit_button.setEnabled(False)
        self.show_results()

        # Save the results to a text file
        self.save_results_to_file()

    def show_results(self):
        result_window = QMainWindow()
        result_window.setWindowTitle("Quiz Results")
        result_widget = QWidget()
        result_layout = QVBoxLayout(result_widget)
        result_window.setCentralWidget(result_widget)

        summary = QLabel()
        results = self.calculate_results()
        summary_text = f"Total Score: {results['total_score']} / {results['total_questions']}\n"
        for subject, subject_results in results['subjects'].items():
            summary_text += f"{subject}: {subject_results['score']} / {subject_results['total']}\n"
        summary.setText(summary_text)
        summary.setFont(QFont('Arial', 16))
        result_layout.addWidget(summary)

        result_scroll_area = QScrollArea()
        result_scroll_area.setWidgetResizable(True)
        result_layout.addWidget(result_scroll_area)

        result_inner_widget = QWidget()
        result_inner_layout = QVBoxLayout(result_inner_widget)
        result_scroll_area.setWidget(result_inner_widget)

        for subject, subject_results in results['subjects'].items():
            toggle_button = QPushButton(f"{subject}")
            toggle_button.setCheckable(True)
            toggle_button.setChecked(False)  # Do not auto-expand
            subject_layout = QVBoxLayout()
            subject_group = QWidget()
            subject_group.setLayout(subject_layout)
            subject_group.setVisible(False)  # Hide by default

            for question_result in subject_results['questions']:
                question_group = QGroupBox(question_result['question'])
                question_layout = QVBoxLayout()
                question_group.setLayout(question_layout)
                user_answer_label = QLabel(f"Your answer: {question_result['your_answer']} - {question_result['your_answer_value']}")
                correct_answer_label = QLabel(f"Correct answer: {question_result['correct_answer']} - {question_result['correct_answer_value']}")
                result_label = QLabel(question_result['result'])

                if question_result['result'] == 'Correct':
                    user_answer_label.setStyleSheet("color: green;")
                    result_label.setStyleSheet("color: green;")
                else:
                    user_answer_label.setStyleSheet("color: red;")
                    result_label.setStyleSheet("color: red;")

                question_layout.addWidget(user_answer_label)
                question_layout.addWidget(correct_answer_label)
                question_layout.addWidget(result_label)
                subject_layout.addWidget(question_group)

            toggle_button.toggled.connect(lambda checked, group=subject_group: group.setVisible(checked))
            result_inner_layout.addWidget(toggle_button)
            result_inner_layout.addWidget(subject_group)

        result_window.setGeometry(200, 200, 800, 600)
        result_window.show()
        self.result_window = result_window

    def calculate_results(self):
        total_score = 0
        total_questions = 0
        results = {
            'total_score': 0,
            'total_questions': 0,
            'subjects': {}
        }

        for subject, questions in self.quiz_data.items():
            subject_score = 0
            subject_total = len(questions)
            subject_results = []
            for index, question_data in enumerate(questions):
                correct_answer = question_data['answer']
                correct_answer_value = question_data['options'][correct_answer]
                user_answer = self.selected_answers[subject][index]
                user_answer_value = question_data['options'][user_answer]
                if user_answer == correct_answer:
                    subject_score += 1
                    result = 'Correct'
                else:
                    result = 'Incorrect'
                subject_results.append({
                    'question': question_data['question'],
                    'your_answer': user_answer,
                    'your_answer_value': user_answer_value,
                    'correct_answer': correct_answer,
                    'correct_answer_value': correct_answer_value,
                    'result': result
                })
            results['subjects'][subject] = {
                'score': subject_score,
                'total': subject_total,
                'questions': subject_results
            }
            total_score += subject_score
            total_questions += subject_total

        results['total_score'] = total_score
        results['total_questions'] = total_questions

        return results

    def save_results_to_file(self):
        results = self.calculate_results()
        with open('quiz_results.txt', 'w', encoding='utf-8') as file:
            file.write(f"Total Score: {results['total_score']} / {results['total_questions']}\n")
            for subject, subject_results in results['subjects'].items():
                file.write(f"{subject}: {subject_results['score']} / {subject_results['total']}\n")
                for question_result in subject_results['questions']:
                    file.write(f"Question: {question_result['question']}\n")
                    file.write(f"Your answer: {question_result['your_answer']} - {question_result['your_answer_value']}\n")
                    file.write(f"Correct answer: {question_result['correct_answer']} - {question_result['correct_answer_value']}\n")
                    file.write(f"Result: {question_result['result']}\n")
                    file.write("\n")

    def update_timer(self):
        mins, secs = divmod(self.time_remaining, 60)
        time_format = '{:02d}:{:02d}'.format(mins, secs)
        self.timer_label.setText(f"Time Remaining: {time_format}")
        if self.time_remaining > 0:
            self.time_remaining -= 1
            QTimer.singleShot(1000, self.update_timer)
        else:
            self.submit_test()

if __name__ == "__main__":
    # Load the quiz data
    file_path = 'quiz_data.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        quiz_data = json.load(file)

    time_limit = 240 * 60  # Set time limit in seconds (e.g., 4 hours)

    app = QApplication(sys.argv)
    quiz_app = QuizApp(quiz_data, time_limit)
    quiz_app.show()
    sys.exit(app.exec_())
