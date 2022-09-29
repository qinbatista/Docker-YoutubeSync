import sys, os
import socket
import threading
from time import ctime
def main():
	new_ssh=[
		'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC4LfvwATHC4qVJ4zrkAM7DHHU5juXEP+kwhaW2naReGdQuv5ykveb5lPi+W02D/xwqUEFP1mwZtCTNj2gMk7yfY/Xj5DFvIaByuvui+fO4QQCxVtERg6n9WEVQv1fJsm6w62YeZgxtMhhMy7fhpjbiTBM8KaunA3Gxj3rmZ+BI5SUvGTftekYbNcUVagfHYD+FNj40bL5g2DRcDd0BA1Mc5Zio8dfJaosY/RsrdgMyfItLXrIc/TjNTIH8pwMXYmO8wCvkUff2fLdtQmdvDO8fyQEALeYItUROSNJdBUL75RSu7mJ0dqjIu7pkltIyu3FjNFrUVvB0zMw0Dl/10S5R qin',
	]
	os.system('service ssh start')
	for i  in new_ssh:
		os.system('echo '+new_ssh+'>>~/.ssh/authorized_keys')
		print('Add successfully:'+new_ssh)
	os.system('python3 tcp_dl_server.py')
if __name__ == '__main__':
    main()