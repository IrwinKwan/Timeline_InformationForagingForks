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

import os
from datetime import timedelta
from pyparsing import *
from math import ceil
import svgwrite
from collections import OrderedDict

from events import CodeError, DataLoader

class TimelineDecorations:
	def __init__(self, svg_timeline, coded_events, participant):
		self.svg_timeline = svg_timeline
		self.coded_events = coded_events
		self.participant = participant

	def draw(self):
		self._draw_x_axis()
		self._draw_x_axis(Timeline.CHART_HEIGHT)
		self._draw_x_axis(Timeline.HEIGHT)
		self._draw_x_tickmarks()
		self._draw_x_labels()
		self._draw_participant_label()

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

	def _draw_sessiontime(self):
		duration = self._calculate_timeline_duration(self.coded_events)
		minute = 1
		for xpos in range(0, int(ceil(duration.total_seconds())), Timeline.X_LABEL_GAP):

			self.svg_timeline.add(self.svg_timeline.text(minute,
				insert=(xpos + Timeline.X_OFFSET, 14),
				font_family="sans-serif",
				font_size="14"))
			minute += 1



	def _draw_videotime(self):
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

	def _draw_x_labels(self):
		self._draw_videotime()
		self._draw_sessiontime()

	def _draw_participant_label(self):
		self.svg_timeline.add(self.svg_timeline.text("P%02d" % (self.participant),
				insert=(0, Timeline.Y_OFFSET + Timeline.HEIGHT + 20),
				font_family="sans-serif",
				font_size="14"))

	def draw_legend(self):
		legend = self.svg_timeline.text("",
			insert=(0, Timeline.Y_OFFSET),
			font_family="sans-serif",
			text_anchor="end",
			font_size="9")

		startpos = Timeline.X_OFFSET - 2

		for key, value in EventLine.COLOR.items():

			legend.add(svgwrite.text.TSpan(key.replace("_", " ").capitalize(), insert=None, fill=value,
				x=[startpos], dy=[10]))

		self.svg_timeline.add(legend)


class Square:
	def __init__(self, svg_timeline, event):

		self.svg_timeline = svg_timeline
		self.foraging = event['Foraging']
		self.index = event['Index']

		try:
			self.retrospective = event['Retrospective fork']
		except:
			self.retrospective = ''

		if event['LearningDoing'] and not event['Forks']:
			raise CodeError('Coded Data error: learning/doing coded but the fork is not.')

		self.fork = event['Forks']
		self.learning_or_doing = event['LearningDoing']

	def _draw_text(self, xpos):
		size = "14"
		style = None

		fork_text = ''

		if self.fork > 0 and self.retrospective == 'y':
			fork_text = 'f'
			style = self.svg_timeline.g(style='text-decoration:underline; font-weight:bold')
		elif self.fork == 0 and self.retrospective.lower() == 'y':
			fork_text = 'x'
		elif self.fork > 0 and self.retrospective == 'n':
			fork_text = 'x'
		elif self.fork == 0 and self.retrospective.lower() == 'n':
			
			fork_text = 'f'

		text = self.svg_timeline.text(
			fork_text,
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
		opacity = "0.3"
		if self.foraging:
			fill = "beige"
			opacity = "0.7"

		self.svg_timeline.add(self.svg_timeline.rect(
			insert=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET),
			size=(Timeline.SQUARE_WIDTH, Timeline.CHART_HEIGHT),
			fill=fill,
			opacity=opacity,
			stroke_width="0"))

		self._draw_text(xpos)



class CommandTooSoonException(Exception):
	pass

