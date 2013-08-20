#!/usr/bin/env python

"""This script takes input data from a coded spreadsheet with
foraging information in it and a processed Fluorite log with
Eclipse commands in it and then creates a visual timeline
of the participant's actions.

Inputs:

Place in the data directory:

- A codes file in tab-separated format, usually
copy-pastable from Excel, ex: p03-coded.tab

- A commands file in tab-separated format, usually
copy-pastable from Excel, ex: p03-commands.tab

Output:

- An SVG file of the timeline, ex: p03.svg

===

Copyright (c) 2013, Iriwn Kwan All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer. Redistributions in binary
form must reproduce the above copyright notice, this list of conditions and
the following disclaimer in the documentation and/or other materials provided
with the distribution. Neither the name of the <ORGANIZATION> nor the names of
its contributors may be used to endorse or promote products derived from this
software without specific prior written permission. THIS SOFTWARE IS PROVIDED
BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

import sys
import os
from datetime import time, datetime, date, timedelta
from collections import OrderedDict
from pyparsing import *
from math import ceil
import svgwrite
import re

class VideoTime:
	@staticmethod
	def convert_to_timestamp(video_time_stamp):
		(minute, s) = video_time_stamp.split(':')
		(second, millisecond) = s.split('.')

		# Use today's date as a placeholder for creating a datetime object for time subtraction
		return datetime.combine(date.today(), time(0, int(minute), int(second), int(millisecond) * 1000))


class Command:
	def __init__(self, line):

		fields = ['Participant',
			'CommandID',
			'Time',
			'Command',
			'ActiveFile',
			'ASTMethod',
			'EclipseSpecial',
			'Find',
			'Replace',
			'DocOffset',
			'LineOfCode']
		line_data = line.rstrip('\n').split('\t', len(fields))
		self.record = OrderedDict(zip(fields, line_data))

		self.record['CommandID'] = int(self.record['CommandID'])
		self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])
		self.record['DocOffset'] = int(self.record['DocOffset'])
		self.record['LineOfCode'] = self._strip_quotes(self.record['LineOfCode'])

	def _strip_quotes(self, field):
		return field.rstrip('"').lstrip('"')

	def __len__(self):
		return len(self.record)

	def __getitem__(self, key):
		return self.record[key]

	def header(self):
		return ('\t'.join(k for k in self.record.keys()))

	def __str__(self):
		return ('\t'.join(str(v) for v in self.record.values()))


class CodeError(Exception):
	pass


class CodedEvent:
	def __init__(self, line):
		fields = ['Index',
			'Time',
			'Transcription',
			'Foraging',
			'Start', 'End', 'Ongoing', 'Code1', 'Code2', 'Code3',
			'Forks',
			'LearningDoing',
			'Fork matches goal', 'Fork during foraging',
			'Retrospective fork',
			'Retrospective quote']
		line_data = line.split('\t')

		self.record = None
		if self._is_coded_row(line_data):
			self.valid = True

			
			self.record = OrderedDict(zip(fields, line_data))
			self._remove_unused_keys()

			self.record['Index'] = int(self.record['Index'])
			self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])
			self.record['Forks'] = int(self.record['Forks'])
			self.record['Foraging'] = self._convert_yesno_to_boolean(self.record, 'Foraging')

			self.record['LearningDoing'] = self.record['LearningDoing'].upper()

		else:
			self.record = None
			self.valid = False

	def _remove_unused_keys(self):
		keys_to_delete = ['Transcription', 'Start', 'End', 'Ongoing', 'Code1', 'Code2', 'Code3',
			'Fork matches goal', 'Fork during foraging', 'Retrospective quote']
		for k in keys_to_delete:
			self.record.pop(k, None)

	def _convert_yesno_to_boolean(self, record, key):
		if record[key].lower() == 'y' or record[key] == '1':
			return True
		elif record[key] == '' or record[key].lower() == 'n' or record[key] == '0':
			return False
		else:
			raise CodeError("There's a problem with coding %s not being Y or N for index %s at %s."
				% (key, record['Index'], str(record['Time'])))

	def _is_coded_row(self, line_data):
		if not line_data[0] or not line_data[1]:
			return False
		else:
			return True

	@property
	def valid(self):
		return self.valid

	def __len__(self):
		return len(self.record)

	def __getitem__(self, key):
		return self.record[key]

	def header(self):
		return ('\t'.join(k for k in self.record.keys()))

	def __str__(self):
		return ('\t'.join(str(v) for v in self.record.values()))

class TimelineDecorations:
	def __init__(self, svg_timeline, coded_events):
		self.svg_timeline = svg_timeline
		self.coded_events = coded_events

	def draw(self):
		self._draw_x_axis()
		self._draw_x_axis(Timeline.CHART_HEIGHT)
		self._draw_x_axis(Timeline.HEIGHT)
		self._draw_x_tickmarks()
		self._draw_x_labels()

	def _calculate_timeline_duration(self, events):
		start = events[0]
		end = events[-1]
		start_time = start['Time']
		end_time = end['Time'] + timedelta(0, 29, 0, 999)
		return end_time - start_time

	def _draw_x_axis(self, ypos=0):
		duration = self._calculate_timeline_duration(self.coded_events)

		self.svg_timeline.add(self.svg_timeline.line(
			start=(Timeline.X_OFFSET, Timeline.Y_OFFSET + ypos),
			end=(Timeline.X_OFFSET + duration.total_seconds(), Timeline.Y_OFFSET + ypos)).
			stroke(color='black', width=1))

	def _draw_x_tickmarks(self):
		duration = self._calculate_timeline_duration(self.coded_events)

		alternate = 0
		for xpos in range(0, int(ceil(duration.total_seconds())), Timeline.X_GAP):

			tickmark = self.svg_timeline.line(
				start=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET), \
				end=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET + Timeline.HEIGHT),
				opacity="0.5") \
				.stroke(color='black', width=1)

			if alternate % 2:
				tickmark.dasharray("3,1")

			self.svg_timeline.add(tickmark)

			alternate += 1

	def _draw_x_labels(self):
		duration = self._calculate_timeline_duration(self.coded_events)

		ce_index = 0
		for xpos in range(0, int(ceil(duration.total_seconds())), Timeline.X_LABEL_GAP):
			try:
				self.svg_timeline.add(self.svg_timeline.text(self.coded_events[ce_index]['Time'].strftime(Timeline.TIMELABEL),
					insert=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET + Timeline.HEIGHT + 20),
					font_family="sans-serif",
					font_size="14"))
			except IndexError:
				pass

			ce_index += 2

	def draw_legend(self):
		legend = self.svg_timeline.text("",
			insert=(0, Timeline.Y_OFFSET),
			font_family="sans-serif",
			text_anchor="end",
			font_size="9")

		startpos = Timeline.X_OFFSET - 2

		legend.add(svgwrite.text.TSpan("Open", insert=None, fill=EventLine.COLOR_OPEN,
			x=[startpos], dy=[10]))
		legend.add(svgwrite.text.TSpan("Select", insert=None, fill=EventLine.COLOR_SELECT,
			x=[startpos], dy=[10]))
		legend.add(svgwrite.text.TSpan("Move", insert=None, fill=EventLine.COLOR_MOVE,
			x=[startpos], dy=[10]))
		legend.add(svgwrite.text.TSpan("Run", insert=None, fill=EventLine.COLOR_RUN,
			x=[startpos], dy=[10]))
		legend.add(svgwrite.text.TSpan("Misc", insert=None, fill=EventLine.COLOR_DEFAULT,
			x=[startpos], dy=[10]))

		self.svg_timeline.add(legend)


class Square:
	def __init__(self, svg_timeline, event):

		self.svg_timeline = svg_timeline
		self.foraging = event['Foraging']
		self.retrospective = event['Retrospective fork']

		if event['LearningDoing'] and not event['Forks']:
			raise CodeError('Coded Data error: learning/doing coded but the fork is not.')

		self.fork = event['Forks']
		self.learning_or_doing = event['LearningDoing']

	def _draw_text(self, xpos):
		size = "14"

		if self.retrospective.lower() == 'y':
			style = self.svg_timeline.g(style='text-decoration:underline; font-weight:bold')
		elif self.retrospective.lower() == 'n':
			style = self.svg_timeline.g(style='font-style:italics')
		else:
			style = None

		if not self.learning_or_doing and self.retrospective.lower() == 'y':
			self.learning_or_doing = 'f+'
			style = None
		elif not self.learning_or_doing and self.retrospective.lower() == 'n':
			self.learning_or_doing = 'f-'
			style = None

		text = self.svg_timeline.text(
			self.learning_or_doing,
			insert=(xpos + Timeline.SQUARE_WIDTH/2 + Timeline.X_OFFSET, Timeline.CHART_HEIGHT/2 + Timeline.Y_OFFSET),
			font_family="sans-serif",
			font_size=size,
			text_anchor="middle",
			dy="5")
		if style:
			style.add(text)
			self.svg_timeline.add(style)
		else:
			self.svg_timeline.add(text)

	def draw(self, xpos):
		"""Draws the square according to its properties"""

		fill = "white"
		if self.foraging:
			fill = "beige"

		self.svg_timeline.add(self.svg_timeline.rect(
			insert=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET),
			size=(Timeline.SQUARE_WIDTH, Timeline.CHART_HEIGHT),
			fill=fill,
			opacity="0.8",
			stroke_width="0"))

		self._draw_text(xpos)



class CommandTooSoonException(Exception):
	pass

class EventLine:

	HEIGHT = 10

	COLOR_OPEN = 'chocolate'
	COLOR_SELECT = 'darkviolet'
	COLOR_MOVE = 'red'
	COLOR_RUN = 'blue'
	COLOR_DEFAULT = 'darkgreen'

	def __init__(self, svg_timeline, event, start):
		self.svg_timeline = svg_timeline
		self.event = event
		self.start_time = start

	def _draw_open(self, xpos):
		self._draw(EventLine.COLOR_OPEN, 0, xpos)

	def _draw_select(self, xpos):
		self._draw(EventLine.COLOR_SELECT, 10, xpos)

	def _draw_move(self, xpos):
		self._draw(EventLine.COLOR_MOVE, 20, xpos)

	def _draw_run(self, xpos):
		self._draw(EventLine.COLOR_RUN, 30, xpos)

	def _draw_default(self, xpos):
		self._draw(EventLine.COLOR_DEFAULT, 40, xpos)

	def _draw(self, color, top, xpos):
		self.svg_timeline.add(self.svg_timeline.line(
				start=(xpos + Timeline.X_OFFSET, top + Timeline.Y_OFFSET),
				end=(xpos + Timeline.X_OFFSET, Timeline.HEIGHT + Timeline.Y_OFFSET)).
				stroke(color=color, width=1, opacity=0.9))

	def draw(self):
		xpos = Timeline.calculate_x_position(self.start_time, self.event['Time'])

		if self.event['Command'] == 'FileOpenCommand':
			self._draw_open(xpos)
		elif self.event['Command'] == 'SelectTextCommand':
			self._draw_select(xpos)
		elif self.event['Command'] == 'MoveCaretCommand':
			self._draw_move(xpos)
		elif self.event['Command'] == 'RunCommand':
			self._draw_default(xpos)


class MethodLaneException(Exception):
	pass

class MethodBar:
	TEXT_WIDTH = 120

	def __init__(self, svg_timeline, event_start, timeline_start, visited_methods):

		self.svg_timeline = svg_timeline
		self.start = event_start
		self.my_name = MethodBar.method_name(event_start)
		self.timeline_start = timeline_start

		self.visited_methods = visited_methods
		method_decorations = visited_methods.get(self.my_name)
		self.background = method_decorations['color']
		self.lane = method_decorations['lane']
		self.last_text = method_decorations['last_text']

	def same_method(self, new_event):
		"""Is the incoming method the same as the current method?"""
		if new_event and MethodBar.method_name(new_event) == self.my_name:
			return True
		else:
			return False

	@staticmethod
	def method_name(event):
		ast_method = event['ASTMethod']

		if ast_method and ast_method != 'null':

			try:
				index_semicolon = ast_method.index(';')
				index_slash = ast_method.rfind('/', 0, index_semicolon)

				filename = ast_method[index_slash + 1: index_semicolon ]

				index_period = ast_method.index('.')
				index_open = ast_method.index('(')
				method = ast_method[index_period + 1: index_open]

				if not method:
					method = "Constructor"

				text_string = filename + ":" + method

			except ValueError:
				text_string = ast_method

		else:
			text_string = "None"

		return text_string

	def _xstart(self):
		return Timeline.calculate_x_position(self.timeline_start, self.start['Time'])

	def _draw_text(self, x_start):
		if not self.last_text:
			return True
			# print "NONE going to write %s at %d,%d" % (self.my_name, (bar_x_start + Timeline.X_OFFSET), self.lane)
		elif (self.last_text + MethodBar.TEXT_WIDTH) < (x_start):
			return True
			# print "%d: going to write %s at %d,%d" % (self.last_text, self.my_name, (bar_x_start + Timeline.X_OFFSET), self.lane)
		else:
			return False

	def _draw_bar(self, x_start):
		"""Draws the elapsed time for visiting a method"""
		duration = self.end['Time'] - self.start['Time']
		self.svg_timeline.add(self.svg_timeline.rect(
			insert=(x_start, Timeline.METHOD_LANE_HEIGHT * self.lane + Timeline.CHART_HEIGHT + Timeline.Y_OFFSET),
			size=(duration.total_seconds(), Timeline.METHOD_LANE_HEIGHT),
			fill=self.background,
			opacity="0.3",
			stroke_width="0"))

	def _draw_method(self, x_start):
		"""Draws the method text"""
		textcolor = "midnightblue"
		if self.my_name != 'None':
			textcolor = "black"

		self.last_text = x_start
		self.svg_timeline.add(self.svg_timeline.text(
			self.my_name,
			insert=(x_start, 2 + Timeline.CHART_HEIGHT + Timeline.METHOD_LANE_HEIGHT * self.lane + Timeline.Y_OFFSET),
			font_family="sans-serif",
			font_size="8",
			text_anchor="start",
			fill=textcolor,
			dy="5"))

	def draw(self, end):
		"""Draws the method's bar from start (stored in the instance) to the end parameter"""

		if self.lane < 0 or self.lane > Timeline.METHOD_LANES - 1:
			raise MethodLaneException("Method Lane outside range %d and %d" % (1, Timeline.METHOD_LANES))

		self.end = end

		x_start = self._xstart() + Timeline.X_OFFSET

		self._draw_bar(x_start)
		if self._draw_text(x_start):
			self._draw_method(x_start)

		self.visited_methods.update_last_text(self.my_name, self.last_text)
		return self.visited_methods


