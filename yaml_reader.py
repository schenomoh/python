#pip install pyyaml
import yaml
space_indent=2

def load(file):
	f=open(file, 'r+')
	data= f.read()
	f.close()
	
	return yaml.safe_load(data)

	
