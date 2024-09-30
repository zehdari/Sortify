import sys
import os
import random
import time
from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QFileDialog, QCheckBox, QGroupBox, QScrollArea
)
from PyQt6.QtCore import QTimer, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QFont
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

from sortAlgorithms import *

def resource_path(relative_path):
    """Get absolute path to resource, works for PyInstaller and development."""
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SortingVisualizer(QWidget):
    def __init__(self, parent=None, array_size=50, algorithm_name="Bubble Sort"):
        super().__init__(parent)
        self.array_size = array_size
        self.arr = random.sample(range(1, self.array_size + 1), self.array_size)
        self.max_value = max(self.arr)

        # Initialize counters
        self.comparisons = 0
        self.accesses = 0
        self.timer_interval = 0  # Default timer interval in ms
        self.steps_per_call = 1  

        # Initialize sorting algorithm
        self.sorting_algorithm = get_algorithm_by_name(algorithm_name)

        # Setup the Qt graphics scene and view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setMinimumWidth(300)

        # Create layout and add view
        layout = QVBoxLayout()
        layout.addWidget(self.view)

        # Add dropdown to select sorting algorithm
        self.algorithm_dropdown = QComboBox()
        self.algorithm_dropdown.addItems([
            "Bubble Sort",
            "Selection Sort",
            "Insertion Sort",
            "Merge Sort",
            "Quick Sort",
            "Heap Sort",
            "Shell Sort",
            "Cocktail Sort"
        ])
        self.algorithm_dropdown.setCurrentText(algorithm_name)
        self.algorithm_dropdown.currentIndexChanged.connect(self.change_sorting_algorithm)
        layout.addWidget(self.algorithm_dropdown)

        # Labels to display stats
        self.comparisons_label = QLabel(f"Comparisons: {self.comparisons}")
        self.accesses_label = QLabel(f"Array Accesses: {self.accesses}")
        layout.addWidget(self.comparisons_label)
        layout.addWidget(self.accesses_label)

        # Label to display runtime
        self.runtime_label = QLabel(f"Runtime: 0 ms")
        layout.addWidget(self.runtime_label)

        # Add buttons and inputs arranged vertically
        self.buttons_layout = QVBoxLayout()

        # Sort Button
        self.sort_button = QPushButton("Sort")
        self.sort_button.clicked.connect(self.start_sorting)
        self.buttons_layout.addWidget(self.sort_button)

        # Now add the buttons_layout to the main layout
        layout.addLayout(self.buttons_layout)
        self.setLayout(layout)
        self.rectangles = []
        # Delay create_bars() until the widget is fully loaded
        QTimer.singleShot(0, self.create_bars) 

        # Set up a QTimer for smooth animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.visualize_step)
        self.timer.setInterval(self.timer_interval)

        # Initialize green_fill_timer to None 
        self.green_fill_timer = None 

        # Define total duration for green fill
        self.green_fill_total_duration = 2000  # in milliseconds

        # Define desired timer interval for green fill
        self.green_fill_timer_interval = 30  # in milliseconds

        # Calculate steps_per_tick based on array size
        self.calculate_green_fill_parameters()

        # Track previously highlighted indices
        self.previous_highlighted_indices = []

    def calculate_green_fill_parameters(self):
        """
        Calculate steps_per_tick to ensure the green fill animation completes
        within the total_duration regardless of array size.
        """
        num_bars = len(self.arr)
        max_ticks = self.green_fill_total_duration / self.green_fill_timer_interval
        self.steps_per_tick = max(1, num_bars // int(max_ticks)) if max_ticks > 0 else 1

    # Create bars based on the array and current window size.
    def create_bars(self):
        # Stop the green fill timer if it's active
        if self.green_fill_timer is not None and self.green_fill_timer.isActive():
            self.green_fill_timer.stop()
            self.green_fill_timer = None 
            self.reset_colors() 

        scene_width = self.view.viewport().width()
        scene_height = self.view.viewport().height()

        bar_width = scene_width / len(self.arr)
        self.scene.clear()
        self.rectangles = []

        for i, value in enumerate(self.arr):
            bar_height = (value / self.max_value) * scene_height
            rect_item = QGraphicsRectItem(QRectF(
                i * bar_width,
                scene_height - bar_height,
                bar_width,
                bar_height
            ))
            rect_item.setBrush(QColor('blue'))
            rect_item.setPen(QPen(Qt.PenStyle.NoPen))
            self.scene.addItem(rect_item)
            self.rectangles.append(rect_item)

    # Recreate bars when the window is resized
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.create_bars()  

    def visualize_step(self):
        try:
            for _ in range(self.steps_per_call):
                i, j, swap, accesses = next(self.sort_generator)

                # Reset the previous bar colors
                self.reset_colors()

                # Handle comparison or placement
                if i != j:
                    self.rectangles[i].setBrush(QColor('red'))
                    self.rectangles[j].setBrush(QColor('red'))
                else:
                    self.rectangles[i].setBrush(QColor('blue'))

                # Update the heights of the bars after placement
                self.update_bar(i, self.arr[i])

                if swap:
                    self.update_bar(j, self.arr[j])

                # Update the list of highlighted indices
                if i != j:
                    self.previous_highlighted_indices = [i, j]
                else:
                    self.previous_highlighted_indices = [i]

                self.accesses += accesses
                self.comparisons += 1

            self.update_labels()

        except StopIteration:
            # Once sorting is done, reset the colors and stop the timer
            self.reset_colors()
            self.timer.stop()

            # Calculate elapsed time including delays
            elapsed_time = (time.perf_counter() - self.start_time) * 1000 
            self.runtime_label.setText(f"Runtime: {elapsed_time:.2f} ms")

            # Start the green fill animation
            self.start_green_fill_animation()

        except Exception as e:
            print(f"Exception in visualize_step: {e}")
            self.timer.stop()

    def start_green_fill_animation(self):
        """Start the animation to turn bars green from smallest to largest."""
        # Stop the green fill timer if it's active
        if self.green_fill_timer is not None and self.green_fill_timer.isActive():
            self.green_fill_timer.stop()
            self.green_fill_timer = None 
            self.reset_colors() 

        # Sort indices based on the values in arr (from smallest to largest)
        self.green_fill_indices = sorted(range(len(self.arr)), key=lambda i: self.arr[i])
        self.current_green_index = 0

        # Recalculate steps_per_tick in case array size has changed
        self.calculate_green_fill_parameters()

        # Initialize the green_fill_timer with a separate QTimer instance
        self.green_fill_timer = QTimer()
        self.green_fill_timer.timeout.connect(self.green_fill_step)
        self.green_fill_timer.start(self.green_fill_timer_interval)

    def green_fill_step(self):
        """Update multiple bars per timer tick based on steps_per_tick."""
        if self.current_green_index < len(self.green_fill_indices):
            end_index = min(self.current_green_index + self.steps_per_tick, len(self.green_fill_indices))
            for idx in range(self.current_green_index, end_index):
                index = self.green_fill_indices[idx]
                self.rectangles[index].setBrush(QColor('green'))
            self.current_green_index = end_index
        else:
            self.green_fill_timer.stop()
            self.green_fill_timer = None

    def update_bar(self, index, value):
        scene_height = self.view.viewport().height()

        bar_height = (value / self.max_value) * scene_height
        rect_item = self.rectangles[index]
        rect_item.setRect(QRectF(
            rect_item.rect().x(),
            scene_height - bar_height,
            rect_item.rect().width(),
            bar_height
        ))

    def reset_colors(self):
        for index in self.previous_highlighted_indices:
            self.rectangles[index].setBrush(QColor('blue'))
        self.previous_highlighted_indices = []

    def update_labels(self):
        self.comparisons_label.setText(f"Comparisons: {self.comparisons}")
        self.accesses_label.setText(f"Array Accesses: {self.accesses}")

    def set_array_size(self, size):
        self.array_size = size
        self.arr = random.sample(range(1, self.array_size + 1), self.array_size)
        self.max_value = max(self.arr)
        self.create_bars()
        # Recalculate green fill parameters when array size changes
        self.calculate_green_fill_parameters()

    def set_timer_interval(self, interval):
        self.timer_interval = interval
        self.timer.setInterval(self.timer_interval)

    def set_steps_per_call(self, steps):
        self.steps_per_call = steps

    def shuffle_array(self, arr=None):
        self.timer.stop()
        if self.green_fill_timer is not None and self.green_fill_timer.isActive():  
            self.green_fill_timer.stop()
            self.green_fill_timer = None 

        if arr is None:
            self.arr = random.sample(range(1, self.array_size + 1), self.array_size)
        else:
            self.arr = arr.copy()

        self.max_value = max(self.arr)
        self.create_bars()

        # Reset highlighted indices
        self.previous_highlighted_indices = []

        # Recalculate green fill parameters after shuffling
        self.calculate_green_fill_parameters()

    def start_sorting(self):
        self.timer.stop()
        if self.green_fill_timer is not None and self.green_fill_timer.isActive():  
            self.green_fill_timer.stop()
            self.green_fill_timer = None  # Remove reference

        self.sort_generator = self.sorting_algorithm(self.arr)
        # Reset counters
        self.comparisons = 0
        self.accesses = 0
        self.update_labels()

        # Record the start time
        self.start_time = time.perf_counter()

        self.timer.start(self.timer_interval)

        # Reset highlighted indices
        self.previous_highlighted_indices = []

    def change_sorting_algorithm(self):
        selected_algorithm = self.algorithm_dropdown.currentText()
        self.sorting_algorithm = get_algorithm_by_name(selected_algorithm)

    def closeEvent(self, event):
        # Stop the main visualization timer
        if self.timer.isActive():
            self.timer.stop()

        # Stop the green fill timer if it exists and is active
        if self.green_fill_timer is not None and self.green_fill_timer.isActive():  # **Modified Condition**
            self.green_fill_timer.stop()

        event.accept()  # Allow the window to close

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sortify")

        main_layout = QVBoxLayout()

        # Create two sorting visualizers
        self.visualizer1 = SortingVisualizer(algorithm_name="Bubble Sort")
        self.visualizer2 = SortingVisualizer(algorithm_name="Quick Sort")

        visualizers_layout = QHBoxLayout()
        visualizers_layout.addWidget(self.visualizer1)
        visualizers_layout.addWidget(self.visualizer2)

        main_layout.addLayout(visualizers_layout)

        # Shared controls
        controls_layout = QVBoxLayout()  # Changed from QHBoxLayout to QVBoxLayout

        # Array size controls
        size_control_layout = QVBoxLayout()
        self.size_label = QLabel(f"Array Size: {self.visualizer1.array_size}")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(4)
        self.size_slider.setMaximum(5000)
        self.size_slider.setValue(self.visualizer1.array_size)
        self.size_slider.valueChanged.connect(self.adjust_array_size)
        size_control_layout.addWidget(self.size_label)
        size_control_layout.addWidget(self.size_slider)
        controls_layout.addLayout(size_control_layout)

        # Delay controls
        delay_control_layout = QVBoxLayout()
        self.delay_label = QLabel(f"Delay: {self.visualizer1.timer_interval} ms")
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(1000)
        self.delay_slider.setValue(self.visualizer1.timer_interval)
        self.delay_slider.valueChanged.connect(self.adjust_timer_interval)
        delay_control_layout.addWidget(self.delay_label)
        delay_control_layout.addWidget(self.delay_slider)
        controls_layout.addLayout(delay_control_layout)

        # Steps per call controls
        steps_control_layout = QVBoxLayout()
        self.steps_label = QLabel(f"Steps per Call: {self.visualizer1.steps_per_call}")
        self.steps_slider = QSlider(Qt.Orientation.Horizontal)
        self.steps_slider.setMinimum(1)
        self.steps_slider.setMaximum(1000)
        self.steps_slider.setValue(self.visualizer1.steps_per_call)
        self.steps_slider.valueChanged.connect(self.adjust_steps_per_call)
        steps_control_layout.addWidget(self.steps_label)
        steps_control_layout.addWidget(self.steps_slider)
        controls_layout.addLayout(steps_control_layout)

        # Optional: Add spacing between controls
        controls_layout.addSpacing(10)

        main_layout.addLayout(controls_layout)

        # Benchmark Controls Layout
        benchmark_controls_layout = QVBoxLayout()
        benchmark_group = QGroupBox("Benchmark Settings")
        benchmark_group_layout = QVBoxLayout()

        # Algorithm Checkboxes
        self.algorithm_checkboxes = []
        algorithms = [
            "Bubble Sort",
            "Selection Sort",
            "Insertion Sort",
            "Merge Sort",
            "Quick Sort",
            "Heap Sort",
            "Shell Sort",
            "Cocktail Sort"
        ]
        checkbox_layout = QHBoxLayout()
        for algo in algorithms:
            checkbox = QCheckBox(algo)
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.update_benchmark_button_state)
            self.algorithm_checkboxes.append(checkbox)
            checkbox_layout.addWidget(checkbox)
        benchmark_group_layout.addLayout(checkbox_layout)

        # Max Size and Step Size inputs arranged horizontally
        benchmark_input_layout = QHBoxLayout()

        # Max Size input
        max_size_layout = QVBoxLayout()
        self.benchmark_max_size_input = QLineEdit("1000") 
        max_size_layout.addWidget(QLabel("Max Size:"))
        max_size_layout.addWidget(self.benchmark_max_size_input)
        benchmark_input_layout.addLayout(max_size_layout)

        # Step Size input
        step_size_layout = QVBoxLayout()
        self.benchmark_step_size_input = QLineEdit("10")  
        step_size_layout.addWidget(QLabel("Step Size:"))
        step_size_layout.addWidget(self.benchmark_step_size_input)
        benchmark_input_layout.addLayout(step_size_layout)

        benchmark_group_layout.addLayout(benchmark_input_layout)

        # Benchmark Button
        self.benchmark_button = QPushButton("Benchmark")
        self.benchmark_button.clicked.connect(self.run_benchmark)
        self.benchmark_button.setEnabled(True)
        benchmark_group_layout.addWidget(self.benchmark_button)

        benchmark_group.setLayout(benchmark_group_layout)
        benchmark_controls_layout.addWidget(benchmark_group)
        main_layout.addLayout(benchmark_controls_layout)

        # Buttons for start and shuffle, arranged horizontally
        buttons_layout = QHBoxLayout()

        # Start Race Button
        self.start_button = QPushButton("Start Race")
        self.start_button.clicked.connect(self.start_race)
        buttons_layout.addWidget(self.start_button)

        # Shuffle Button
        self.shuffle_button = QPushButton("Shuffle")
        self.shuffle_button.clicked.connect(self.sync_shuffle)
        buttons_layout.addWidget(self.shuffle_button)

        # Add the buttons layout to the main layout
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

    def adjust_array_size(self):
        self.visualizer1.timer.stop()
        self.visualizer2.timer.stop()
        size = self.size_slider.value()
        self.size_label.setText(f"Array Size: {size}")
        self.visualizer1.set_array_size(size)
        self.visualizer2.set_array_size(size)

    def adjust_timer_interval(self):
        interval = self.delay_slider.value()
        self.delay_label.setText(f"Delay: {interval} ms")
        self.visualizer1.set_timer_interval(interval)
        self.visualizer2.set_timer_interval(interval)

    def adjust_steps_per_call(self):
        steps = self.steps_slider.value()
        self.steps_label.setText(f"Steps per Call: {steps}")
        self.visualizer1.set_steps_per_call(steps)
        self.visualizer2.set_steps_per_call(steps)

    def sync_shuffle(self):
        # Generate a new random array
        array_size = self.visualizer1.array_size
        new_array = random.sample(range(1, array_size + 1), array_size)

        # Set the same array in both visualizers
        self.visualizer1.shuffle_array(arr=new_array)
        self.visualizer2.shuffle_array(arr=new_array)

    def start_race(self):
        # Start sorting in both visualizers
        self.visualizer1.start_sorting()
        self.visualizer2.start_sorting()

    def run_benchmark(self):
        selected_algorithms = [cb.text() for cb in self.algorithm_checkboxes if cb.isChecked()]
        if not selected_algorithms:
            print("No algorithms selected for benchmarking.")
            return

        # Get max size and step size from inputs
        try:
            max_size = int(self.benchmark_max_size_input.text())
            step_size = int(self.benchmark_step_size_input.text())
        except ValueError:
            max_size = 5000
            step_size = 250
            self.benchmark_max_size_input.setText(str(max_size))
            self.benchmark_step_size_input.setText(str(step_size))

        if max_size < 10:
            max_size = 10
            self.benchmark_max_size_input.setText(str(max_size))
        if step_size < 1:
            step_size = 1
            self.benchmark_step_size_input.setText(str(step_size))

        sizes = list(range(10, max_size + 1, step_size))
        runtimes_dict = {algo: [] for algo in selected_algorithms}

        for algo_name in selected_algorithms:
            sorting_function = get_algorithm_by_name(algo_name, False)
            for size in sizes:
                arr = random.sample(range(size), size)
                arr_copy = arr.copy()

                start_time = time.perf_counter()

                # Run the sorting algorithm without visualization
                sort_generator = sorting_function(arr_copy)
                for _ in sort_generator:
                    pass  # We don't need to process the steps

                end_time = time.perf_counter()
                elapsed_time = (end_time - start_time) * 1000  # Convert to milliseconds with decimals
                runtimes_dict[algo_name].append(elapsed_time)

        # Display all benchmark results on a single chart
        self.display_benchmark_results(sizes, runtimes_dict, selected_algorithms)

    def display_benchmark_results(self, sizes, runtimes_dict, algorithm_names):
        # Create a new window to display the chart
        self.chart_window = QChartWindow(sizes, runtimes_dict, algorithm_names)
        self.chart_window.show()

    def update_benchmark_button_state(self):
        # Enable the benchmark button if at least one checkbox is checked
        any_checked = any(cb.isChecked() for cb in self.algorithm_checkboxes)
        self.benchmark_button.setEnabled(any_checked)

    def closeEvent(self, event):
        # Close child SortingVisualizer instances
        self.visualizer1.close()
        self.visualizer2.close()
        # Ensure the application quits completely
        QApplication.quit()
        event.accept()  # Allow the window to close