class Timeline:
	"""The representation of a timeline., including the graphical SVG view.

	X_OFFSET: The space of the chart away from the left edge of the screen.
	Y_OFFSET: The space of the chart away from the top of the screen.
	HEIGHT: The height of the chart.
	SQUARE_WIDTH: The width of one square
	X_GAP: The gap between tickmarks on x-axis
	TIMELABEL: The strftime label on x-axis
	"""
	X_MARGIN = 10
	X_OFFSET = 60
	Y_OFFSET = 10

	CHART_HEIGHT = 60
	METHOD_LANES = 19
	METHOD_LANE_HEIGHT = 10
	METHOD_HEIGHT = METHOD_LANES * METHOD_LANE_HEIGHT

	SQUARE_WIDTH = 30
	HEIGHT = CHART_HEIGHT + METHOD_HEIGHT

	X_GAP = 30
	X_LABEL_GAP = 60

	TIMELABEL = "%M:%S"

	def __init__(self, pid, codedevents_list, commands_list):
		self.coded_events = codedevents_list
		self.commands = commands_list
		self.pid = pid
		self.svg_timeline = svgwrite.Drawing(filename = str(pid) + ".svg", size=("2400px", "600px"))

		self.start_time = self.coded_events[0]['Time']

		self.visited_methods = VisitedMethods()

	@staticmethod
	def calculate_x_position(start_time, event_time):
		diff = event_time - start_time

		if diff.total_seconds() < 0:
			raise CommandTooSoonException('This command occurs before the start of the task.')

		return round(diff.total_seconds(), 0)

	def before_start(self, event):
		diff = event['Time'] - self.start_time
		if diff.total_seconds() < 0:
			return True
		else:
			return False

	def _merge(self):
		"""Merges codedevents and commands into one list."""
		self.events = [] # Keyed by index

	def __len__(self):
		return len(self.commands_list)

	def __str__(self):
		return '\n'.join(str(i) for i in self.commands_list)

	def _draw_timeline_decorations(self):
		decorations = TimelineDecorations(self.svg_timeline, self.coded_events)
		decorations.draw()
		decorations.draw_legend()

	def _draw_coded_event(self, event, xpos):
		square = Square(self.svg_timeline, event)
		square.draw(xpos)

	def _draw_coded_events(self):
		xpos = 0
		for event in self.coded_events:
			self._draw_coded_event(event, xpos)
			xpos += Timeline.SQUARE_WIDTH

	def _draw_command_event(self, event):
		line = EventLine(self.svg_timeline, event, self.start_time)
		line.draw()

	def _draw_command_events(self):
		for event in self.commands:
			try:
				self._draw_command_event(event)
			except CommandTooSoonException:
				pass

	def _draw_methods(self):
		start_event = None
		previous = None
		xpos = 0
		lane = 0
		
		for event in self.commands:
			if not self.before_start(event):
				
				if not start_event:
					
					start_event = MethodBar(self.svg_timeline, event, self.start_time, self.visited_methods)

				if previous and not start_event.same_method(previous):
					self.visited_methods = start_event.draw(event)
					#self.visited_methods.update_last_text(start_event.my_name, start_event.textpos)
					#print "update textpos: %s, %s" % (start_event.my_name, start_event.textpos)
					start_event = MethodBar(self.svg_timeline, event, self.start_time, self.visited_methods)

				previous = event
				xpos += Timeline.SQUARE_WIDTH

			else:
				previous = event

	def draw(self):
		"""Converts the textual commands_list to a graphical timeline view in SVG."""
		self._draw_command_events()
		self._draw_coded_events()
		self._draw_methods()
		self._draw_timeline_decorations()

		self.svg_timeline.save()
		

