import pandas
import boto3
import os
import paramiko



import argparse

ami_list = {'ubuntu-22.04' : 'ami-0989fb15ce71ba39e'}

def create_key_pair(args):
    ec2_client = boto3.client("ec2", region_name=args.region_name)
    key_pair = ec2_client.create_key_pair(KeyName=args.key_name)
    private_key = key_pair["KeyMaterial"]
    
    with os.fdopen(os.open( args.filename, os.O_WRONLY | os.O_CREAT, 0o400), "w+") as handle:
        handle.write(private_key)
        print( f'saved as {args.filename}')



def create_inst(args):
    ec2_client = boto3.client("ec2", region_name=args.region_name)
    try:
        instances = ec2_client.run_instances(
            ImageId=args.ami_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=args.i_type,
            SecurityGroupIds=['sg-09f854c293daac9f4'],
            KeyName=args.key_name
        )
    except Exception as e:
        print( f"There is an error: {e}")
        return
    
    print(instances["Instances"][0]["InstanceId"])

def get_public_ip(instance_id, region_name='eu-north-1'):
    ec2_client = boto3.client("ec2", region_name=region_name)
    reservations = ec2_client.describe_instances(InstanceIds=[instance_id]).get("Reservations")
    
    for reservation in reservations:
        for instance in reservation['Instances']:
            return(instance.get("PublicIpAddress"))



def get_running_instances(args):
    ec2_client = boto3.client("ec2", region_name=args.region_name)
    reservations = ec2_client.describe_instances(Filters=[
    {
        "Name": "instance-state-name",
        "Values": ["running"],
    },
    {
        "Name": "instance-type",
        "Values": ["t3.micro"]
    }]).get("Reservations")
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            public_ip = instance["PublicIpAddress"]
            private_ip = instance["PrivateIpAddress"]
            print(f"{instance_id} : {instance_type}\tIP pub:{public_ip}\tIP priv:{private_ip}")

def stop_instance(args):
    ec2_client = boto3.client("ec2", region_name=args.region_name)
    response = ec2_client.stop_instances(InstanceIds=[args.instance_id])
    print(response)

def execute(args):
    key = paramiko.RSAKey.from_private_key_file(args.key)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:

        client.connect(hostname=get_public_ip(args.instance_id, args.region_name), username="ubuntu", pkey=key)

        stdin, stdout, stderr = client.exec_command(args.command)
        print('Out:\n\t', stdout.read())
        print('Err/Warn:\n\t', stderr.read())

        client.close()

    except Exception as e:
        print(e)

def terminate_instance(args):
    ec2_client = boto3.client("ec2", region_name=args.region_name)
    response = ec2_client.terminate_instances(InstanceIds=[args.instance_id])
    print(response)

##################################################################################### BUCKETS

def create_bucket(args):
    s3_client = boto3.client('s3')
    location = {'LocationConstraint': args.region_name}
    try:
        response = s3_client.create_bucket(Bucket=args.bucket_name, CreateBucketConfiguration=location)
        print(response)
    except Exception as e:
        print( f"There is an error: {e}")
    


def list_buckets(args):
    s3_client = boto3.client('s3')
    response = s3_client.list_buckets()
    print('Existing buckets:')
    for bucket in response['Buckets']:
        print(f'{bucket["Name"]}')

def upload(args):
    s3_client = boto3.client('s3')
    response = s3_client.upload_file(Filename=args.filename, Bucket=args.bucket_name, Key=args.rfilename)
    print(response)

def list_bucket(args):
    s3_client = boto3.resource('s3')
    my_bucket = s3_client.Bucket(args.bucket_name)
    for file in my_bucket.objects.all():
        print(file.key)


def read_from_bucket(args):
    s3_client = boto3.client('s3')
    try:
        obj = s3_client.get_object( Bucket = args.bucket_name, Key = args.filename)
    except Exception as e:
        print( f'There is a problem with reading file: {e}')
        return 
    data = pandas.read_csv(obj['Body'])
    print( 'Printing the data frame...')
    print(data.head())


def delete_from_bucket(args):

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(args.bucket_name)
    if args.rcrsv:
        for obj in bucket.objects.filter(Prefix=args.filename + '/'):
            s3_client.Object(bucket.name,obj.key).delete()
    else:
        s3_client.Object(args.bucket_name, args.filename).delete()

    print("[+] DONE")

def destroy_bucket(args):
    s3_client = boto3.client('s3')
    
    objects = s3_client.list_objects_v2(Bucket=args.bucket_name)
    fileCount = objects['KeyCount']

    if fileCount == 0:
        s3_client.delete_bucket(Bucket=args.bucket_name)
        print("{} has been deleted successfully !!!".format(args.bucket_name))
    else:
        print("{} is not empty, {} objects present".format(args.bucket_name,fileCount))
        print("Please make sure S3 bucket is empty before deleting it !!!")


