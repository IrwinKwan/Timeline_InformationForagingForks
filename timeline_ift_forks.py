#!/usr/bin/env python

"""This script takes input data from a coded spreadsheet with
foraging information in it and forks from a copy/paste of
 the "correct" tab creates a visual timeline
of the participant's actions.

Output:

- An SVG file of the timeline, ex: p0X.svg

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


class ForagingSegment:
    def __init__(self, svg_timeline, event, section=None):
        self.svg_timeline = svg_timeline
        self.foraging = event['Foraging']

    def _draw_text(self, xpos):
        size = "14"
        style = None

        text = self.svg_timeline.text(
            self._fork_text(),
            insert=(xpos + Timeline.SQUARE_WIDTH/2 + Timeline.X_OFFSET, Timeline.CHART_HEIGHT - 10 + Timeline.Y_OFFSET),
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

        # Foraging Background
        self.svg_timeline.add(self.svg_timeline.rect(
            insert=(xpos + Timeline.X_OFFSET, Timeline.Y_OFFSET),
            size=(Timeline.SQUARE_WIDTH, Timeline.CHART_HEIGHT),
            fill=fill,
            opacity=opacity,
            stroke_width="0"))


class ForkOutcomeSegment(object):
    def __init__(self, svg_timeline, event, section=None):
        self.svg_timeline = svg_timeline
        self.index = event['Index']
        self.forks = event['Forks']

        self.lane = 0
        self.total = len(self.forks)

    def _fork_text(self, fork):
        fork_text = ''

        try:
            fork_type = fork.name

            # Since we can't really plot two forks at the same spot on the graph, plot the first one only.
            if fork_type == "Verified":
                fork_text = 'v'
                style = self.svg_timeline.g(style='text-decoration:underline; font-weight:bold')
            elif fork_type == "Undetected":
                fork_text = 'u'
            elif fork_type == "False":
                fork_text = '_'
            elif fork_type == "No":
                fork_text = ''
            elif fork_type == "Unverified":
                fork_text = "~v"
            elif fork_type == "No Data":
                fork_text = ''
            elif fork_type == "ERROR":
                fork_text = '!'
            elif fork_type == "Removed":
                fork_text = ''
        except IndexError:
            fork_type = ''

        return fork_text

    def _draw_text(self, xpos, fork):
        style = None
        h = 12
        size = int(14 - (2 * self.total))
        x = Timeline.SQUARE_WIDTH/self.total

        text = self.svg_timeline.text(
            self._fork_text(fork),
            insert=(xpos + x/2 + Timeline.X_OFFSET, Timeline.CHART_HEIGHT - h + Timeline.Y_OFFSET),
            font_family="sans-serif",
            font_size=str(size),
            text_anchor="middle",
            dy="5")

        if style:
            style.add(text)
            self.svg_timeline.add(style)
        else:
            self.svg_timeline.add(text)

    def _success_fill(self, fork):
        successful = fork.success
        success_fill = "white"

        if fork.name != 'Removed':
            if successful == 'NA':
                success_fill = "gold"
            elif successful == 'successful':
                success_fill = "palegreen"
            elif successful == 'unsuccessful':
                success_fill = "orangered"
            else:
                success_fill = "white"

        return success_fill

    def _draw_square(self, xpos, fork):

        h = EventLine.HEIGHT * 2

        # Successful/Not Successful Background
        self.svg_timeline.add(self.svg_timeline.rect(
            insert=(xpos + Timeline.X_OFFSET, Timeline.CHART_HEIGHT - h + Timeline.Y_OFFSET),
            size=(Timeline.SQUARE_WIDTH * 1.0/self.total, h),
            fill=self._success_fill(fork),
            opacity=1.0,
            stroke_width="0"))

    def draw(self, xpos):
        """Draws the square according to its properties"""

        for fork in self.forks:
            self._draw_square(xpos, fork)
            self._draw_text(xpos, fork)
            xpos += Timeline.SQUARE_WIDTH/2


class CommandTooSoonException(Exception):
    pass


class ForkFeatureType:

    HEIGHT = 10

    COLOR = OrderedDict()

    # Each tuple represents the color, the starting 'top' position, and the lane.
    COLOR['Position'] = ('maroon', 1)
    COLOR['Proximity'] = ('indigo', 2)
    COLOR['Familiarity'] = ('yellow', 3)
    COLOR['JEdit Source'] = ('magenta', 4)
    COLOR['Method arguments/return type'] = ('red', 5)
    COLOR['Size of code'] = ('orange', 6)
    COLOR['Domain Text'] = ('green', 7)
    COLOR['GUI Text'] = ('steelblue', 8)
    COLOR['Contrast'] = ('red', 9)
    COLOR['Synonyms'] = ('pink', 10)
    COLOR['Antonyms'] = ('green', 11)
    COLOR['Level of Abstraction'] = ('blue', 12)
    COLOR['Comments'] = ('deeppink', 13)
    COLOR['File Type'] = ('darkgreen', 14)
    COLOR['Hardcoded Numbers'] = ('olive', 15)
    COLOR['Values of Variables'] = ('darkolivegreen', 16)
    COLOR['Examples'] = ('olivedrab', 17)
    COLOR['Exception'] = ('greenyellow', 18)
    COLOR['External Doc'] = ('slateblue', 19)
    COLOR['Unknown'] = ('darkslategrey', 20)

    # COLOR['default'] = ('darkslategrey', 250, 21)

    def __init__(self, svg_timeline, events, start):
        self.svg_timeline = svg_timeline
        self.events = events
        self.num_events = len(events)
        self.start_time = start

    def _draw(self, fork, point, xpos):
        """Draw a line between two points horizontally on the lane."""

        segment_width = 30
        fractional_width = int(float(segment_width)/self.num_events)
        start_offset = fractional_width * (fork['Order'] - 1)
        color = point[0]
        lane = point[1]

        print (fork['Fork'], fork['Order'], color)
        print start_offset

        x_baseline = Timeline.X_OFFSET + xpos - segment_width

        start = (x_baseline + start_offset,
            ((lane - 1) * EventLine.HEIGHT) + Timeline.Y_OFFSET + EventLine.HEIGHT/2)
        end = (x_baseline + start_offset + fractional_width,
            ((lane - 1) * EventLine.HEIGHT) + Timeline.Y_OFFSET + EventLine.HEIGHT/2)

        self.svg_timeline.add(self.svg_timeline.line(
            start=start, end=end).
            stroke(color=color, width=EventLine.HEIGHT, opacity=0.9))


    def draw(self):
        xpos = Timeline.calculate_x_position(self.start_time, self.events[0]['Time'])

        for fork in self.events:
            for ft in fork['FeatureType']:
                self._draw(fork, self.COLOR[ft], xpos)


class EventLine:

    HEIGHT = 10

    COLOR = OrderedDict()
    COLOR['open'] = 'maroon'
    COLOR['select'] = 'indigo'
    COLOR['move'] = 'yellow'
    COLOR['move_keyboard'] = 'magenta'
    COLOR['edit'] = 'red'
    COLOR['text_search'] = 'orange'
    COLOR['find_next'] = 'green'
    COLOR['find_dialog'] = 'steelblue'
    COLOR['search_declarations'] = 'red'
    COLOR['file_search'] = 'pink'
    COLOR['search_references'] = 'green'

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
        self._draw(EventLine.COLOR['open'], 0, 1, xpos)

    def _draw_select(self, xpos):
        self._draw(EventLine.COLOR['select'], 30, 2, xpos)

    def _draw_move(self, xpos):
        self._draw(EventLine.COLOR['move'], 60, 3, xpos)

    def _draw_keyboard_move(self, xpos):
        self._draw(EventLine.COLOR['move_keyboard'], 60, 4, xpos)

    def _draw_edit(self, xpos):
        self._draw(EventLine.COLOR['edit'], 70, 5, xpos)

    def _draw_find(self, xpos):
        self._draw(EventLine.COLOR['text_search'], 140, 6, xpos)

    def _draw_find_next(self, xpos):
        self._draw(EventLine.COLOR['find_next'], 140, 7, xpos)

    def _draw_search_declarations(self, xpos):
        self._draw(EventLine.COLOR['search_declarations'], 140, 9, xpos)

    def _draw_search_file(self, xpos):
        self._draw(EventLine.COLOR['file_search'], 140, 10, xpos)

    def _draw_search_references(self, xpos):
        self._draw(EventLine.COLOR['search_references'], 140, 11, xpos)

    def _draw_assist(self, xpos):
        self._draw(EventLine.COLOR['assist'], 140, 12, xpos)
        
    def _draw_save(self, xpos):
        self._draw(EventLine.COLOR['save'], 180, 13, xpos)

    def _draw_run(self, xpos):
        self._draw(EventLine.COLOR['run'], 180, 14, xpos)

    def _draw_debugging(self, xpos):
        self._draw(EventLine.COLOR['debugging'], 200, 15, xpos)

    def _draw_breakpoint_ruler(self, xpos):
        self._draw(EventLine.COLOR['breakpoint_ruler'], 210, 16, xpos)

    def _draw_java_perspective(self, xpos):
        self._draw(EventLine.COLOR['java_perspective'], 210, 17, xpos)

    def _draw_terminate(self, xpos):
        self._draw(EventLine.COLOR['terminate'], 190, 18, xpos)

    def _draw_open_editor(self, xpos):
        self._draw(EventLine.COLOR['open_editor'], 220, 19, xpos)

    def _draw_call_hierarchy(self, xpos):
        self._draw(EventLine.COLOR['call_hierarchy'], 140, 20, xpos)

    def _draw_default(self, xpos):
        self._draw(EventLine.COLOR['default'], 240, 21, xpos)

    def _draw(self, color, top, lane, xpos):

        # self.svg_timeline.add(self.svg_timeline.line(
        #       start=(xpos + Timeline.X_OFFSET, top + Timeline.Y_OFFSET),
        #       end=(xpos + Timeline.X_OFFSET, Timeline.HEIGHT + Timeline.Y_OFFSET)).
        #       stroke(color=color, width=1, opacity=0.9))

        self.svg_timeline.add(self.svg_timeline.line(
            start=(xpos + Timeline.X_OFFSET, ((lane - 1) * EventLine.HEIGHT) + Timeline.Y_OFFSET),
            end=(xpos + Timeline.X_OFFSET, ((lane - 1) * EventLine.HEIGHT) + EventLine.HEIGHT + Timeline.Y_OFFSET)).
            stroke(color=color, width=1, opacity=0.9))

    def _eclipseCommand(self, xpos):
        ec = self.event['EclipseCommand']

        if self.event['EclipseCommand'] == 'AUTOGEN:::org.eclipse.jdt.debug.CompilationUnitEditor.BreakpointRulerActions/org.eclipse.jdt.debug.ui.actions.ManageBreakpointRulerAction':
            # Clicking in the Java Code Editor breakpoint gutter
            self._draw_debugging(xpos)
        elif ec == "AUTOGEN:::org.eclipse.jdt.internal.ui.CompilationUnitEditor.ruler.actions/org.eclipse.jdt.internal.ui.javaeditor.JavaSelectRulerAction":
            # Clicking in the Java Code Editor gutter
            pass
        elif ec == "eventLogger.styledTextCommand.COLUMN_NEXT":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.COLUMN_PREVIOUS":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.DELETE_PREVIOUS":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.LINE_DOWN":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.LINE_UP":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.SELECT_COLUMN_NEXT":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.SELECT_COLUMN_PREVIOUS":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "eventLogger.styledTextCommand.SELECT_LINE_UP":
            # Using the keyboard
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.debug.ui.commands.DebugLast":
            # Debuggung, run the program in debug mode
            self._draw_run(xpos)
        elif ec == "org.eclipse.debug.ui.commands.Resume":
            self._draw_debugging(xpos)
        elif ec == "org.eclipse.debug.ui.commands.RunLast":
            self._draw_run(xpos)
        elif ec == "org.eclipse.debug.ui.commands.StepInto":
            self._draw_debugging(xpos)
        elif ec == "org.eclipse.debug.ui.commands.StepOver":
            self._draw_debugging(xpos)
        elif ec == "org.eclipse.debug.ui.commands.StepReturn":
            self._draw_debugging(xpos)
        elif ec == "org.eclipse.debug.ui.commands.Terminate":
            self._draw_terminate(xpos)
        elif ec == "org.eclipse.debug.ui.commands.eof":
            # Some kind of keyboard command
            pass
        elif ec == "org.eclipse.jdt.ui.JavaPerspective":
            # Change to the Java Perspective
            self._draw_debugging(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.gotoBreadcrumb":
            # The breadcrumbs outlining a file path
            pass
        elif ec == "org.eclipse.jdt.ui.edit.text.java.open.call.hierarchy":
            self._draw_call_hierarchy(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.open.editor":
            # Opens an editor in a special way
            self._draw_open(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.organize.imports":
            # Organizing the import statements of the file
            pass
        elif ec == "org.eclipse.jdt.ui.edit.text.java.search.declarations.in.project":
            self._draw_search_declarations(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.search.declarations.in.workspace":
            self._draw_search_declarations(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.search.references.in.project":
            self._draw_search_references(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.search.references.in.workspace":
            self._draw_search_references(xpos)
        elif ec == "org.eclipse.jdt.ui.edit.text.java.show.outline":
            self._draw_search_references(xpos)
        elif ec == "org.eclipse.jdt.ui.navigate.open.type":
            # Opening a type declaration in one of the explicit Dialogs
            pass
        elif ec == "org.eclipse.jdt.ui.navigate.open.type.in.hierarchy":
            self._draw_call_hierarchy(xpos)
        elif ec == "org.eclipse.search.ui.openFileSearchPage":
            self._draw_search_file(xpos)
        elif ec == "org.eclipse.search.ui.openSearchDialog":
            self._draw_find(xpos)
        elif ec == "org.eclipse.search.ui.performTextSearchFile":
            # Trying to open text search from menu (P10) and failing
            self._draw_find(xpos)
        elif ec == "org.eclipse.search.ui.performTextSearchWorkspace":
            self._draw_find(xpos)
        elif ec == "org.eclipse.ui.edit.findNext":
            self._draw_find_next(xpos)
        elif ec == "org.eclipse.ui.edit.selectAll":
            # Select all text
            pass
        elif ec == "org.eclipse.ui.edit.text.contentAssist.proposals":
            # Suggestions for autocompletion
            pass
        elif ec == "org.eclipse.ui.edit.text.folding.collapse_all":
            # Collapse folds
            pass
        elif ec == "org.eclipse.ui.edit.text.goto.lineEnd":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.goto.lineStart":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.goto.textStart":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.goto.wordNext":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.goto.wordPrevious":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.select.lineStart":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.select.wordNext":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.select.wordPrevious":
            # Moving using keyboard commands
            self._draw_keyboard_move(xpos)
        elif ec == "org.eclipse.ui.edit.text.showInformation":
            # When JavaDoc tooltip is made editable
            pass
        elif ec == "org.eclipse.ui.file.properties":
            # Looking at file properties
            pass
        elif ec == "org.eclipse.ui.file.refresh":
            # Refreshing a file, kind of like open
            self._draw_open(xpos)
        elif ec == "org.eclipse.ui.file.save":
            self._draw_save(xpos)
        elif ec == "org.eclipse.ui.navigate.openResource":
            # Using the Open Resource window
            self._draw_open(xpos)
        elif ec == "org.eclipse.ui.perspectives.showPerspective":
            # Overlaps with Java perspective
            pass
        elif ec == "org.eclipse.ui.views.showView":
            # Show a plugin view Eclipse
            pass
        elif ec == "org.eclipse.ui.window.newEditor":
            # **Check this.
            pass
        else:
            print "We missed an event %s" % self.event

    def draw(self):
        xpos = Timeline.calculate_x_position(self.start_time, self.event['Time'])

        if self.event['Command'] == 'FileOpenCommand':
            # Occurs whenever a 'file is brought into focus'. Ex: Opening files, switching tabs, closing other tabs, etc.
            self._draw_open(xpos)
        elif self.event['Command'] == 'SelectTextCommand':
            # When user selects/highlights text
            self._draw_select(xpos)
        elif self.event['Command'] == 'MoveCaretCommand':
            # When the user moves the editor caret
            # self._draw_move(xpos)
            pass
        elif self.event['Command'] == 'CopyCommand' \
            or self.event['Command'] == 'CutCommand' \
            or self.event['Command'] == 'PasteCommand':
            # Cut, copy, paste
            pass
        elif self.event['Command'] == 'RunCommand':
            # Runs program in Eclipse
            self._draw_run(xpos)
        elif self.event['Command'] == 'Insert' \
            or self.event['Command'] == 'Delete' \
            or self.event['Command'] == 'Replace' \
            or self.event['Command'] == 'UndoCommand':
            # Inserting, deleting, or replacing data. Also undo.
            self._draw_edit(xpos)
        elif self.event['Command'] == 'InsertStringCommand':
            # This overlaps with 'Insert'
            pass
        elif self.event['Command'] == 'FindCommand':
            # Using one kind of 'find', not exactly sure which one
            self._draw_find(xpos)
        elif self.event['Command'] == 'AssistCommand':
            # Assistance when editing files, the AutoComplete in Eclipse
            pass
        elif self.event['Command'] == 'EclipseCommand':
            # This brings ups to a set of other events, which are described above
            self._eclipseCommand(xpos)          
        else:
            self._draw_default(xpos)


class MethodLaneException(Exception):
    pass

class MethodBar:
    TEXT_WIDTH = 120
    METHOD_NULL = "Other"

    # Threshold in seconds, if visits are less or equal to this value, don't draw it as visited.
    VISIT_THRESHOLD = 0.1 

    def __init__(self, svg_timeline, event_start, timeline_start, timeline_height, visited_methods):
        self.svg_timeline = svg_timeline
        self.start = event_start
        self.my_name = MethodBar.method_name(event_start)
        self.timeline_start = timeline_start
        self.timeline_height = timeline_height

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

    def _text_exists(self, x_start):
        if not self.last_text:
            return True
        elif (self.last_text + MethodBar.TEXT_WIDTH) < x_start:
            return True
        else:
            return False

    def _draw_bar(self, x_start):
        """Draws the elapsed time for visiting a method"""

        self.background = "grey" # Overwrite the background to create a null color.

        duration = self.end['Time'] - self.start['Time']
        self.svg_timeline.add(self.svg_timeline.rect(
            insert=(x_start, Timeline.METHOD_LANE_HEIGHT * self.lane + self.timeline_height + Timeline.Y_OFFSET),
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
            insert=(x_start, 2 + self.timeline_height + Timeline.METHOD_LANE_HEIGHT * self.lane + Timeline.Y_OFFSET),
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
            if self._text_exists(x_start):
                self._draw_method(x_start)

            self.visited_methods.update_last_text(self.my_name, self.last_text)

        return self.visited_methods


class PatchLaneException(Exception):
    pass


class PatchBar(object):
    """Method cloned, but not yet adapted."""
    TEXT_WIDTH = 120

    COLORS = {
        'Package Explorer': 'cyan',
        'Editor': 'skyblue',
        'Stack Trace': 'lightsalmon',
        'Search Results': 'peachpuff',
        'Variables': 'springgreen',
        'Outline': 'lightgreen',
        'Bug Report': 'olive',
        'Firefox Web Browser': 'darkseagreen',
        'Misc': 'lightgray'
    }

    def __init__(self, svg_timeline, fork_event, lane, timeline_start, timeline_height):
        self.svg_timeline = svg_timeline

        self.label = fork_event["Patch"]
        self._lane = lane

        self._start = fork_event["Start"]
        self._end = fork_event["End"]

        self._timeline_start = timeline_start
        self._timeline_height = timeline_height

        self._y = self._timeline_height + Timeline.METHOD_LANE_HEIGHT * self._lane + Timeline.Y_OFFSET

    @property
    def label(self):
        return self._patch_label

    @label.setter
    def label(self, patch):
        patch_name = patch.split(":")
        self._patch_label = patch_name[0].strip()

    @property
    def color(self):
        try:
            return PatchBar.COLORS[self.label]
        except:
            return PatchBar.COLORS['Misc']

    @property
    def xstart(self):
        return Timeline.calculate_x_position(self._timeline_start, self._start)

    def _svg_bar(self):
        """Draws the elapsed time bar"""
        x_start = self.xstart + Timeline.X_OFFSET

        duration = self._end - self._start
        self.svg_timeline.add(self.svg_timeline.rect(
            insert=(x_start, self._y),
            size=(duration.total_seconds(), Timeline.METHOD_LANE_HEIGHT),
            fill=self.color,
            opacity="0.4",
            stroke_width="0"))

    def _svg_text(self):
        """Draws the patch label"""
        x_start = self.xstart + Timeline.X_OFFSET
        textcolor = "black"

        self.svg_timeline.add(self.svg_timeline.text(
            self.label,
            insert=(x_start, 2 + self._y),
            font_family="sans-serif",
            font_size="8",
            text_anchor="start",
            fill=textcolor,
            dy="5"))

    def draw(self):
        """Draws the method's bar from start (stored in the instance) to the end"""
        self._svg_text()
        self._svg_bar()


