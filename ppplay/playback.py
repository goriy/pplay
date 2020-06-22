#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ppplay.vlc
import math
import mutagen

class playback:
  #############################################################################
  def __init__(self):
    self.filename = ''
    self.filetitle = ''
    self.playing = False
    self.loaded = False
    self.time_step = 5.0
    self.loops = 1
    self.bitrate_s = "---"
    self.mplay = None

  #############################################################################
  def seconds_to_norm(self, value):
    mins = int(value) // 60
    secs = int(value) % 60
    mill = int((value - int(value)) * 100.0)
    result = "%d:%02d.%02d" % (mins, secs, mill)
    return result

  #############################################################################
  def unload(self):
    self.stop()

  #############################################################################
  def load_file(self, filename):
    if not os.path.isfile(filename):
      return False
    self.filename = filename
    self.filetitle = os.path.basename(filename)
    fi = mutagen.File(filename)
    self.bitrate = fi.info.bitrate // 1024
    self.length  = fi.info.length

    self.mplay = ppplay.vlc.MediaPlayer(filename)
    self.mplay.play()
    self.mplay.set_pause(1)

    #self.bitrate = self.mplay.get_rate()
    #self.length  = self.mplay.get_length() / 1000.0
    self.length_f = self.seconds_to_norm(self.length)
    self.bitrate_s = "%sk" % (self.bitrate)

    if (self.length < 30.0):
      self.time_step = 2.0
    else:
      self.time_step = 5.0

    self.loaded = True
    self.loops = 1
    return True

  #############################################################################
  def is_paused(self):
    if not self.loaded: return True
    state = self.mplay.get_state()
    if (state == ppplay.vlc.State.Paused):
      result = True
    else:
      result = False
    return result

  #############################################################################
  def is_ended(self):
    if not self.loaded: return False
    state = self.mplay.get_state()
    if (state == ppplay.vlc.State.Ended):
      result = True
    else:
      result = False
    return result

  #############################################################################
  def get_position(self):
    if not self.loaded:
      return ("-:--:-- / -:--:--", 0, "---")
    perc = self.mplay.get_position()
    #self.length   = self.mplay.get_length() / 1000.0
    #self.length_f = self.seconds_to_norm(self.length)
    #print(perc, self.length)
    pos = perc * self.length
    pos_f = self.seconds_to_norm(pos)
    result = "%s / %s" % (pos_f, self.length_f)
    perc = (perc * 100)
    return (result, perc, self.bitrate_s)

  #############################################################################
  def set_position_percent(self, value):
    #print("set position:", value, self.length)
    pos = float(value) / 100.0
    self.mplay.set_position(pos)

  #############################################################################
  def diff_position(self, value):
    pos = self.mplay.get_position()
    pos += value * (self.time_step/self.length)
    if (pos >= 1.0):  pos = 1.0
    if (pos < 0):     pos = 0
    self.mplay.set_position(pos)

  #############################################################################
  def start(self, loops = None, start = None):
    if start is None:
      st = 0.0 # self.start_position
    else:
      st = start
      self.mplay.stop()
      self.mplay.set_position(st)
      self.mplay.play()
    if loops is None:
      lo = self.loops
    else:
      lo = loops

    #print("start play")

    self.mplay.set_pause(0)

    self.loops = lo
    self.playing = True

  #############################################################################
  def stop(self):
    if self.playing:
      self.mplay.set_pause(1)
      self.playing = False

  #############################################################################
  def unload(self):
    if self.playing:
      if not self.mplay is None: self.mplay.stop()
      self.playing = False
      self.loaded = False

  #############################################################################
  def play_toggle(self):
    if self.playing:
      self.stop()
    else:
      self.start()
    return self.playing

  #############################################################################
  #def volume_down(self):
  #  self.mplay.audio_set_volume(self.mplay.audio_get_volume()*0.9)
  #  return self.mplay.audio_get_volume() / 100.0
  #
  #############################################################################
  #def volume_up(self):
  #  self.mplay.audio_set_volume(self.mplay.audio_get_volume()*1.1)
  #  return self.mplay.audio_get_volume() / 100.0

  #############################################################################
  def volume_get(self):
    result = 1.0
    if self.loaded: result = self.mplay.audio_get_volume() / 100.0
    return result

  #############################################################################
  def calc_vol(self, val):
  #  val += 1.0
  #  #if (val <= 0.0):  return 0
  #  v = ((math.log(val*2) - math.log(2)) * 100.0)
  #  v *= 100.0/69
    v = math.sqrt(val) * 100
    return int(v)

  #############################################################################
  def volume_set(self,value):
    #print("** set volume", value, self.calc_vol(value))
    self.mplay.audio_set_volume(self.calc_vol(value))
    return self.mplay.audio_get_volume() / 100.0
