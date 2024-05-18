import math
import os
import shutil
import sys

import pandas as pd

from lines import get_image_lines


def process_pdf(filename):
    shutil.rmtree("tmp", ignore_errors=True)

    os.system(f"pdf2htmlEX --dest-dir tmp/ --embed-image 0 {filename}")

    os.system(f"textricator text --input-format=pdf.pdfbox {filename} tmp/contents.csv")
    rows = pd.read_csv("tmp/contents.csv")
    rows[["ulx", "uly", "lrx", "lry"]] = rows[["ulx", "uly", "lrx", "lry"]] * 2

    ignore_bounds = [
        (600, 180, 625, 210),  # page number
        (310, 1380, 520, 1420),  # footer
    ]

    # remove rows that are entirely within the ignore bounds
    rows = rows[
        ~rows.apply(
            lambda row: any(
                (row["ulx"] >= iulx)
                & (row["uly"] >= iuly)
                & (row["lrx"] <= ilrx)
                & (row["lry"] <= ilry)
                for iulx, iuly, ilrx, ilry in ignore_bounds
            ),
            axis=1,
        )
    ]

    page_count = rows["page"].max()

    for page_num in range(1, page_count + 1):
        lines = get_image_lines(f"tmp/bg{page_num:x}.png")
        words = rows[rows["page"] == page_num]

        leftmost_text = words["ulx"].min()

        def is_word_struck(ulx, uly, lrx, lry):
            for line in lines:
                x1, y1, x2, y2 = line
                if (uly <= y1) & (lry >= y1) & (ulx <= x2) & (lrx >= x1):
                    return True
            return False

        words["bold"] = rows["font"].str.lower().str.contains("bold")
        words["italic"] = rows["font"].str.lower().str.contains("italic")

        formatting = []  # track nesting of italic, bold, struck

        def get_formatting(bold, italic, struck, word) -> str:
            nonlocal formatting
            output = ""
            if italic or bold or struck:
                output += " "
            if italic:
                if "italic" not in formatting:
                    formatting.append("italic")
                    output += "_"
            if bold:
                if "bold" not in formatting:
                    formatting.append("bold")
                    output += "**"
            if struck:
                if "struck" not in formatting:
                    formatting.append("struck")
                    output += "~~"
            end_format = False
            if not struck:
                if "struck" in formatting:
                    formatting.remove("struck")
                    output += "~~"
                    end_format = True
            if not bold:
                if "bold" in formatting:
                    formatting.remove("bold")
                    output += "**"
                    end_format = True
            if not italic:
                if "italic" in formatting:
                    formatting.remove("italic")
                    output += "_"
                    end_format = True
            if end_format:
                output += " "
            output += ("" if output else " ") + word
            return output

        font_sizes_list = list(sorted(set(words["fontSize"]), reverse=True))
        header_sizes = dict.fromkeys(font_sizes_list, 0)
        for font_size in font_sizes_list:
            if font_size > 12:
                header_sizes[font_size] = max(header_sizes.values()) + 1

        prev_y = None
        start_of_line = True
        header = ""

        for _, word in words.iterrows():
            ulx, uly, lrx, lry, content, bold, italic, font_size = word[
                ["ulx", "uly", "lrx", "lry", "content", "bold", "italic", "fontSize"]
            ]

            if prev_y is None:
                prev_y = uly - font_size * 2

            if uly != prev_y:
                indent = " " * math.floor((ulx - leftmost_text) / font_size)
                start_of_line = True
                eol = get_formatting(False, False, False, "  ")
                newlines = "\n" * min(2, math.floor((uly - prev_y) / font_size) - 1)
                header = "#" * header_sizes[font_size]

                print(eol + newlines + indent, end="")
                if header:
                    print(header + " ", end="")

                prev_y = uly

            if header:
                formatted = get_formatting(False, False, False, content)
            else:
                struck = is_word_struck(ulx, uly, lrx, lry)
                formatted = get_formatting(bold, italic, struck, content)

            if start_of_line:
                formatted = formatted.lstrip()
                start_of_line = False
            print(formatted, end="")
        # formatted = get_formatting(False, False, False, "")
        # print(formatted)

    # Recursively delete tmp
    # shutil.rmtree("tmp")


if __name__ == "__main__":
    process_pdf(sys.argv[1])
