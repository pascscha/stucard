colors_fg = {"default": "39",
             "black": "30",
             "red": "31",
             "green": "32",
             "yellow": "33",
             "blue": "34",
             "magenta": "35",
             "cyan": "36",
             "lightgray": "37",
             "darkgray": "90",
             "lightred": "91",
             "lightgreen": "92",
             "lightyellow": "93",
             "lightblue": "94",
             "lightmagenta": "95",
             "lightcyan": "96",
             "white": "97"}
colors_bg = {"default": "49",
             "black": "40",
             "red": "41",
             "green": "42",
             "yellow": "43",
             "blue": "44",
             "magenta": "45",
             "cyan": "46",
             "lightgray": "47",
             "darkgray": "100",
             "lightred": "101",
             "lightgreen": "102",
             "lightyellow": "103",
             "lightblue": "104",
             "lightmagenta": "105",
             "lightcyan": "106",
             "white": "107"}


def colorize(text):
    text = " " + text

    sections = text.split("{")
    out = sections[0]

    bg = colors_bg["default"]
    fg = colors_fg["default"]

    for section in sections[1:]:
        clr, txt = section.split("}")

        mode, clr = clr.lower().split("_")
        if mode == "fg":
            fg = colors_fg[clr]
        else:
            bg = colors_bg[clr]
        out = "{}\033[{};{}m{}".format(out, bg, fg, txt)
    return out[1:]


def show_tag(file):
    with open(file, "r") as f:
        tag = f.read()
    tag = tag + "{BG_DEFAULT}{FG_DEFAULT}"
    tag = colorize(tag)
    print(tag)
