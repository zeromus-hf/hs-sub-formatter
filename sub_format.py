#! /usr/bin/env python

import sys
import codecs
import argparse
import pickle
import re

from collections import OrderedDict

ap = argparse.ArgumentParser(description='Parses subtitle files with formatting comments and outputs formatted equivalent.')

ap.add_argument('input_file', type=unicode, help='Input file to process.')
ap.add_argument('output_file', type=unicode, help='Output filename. See other options on how to format output.')

ap.add_argument('--output-pickle', action='store_true', help="Output subtitle as pickle string, if not then the ouput is a subtitle file that is a properly formatted equivalent")
ap.add_argument('--input-pickle', action='store_true', help="Read input as a pickle string, if not then input is a subtitle file")
ap.add_argument('--dry-run', '-r', action='store_true', help='Do not output any file')
ap.add_argument('--debug', action='store_true', help='dump trace when erroring')

class subtitle(object):
	def __init__(self, sub_id, text, line, comment_line):
			self.sub_id  = sub_id
			self.text    = text
			self.comment = None
			self.line    = line
			self.comment_line = comment_line


	def __str__(self):
		return '{} (line {})'.format(self.sub_id, self.line)

def parse_subs(fp):
	# Store all our subtitle entries here
	sub_entries = {}

	# Divide entries in sections by keeping track of current section
	section_ids  = []
	sections     = []
	section_name = ''

	# Define all our regex patterns
	RE_COMMENT_SUB       = r'^\s*//\s*#sub\s*"([^"]+?)"\s*(.+)\s*$'
	RE_SUB               = r'^\s*#sub\s*"([^"]+?)"\s*(.+)\s*$'
	RE_COMMENT_BORDER_1  = r'^\s*/{3,}\s*$'
	RE_COMMENT_BORDER_2  = r'^\s*//\s*-+\s*$'
	RE_COMMENT_OTHER     = r'^//\s*(.+)\s*$'

	# Order to check patterns
	patterns = (RE_COMMENT_SUB, RE_SUB, RE_COMMENT_BORDER_1, RE_COMMENT_BORDER_2, RE_COMMENT_OTHER)

	# Keep track of last subtitle entry
	entry = None

	last_comment_type = None

	ambiguous_entries = OrderedDict()

	def readline_gen():
		first_line = fp.readline()

		if first_line[:1] == u'\ufeff':
			first_line = first_line[1:]
		
		if first_line:
			yield first_line.rstrip('\r\n')

			while True:
				line = fp.readline()
				if line:
					yield line.rstrip('\r\n')
				else:
					break

	pattern = None
	entry   = None

	error   = False

	for line_no, line in enumerate(readline_gen(), 1):
		matches = None

		# Skip blank lines
		if not line.strip():
			continue

		last_pattern = pattern

		# Iterate through patterns
		for pattern in patterns:
			matches = re.search(pattern, line)

			if matches is not None:
				matches = matches.groups()
				break

		# See if this is just a continuation of the last entry
		if matches is None:
			if last_pattern == RE_SUB:
				entry.text = entry.text.rstrip() + ' ' + line
				pattern    = last_pattern

			else:
				# Error if no pattern
				print u'Unknown line {} at line {}'.format(line, line_no)
				error = True

			continue

		is_border = pattern in (RE_COMMENT_BORDER_1, RE_COMMENT_BORDER_2)

		if not is_border:
			last_comment_type = None

		# If matches a subtitle pattern
		if pattern in (RE_COMMENT_SUB, RE_SUB):
			is_comment = pattern == RE_COMMENT_SUB

			id, text = matches

			# Try to find an existing entry
			entry      = sub_entries.get(id)

			# Fill comment field
			if is_comment:

				# No existing entry
				if entry is None:
					sub_entries[id] = entry = subtitle(id, None, None, line_no)
					section_ids.append(id)

				# Fill existing comment
				if entry.comment is None:
					entry.comment      = text
					entry.comment_line = line_no

				# Comment already exists
				elif entry.comment != text:

					# Keep track of duplicates to ask later
					print u'error: existing sub {} with comment "{}" on line {} has overwriting comment "{}" at line {}' \
							.format(entry, entry.comment, entry.comment_line, text, line_no)

					amb = ambiguous_entries.get(id)

					if amb is None:
						ambiguous_entries[id] = amb = {
							'texts'   : [],
							'comments': [ entry.comment, text ]
						}

					amb['comments'].append(text)

				else:
					# Exact duplicate comments should be okay
					print u'warning: sub {} with comment "{}" on line {} has duplicate comment at line {}' \
							.format(entry, entry.comment, entry.comment_line, line_no)
			else:
				
				if entry is None:
					sub_entries[id] = entry = subtitle(id, text, line_no, None)
					section_ids.append(id)

				elif entry.text is None:
					entry.text = text
					entry.line = line_no

				else:
					print u'sub {} with text "{}" has duplicate entry "{}" at line {}'.format(entry, entry.text, text, line_no)

					amb = ambiguous_entries.get(id)

					if amb is None:
						ambiguous_entries[id] = amb = {
							'texts'    : [ entry.text, text ],
							'comments' : []
						}

					amb['texts'].append(text)

		elif pattern in (RE_COMMENT_BORDER_1, RE_COMMENT_BORDER_2): 
			last_comment_type = pattern

		elif pattern == RE_COMMENT_OTHER:

			if section_ids:
				sections.append((section_name, tuple(section_ids)))
				section_ids = []

			elif sections:
				raise Exception(u'Unused section name {}'.format(section_name))

			section_name, = matches
		else:
			raise Exception(u'Unknown pattern {}'.format(pattern))

	if section_ids:
		sections.append((section_name, tuple(section_ids)))
		section_ids = []


	def choose(question, start, end):
		choice = raw_input('{} [{}-{}]'.format(question, start, end))

		if not re.match(r'\d+', choice):
			return None

		choice = int(choice)

		if start <= choice <= end:
			return choice

		return None

	if error:
		raise Exception('Please resolve the unknown lines')
			

	# Ask user to resolve ambiguities
	if ambiguous_entries:
		for id, info in ambiguous_entries.iteritems():
			entry = sub_entries[id]

			while info['texts'] or info['comments']:
				print u'Ambiguous subs and their comments for:'
			
				if entry.comment:
					print u'\t//#sub "{}" {}'.format(id, entry.comment)

				if entry.text:
					print u'\t#sub "{}" {}'.format(id, entry.text)

				print

				if info['comments']:
					print '\tAmbiguous comments:'

					for i, comment in enumerate(info['comments'], 1):
						print u'\t{}) {}'.format(i, comment)

					print

				if info['texts']:
					print '\tAmbiguous texts:'

					for i, text in enumerate(info['texts'], 1):
						print u'\t{}) {}'.format(i, text)

					print

				if info['comments']:
					choice = choose('Choose comment to resolve {}'.format(id), 1, len(info['comments']))

					if choice is not None:
						entry.comment = info['comments'][choice - 1]
						info['comments'] = []
					else:
						raise Exception('Canceled')
				elif info['texts']:
					choice = choose('Choose text to resolve {}'.format(id), 1, len(info['texts']))

					if choice is not None:
						sub.text = info['texts'][choice - 1]
						info['texts'] = []
					else:
						raise Exception('Canceled')

				if not info['comments'] and not info['texts']:
					break

	with_comments = sum(map(lambda x: 1 if x.comment else 0, sub_entries.values()))
	no_text       = sum(map(lambda x: 1 if x.text is None else 0, sub_entries.values()))
	no_comments   = len(sub_entries) - with_comments

	print 'Total subs:', len(sub_entries)
	print 'w/ comments:', with_comments
	print 'w/o comments:', no_comments
	print 'comments w/o subs:', no_text
	print 'Sections:', len(sections)

	data = {}

	for name, ids in sections:
		subs = data.get(name)

		if data.get(name) is None:
			data[name] = subs = {}

		for id in ids:
			subs[id] = sub_entries[id]

	return data



