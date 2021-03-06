#!/usr/bin/python -u
import boto.ec2, boto.vpc, time, sys, cgi

def chunk(msg=""):
	return "\r\n%X\r\n%s" % ( len( msg ) , msg )

def cgiPrint(s):
	sys.stdout.write( chunk( "%s\n" % s) )
	sys.stdout.flush()

def copyAmi(conn, connVpc, location, amiName):
        try:
                amiId = filter(lambda x: x.location == location, conn.get_all_images())[0].id
                subnetId = filter(lambda x: x.tags.get('Name')=='temp', connVpc.get_all_subnets())[0].id
                # create an instance using public AMI
                instanceId = conn.run_instances(amiId, instance_type="c3.8xlarge", subnet_id=subnetId).instances[0].id
                while conn.get_all_instances(instanceId)[0].instances[0].state == 'pending' :
                        cgiPrint('launching new instance %s of "%s" ...' % (instanceId, amiName))
                        time.sleep(5)
                if conn.get_all_instances(instanceId)[0].instances[0].state != 'running' :
                        cgiPrint('failed to launch instance')
                        return None

                # create AMI using the instance
                newAmiId = conn.create_image(instance_id=instanceId, name=amiName, no_reboot=True)
                while conn.get_image(newAmiId).state == 'pending' :
                        cgiPrint('creating new AMI %s ...' % newAmiId)
                        time.sleep(5)
                if conn.get_all_instances(instanceId)[0].instances[0].state != 'running' :
                        cgiPrint('failed to create AMI')
                        return None

                # make the AMI public
                cgiPrint('making new AMI %s public ...' % newAmiId)
                conn.modify_image_attribute(newAmiId, operation='add', groups='all')
                return newAmiId
        except Exception as e:
                cgiPrint(e.message)
                return None
        finally:
                ## terminate instance
                if 'instanceId' in locals():
                        cgiPrint("terminating instance %s" % instanceId)
                        conn.terminate_instances(instanceId)
                        cgiPrint('done')


sys.stdout.write("Transfer-Encoding: chunked\r\n")
sys.stdout.write("Content-Type: text/plain\r\n")

		
arguments = cgi.FieldStorage()
if 'amiId' in arguments and 'amiName' in arguments:
	amiId = arguments['amiId'].value.lower()
	amiName = arguments['amiId'].value.upper()
else:
        cgiPrint("Parameter amiId is required, which is the id of an AMI in Singapore region.")
        cgiPrint("Parameter amiName is required, which is the name of the new AMI.")
        cgiPrint("Example: http://utils.cloudselect.com/aws/copy-ami.py?amiId=ami-12345678&amiName=XXXXX")
        sys.exit(1)

try:
        regions = ['ap-northeast-1', 'ap-southeast-1', 'ap-southeast-2', 'eu-west-1', 'sa-east-1', 'us-east-1', 'us-west-1', 'us-west-2']
        conns = {}
        for r in regions:
                conns[r] = {
                        'ec2': boto.ec2.connect_to_region(r),
                        'vpc': boto.vpc.connect_to_region(r)
                }
        result = ''
        location = conns['ap-southeast-1']['ec2'].get_image(amiId).location
        cgiPrint('########## COPY AMI IN ap-southeast-1 ##########')
        newAmiId = copyAmi(conns['ap-southeast-1']['ec2'], conns['ap-southeast-1']['vpc'], location, amiName)
        result += '%s,%s,%s\n' % (amiName, 'ap-southeast-1', newAmiId)
        for r in regions:
                if r != 'ap-southeast-1' :
                        cgiPrint('########## COPY AMI IN %s ##########' % r)
                        newAmiId = copyAmi(conns[r]['ec2'], conns[r]['vpc'], location, amiName)
                        result += '%s,%s,%s\n' % (amiName, r, newAmiId)
        cgiPrint(result)

except Exception as e:
	cgiPrint(e.message)
	sys.exit(1)

