# aws-grab

Boots an EC2 instance and uses it to download a bunch of files.

---

# Usage:

`$ aws-grab.py --keypair <aws-keypair-name> --urlfile <list-of-urls>`

---

# Configuration:

You'll need to have your [aws credentials condfigured](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html), and ensure that the
SSH keypair you use is loaded into your ssh-agent.

# AWS Usage:

A t2.nano instance will be booted into your default VPC and security group which must be configured to allow you to connect via SSH. The list of files 
you specificy will be sent to the instance where it will be fed into [aria2](https://github.com/tatsuhiro-t/aria2). Once downloaded the files will be
packed into a tgz and transferred back to your local machine. The instance will be terminated upon download completion.
