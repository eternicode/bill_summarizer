import itertools
from typing import List, Tuple

import cv2


def get_lines_bruteforce(image_bw) -> List[Tuple[int, int, int, int]]:
    lines = []
    line = ()
    is_line = False

    height, width = image_bw.shape

    for y in range(height):
        for x in range(width):
            if image_bw[y, x] < 200:
                if not is_line:
                    is_line = True
                    line = (x, y)
            else:
                if is_line:
                    is_line = False
                    line += (x - 1, y)
                    lines.append(line)
    return lines


def get_lines_algorithm(image_bw) -> List[Tuple[int, int, int, int]]:
    # edges = cv2.Canny(image, 100, 150, apertureSize=3)
    image_inverted = 255 - image_bw

    lines = cv2.HoughLinesP(
        image_inverted,
        1,
        3.14159 / 180,
        threshold=20,
        minLineLength=10,
        maxLineGap=1,
    )

    return [line[0] for line in lines]


def get_image_lines(filename):
    image_grey = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)

    # White out the state seal in the corner
    height, width = image_grey.shape
    seal_bounding_box = (120, height - 170, 230, height - 70)
    bottom_bounding_box = (0, height - 3, width, height)
    for box in [seal_bounding_box, bottom_bounding_box]:
        cv2.rectangle(
            image_grey,
            (box[0], box[1]),
            (box[2], box[3]),
            (255, 255, 255),
            -1,
        )

    return get_lines_bruteforce(image_grey)


if __name__ == "__main__":
    lines = get_image_lines("docs/bg1.png")

    print(len(lines))
    if len(lines) < 10:
        print(lines)

    colors = list(itertools.product([0, 127, 255], repeat=3))[1:-1]
    verify = cv2.imread("docs/bg1.png")
    color = colors[-1]
    for line in lines:
        color = colors[(colors.index(color) + 1) % len(colors)]

        x1, y1, x2, y2 = line
        cv2.line(verify, (x1, y1), (x2, y2), color, 1)
    cv2.imwrite("docs/bg1-verify.png", verify)
