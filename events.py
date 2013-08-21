#!/usr/bin/env python

import os
from collections import OrderedDict
from datetime import time, datetime, date

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
			'EclipseCommand',
			'Find',
			'Replace',
			'DocOffset',
			'LineOfCode']
		line_data = line.rstrip('\n').split('\t', len(fields))
		self.record = OrderedDict(zip(fields, line_data))

		try:
			self.record.pop('Participant', None)
			self.record['CommandID'] = int(self.record['CommandID'])
			self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])
			self.record['DocOffset'] = int(self.record['DocOffset'])
			self.record['LineOfCode'] = self._strip_quotes(self.record['LineOfCode'])
		except ValueError, e:
			print "Exception at index %d: %s" % (self.record['CommandID'], str(e))

	def _strip_quotes(self, field):
		return field.rstrip('"').lstrip('"')

	def __len__(self):
		return len(self.record)

	def __getitem__(self, key):
		return self.record[key]

	def __setitem__(self, key, value):
		self.record[key] = value

	def header(self):
		return ('\t'.join(k for k in self.record.keys()))

	def __str__(self):
		return ('\t'.join(str(v) for v in self.record.values()))

	def tab(self):
		# Don't output the Line of Code. Also, strip today's date from the timestamp.
		r = self.record
		r['Time'] = "00:%s.%03d" % (str(r['Time'].strftime("%M:%S")), r['Time'].microsecond/1000)
		return ('\t'.join(str(v) for v in r.values()[0:-1]))

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

			try:
				self.record['Index'] = int(self.record['Index'])
				self.record['Time'] = VideoTime.convert_to_timestamp(self.record['Time'])

				try:
					self.record['Forks'] = int(self.record['Forks'])
				except (KeyError, ValueError), e:
					print "Exception at index %d, check if it's a missing fork? %s" % (self.record['Index'], str(e))
					self.record['Forks'] = 0

				self.record['Foraging'] = self._convert_yesno_to_boolean(self.record, 'Foraging')
				self.record['LearningDoing'] = self.record['LearningDoing'].upper()

				try:
					self.record['Retrospective fork']
				except KeyError:
					self.record['Retrospective fork'] = ''

			except (KeyError, IndexError), e:
				print "Error at index %d: %s" % (self.record['Index'], str(e))
				print self.record
				

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

	def tab(self):
		r = self.record
		r['Time'] = "00:%s.%03d" % (str(r['Time'].strftime("%M:%S")), r['Time'].microsecond/1000)
		return ('\t'.join(str(v) for v in r.values()))

class DataLoader:
	@staticmethod
	def load_commands(p):
		filename = DataLoader.commands(p)
		command_list = []
		with open(filename) as f:
			f.readline() # Read past header
			f.readline() # Read past the start timestamp

			for line in f:
				c = Command(line)
				command_list.append(c)
		return command_list

	@staticmethod
	def load_codedevents(p):
		filename = DataLoader.codedevents(p)
		codedevent_list = []
		with open(filename) as f:
			f.readline() # Read past the first header row
			f.readline() # Read past the second header row

			for line in f:
				ce = CodedEvent(line)
				if ce.valid:
					codedevent_list.append(ce)

		return codedevent_list

	@staticmethod
	def commands(pid):
		return os.path.join("data", "p%02d-commands.txt" % (pid))

	@staticmethod
	def codedevents(pid):
		return os.path.join("data", "p%02d-coded.txt" % (pid))
