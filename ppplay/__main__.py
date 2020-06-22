#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import tkinter as tk
import tkinter.font as font
from tkinter import ttk
from tkinter import filedialog

from ppplay import version
from ppplay import playback

root = None
Wnd = None

keycodes = {'L': 76, 'A': 65, 'U': 85, 'Space': 32, 'O': 79, 'D': 68}

###############################################################################
def resource_path(relative_path = None):
  try:
      base_path = sys._MEIPASS
  except Exception:
      base_path = os.path.abspath(os.path.dirname(__file__))
  if relative_path is None:
    return base_path
  else:
    return os.path.join(base_path, relative_path)

###############################################################################
def font2string(font):
  # spaces in the family name need to be escaped
  font['family'] = font['family'].replace(' ', '\ ').replace("\\\\", "\\")
  font_str = "%(family)s %(size)i %(weight)s %(slant)s" % font
  if font['underline']:
      font_str += ' underline'
  if font['overstrike']:
      font_str += ' overstrike'
  return font_str
###############################################################################
def string2font(font_str):
  result = {}
  fnt = font_str.split(' ')
  family = fnt.pop(0)
  while family[-1:] == "\\":
    family = family[:len(family)-1]
    family += ' ' + fnt.pop(0)

  result['family'] = family
  result['size']   = int(fnt.pop(0))
  result['weight'] = fnt.pop(0)
  result['slant']  = fnt.pop(0)
  return result

###############################################################################
###############################################################################
###############################################################################
class CreateToolTip(object):
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffb0", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

