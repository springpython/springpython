#!/usr/bin/env python

#  This software code is made available "AS IS" without warranties of any
#  kind.  You may copy, display, modify and redistribute the software
#  code either by itself or as incorporated into your code; provided that
#  you do not remove any proprietary notices.  Your use of this software
#  code is at your own risk and you waive any claim against Amazon
#  Digital Services, Inc. or its affiliates with respect to your use of
#  this software code. (c) 2006-2007 Amazon Digital Services, Inc. or its
#  affiliates.

import S3
import time
import sys

AWS_ACCESS_KEY_ID = '<INSERT YOUR AWS ACCESS KEY ID HERE>'
AWS_SECRET_ACCESS_KEY = '<INSERT YOUR AWS SECRET ACCESS KEY HERE>'
# remove these next two lines when you've updated your credentials.
#print "update s3-driver.py with your AWS credentials"
#sys.exit();

# convert the bucket to lowercase for vanity domains
# the bucket name must be lowercase since DNS is case-insensitive
BUCKET_NAME = AWS_ACCESS_KEY_ID.lower() + '-test-bucket'
KEY_NAME = 'test-key'

conn = S3.AWSAuthConnection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
generator = S3.QueryStringAuthGenerator(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)


# Check if the bucket exists.  The high availability engineering of 
# Amazon S3 is focused on get, put, list, and delete operations. 
# Because bucket operations work against a centralized, global
# resource space, it is not appropriate to make bucket create or
# delete calls on the high availability code path of your application.
# It is better to create or delete buckets in a separate initialization
# or setup routine that you run less often.
if (conn.check_bucket_exists(BUCKET_NAME).status == 200):
  print '----- bucket already exists! -----'
else:
  print '----- creating bucket -----'
  print conn.create_located_bucket(BUCKET_NAME, S3.Location.DEFAULT).message
  # to create an EU bucket
  #print conn.create_located_bucket(BUCKET_NAME, S3.Location.EU).message

print '----- bucket location -----'
print conn.get_bucket_location(BUCKET_NAME).location

print '----- listing bucket -----'
print map(lambda x: x.key, conn.list_bucket(BUCKET_NAME).entries)

print '----- putting object (with content type) -----'
print conn.put(
        BUCKET_NAME,
        KEY_NAME,
        S3.S3Object('this is a test'),
        { 'Content-Type': 'text/plain' }).message

print '----- listing bucket -----'
print map(lambda x: x.key, conn.list_bucket(BUCKET_NAME).entries)

print '----- getting object -----'
print conn.get(BUCKET_NAME, KEY_NAME).object.data

print '----- query string auth example -----'
print "\nTry this url out in your browser (it will only be valid for 60 seconds).\n"
generator.set_expires_in(60);
url = generator.get(BUCKET_NAME, KEY_NAME)
print url
print '\npress enter> ',
sys.stdin.readline()

print "\nNow try just the url without the query string arguments.  it should fail.\n"
print generator.make_bare_url(BUCKET_NAME, KEY_NAME)
print '\npress enter> ',
sys.stdin.readline()


print '----- putting object with metadata and public read acl -----'
print conn.put(
    BUCKET_NAME,
    KEY_NAME + '-public',
    S3.S3Object('this is a publicly readable test'),
    { 'x-amz-acl': 'public-read' , 'Content-Type': 'text/plain' }
).message

print '----- anonymous read test ----'
print "\nYou should be able to try this in your browser\n"
public_key = KEY_NAME + '-public'
print generator.make_bare_url(BUCKET_NAME, public_key)
print "\npress enter> ",
sys.stdin.readline()

print "----- getting object's acl -----"
print conn.get_acl(BUCKET_NAME, KEY_NAME).object.data

print "\n----- path style url example -----";
print "Non-location-constrained buckets can also be specified as part of the url path.  (This was the original url style supported by S3.)\n";
print "Try this url out in your browser (it will only be valid for 60 seconds).\n"
generator.calling_format = S3.CallingFormat.PATH
url = generator.get(BUCKET_NAME, KEY_NAME)
print url
print "\npress enter> ",
sys.stdin.readline()

print '----- deleting objects -----'
print conn.delete(BUCKET_NAME, KEY_NAME).message
print conn.delete(BUCKET_NAME, KEY_NAME + '-public').message

print '----- listing bucket -----'
print map(lambda x: x.key, conn.list_bucket(BUCKET_NAME).entries)

print '----- listing all my buckets -----'
print map(lambda x: x.name, conn.list_all_my_buckets().entries)

print '----- deleting bucket ------'
print conn.delete_bucket(BUCKET_NAME).message


