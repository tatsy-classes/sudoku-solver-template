import os
import re
import glob

import cv2
import numpy as np
import pytest
import colorama
from sudoku import solve

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CUR_DIR, "data")


def get_test_data():
    rng = np.random.RandomState(31415)

    levels = [1, 2, 3]
    data = []
    for level in levels:
        image_paths = glob.glob(os.path.join(DATA_DIR, "level{:d}/*.jpg".format(level)))
        if len(image_paths) > 10:
            idx = rng.choice(len(image_paths), 10)
            image_paths = [image_paths[i] for i in idx]
            image_paths = sorted(image_paths)
        data.extend([(path, level) for path in image_paths])

    return data


def check(answer, problem):
    # check if the answer is the one from the problem
    match = (answer == problem).astype("int32")
    if not (match[problem != 0] == 1).all():
        return (False, "Recognized numbers may be wrong")

    # check each row
    nums = list(range(1, 10))
    for i in range(9):
        s = set(answer[i])

        ok = True
        if 0 in s:
            ok = False

        if len(s) != 9:
            ok = False

        for n in nums:
            if n not in s:
                ok = False
                break

        if not ok:
            return (False, "A row does not contain all numbers 1-9")

    for j in range(9):
        s = set(answer[:, j])

        ok = True
        if 0 in s:
            ok = False

        if len(s) != 9:
            ok = False

        for n in nums:
            if n not in s:
                ok = False
                break

        if not ok:
            return (False, "A column does not contain all numbers 1-9")

    for i in range(0, 9, 3):
        for j in range(0, 9, 3):
            blk = answer[i : i + 3, j : j + 3].flatten()
            s = set(blk)

            ok = True

            if 0 in s:
                ok = False

            if len(s) != 9:
                ok = False

            for n in nums:
                if n not in s:
                    ok = False
                    break

            if not ok:
                return (False, "A block does not contain all numbers 1-9")

    return (True, "Success")


class Sudoku(object):
    def __init__(self, image_path: str, text_path: str) -> None:
        self.image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)

        num_dict = {str(i): i for i in range(0, 10)}
        with open(text_path, "r") as f:
            text = f.read()

        text_chars = re.split(r"[\s]+", text)
        text_chars = [c for line in text_chars for c in line]
        text_chars = [num_dict[c] for c in text_chars if c != ""]
        self.problem = np.array(text_chars, dtype="int32").reshape((9, 9))


@pytest.fixture(scope="session")
def score():
    colorama.init()
    s = np.zeros((1), dtype="int32")

    yield s

    print()
    print(colorama.Back.BLUE + "[INFO] Your score is {:d}".format(s.item()), end="")
    print(colorama.Style.RESET_ALL)


@pytest.mark.parametrize("image_path, level", get_test_data())
def test_solve(image_path: str, level: int, score):
    basename = os.path.splitext(image_path)[0]
    answer_path = basename + ".txt"
    sudoku = Sudoku(image_path, answer_path)
    output = solve(sudoku.image)

    assert isinstance(output, np.ndarray), "Return NumPy's NDArray!"
    assert output.dtype == np.int32, "Return NumPy array with int32 data type!"
    assert output.ndim == 2, "#dimensions of NumPy array must be 2!"
    assert output.shape[0] == 9 and output.shape[1] == 9, "Size of the NumPy array must be 9x9!"

    succ, msg = check(output, sudoku.problem)
    if succ:
        score += level
    else:
        pytest.fail("Your answer is wrong: {:s}".format(msg))
