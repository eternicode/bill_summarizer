import logging
import math
import subprocess
import sys
from datetime import datetime
from tempfile import mkdtemp

import pandas as pd

from lines import get_image_lines

log = logging.getLogger(__file__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(name)s:%(lineno)d %(levelname)s %(message)s",
)


class MDFormatter:
    def __init__(self):
        self.content = ""
        self.is_bold = False
        self.is_italic = False
        self.is_struck = False

    def setBold(self, is_bold):
        if is_bold == self.is_bold:
            return
        self.is_bold = is_bold
        self.content += "**"

    def setItalic(self, is_italic):
        if is_italic == self.is_italic:
            return
        self.is_italic = is_italic
        self.content += "_"

    def setStruck(self, is_struck):
        if is_struck == self.is_struck:
            return
        self.is_struck = is_struck
        self.content += "~~"

    def addContent(self, content, bold, italic, struck):
        self.content += " "
        self.setBold(bold)
        self.setItalic(italic)
        self.setStruck(struck)
        self.content += content


def process_pdf(filename):
    log.info("Creating temp dir")
    tempdir = mkdtemp(dir="tmp/", prefix=datetime.now().strftime("%Y-%m-%d-%H%M%S_"))
    log.info(f"Temp dir: {tempdir}")

    log.info("Extracting images with pdf2htmlEX")
    with (
        open(f"{tempdir}/pdf2htmlEX.err", "w") as errfile,
        open(f"{tempdir}/pdf2htmlEX.log", "w") as outfile,
    ):
        subprocess.run(
            [
                "pdf2htmlEX",
                "--dest-dir",
                tempdir,
                "--embed-image",
                "0",
                filename,
            ],
            check=True,
            stderr=errfile,
            stdout=outfile,
        )

    log.info("Extracting text with textricator")
    with (
        open(f"{tempdir}/textricator.err", "w") as errfile,
        open(f"{tempdir}/textricator.log", "w") as outfile,
    ):
        subprocess.run(
            [
                "textricator",
                "text",
                "--input-format=pdf.pdfbox",
                filename,
                f"{tempdir}/contents.csv",
            ],
            check=True,
            stderr=errfile,
            stdout=outfile,
        )

    log.info("Reading in content CSV")
    rows = pd.read_csv(f"{tempdir}/contents.csv", na_filter=False)
    rows[["ulx", "uly", "lrx", "lry"]] = rows[["ulx", "uly", "lrx", "lry"]] * 2

    ignore_bounds = [
        (600, 180, 625, 210),  # page number
        (310, 1380, 520, 1420),  # footer
    ]

    log.info("Masking out ignored regions")
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

    log.info("Getting strikethrough data")
    page_count = rows["page"].max()
    page_lines = {
        page_num: get_image_lines(f"{tempdir}/bg{page_num:x}.png")
        for page_num in range(1, page_count + 1)
    }

    log.info("Processing content formatting")
    # Annotate rows with bold and italic
    log.info("(Bold)")
    rows["bold"] = rows["font"].str.lower().str.contains("bold")
    log.info("(Italic)")
    rows["italic"] = rows["font"].str.lower().str.contains("italic")
    log.info("(Struck)")
    rows["struck"] = rows.apply(
        lambda row: any(
            (row["uly"] <= y1)
            & (row["lry"] >= y1)
            & (row["ulx"] <= x2)
            & (row["lrx"] >= x1)
            for x1, y1, x2, y2 in page_lines[row["page"]]
        ),
        axis=1,
    )

    formatter = MDFormatter()

    for page_num in range(1, page_count + 1):
        log.info(f"Processing page {page_num}/{page_count}")
        words = rows[rows["page"] == page_num]

        leftmost_text = words["ulx"].min()

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
            ulx, uly, content, bold, italic, struck, font_size = word[
                ["ulx", "uly", "content", "bold", "italic", "struck", "fontSize"]
            ]

            if prev_y is None:
                prev_y = uly - font_size * 2

            if uly != prev_y:
                indent = " " * math.floor((ulx - leftmost_text) / font_size)
                start_of_line = True
                eol = get_formatting(False, False, False, "  ")
                newlines = "\n" * min(2, math.floor((uly - prev_y) / font_size) - 1)
                header = "#" * header_sizes[font_size]

                # formatter.addContent(eol + newlines + indent, False, False, False)
                print(eol + newlines + indent, end="", flush=True)
                if header:
                    # formatter.addContent(header + " ", False, False, False)
                    print(header + " ", end="", flush=True)

                prev_y = uly

            if header:
                # formatter.addContent(content, False, False, False)
                formatted = get_formatting(False, False, False, content)
            else:
                # formatter.addContent(content, bold, italic, struck)
                formatted = get_formatting(bold, italic, struck, content)

            if start_of_line:
                formatted = formatted.lstrip()
                start_of_line = False
            print(formatted, end="", flush=True)
        formatted = get_formatting(False, False, False, "")
        print(formatted, flush=True)

    # print(formatter.content)

    # Recursively delete tmp
    # shutil.rmtree(tempdir, ignore_errors=True)


if __name__ == "__main__":
    process_pdf(sys.argv[1])
