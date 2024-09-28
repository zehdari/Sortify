import sys
import os  # Added import os
import random
import time
from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsView, QGraphicsRectItem,
    QVBoxLayout, QWidget, QSlider, QPushButton, QHBoxLayout,
    QLabel, QComboBox, QLineEdit, QFileDialog
)
from PyQt6.QtCore import QTimer, QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QColor, QPen, QFont
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis

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
        self.timer_interval = 0  # Default delay in milliseconds
        self.steps_per_call = 1    # Default steps per call

        # Initialize sorting algorithm
        self.sorting_algorithm = get_algorithm_by_name(algorithm_name)

        # Setup the Qt graphics scene and view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setMinimumWidth(300)  # Set a minimum width for better display

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
            "Shell Sort"
            # You can add more algorithms here
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

        # Create a horizontal layout for the benchmark button and settings in the same row
        benchmark_row_layout = QHBoxLayout()

        # Benchmark Button
        self.benchmark_button = QPushButton("Benchmark")
        self.benchmark_button.clicked.connect(self.run_benchmark)
        benchmark_row_layout.addWidget(self.benchmark_button)

        # Max Size input
        self.max_size_input = QLineEdit("1000")  # Default value to 1000
        benchmark_row_layout.addWidget(QLabel("Max Size:"))
        benchmark_row_layout.addWidget(self.max_size_input)

        # Step Size input
        self.step_size_input = QLineEdit("10")  # Default value to 10
        benchmark_row_layout.addWidget(QLabel("Step Size:"))
        benchmark_row_layout.addWidget(self.step_size_input)

        # Add the benchmark_row_layout to the main layout
        self.buttons_layout.addLayout(benchmark_row_layout)

        # Now add the buttons_layout to the main layout
        layout.addLayout(self.buttons_layout)
        self.setLayout(layout)
        self.rectangles = []
        # Delay create_bars() until the widget is fully loaded
        QTimer.singleShot(0, self.create_bars)  # Ensure bars are created after loading

        # Set up a QTimer for smooth animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.visualize_step)

        # Track previously highlighted indices
        self.previous_highlighted_indices = []

    def create_bars(self):
        """Create bars based on the array and current window size."""
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

    def resizeEvent(self, event):
        """Handle resizing of the window to update the bars properly."""
        super().resizeEvent(event)
        self.create_bars()  # Recreate bars when the window is resized

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
            elapsed_time = (time.perf_counter() - self.start_time) * 1000  # Convert to milliseconds
            self.runtime_label.setText(f"Runtime: {elapsed_time:.2f} ms")

            # Start the green fill animation
            self.start_green_fill_animation()

        except Exception as e:
            print(f"Exception in visualize_step: {e}")
            self.timer.stop()

    def start_green_fill_animation(self):
        """Start the animation to turn bars green from smallest to largest."""
        total_duration = 2000  # Total duration in milliseconds
        num_bars = len(self.arr)
        delay_between_bars = total_duration / num_bars

        # Ensure delay is at least 1 ms
        delay_between_bars = max(1, delay_between_bars)

        # Sort indices based on the values in arr (from smallest to largest)
        self.green_fill_indices = sorted(range(num_bars), key=lambda i: self.arr[i])
        self.current_green_index = 0

        self.green_fill_timer = QTimer()
        self.green_fill_timer.timeout.connect(self.green_fill_step)
        self.green_fill_timer.start(int(delay_between_bars))

    def green_fill_step(self):
        if self.current_green_index < len(self.green_fill_indices):
            index = self.green_fill_indices[self.current_green_index]
            self.rectangles[index].setBrush(QColor('green'))
            self.current_green_index += 1
        else:
            self.green_fill_timer.stop()

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

    def update_labels(self):
        self.comparisons_label.setText(f"Comparisons: {self.comparisons}")
        self.accesses_label.setText(f"Array Accesses: {self.accesses}")

    def set_array_size(self, size):
        self.array_size = size
        self.arr = random.sample(range(1, self.array_size + 1), self.array_size)
        self.max_value = max(self.arr)
        self.create_bars()

    def set_timer_interval(self, interval):
        self.timer_interval = interval
        self.timer.setInterval(self.timer_interval)

    def set_steps_per_call(self, steps):
        self.steps_per_call = steps

    def shuffle_array(self, arr=None):
        self.timer.stop()
        if hasattr(self, 'green_fill_timer'):
            self.green_fill_timer.stop()

        if arr is None:
            self.arr = random.sample(range(1, self.array_size + 1), self.array_size)
        else:
            self.arr = arr.copy()

        self.max_value = max(self.arr)
        self.create_bars()

        # Reset highlighted indices
        self.previous_highlighted_indices = []

    def start_sorting(self):
        self.timer.stop()
        if hasattr(self, 'green_fill_timer'):
            self.green_fill_timer.stop()

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

    def run_benchmark(self):
        # Run benchmark synchronously
        self.perform_benchmark()

    def perform_benchmark(self):
        try:
            selected_algorithm_name = self.algorithm_dropdown.currentText()
            sorting_function = get_algorithm_by_name(selected_algorithm_name)

            # Get max size and step size from inputs
            try:
                max_size = int(self.max_size_input.text())
                step_size = int(self.step_size_input.text())
            except ValueError:
                max_size = 5000
                step_size = 250
                self.max_size_input.setText(str(max_size))
                self.step_size_input.setText(str(step_size))

            if max_size < 10:
                max_size = 10
                self.max_size_input.setText(str(max_size))
            if step_size < 1:
                step_size = 1
                self.step_size_input.setText(str(step_size))

            sizes = list(range(10, max_size + 1, step_size))
            runtimes = []

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
                runtimes.append(elapsed_time)

            # Display the benchmark results
            self.display_benchmark_results(sizes, runtimes, selected_algorithm_name)
        except Exception as e:
            print(f"Exception during benchmarking: {e}")

    def display_benchmark_results(self, sizes, runtimes, algorithm_name):
        # Create a new window to display the chart
        self.chart_window = QChartWindow(sizes, runtimes, algorithm_name)
        self.chart_window.show()

    def closeEvent(self, event):
        # Stop the main visualization timer
        if self.timer.isActive():
            self.timer.stop()
    
        # Stop the green fill timer if it exists and is active
        if hasattr(self, 'green_fill_timer') and self.green_fill_timer.isActive():
            self.green_fill_timer.stop()
    
        event.accept()  # Allow the window to close