def format_subs(data, fp):
	def enum_dict(d):
		keys = d.keys()

		keys.sort()

		for key in keys:
			yield key, d[key]

	for section, entries in enum_dict(data):
		if section:
			fp.write(u'// -----------------------------------------------\n')
			fp.write(u'// {}\n'.format(section))
			fp.write(u'// -----------------------------------------------\n\n')

		for sub_id, entry in enum_dict(entries):
			if entry.comment:
				fp.write(u'//#sub "{}" {}\n'.format(sub_id, entry.comment))

			if entry.text:
				fp.write(u'#sub "{}" {}\n'.format(sub_id, entry.text))

			fp.write('\n')


def main():
	args = ap.parse_args()

	if args.dry_run:
		print 'Dry-run specified.'

	data = None

	try:
		if args.input_pickle:
			with open(args.input_file, 'rb') as fp:
				data = pickle.load(fp)
				fp.close()

		else:

			with codecs.open(args.input_file, mode='rb', encoding='utf-8') as fp:
				data = parse_subs(fp)
				fp.close()

	except Exception as e:
		print u'error: {}'.format(e)

		if args.debug:
			raise

		return 1

	if not args.dry_run:
		if args.output_pickle:
			with open(args.output_file, 'wb') as fp:
				pickle.dump(fp)
				fp.close()
		else:

			with codecs.open(args.output_file, mode='wb', encoding='utf-8') as fp:
				text = format_subs(data, fp)
				fp.close()

	return 0

if __name__ == '__main__':
	exit(main())

