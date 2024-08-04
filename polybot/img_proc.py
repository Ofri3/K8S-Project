import random
from pathlib import Path
from matplotlib.image import imread, imsave

def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')  # Use cmap='gray' if the image is in grayscale
        return str(new_path)

    def blur(self, blur_level=10, iterations=1):
        """
        Apply blur filter to the image.

        Args:
        blur_level (int): The size of the blur kernel.
        iterations (int): Number of times to apply the blur filter (default is 1).
        """
        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        for _ in range(iterations):
            result = []
            for i in range(height - blur_level + 1):
                row_result = []
                for j in range(width - blur_level + 1):
                    sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                    average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                    row_result.append(average)
                result.append(row_result)

            self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self, times=1):
        """
        Rotate the image.
        :param times: Number of times to rotate the image (default is 1).
        """
        # Determine the actual number of rotations needed (0 to 3)
        rotations = times % 4

        # Define a function to rotate the image data 90 degrees clockwise
        def rotate_90_clockwise(data):
            rotated_data = []
            width, height = len(data[0]), len(data)
            for x in range(width - 1, -1, -1):
                row = [data[y][x] for y in range(height)]
                rotated_data.append(row)
            return rotated_data

        # Perform the rotation
        for _ in range(rotations):
            self.data = rotate_90_clockwise(self.data)

    def salt_n_pepper(self, salt_prob=0.01, pepper_prob=0.01, iterations=1):
        """
        Add salt and pepper noise to the image.

        Args:
        salt_prob (float): Probability of a pixel getting set to max intensity (salt).
        pepper_prob (float): Probability of a pixel getting set to min intensity (pepper).
        iterations (int): Number of times to apply the salt and pepper noise (default is 1).
        """
        height = len(self.data)
        width = len(self.data[0])
        for _ in range(iterations):
            for i in range(height):
                for j in range(width):
                    rand_val = random.random()  # Generate a random number between 0 and 1
                    if rand_val < salt_prob:
                        self.data[i][j] = 255  # Set pixel to white (salt)
                    elif rand_val < salt_prob + pepper_prob:
                        self.data[i][j] = 0  # Set pixel to black (pepper)


    def concat(self, another_img, direction='horizontal'):
        """
        Concatenate another image to this image either horizontally or vertically.

        Args:
        another_img (Img): Another image object to concatenate.
        direction (str): 'horizontal' or 'vertical', the direction of concatenation.
        """
        # Check if dimensions are compatible for concatenation
        if direction == 'horizontal':
            if len(self.data) != len(another_img.data):
                raise RuntimeError("Images have different heights and cannot be concatenated horizontally.")
        elif direction == 'vertical':
            if len(self.data[0]) != len(another_img.data[0]):
                raise RuntimeError("Images have different widths and cannot be concatenated vertically.")
        else:
            raise ValueError("Invalid direction. Please specify 'horizontal' or 'vertical'.")

        # Concatenate images based on direction
        if direction == 'horizontal':
            self.data = [row_self + row_another for row_self, row_another in zip(self.data, another_img.data)]
        else:  # Vertical concatenation
            self.data += another_img.data

    def segment(self):
        if not self.data:
            raise RuntimeError("Image data is empty")

        # Define a threshold value to determine if two pixels are similar
        threshold = 10

        # Initialize a list to store the segments
        segments = []

        # Function to check if two pixel values are similar
        def is_similar(pixel1, pixel2):
            return abs(pixel1 - pixel2) < threshold

        # Function to find the segment index of a given pixel
        def find_segment(pixel):
            for i, segment in enumerate(segments):
                if is_similar(segment[0][2], pixel):
                    return i
            return None

        # Iterate through each pixel in the image
        for y, row in enumerate(self.data):
            for x, pixel in enumerate(row):
                segment_index = find_segment(pixel)
                if segment_index is not None:
                    segments[segment_index].append((x, y, pixel))
                else:
                    # Create a new segment
                    segments.append([(x, y, pixel)])  # Store pixel value along with coordinates

        # Generate a new image where each segment is represented by a unique color
        new_image = [[0] * len(row) for row in self.data]

        # Assign a unique color to each segment
        for i, segment in enumerate(segments):
            color = 0 if segment[0][2] < 128 else 255  # Assign black for darker segments and white for lighter segments
            for x, y, _ in segment:
                new_image[y][x] = color

        # Update the image data
        self.data = new_image

    def median(self, intensity=3):
        """
        Apply median filter to the image with adjustable intensity.
        """
        result = [[0] * len(self.data[0]) for _ in range(len(self.data))]

        for i in range(len(self.data)):
            for j in range(len(self.data[0])):
                # Extract the neighborhood pixels
                neighborhood = []
                for x in range(max(0, i - 1), min(len(self.data), i + 2)):
                    for y in range(max(0, j - 1), min(len(self.data[0]), j + 2)):
                        neighborhood.append(self.data[x][y])

                # Sort the neighborhood pixels and take the median
                neighborhood.sort()
                median_index = len(neighborhood) // 2
                median_value = neighborhood[median_index]

                # Update the result pixel with the median value
                result[i][j] = min(max(median_value * intensity, 0), 255)  # Clamp values to [0, 255]

        # Update the image data with the result
        self.data = result

    def edge_extraction(self, intensity=1):
        """
        Apply edge extraction filter to the image with adjustable intensity.
        """
        # Define the edge detection kernel
        kernel = [[-1, -1, -1],
                  [-1,  8, -1],
                  [-1, -1, -1]]

        # Convolve the image with the kernel
        result = [[0] * len(self.data[0]) for _ in range(len(self.data))]
        for i in range(len(self.data) - 2):
            for j in range(len(self.data[0]) - 2):
                total = 0
                for k in range(3):
                    for l in range(3):
                        total += self.data[i + k][j + l] * kernel[k][l]
                result[i + 1][j + 1] = min(max(total * intensity, 0), 255)  # Clamp values to [0, 255]

        # Update the image data with the result
        self.data = result

    # Instantiate the Img class with the path to your image file
my_img = Img(r'test/beatles.jpeg')

    # Perform operations on the image
my_img.blur()
my_img.contour()
my_img.concat(my_img, direction='horizontal')
    # You can perform other operations as needed

    # Save the modified image
    # saved_path = my_img.save_img()
