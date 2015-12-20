from fabric.api import env, run, sudo
from fabric.operations import get, put
from fabric.context_managers import cd, settings

import boto3
import argparse
import sys
import os
import uuid
import requests
import contextlib

version = '0.1'
instance_type = 't2.nano'
ami = 'ami-5189a661'    # ubuntu trusty
name_tag = 'aws-grab-{}'

ec2 = boto3.resource('ec2')
client = boto3.client('ec2')

@contextlib.contextmanager
def capture():
    """ capture stdout and stderr for later logging """
    import sys
    from cStringIO import StringIO
    oldout,olderr = sys.stdout, sys.stderr
    try:
        out=[StringIO(), StringIO()]
        sys.stdout,sys.stderr = out
        yield out
    finally:
        sys.stdout,sys.stderr = oldout, olderr
        out[0] = out[0].getvalue()
        out[1] = out[1].getvalue()

def print_captured_output(output):
    for line in output[0].split('\n'):
        if line!= '':
            print 'stdout: {}'.format(line)
    for line in output[1].split('\n'):
        if line!= '':
            print 'stderr: {}'.format(line)

def launch(keyname):
    nics = [{
        'DeviceIndex': 0,
        'AssociatePublicIpAddress': True
    }]
    instance = ec2.create_instances(
        ImageId=ami, 
        InstanceType=instance_type, 
        KeyName=keyname, 
        MinCount=1, 
        MaxCount=1)

    instance = instance.pop()
    instance.wait_until_running()

    print 'Instance running, waiting for SSH access ...'

    waiter = client.get_waiter('instance_status_ok')
    try:
        waiter.wait(InstanceIds=[instance.instance_id])
    except Exception as e:
        print 'Instance failed to report status ok, terminating instance!'
        instance.terminate()
        return

    instance.load()
    return instance

def install_aria():
    sudo('apt-get update && apt-get -y install aria2')

def execute_download(urlfile):
    run('mkdir ~/download')
    put(urlfile_path, '~/files')
    with settings(warn_only=True):
        with cd('~/download/'):
            run('aria2c -i ~/files')
    run('tar czf ~/download.tgz ~/download/')
    get('~/download.tgz', './download.tgz')
    run('rm -rf ~/download files download.tgz')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Boot an aws instance and have it download a list of files for you.')
    parser.add_argument('-k', '--keypair', action='store', required=True)
    parser.add_argument('-u', '--urlfile', action='store', required=True)

    args = parser.parse_args()

    urlfile_path = os.path.abspath(args.urlfile)

    if not os.path.isfile(urlfile_path):
        print 'Cannot read url list file {}'.format(args.urlfile)
        sys.exit()

    print 'Launching instance ...'
    instance = launch(args.keypair)

    env.host_string = instance.public_dns_name
    env.user = 'ubuntu'
    install_aria()
    execute_download(urlfile_path)
    print 'Download complete, terminating instance.'
    instance.terminate()
