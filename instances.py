#!/usr/bin/python
import boto,cgi
from datetime import *

arguments = cgi.FieldStorage()
keyword = 'CS2-PRD' 
if 'keyword' in arguments:
	keyword = arguments['keyword'].value.upper()

boto.connect_ec2()
conn = boto.ec2.connect_to_region('ap-southeast-1')
reservations = conn.get_all_instances()
instances = []
for res in reservations:
        instances += res.instances
instances = filter(lambda x: keyword in x.tags.get('Name','').upper(), instances)
instances = sorted(instances, key=lambda x: x.tags.get('Name'))
print "Content-Type: text/html"
print ""

print """
<html><body>
<table border="1">
<tr><th>Instance name</th><th>Instance Type</th><th>Platform</th><th>Public IP</th><th>Private IP</th><th>State</th></tr>
"""

for i in instances:
	if i.state == 'running':
		state = '<font color="green">running</font>'
	else:
		state = '<font color="red">%s</font>' % i.state
	print "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (i.tags.get('Name'), i.instance_type, i.platform or 'linux', i.ip_address, i.private_ip_address, state)

print """ 
</table>
</body></html>
"""

