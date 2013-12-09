#!/usr/bin/env python

import sqlalchemy as sa
import os, sys, re
import datetime
import os.path as op
import shutil
import optparse
from lxml import etree

_dry = True
_verbose = 0

def relabel_session_files(oldlabel, newlabel, olddir, newdir):
	v = _verbose >= 1; vv = _verbose >= 2
	if v:
		print ""
		print "Relabel '%s' -> '%s'" % (oldlabel, newlabel)
		print "Move '%s' -> '%s'" % (olddir, newdir)
	
	oldxml = olddir + '.xml'
	newxml = newdir + '.xml'
	
	# source must exist and destination must not
	if not (op.isfile(oldxml) and op.isdir(olddir)):
		raise IOError(-1, 'Missing directory or xml file in: ' + str(olddir))
	if op.exists(newdir) or op.exists(newxml):
		raise IOError(-1, 'New dir or xml exists: ' + str(newdir))
	
	# parse xml and find the pieces to replace
	sessxml = etree.parse(oldxml)
	sessnode = sessxml.getroot()
	
	label = sessnode.get('label')
	if not label == oldlabel:
		raise IOError('label (%s) and label in file (%s) mismatch.' % (oldlabel, label))
	
	pathnode = sessnode.xpath('//xnat:prearchivePath', namespaces=sessnode.nsmap)
	if not pathnode:
		raise IOError(-1, 'No xnat:prearchivePath in ' + oldxml)
	elif len(pathnode) > 1:
		print >>sys.stderr, "WARN: Multiple prearchivePath elements in", sessxml
	pathnode = pathnode[0]
	if pathnode.text != olddir:
		raise IOError(-1, 'xnat:prearchivePath (%s) does not match sessdir (%s)' % (path, olddir))
	
	# replace them
	sessnode.set('label', newlabel)
	pathnode.text = newdir
	
	if _dry:
		print "Would write to", newxml
		if vv: print etree.tostring(sessxml, encoding='UTF-8')
	else:
		with open(newxml, 'wb') as handle:
			handle.write(etree.tostring(sessxml, encoding='UTF-8'))
		shutil.move(olddir, newdir)
		os.unlink(oldxml)
def _parser():
	p = optparse.OptionParser('%prog [OPTIONS] PROJECT')

	p.add_option('--dry', dest='dry', action='store_true', default=False,
		help='Dry run only, do not perform any actions.')

	p.add_option('-v', '--verbose', dest='verbose', action='count', default=0,
		help='Increase verbosity, may be given more than once.')

	return p

def main(args=None):
	if args is None: args = sys.argv[1:]

	parser = _parser()
	opts, args = parser.parse_args(args)
	
	project = 'TCIA_GBM_PUB'
	if args:
		project = args[0]

	global _verbose; _verbose=opts.verbose
	global _dry; _dry=opts.dry

	v = _verbose >= 1; vv = _verbose >= 2
	
	engine = sa.create_engine('postgresql://xnat:xnat@localhost/xnat', echo=vv)
	conn = engine.connect()
	
	meta = sa.MetaData(bind=conn)
	pa = prearchive = sa.Table('prearchive', meta, schema='xdat_search', autoload=True)
	
	cols = pa.c.keys()
	select = pa.select().where(pa.c.project == project)
	for row in select.execute():
		if vv: print >>sys.stderr, '\nROW:', row
		if None in (row.scan_date, row.scan_time):
			print >>sys.stderr, \
				"WARN: Skipping due to missing scan_date (%r) or scan_time (%r) " \
				"for name / folder: %s / %s" \
				% (row.scan_date, row.scan_time, row.name, row.foldername)
			continue
		scan_date = row.scan_date.date().isoformat()
		scan_time = scan_date + '_' + row.scan_time.replace(':', '-')
		
		# already processed?
		if row.name.endswith(scan_time):
			if v: print >>sys.stderr, "Already done:", row.name
			continue
		
		old_name = row.name
		new_name = row.name + '_' + scan_time
		sessdir = row.url
		newdir = sessdir + '_' + scan_time
		
		relabel_session_files(old_name, new_name, sessdir, newdir)
		
		# update with new name and directory path
		new_vals = {
			pa.c.name: new_name,
			pa.c.url: newdir,
			pa.c.foldername: op.basename(newdir)
		}
		where = sa.sql.and_(*[ pa.c[col] == row[col] for col in cols ])
		update = pa.update().values(new_vals).where(where)
		
		if _dry:
			print "Would update database."
			if v:
				compiled = update.compile()
				print "DB update:"
				print compiled
				print "DB params:"
				print compiled.params
		else:
			update.execute()

	return locals()

	
if __name__ == '__main__':
	vars = main()