class QChartWindow(QWidget):
    def __init__(self, sizes, runtimes, algorithm_name):
        super().__init__()
        self.setWindowTitle(f"Benchmark of {algorithm_name}")
        self.setMinimumSize(1000, 800)  # Set a larger initial size

        # Create the chart and add data
        self.series = QLineSeries()
        for size, runtime in zip(sizes, runtimes):
            self.series.append(size, runtime)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle(f"Benchmark of {algorithm_name}")

        # Customize axes
        axis_x = QValueAxis()
        axis_x.setTitleText("Array Size (n)")
        axis_x.setLabelFormat("%d")
        max_labels = 10  # Maximum number of labels to display
        tick_interval = max(1, len(sizes) // max_labels)
        axis_x.setTickCount(min(len(sizes), max_labels + 1))
        axis_x.setRange(min(sizes), max(sizes))

        axis_y = QValueAxis()
        axis_y.setTitleText("Runtime (ms)")
        axis_y.setLabelFormat("%.3f")  # Show more decimal places
        axis_y.setRange(0, max(runtimes) * 1.1)  # Add 10% padding

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
        self.series.attachAxis(axis_x)
        self.series.attachAxis(axis_y)

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
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Graph As",
            "",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
            options=options
        )
        if filename:
            pixmap = self.chart_view.grab()
            pixmap.save(filename)

def get_algorithm_by_name(name):
    if name == "Bubble Sort":
        return bubble_sort
    elif name == "Selection Sort":
        return selection_sort
    elif name == "Insertion Sort":
        return insertion_sort
    elif name == "Merge Sort":
        return merge_sort
    elif name == "Quick Sort":
        return quick_sort
    elif name == "Heap Sort":
        return heap_sort
    elif name == "Shell Sort":
        return shell_sort
    else:
        return bubble_sort  # Default to Bubble Sort

# Sorting algorithm implementations

def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            yield j, j + 1, False, 2  # Comparison
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                yield j, j + 1, True, 4  # Swap happened
                swapped = True
        if not swapped:
            break

def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            yield min_idx, j, False, 2  # Comparison
            if arr[j] < arr[min_idx]:
                min_idx = j
        if min_idx != i:
            arr[i], arr[min_idx] = arr[min_idx], arr[i]
            yield i, min_idx, True, 4  # Swap happened
        else:
            yield i, min_idx, False, 2  # No swap

def insertion_sort(arr):
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        while j >= 0:
            yield j, j + 1, False, 2  # Comparison
            if arr[j] > key:
                arr[j + 1] = arr[j]
                yield j + 1, j, True, 1  # Shift
                j -= 1
            else:
                break
        arr[j + 1] = key
        yield j + 1, j + 1, True, 1  # Insertion

