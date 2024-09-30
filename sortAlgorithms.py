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
    elif name == "Cocktail Sort":
        return cocktail_sort
    else:
        return bubble_sort 

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

def cocktail_sort(arr):
    n = len(arr)
    swapped = True
    start = 0
    end = n - 1
    while swapped:
        swapped = False
        # Traverse the array from left to right
        for i in range(start, end):
            yield i, i + 1, False, 2  # Comparison
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                yield i, i + 1, True, 4  # Swap occurred
                swapped = True
        if not swapped:
            break
        swapped = False
        end -= 1
        # Traverse the array from right to left
        for i in range(end - 1, start - 1, -1):
            yield i, i + 1, False, 2  # Comparison
            if arr[i] > arr[i + 1]:
                arr[i], arr[i + 1] = arr[i + 1], arr[i]
                yield i, i + 1, True, 4  # Swap occurred
                swapped = True
        start += 1