###############################################################################
###############################################################################
###############################################################################
class App2(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        self.file_loaded = False
        self.update_in_progress = False

        self.cmd_open = tk.Button(self, text="O", command=self.open_file, pady=0)
        self.cmd_dsp  = tk.Button(self, text="D", command=self.open_dsp, pady=0, state=tk.DISABLED)

        self.chk_loop_var = tk.BooleanVar()
        self.chk_loop = tk.Checkbutton (self, text = "L", onvalue=True, offvalue=False, indicatoron=True,
                                        variable = self.chk_loop_var, justify=tk.LEFT, anchor=tk.CENTER, pady=0,
                                        command=self.option_loop_changed)
        self.chk_top_var = tk.BooleanVar()
        self.chk_top = tk.Checkbutton (self, text = "A", onvalue=True, offvalue=False,
                                       variable = self.chk_top_var, justify=tk.LEFT, anchor=tk.CENTER, pady=0,
                                       command=self.option_top_changed)
        self.chk_unload_var = tk.BooleanVar()
        self.chk_unload = tk.Checkbutton (self, text = "U", onvalue=True, offvalue=False,
                                          variable = self.chk_unload_var, justify=tk.LEFT, anchor=tk.CENTER, pady=0,
                                          command=self.option_unload_changed)

        self.chk_unload_var.set(1)

        self.cmd_play = tk.Button(self, text=">", command=self.play_pause, pady=0)
        self.cmd_play.config(state=tk.DISABLED)

        self.volume_bar = tk.Scale(from_=0, to=100, orient=tk.VERTICAL,  width=10,showvalue=0,
                                   sliderlength=20, command=self.slider_volume_changed)
        self.time_bar = tk.Scale(from_=0, to=100, orient=tk.HORIZONTAL,width=10,showvalue=0,
                                 sliderlength=20, command=self.slider_time_changed)

        self.time_info = tk.Label(self, text="12:43.40 / 84:65:53", padx=0, anchor=tk.NW, justify=tk.LEFT, bd=0)
        self.rate_info = tk.Label(self, text="320k", padx=0, anchor=tk.NE, justify=tk.RIGHT, bd=0)

        self.set_font()

        CreateToolTip(self.chk_unload, "Unload after playback end\nhotkey: U")
        CreateToolTip(self.chk_top, "Window is always on top\nhotkey: A")
        CreateToolTip(self.chk_loop, "Loop playback\nhotkey: L")
        CreateToolTip(self.cmd_open, "Open file to play\nhotkey: O")
        CreateToolTip(self.cmd_play, "Play/pause\nhotkey: <Space>")
        CreateToolTip(self.time_bar, "Playback position control\nhotkeys: <Left>, <Right>")
        CreateToolTip(self.volume_bar, "Volume control\nhotkeys: <Up>, <Down>")
        CreateToolTip(self.rate_info, "Bitrate")
        CreateToolTip(self.time_info, "Current playback position")

        self.cmd_open.place(x=0, y=0, height=20, width=20)
        self.cmd_dsp.place(x=23, y=0, height=20, width=20)
        self.chk_top.place(x=46, y=-2, height=20, width=33)
        self.chk_loop.place(x=82, y=-2, height=20, width=33)
        self.chk_unload.place(x=117, y=-2, height=20, width=33)

        self.cmd_play.place(x=0, y=23, height=23, width=23)

        self.time_info.place(x=30,  y=27, height=30, width=155)
        self.rate_info.place(x=170, y=15, height=15, width=50, anchor=tk.NE)

        self.volume_bar.place(relx=1.0, y=0, relheight=1.0, width=15, anchor=tk.NE)
        self.time_bar.place(x=0, rely=1.0, height=15, relwidth=0.92, anchor=tk.SW)

        self.player = playback.playback()
        self.volume_bar.set(100-int(self.player.volume_get() * 100.0))

        self.update_clock()

    ###########################################################################
    def update_all(self):
      if not self.player.loaded:
        self.cmd_play.config(state=tk.DISABLED)
        self.time_bar.config(state=tk.DISABLED)
        self.volume_bar.config(state=tk.DISABLED)
        self.time_info.config(text='no file...')
        self.file_loaded = False
        return

      if not self.file_loaded:
        self.cmd_play.config(state=tk.NORMAL)
        self.time_bar.config(state=tk.NORMAL)
        self.volume_bar.config(state=tk.NORMAL)
        self.file_loaded = True

      self.update_in_progress = True
      if not self.player.is_paused():
        self.cmd_play.config(text="| |", foreground="red")
      else:
        self.cmd_play.config(text=">", foreground="black")

      (poss, perc, bitrate) = self.player.get_position()
      self.time_info.config(text=poss)
      self.rate_info.config(text=bitrate)
      self.time_bar.set(perc)
      self.update()

      if self.player.is_ended():
        if self.chk_loop_var.get():
          self.player.stop()
          self.player.start(start = 0.0)
        elif self.chk_unload_var.get():
          self.player.unload()
          sys.exit(0)

      self.update_in_progress = False

    ###########################################################################
    def set_font(self, font_str = None):
    #  if font_str is None:
    #    font_str = 'Courier 8 normal roman'
    #  self.cmd_open.configure(font=font_str)
    #  self.cmd_dsp.configure(font=font_str)
    #  self.time_info.configure(font=font_str)
      myFont  = font.Font(size=9)
      myFontS = font.Font(size=8)
      myFontB = font.Font(size=9, weight='bold')
      self.cmd_open['font'] = myFont
      self.cmd_dsp['font']  = myFont

      self.cmd_play['font']  = myFontB
      self.time_info['font'] = myFontB
      self.rate_info['font'] = myFontS

      self.chk_top['font']    = myFont
      self.chk_loop['font']   = myFont
      self.chk_unload['font'] = myFont

    ###########################################################################
    def open_file(self):
      #print("** open file")
      self.player.unload()
      fname = filedialog.askopenfilename(title = "Select audio file",filetypes = (("audio files","*.mp3 *.ogg"),("all files","*.*")))
      if fname:
        self.set_file(fname)
        self.play_pause()
      else:
        root.title("mplay (v." + version.__version__ + ")")

    ###########################################################################
    def open_dsp(self):
      #print("** open dsp")
      pass

    ###########################################################################
    def play_pause(self):
      if not self.player.loaded:  return

      if self.player.play_toggle():
        self.cmd_play.config(text="| |", foreground="red")
      else:
        self.cmd_play.config(text=">", foreground="black")
      self.update_all()

    ###########################################################################
    def option_loop_changed(self):
      #print("** loop changed")
      pass

    ###########################################################################
    def option_top_changed(self):
      #print("** top changed")
      root.attributes('-topmost', self.chk_top_var.get())

    ###########################################################################
    def option_unload_changed(self):
      #print("** unload changed")
      pass

    ###########################################################################
    def slider_volume_changed(self, data):
      #print("** volume changed ", data)
      self.player.volume_set((100 - int(data)) / 100.0)

    ###########################################################################
    def slider_time_changed(self, data):
      if not self.update_in_progress:
        #print("** time changed:", data)
        self.player.set_position_percent(data)

    ###########################################################################
    def position_ff(self, event):
      #print("** position_ff")
      self.player.diff_position(1)

    ###########################################################################
    def position_rew(self, event):
      #print("** position_rew")
      self.player.diff_position(-1)

    ###########################################################################
    def volume_down(self, event):
      #print("** volume down")
      self.volume_bar.set(self.volume_bar.get() + 10)

    ###########################################################################
    def volume_up(self, event):
      #print("** volume up")
      self.volume_bar.set(self.volume_bar.get() - 10)

    ###########################################################################
    def toggle_var(self, varname):
      v = varname.get()
      v = not v
      varname.set(v)

    ###########################################################################
    def keypress(self, event):
      global root
      #print(event)
      if event.keycode == keycodes['L']:  # L
        self.toggle_var(self.chk_loop_var)
        self.option_loop_changed()
      elif event.keycode == keycodes['A']:  # A
        self.toggle_var(self.chk_top_var)
        self.option_top_changed()
      elif event.keycode == keycodes['U']:  # U
        self.toggle_var(self.chk_unload_var)
        self.option_unload_changed()
      elif event.keycode == keycodes['Space']:  # <Space>
        self.play_pause()
      elif event.keycode == keycodes['O']:
        self.open_file()
      elif event.keycode == keycodes['D']:
        self.open_dsp()

    ###########################################################################
    def set_file(self, filename):
      global root
      result = False
      if self.player.load_file(filename):
        root.title(self.player.filetitle)
        result = True
      self.update_all()
      return result

    ###########################################################################
    def update_clock(self):
      global root
      self.update_all()
      root.after(100, self.update_clock)

###############################################################################
def close(event):
    #master.withdraw() # if you want to bring it back
    sys.exit(0) # if you want to exit the entire thing

###############################################################################
def main():
    global root
    global Wnd
    global keycodes
    root = tk.Tk()
    root.geometry("185x64")
    root.resizable(False, False)
    #root.attributes("-toolwindow",1)
    #root.overrideredirect(1)  # titleless window
    #root.transient()
    root.title("mplay (v." + version.__version__ + ")")
    if sys.platform.find('linux') < 0:
      root.iconbitmap(default=resource_path("mplay.ico"))
    else:
      keycodes['L'] = 46
      keycodes['A'] = 38
      keycodes['U'] = 30
      keycodes['O'] = 32
      keycodes['D'] = 40
      keycodes['Space'] = 65

    root.bind('<Escape>', close)

    Wnd = App2(root)
    root.bind('<Up>',   Wnd.volume_up)
    root.bind('<Down>', Wnd.volume_down)
    root.bind('<Key>',  Wnd.keypress)
    root.bind('<Right>', Wnd.position_ff)
    root.bind('<Left>',  Wnd.position_rew)

    Wnd.place(relx=0,rely=0,relwidth=1.0,relheight=1.0)

    if len(sys.argv) > 1:
      if Wnd.set_file(sys.argv[1]):
        Wnd.play_pause()

    root.mainloop()
    return 0

###############################################################################
if __name__ == '__main__':
  ret = main()
  sys.exit(ret)
