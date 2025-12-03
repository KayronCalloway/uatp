"""
Demo of UATP capsule encapsulation
"""
from core.capsule import Capsule

# Create a parent capsule
parent_content = {"message": "I am the parent capsule"}
parent_capsule = Capsule(parent_content)
parent_sealed = parent_capsule.encapsulate()
print("Parent Capsule:", parent_sealed)

# Create a child capsule
child_content = {"message": "I am the child capsule"}
child_capsule = Capsule(child_content, parent=parent_sealed["signature"])
child_sealed = child_capsule.encapsulate()
print("Child Capsule:", child_sealed)
