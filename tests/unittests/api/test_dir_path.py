import yaml
import pprint
import os

print(__file__)
print(os.path.join(os.path.dirname(__file__), '..'))
print(os.path.dirname(os.path.realpath(__file__)))
print(os.path.abspath(os.path.dirname(__file__)))

cf = os.path.join(os.path.dirname(__file__), "../..", "config.yaml")
print(cf)

with open(cf, "r") as f:
    pprint.pprint(yaml.safe_load(f))