def merge_sort(arr):
    def merge_sort_rec(arr, start, end):
        if end - start > 1:
            mid = (start + end) // 2
            yield from merge_sort_rec(arr, start, mid)
            yield from merge_sort_rec(arr, mid, end)
            yield from merge(arr, start, mid, end)

    def merge(arr, start, mid, end):
        left_subarray = arr[start:mid]
        right_subarray = arr[mid:end]

        left_idx, right_idx = 0, 0
        current_idx = start

        while left_idx < len(left_subarray) and right_idx < len(right_subarray):
            yield start + left_idx, mid + right_idx, False, 2  # Comparison

            if left_subarray[left_idx] <= right_subarray[right_idx]:
                arr[current_idx] = left_subarray[left_idx]
                left_idx += 1
            else:
                arr[current_idx] = right_subarray[right_idx]
                right_idx += 1

            yield current_idx, current_idx, True, 1  # Placement
            current_idx += 1

        while left_idx < len(left_subarray):
            arr[current_idx] = left_subarray[left_idx]
            left_idx += 1
            yield current_idx, current_idx, True, 1  # Placement
            current_idx += 1

        while right_idx < len(right_subarray):
            arr[current_idx] = right_subarray[right_idx]
            right_idx += 1
            yield current_idx, current_idx, True, 1  # Placement
            current_idx += 1

    yield from merge_sort_rec(arr, 0, len(arr))

def quick_sort(arr):
    def quick_sort_rec(arr, low, high):
        if low < high:
            pi = yield from partition(arr, low, high)
            yield from quick_sort_rec(arr, low, pi - 1)
            yield from quick_sort_rec(arr, pi + 1, high)

    def partition(arr, low, high):
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            yield j, high, False, 2  # Comparison
            if arr[j] < pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
                yield i, j, True, 4  # Swap
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        yield i + 1, high, True, 4  # Swap pivot
        return i + 1

    yield from quick_sort_rec(arr, 0, len(arr) - 1)

def heap_sort(arr):
    n = len(arr)

    def heapify(arr, n, i):
        largest = i
        l = 2 * i + 1     # Left child
        r = 2 * i + 2     # Right child

        if l < n:
            yield i, l, False, 2  # Comparison
            if arr[l] > arr[largest]:
                largest = l

        if r < n:
            yield largest, r, False, 2  # Comparison
            if arr[r] > arr[largest]:
                largest = r

        if largest != i:
            arr[i], arr[largest] = arr[largest], arr[i]
            yield i, largest, True, 4  # Swap
            yield from heapify(arr, n, largest)

    # Build a maxheap
    for i in range(n // 2 - 1, -1, -1):
        yield from heapify(arr, n, i)

    # One by one extract elements
    for i in range(n - 1, 0, -1):
        arr[i], arr[0] = arr[0], arr[i]
        yield i, 0, True, 4  # Swap
        yield from heapify(arr, i, 0)

def shell_sort(arr):
    n = len(arr)
    gap = n // 2

    while gap > 0:
        for i in range(gap, n):
            temp = arr[i]
            j = i

            while j >= gap:
                yield j, j - gap, False, 2  # Comparison
                if arr[j - gap] > temp:
                    arr[j] = arr[j - gap]
                    yield j, j - gap, True, 1  # Shift
                    j -= gap
                else:
                    break
            arr[j] = temp
            yield j, j, True, 1  # Insertion
        gap //= 2

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
        controls_layout = QVBoxLayout()

        # Array size slider
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setMinimum(4)
        self.size_slider.setMaximum(1000)
        self.size_slider.setValue(self.visualizer1.array_size)
        self.size_slider.valueChanged.connect(self.adjust_array_size)
        self.size_label = QLabel(f"Array Size: {self.visualizer1.array_size}")
        controls_layout.addWidget(self.size_label)
        controls_layout.addWidget(self.size_slider)

        # Delay slider
        self.delay_slider = QSlider(Qt.Orientation.Horizontal)
        self.delay_slider.setMinimum(0)
        self.delay_slider.setMaximum(1000)
        self.delay_slider.setValue(self.visualizer1.timer_interval)
        self.delay_slider.valueChanged.connect(self.adjust_timer_interval)
        self.delay_label = QLabel(f"Delay: {self.visualizer1.timer_interval} ms")
        controls_layout.addWidget(self.delay_label)
        controls_layout.addWidget(self.delay_slider)

        # Steps per call slider
        self.steps_slider = QSlider(Qt.Orientation.Horizontal)
        self.steps_slider.setMinimum(1)
        self.steps_slider.setMaximum(1000)
        self.steps_slider.setValue(self.visualizer1.steps_per_call)
        self.steps_slider.valueChanged.connect(self.adjust_steps_per_call)
        self.steps_label = QLabel(f"Steps per Call: {self.visualizer1.steps_per_call}")
        controls_layout.addWidget(self.steps_label)
        controls_layout.addWidget(self.steps_slider)

        main_layout.addLayout(controls_layout)

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
    
    def closeEvent(self, event):
        # Close child SortingVisualizer instances
        self.visualizer1.close()
        self.visualizer2.close()
        event.accept()  # Allow the window to close

if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Set the taskbar and window icon
    app.setWindowIcon(QIcon(resource_path("resources/sorticon.ico")))

    # Instantiate the main window with two sorting visualizers
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec())
