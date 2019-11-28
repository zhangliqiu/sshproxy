python3 main.py /Users/likeliekkas/Desktop/config.ini /Users/likeliekkas/Desktop/qizhang.rsa
from pack.SSHproxy import UNIX_SSHproxy
client = UNIX_SSHproxy('/Users/likeliekkas/Desktop/config.ini')
client.local_rsa_file='/Users/likeliekkas/Desktop/qizhang.rsa'
print(client.connect())
print(client.remote_rsa_file = client.check_remote_rsa())
sock_port = client.socks_port
rsa_file = client.remote_rsa_file
ssh_port = client.proxy_server_port
username = client.proxy_server_user
hostname = client.proxy_server_ip
