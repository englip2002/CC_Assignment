# Cloud Computing Assignment

## Functional Requirement
1. A web page with students database contains information, such
as each student’s personal information, progress reports etc.
Refer: http://i2hub.tarc.edu.my:8846
2. User-generated media files e.g. progress reports are stored in
Amazon Simple Storage Service (Amazon S3), a highly available
and durable storage service.
3. Amazon RDS provides a managed, highly available SQL database
for storing and querying data.
4. Cloud Watch can be used to monitor resources and applications
in real time. Cloud watch supports multiple types of actions such
as executing an auto-scaling policy.
5. Make your own unique portfolio tab.

## AWS Service Requirement
1. Amazon Elastic Compute Cloud (EC2)
AWS EC2 is an Infrastructure as a Service by AWS, which gives you a
server with the desired OS, processor, and RAM. You can do anything on
this OS, from installing software to hosting a website. Here, you have
full control over the OS. The system will host at EC2.

Requirements: Amazon Linux 2023

3. Amazon Simple Storage Service (Amazon S3)
The start-up can leverage Amazon S3 to stores application static assets
including certain employee data such as profile images.

Requirements: &lt;your full name as bucket name&gt; e.g. lowchoonkeat-
bucket

4. Amazon Relational Database Service (Amazon RDS)
Amazon RDS is a managed SQL database service. Amazon RDS supports
an array of database engines to store and organise data and helps with
database management tasks, such as Migration, backup, recovery and
patching.

Requirements: MariaDB

5. Amazon CloudWatch
Amazon CloudWatch can be used to monitor AWS resources and
applications real-time for e.g. EC2 and RDS. Amazon CloudWatch can
aggregate data across the availability zone within a region.

6. Amazon Auto Scaling
AWS Auto Scaling is a service that automatically monitors and adjusts
compute resources to maintain performance for applications. As
demand spikes, the AWS Auto Scaling service can automatically scale
those resources, and, as demand drops, scale them back down.

Requirements: Desired: 3, Minimum 2, Maximum 4, 
Scaling Policy: Scale up when CPU > 60%

7. Elastic Load Balancing
Elastic Load Balancing automatically distributes your incoming
application traffic across all the EC2 instances that you are running.

Requirements: Availability Zone, us-east 1a, us-east 1b, us-east 1c 

*Not allow to use elastic beanstalk in this assignment.

## Example From Lecturer

Either add "sudo" before all commands or use "sudo su" first  
Amazon Linux 2023  

!/bin/bash  
dnf install git -y  
git clone https://github.com/lowchoonkeat/aws-live.git  
cd aws-live  
dnf install python-pip -y  
pip3 install flask pymysql boto3  
python3 EmpApp.py  