#############

def list_inst_buck(args):
    if args.i_b == 'i':
        get_running_instances(args)
    else:
        list_buckets(args)

###################################################################33

parser = argparse.ArgumentParser(prog='DigiJED', description='operating cloud infrastructure')

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(title='subcommands', description='valid subcommands', help='')


create_key_parser = subparsers.add_parser('create_key_pair', help='create key pair')
create_key_parser.add_argument('-f', dest='filename', default='./keys/key.pem', help='filename of created key pair')
create_key_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
create_key_parser.add_argument('-k', dest='key_name', default='"ec2-key-pair"', help='keypair name')
create_key_parser.set_defaults(func=create_key_pair)

create_ins_parser = subparsers.add_parser('create_instance', help='create instance')
create_ins_parser.add_argument('--ami_id', dest='ami_id', default=ami_list['ubuntu-22.04'], help='amd id of machine (default is ubuntu 22.04, x86_64, t2.micro)')
create_ins_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
create_ins_parser.add_argument('-k', dest='key_name', default='ec2-key-pair', help='keypair name')
create_ins_parser.add_argument('-t', dest='i_type', default='t3.micro', help='instance type')
create_ins_parser.set_defaults(func=create_inst)

# get_ins_ip_parser = subparsers.add_parser('get_public_ip', help='get public ip of instance')
# get_ins_ip_parser.add_argument('--id', dest='instance_id', help='instance id', required=True)
# get_ins_ip_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
# get_ins_ip_parser.set_defaults(func=get_public_ip)

execute_parser = subparsers.add_parser('exec', help='execute command on instance')
execute_parser.add_argument('--id', dest='instance_id', help='instance id', required=True)
execute_parser.add_argument('-c', dest='command', help='command', required=True)
execute_parser.add_argument('-k', dest='key', help='access key file', required=True)
execute_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
execute_parser.set_defaults(func=execute)


list_ins_b_parser = subparsers.add_parser('list', help='list running instance in region or excisting buckets')
list_ins_b_parser.add_argument('-l', dest="i_b", choices=['i', 'b'], default='i', help='list instances or bucket`s names')
list_ins_b_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
list_ins_b_parser.set_defaults(func=list_inst_buck)


stop_instance_parser = subparsers.add_parser('stop_instance', help='stop instance with id')
stop_instance_parser.add_argument('--id', dest='instance_id', help='instance id', required=True)
stop_instance_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
stop_instance_parser.set_defaults(func=stop_instance)

terminate_instance_parser = subparsers.add_parser('terminate_instance', help='terminate instance with id')
terminate_instance_parser.add_argument('--id', dest='instance_id', help='instance id', required=True)
terminate_instance_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
terminate_instance_parser.set_defaults(func=terminate_instance)


create_bkt_parser = subparsers.add_parser('create_bucket', help='create bucket')
create_bkt_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
create_bkt_parser.add_argument('-r', dest='region_name', default='eu-north-1', help='region name')
create_bkt_parser.set_defaults(func=create_bucket)

upload_bkt_parser = subparsers.add_parser('upload', help='upload file to bucket')
upload_bkt_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
upload_bkt_parser.add_argument('-f', dest='filename', help='local filename', required=True)
upload_bkt_parser.add_argument('-r', dest='rfilename', help='remote filename', required=True)
upload_bkt_parser.set_defaults(func=upload)

list_bkt_parser = subparsers.add_parser('list_bucket', help='list bucket`s content')
list_bkt_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
list_bkt_parser.set_defaults(func=list_bucket)

read_item_parser = subparsers.add_parser('read_bucket', help='read data from bucket')
read_item_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
read_item_parser.add_argument('-f', dest='filename', help='filename', required=True)
read_item_parser.set_defaults(func=read_from_bucket)

detele_item_parser = subparsers.add_parser('delete_item', help='delete file from bucket')
detele_item_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
detele_item_parser.add_argument('-f', dest='filename', help='filename', required=True)
detele_item_parser.add_argument('-r', dest='rcrsv', action="count")
detele_item_parser.set_defaults(func=delete_from_bucket)

destroy_bkt_parser = subparsers.add_parser('destroy_bucket', help='destroy bucket')
destroy_bkt_parser.add_argument('-n', dest='bucket_name', help='bucket name', required=True)
destroy_bkt_parser.set_defaults(func=destroy_bucket)


if __name__ == '__main__':
    args = parser.parse_args()
    if not vars(args):
        parser.print_usage()
    else:
        args.func(args)