class FeatureTypesChart(object):
    @staticmethod
    def draw_legend(legend):
        startpos = Timeline.X_OFFSET - 2
        for key, value in ForkFeatureType.COLOR.items():
            legend.add(svgwrite.text.TSpan(key.replace("_", " ").capitalize(), insert=None, fill=value[0],
                x=[startpos], dy=[10]))

        return legend


class EventLinesChart(object):
    @staticmethod
    def draw_legend(legend):
        startpos = Timeline.X_OFFSET - 2
        for key, value in EventLine.COLOR.items():
                legend.add(svgwrite.text.TSpan(key.replace("_", " ").capitalize(), insert=None, fill=value,
                    x=[startpos], dy=[10]))
        return legend


class TimelineDecorations:
    def __init__(self, svg_timeline, coded_events, participant):
        self.svg_timeline = svg_timeline
        self.coded_events = coded_events
        self.participant = participant

    def draw(self):

        self._draw_x_axis() # The top line

        # These are divisions for EventLine.
        # self._draw_x_axis(30)
        # self._draw_x_axis(50)
        # self._draw_x_axis(110)
        # self._draw_x_axis(130)
        # self._draw_x_axis(180)
        # self._draw_x_axis(200)

        # The line above the Success/Not Success section
        self._draw_x_axis(Timeline.CHART_HEIGHT - 2 * EventLine.HEIGHT)

        # THe line above the Patches
        self._draw_x_axis(Timeline.CHART_HEIGHT)

        # THe line above the methods
        self._draw_x_axis(Timeline.CHART_AND_PATCH_HEIGHT)

        # The bottom line
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

    def draw_legend(self, legend_types):
        legend = self.svg_timeline.text("",
            insert=(0, Timeline.Y_OFFSET),
            font_family="sans-serif",
            text_anchor="end",
            font_size="8")

        if legend_types == 'EventLine':
            legend = EventLinesChart.draw_legend(legend)
        elif legend_types == 'FeatureType':
            legend = FeatureTypesChart.draw_legend(legend)

        self.svg_timeline.add(legend)