class EventLine:

	HEIGHT = 10

	COLOR = OrderedDict()
	COLOR['open'] = 'maroon'
	COLOR['select'] = 'indigo'
	COLOR['move'] = 'yellow'
	COLOR['move_keyboard'] = 'magenta'
	COLOR['edit'] = 'red'
	COLOR['find'] = 'orange'
	COLOR['assist'] = 'blue'
	COLOR['save'] = 'deeppink'
	COLOR['run'] = 'darkgreen'
	COLOR['debugging'] = 'olive'
	COLOR['breakpoint_ruler'] = 'darkolivegreen'
	COLOR['java_perspective'] = 'olivedrab'
	COLOR['terminate'] = 'greenyellow'
	COLOR['open_editor'] = 'slateblue'
	COLOR['call_hierarchy'] = 'steelblue'
	COLOR['default'] = 'darkslategrey'

	def __init__(self, svg_timeline, event, start):
		self.svg_timeline = svg_timeline
		self.event = event
		self.start_time = start

	def _draw_open(self, xpos):
		self._draw(EventLine.COLOR['open'], -5, xpos)

	def _draw_select(self, xpos):
		self._draw(EventLine.COLOR['select'], 30, xpos)

	def _draw_move(self, xpos):
		self._draw(EventLine.COLOR['move'], 60, xpos)

	def _draw_keyboard_move(self, xpos):
		self._draw(EventLine.COLOR['move_keyboard'], 60, xpos)

	def _draw_edit(self, xpos):
		self._draw(EventLine.COLOR['edit'], 70, xpos)

	def _draw_find(self, xpos):
		self._draw(EventLine.COLOR['find'], 140, xpos)

	def _draw_assist(self, xpos):
		self._draw(EventLine.COLOR['assist'], 140, xpos)

	def _draw_save(self, xpos):
		self._draw(EventLine.COLOR['save'], 180, xpos)

	def _draw_run(self, xpos):
		self._draw(EventLine.COLOR['run'], 180, xpos)

	def _draw_debugging(self, xpos):
		self._draw(EventLine.COLOR['debugging'], 200, xpos)

	def _draw_breakpoint_ruler(self, xpos):
		self._draw(EventLine.COLOR['breakpoint_ruler'], 210, xpos)

	def _draw_terminate(self, xpos):
		self._draw(EventLine.COLOR['terminate'], 190, xpos)

	def _draw_java_perspective(self, xpos):
		self._draw(EventLine.COLOR['java_perspective'], 210, xpos)

	def _draw_open_editor(self, xpos):
		self._draw(EventLine.COLOR['open_editor'], 220, xpos)

	def _draw_call_hierarchy(self, xpos):
		self._draw(EventLine.COLOR['call_hierarchy'], 140, xpos)		

	def _draw_default(self, xpos):
		self._draw(EventLine.COLOR['default'], 240, xpos)

	def _draw(self, color, top, xpos):
		# add bottom.
		self.svg_timeline.add(self.svg_timeline.line(
				start=(xpos + Timeline.X_OFFSET, top + Timeline.Y_OFFSET),
				end=(xpos + Timeline.X_OFFSET, Timeline.HEIGHT + Timeline.Y_OFFSET)).
				stroke(color=color, width=1, opacity=0.9))

	def _eclipseCommand(self, xpos):
		if self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.StepOver" \
			or self.event['EclipseCommand'] ==  "org.eclipse.debug.ui.commands.StepInto" \
			or self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.StepReturn" \
			or self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.Resume":
			self._draw_debugging(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.Terminate":
			self._draw_terminate(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.DebugLast" \
			or self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.RunLast":
			self._draw_run(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.debug.ui.commands.eof":
			pass
		elif self.event['EclipseCommand'] == "org.eclipse.jdt.ui.edit.text.java.gotoBreadcrumb":
			pass
		elif self.event['EclipseCommand'] == "org.eclipse.ui.views.showView":
			pass
		elif self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.showInformation":
			pass
		elif self.event['EclipseCommand'] == 'AUTOGEN:::org.eclipse.jdt.internal.ui.CompilationUnitEditor.ruler.actions/org.eclipse.jdt.internal.ui.javaeditor.JavaSelectRulerAction':
			print "Add an event and check what a JavaSelectRulerAction is"
			pass
		elif self.event['EclipseCommand'] == 'org.eclipse.ui.edit.selectAll':
			pass
		elif self.event['EclipseCommand'] == "eventLogger.styledTextCommand.COLUMN_NEXT" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.COLUMN_PREVIOUS" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.DELETE_PREVIOUS" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.LINE_DOWN" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.LINE_UP" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.SELECT_COLUMN_NEXT" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.SELECT_COLUMN_PREVIOUS" \
			or self.event['EclipseCommand'] == "eventLogger.styledTextCommand.SELECT_LINE_UP" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.goto.lineEnd" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.goto.lineStart" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.goto.textStart" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.goto.wordNext" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.goto.wordPrevious" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.select.lineStart" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.select.wordNext" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.select.wordPrevious":
			# Keyboard commands for navigating text
			self._draw_keyboard_move(xpos)
		elif self.event['EclipseCommand'] == 'AUTOGEN:::org.eclipse.jdt.debug.CompilationUnitEditor.BreakpointRulerActions/org.eclipse.jdt.debug.ui.actions.ManageBreakpointRulerAction':
			self._draw_breakpoint_ruler(xpos)
		elif self.event['EclipseCommand'] == 'org.eclipse.jdt.ui.JavaPerspective':
			self._draw_java_perspective(xpos)
		elif self.event['EclipseCommand'] == 'org.eclipse.ui.perspectives.showPerspective':
			# This overlaps with JavaPerspective
			pass
		elif self.event['EclipseCommand'] == 'org.eclipse.jdt.ui.edit.text.java.open.call.hierarchy':
			self._draw_call_hierarchy(xpos)
		elif self.event['EclipseCommand'] == 'org.eclipse.jdt.ui.navigate.open.type.in.hierarchy':
			self._draw_call_hierarchy(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.contentAssist.proposals":
			self._draw_assist(xpos)
		elif self.event['EclipseCommand'] == 'org.eclipse.jdt.ui.edit.text.java.open.editor':
			# An open declaration or similar that requires going to another file
			self._draw_open_editor(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.search.ui.openFileSearchPage" \
			or self.event['EclipseCommand'] == "org.eclipse.search.ui.openSearchDialog" \
			or self.event['EclipseCommand'] == "org.eclipse.search.ui.performTextSearchFile" \
			or self.event['EclipseCommand'] == "org.eclipse.search.ui.performTextSearchWorkspace" \
			or self.event['EclipseCommand'] == "org.eclipse.ui.edit.findNext"\
			or self.event['EclipseCommand'] == "org.eclipse.jdt.ui.edit.text.java.search.declarations.in.project" \
			or self.event['EclipseCommand'] == "org.eclipse.jdt.ui.edit.text.java.search.declarations.in.workspace" \
			or self.event['EclipseCommand'] == "org.eclipse.jdt.ui.edit.text.java.search.references.in.project":
			self._draw_find(xpos)
		elif self.event['EclipseCommand'] == "org.eclipse.ui.edit.text.folding.collapse_all":
			pass
		elif self.event['EclipseCommand'] == "org.eclipse.ui.file.save":
			self._draw_save(xpos)
		else:
			print 'EclipseCommand ' + self.event['EclipseCommand']
			self._draw_default(xpos)

	def draw(self):
		xpos = Timeline.calculate_x_position(self.start_time, self.event['Time'])

		if self.event['Command'] == 'FileOpenCommand':
			self._draw_open(xpos)
		elif self.event['Command'] == 'SelectTextCommand':
			self._draw_select(xpos)
		elif self.event['Command'] == 'MoveCaretCommand':
			# self._draw_move(xpos)
			pass
		elif self.event['Command'] == 'CopyCommand' \
			or self.event['Command'] == 'CutCommand' \
			or self.event['Command'] == 'PasteCommand':
			pass
		elif self.event['Command'] == 'RunCommand':
			self._draw_run(xpos)
		elif self.event['Command'] == 'Insert' \
			or self.event['Command'] == 'Delete' \
			or self.event['Command'] == 'Replace' \
			or self.event['Command'] == 'UndoCommand':
			self._draw_edit(xpos)
		elif self.event['Command'] == 'InsertStringCommand':
			# This overlaps with 'Insert'
			pass
		elif self.event['Command'] == 'FindCommand':
			self._draw_find(xpos)
		elif self.event['Command'] == 'AssistCommand':
			self._draw_assist(xpos)
		elif self.event['Command'] == 'EclipseCommand':
			self._eclipseCommand(xpos)			
		else:
			print self.event['Command']
			self._draw_default(xpos)


class MethodLaneException(Exception):
	pass

class MethodBar:
	TEXT_WIDTH = 120
	METHOD_NULL = "Other"

	# Threshold in seconds, if visits are less or equal to this value, don't draw it as visited.
	VISIT_THRESHOLD = 0.1 

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
		if new_event and (MethodBar.method_name(new_event) == self.my_name):
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
			text_string = event['ActiveFile'] + ":" + MethodBar.METHOD_NULL

		return text_string

	def _xstart(self):
		return Timeline.calculate_x_position(self.timeline_start, self.start['Time'])

	def _draw_text(self, x_start):
		if not self.last_text:
			return True
		elif (self.last_text + MethodBar.TEXT_WIDTH) < (x_start):
			return True
		else:
			return False

	def _draw_bar(self, x_start):
		"""Draws the elapsed time for visiting a method"""
		duration = self.end['Time'] - self.start['Time']
		self.svg_timeline.add(self.svg_timeline.rect(
			insert=(x_start, Timeline.METHOD_LANE_HEIGHT * self.lane + Timeline.CHART_HEIGHT + Timeline.Y_OFFSET),
			size=(duration.total_seconds(), Timeline.METHOD_LANE_HEIGHT),
			fill=self.background,
			opacity="0.4",
			stroke_width="0"))

	def _draw_method(self, x_start):
		"""Draws the method text"""
		textcolor = "midnightblue"
		if self.my_name !=  MethodBar.METHOD_NULL:
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

		duration = self.end['Time'] - self.start['Time']
		if duration.total_seconds() > MethodBar.VISIT_THRESHOLD:
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
	OUTPUT_DIR = "../timeline_forks_data"
	X_MARGIN = 10
	X_OFFSET = 80
	Y_OFFSET = 16

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
		self.svg_timeline = svgwrite.Drawing(filename = os.path.join(Timeline.OUTPUT_DIR, "%02d.svg" % pid), size=("2220px", "290px"))

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
		decorations = TimelineDecorations(self.svg_timeline, self.coded_events, self.pid)
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

	def _draw_overlap(self, xpos):
		self.svg_timeline.add(self.svg_timeline.line(
				start=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET),
				end=(xpos + Timeline.X_OFFSET, 5 + Timeline.Y_OFFSET)).
				stroke(color="black", width=1, opacity=1.0))

	def _draw_command_events(self):
		event_queue = {}
		for event in self.commands:
						
			try:
				xpos = Timeline.calculate_x_position(self.start_time, event['Time'])
				if xpos in event_queue:
					self._draw_overlap(xpos)
				else:
					event_queue[xpos] = event

				self._draw_command_event(event)
			except CommandTooSoonException:
				pass

		# Draw everything in the queue

	def _event_at_session_start(self, event):
		ev_start_at_session = event
		ev_start_at_session['Time'] = self.start_time
		return ev_start_at_session

	def _draw_methods(self):
		start_event = None
		xpos = 0
		
		for event in self.commands:
			if 'error' not in event:
				if self.before_start(event):
					start_event = MethodBar(self.svg_timeline, self._event_at_session_start(event), self.start_time, self.visited_methods)
				else:
					if not start_event:
						start_event = MethodBar(self.svg_timeline, event, self.start_time, self.visited_methods)

					if not start_event.same_method(event):
						self.visited_methods = start_event.draw(event)
						start_event = MethodBar(self.svg_timeline, event, self.start_time, self.visited_methods)
					
			xpos += Timeline.SQUARE_WIDTH

		# Draw the final event
		if 'error' not in event:
			self.visited_methods = start_event.draw(event)

	def draw(self):
		"""Converts the textual commands_list to a graphical timeline view in SVG."""
		
		self._draw_coded_events()
		self._draw_command_events()
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
		self.next = 0

	def is_unknown(self, method_name):
		method = method_name.split(':')[-1]
		if method == MethodBar.METHOD_NULL:
			return True
		else:
			return False

	def get(self, method_name):
		if not method_name in self.methods:
			m = {}
			if self.is_unknown(method_name):
				m['color'] = 'grey'
			else:
				m['color'] = VisitedMethods.COLORS[self.next % len(VisitedMethods.COLORS)]

			m['last_text'] = None
			m['lane'] = self.next
			self.methods[method_name] = m
			self.next = (self.next + 1) % VisitedMethods.LANES
			if self.next == 0:
				self.next += 1

		return self.methods[method_name]

	def update_last_text(self, method_name, last_text):
		m = self.get(method_name)
		m['last_text'] = last_text
		self.methods[method_name] = m


if __name__ == "__main__":
	#participants = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] # P11 has incomplete commands data
	participants = [7]

	for p in participants:
		print "Participant %d" % p
		t = Timeline(p, DataLoader.load_codedevents(p), DataLoader.load_commands(p))
		t.draw()