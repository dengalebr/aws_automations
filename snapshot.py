#!/usr/bin/python
import boto
from datetime import *
import sys
import cgi
import cgitb; cgitb.enable() # Optional; for debugging only

print "Content-Type: text/html"
print ""

arguments = cgi.FieldStorage()
if not 'instance' in arguments:
	print "Please provide instance parameter"
	sys.exit(0)

keyword = arguments['instance'].value
boto.connect_ec2()
conn = boto.ec2.connect_to_region('ap-southeast-1')
reservations = conn.get_all_instances()
instances = []
for res in reservations:
	instances += res.instances

instances = filter((lambda x: 'Name' in x.tags and 'CFX-' in x.tags['Name']), instances)
instances = filter((lambda x: keyword in x.tags['Name']), instances)
if not instances:
        print "No instance matches name '%s'" % keyword
        sys.exit(0)

instances = map (lambda x: x.id, instances)
volumes = conn.get_all_volumes()
volumes = filter((lambda x: x.attach_data.instance_id in instances), volumes)
print "creating snapshot of instances with names containing '%s'</br>" % keyword
for v in volumes:
	print v.id + '</br>'
	conn.create_snapshot(v.id, "Ad-hoc snapshot")