class Timeline:
    """The representation of a timeline., including the graphical SVG view.

    X_OFFSET: The space of the chart away from the left edge of the screen.
    Y_OFFSET: The space of the chart away from the top of the screen.
    HEIGHT: The height of the chart.
    SQUARE_WIDTH: The width of one square
    X_GAP: The gap between tickmarks on x-axis
    TIMELABEL: The strftime label on x-axis"""
    OUTPUT_DIR = "../timeline_forks_data"
    X_MARGIN = 10
    X_OFFSET = 80
    Y_OFFSET = 16

    CHART_HEIGHT = 220 # The height of the "main" area of the graph.

    PATCH_LANES = 4
    PATCH_LANE_HEIGHT = PATCH_LANES * EventLine.HEIGHT

    METHOD_LANES = 19
    METHOD_LANE_HEIGHT = 10
    METHOD_HEIGHT = METHOD_LANES * METHOD_LANE_HEIGHT

    CHART_AND_PATCH_HEIGHT = CHART_HEIGHT + PATCH_LANE_HEIGHT # If we add more parts of the chart, it's going to need
                                                              # refactoring so that we can add arbitrary sections.

    SQUARE_WIDTH = 30
    HEIGHT = CHART_HEIGHT + PATCH_LANE_HEIGHT + METHOD_HEIGHT

    X_GAP = 30
    X_LABEL_GAP = 60

    TIMELABEL = "%M:%S"

    def __init__(self, pid, codedevents_list, commands_list, feature_type_matrix):

        # One day, break this chart into composable sections.
        self.sections = []

        self.coded_events = codedevents_list
        self.commands = commands_list
        self.feature_type_matrix = feature_type_matrix

        self.pid = pid
        self.svg_timeline = svgwrite.Drawing(filename = os.path.join(Timeline.OUTPUT_DIR, "%02d-forks.svg" % pid), size=("2220px", "520px"))

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

    def _aggregate(self):
        """Aggregates some data from one data list into another."""
        pass

    def __len__(self):
        return len(self.commands_list)

    def __str__(self):
        return '\n'.join(str(i) for i in self.commands_list)

    def _draw_timeline_decorations(self, legend_type):
        decorations = TimelineDecorations(self.svg_timeline, self.coded_events, self.pid)
        decorations.draw()
        decorations.draw_legend(legend_type)

    def _draw_coded_event(self, event, xpos):
        square = ForagingSegment(self.svg_timeline, event)
        square.draw(xpos)

        outcome = ForkOutcomeSegment(self.svg_timeline, event)
        outcome.draw(xpos)

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
                end=(xpos + Timeline.X_OFFSET, -5 + Timeline.Y_OFFSET)).
                stroke(color="black", width=1, opacity=1.0))

    def _draw_command_events(self):
        event_queue = {}
        for event in self.commands:

            event_time = self._lookup_fork_time(event['Forks'])
            try:
                xpos = Timeline.calculate_x_position(self.start_time, event[''])
                if xpos in event_queue:
                    self._draw_overlap(xpos)
                else:
                    event_queue[xpos] = event

                self._draw_command_event(event)
            except CommandTooSoonException:
                pass

        # Draw everything in the queue

    def _draw_featuretype_events(self):
        event_queue = {}

        for i in range(0, len(self.feature_type_matrix)):
            event = self.feature_type_matrix[i]
            events = []
            events.append(event)

            try:
                event['Time'] = self._lookup_fork_time(event["Fork"])
                xpos = Timeline.calculate_x_position(self.start_time, event['Time'])

                if event['Order'] == 1:
                    next = self.feature_type_matrix[i + 1]
                    while event['Fork'] == next['Fork'] \
                        and event['Order'] < next['Order']:
                        events.append(next)
                        i += 1
                        next = self.feature_type_matrix[i + 1]

                    self._draw_featuretype_event(events, xpos)

            except CommandTooSoonException:
                print "Command Too Soon!"
                pass
            except IndexError:
                pass

    def _draw_featuretype_event(self, events, xpos):
        line = ForkFeatureType(self.svg_timeline, events, self.start_time)
        line.draw()

    def _draw_patches(self):
        lane = 0
        for fork_event in self.feature_type_matrix:
            patch_bar = PatchBar(self.svg_timeline, fork_event, lane % Timeline.PATCH_LANES, self.start_time, Timeline.CHART_HEIGHT)
            patch_bar.draw()
            lane += 1


    def _event_at_session_start(self, event):
        ev_start_at_session = event
        ev_start_at_session['Time'] = self.start_time
        return ev_start_at_session

    def _draw_methods(self):
        start_event = None
        
        for event in self.commands:
            if 'error' not in event:
                if self.before_start(event):
                    start_event = MethodBar(self.svg_timeline, self._event_at_session_start(event), self.start_time, Timeline.CHART_AND_PATCH_HEIGHT, self.visited_methods)
                else:
                    if not start_event:
                        start_event = MethodBar(self.svg_timeline, event, self.start_time, Timeline.CHART_AND_PATCH_HEIGHT, self.visited_methods)

                    if not start_event.same_method(event):
                        self.visited_methods = start_event.draw(event)
                        start_event = MethodBar(self.svg_timeline, event, self.start_time, Timeline.CHART_AND_PATCH_HEIGHT, self.visited_methods)

        # Draw the final event
        if 'error' not in event:
            self.visited_methods = start_event.draw(event)

    def _lookup_fork_time(self, fork_index):
        try:
            return self.coded_events[fork_index]['Time']
        except IndexError, e:
            print len(self.coded_events)
            print fork_index
            raise e

    def draw(self):
        """Converts the textual commands_list to a graphical timeline view in SVG."""
        self._draw_coded_events()
        #self._draw_command_events()
        self._draw_featuretype_events()
        self._draw_patches()
        self._draw_methods()
        self._draw_timeline_decorations("FeatureType")

        self.svg_timeline.add_stylesheet("timeline_information_forks.css", title="ift_forks")
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
    participants = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] # P11 has incomplete commands data
    #participants = [7]

    for p in participants:
        print "Participant %d" % p
        t = Timeline(p, DataLoader.load_codedevents(p), DataLoader.load_commands(p), DataLoader.load_feature_types(p))
        t.draw()