class QChartWindow(QWidget):
    def __init__(self, sizes, runtimes_dict, algorithm_names):
        super().__init__()
        self.setWindowTitle("Benchmark Results")
        self.setMinimumSize(1000, 800)  # Set a larger initial size

        # Create the chart
        self.chart = QChart()
        self.chart.setTitle("Benchmark Results")

        # Define a list of colors for different algorithms
        colors = [
            QColor('red'), QColor('green'), QColor('blue'),
            QColor('magenta'), QColor('cyan'), QColor('orange'),
            QColor('purple'), QColor('brown'), QColor('pink'),
            QColor('gray')
        ]

        # Add a QLineSeries for each algorithm
        for idx, algo_name in enumerate(algorithm_names):
            series = QLineSeries()
            for size, runtime in zip(sizes, runtimes_dict[algo_name]):
                series.append(size, runtime)
            series.setName(algo_name)
            series.setColor(colors[idx % len(colors)])
            self.chart.addSeries(series)

        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        # Customize axes
        axis_x = QValueAxis()
        axis_x.setTitleText("Array Size (n)")
        axis_x.setLabelFormat("%d")
        max_labels = 10  # Maximum number of labels to display
        tick_interval = max(1, len(sizes) // max_labels)
        axis_x.setTickCount(min(len(sizes), max_labels + 1))
        axis_x.setRange(min(sizes), max(sizes))

        # Determine the maximum runtime across all algorithms for Y-axis range
        max_runtime = max([max(runtimes) for runtimes in runtimes_dict.values()]) if algorithm_names else 100
        axis_y = QValueAxis()
        axis_y.setTitleText("Runtime (ms)")
        axis_y.setLabelFormat("%.3f")  # Show more decimal places
        axis_y.setRange(0, max_runtime * 1.1)  # Add 10% padding

        # Set font sizes
        font = QFont()
        font.setPointSize(12)
        axis_x.setLabelsFont(font)
        axis_y.setLabelsFont(font)
        axis_x.setTitleFont(font)
        axis_y.setTitleFont(font)
        self.chart.setTitleFont(font)

        # Add axes to the chart
        self.chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self.chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)

        # Attach axes to the series
        for series in self.chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

        # Create the chart view and set it as the central widget
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)

        layout = QVBoxLayout()
        layout.addWidget(self.chart_view)

        # Add Save Graph button
        self.save_button = QPushButton("Save Graph")
        self.save_button.clicked.connect(self.save_graph)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_graph(self):
        # Open a file dialog to save the image
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph As",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
        )
        if filename:
            pixmap = self.chart_view.grab()
            pixmap.save(filename)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set the taskbar and window icon
    icon_path = resource_path("resources/sorticon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    else:
        print(f"Icon not found at {icon_path}. Continuing without setting the icon.")

    # Instantiate the main window with two sorting visualizers
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