class VisitedMethods:
	"""Keeps track of methods visited so far for this participant and assigns them different
	colors and lanes."""
	COLORS = ['mediumvioletred', 'lime', 'orchid', 'salmon', 'seagreen', 'indigo', 'tomato',
		'turquoise', 'brown', 'steelblue']
	LANES = Timeline.METHOD_LANES

	def __init__(self):
		self.methods = {}
		self.next = 1
		none_method = {'color': 'grey',
			'lane': 0,
			'last_text': None}
		self.methods['None'] = none_method

	def get(self, method_name):
		if not method_name in self.methods:
			# print "creating new%s" % method_name
			m = {}
			m['color'] = VisitedMethods.COLORS[self.next % len(VisitedMethods.COLORS)]
			m['lane'] = self.next
			m['last_text'] = None
			self.methods[method_name] = m
			self.next = (self.next + 1) % VisitedMethods.LANES
			if self.next == 0:
				self.next += 1

		return self.methods[method_name]

	def update_last_text(self, method_name, last_text):
		m = self.get(method_name)
		m['last_text'] = last_text
		self.methods[method_name] = m


class DataLoader:
	@staticmethod
	def load_commands(filename):
		command_list = []
		with open(filename) as f:
			f.readline() # Read past header
			f.readline() # Read past the start timestamp

			for line in f:
				c = Command(line)
				command_list.append(c)
		return command_list

	@staticmethod
	def load_codedevents(filename):
		codedevent_list = []
		with open(filename) as f:
			f.readline() # Read past the first header row
			f.readline() # Read past the second header row

			for line in f:
				ce = CodedEvent(line)
				if ce.valid:
					codedevent_list.append(ce)

		return codedevent_list


def data_commands(pid):
	return os.path.join("data", "p%02d-commands.txt" % (pid))

def data_codedevents(pid):
	return os.path.join("data", "p%02d-coded.txt" % (pid))


if __name__ == "__main__":
	# participants = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
	participants = [2]

	for p in participants:
		t = Timeline(p, DataLoader.load_codedevents(data_codedevents(p)), DataLoader.load_commands(data_commands(p)))
		t.draw()