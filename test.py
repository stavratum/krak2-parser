# reading .j file and reproducing it with edited instructions  
# only works with generated files from krak2

import krak2
import sys

if len(sys.argv) < 2:
    print("usage: python test.py <input> <output>")
    print("example: python test.py Test.j Test_edited.j")
    print("example: python test.py Test.j")
    print("^ will write to the same file (you will lose the original file)")
    print()

    exit(1)

input = sys.argv[1]
output = sys.argv[-1]

print("input: ", input)
print("output: ", output)

krak = krak2.Parser(input)
j = krak.parse_class()

# edit instructions here

def process_method_spec(method: krak2.JMethod, instructions: list, remove: list) -> bool:
    labels = method.code.labels

    start_label = -1
    instr = 0
    i = 0

    while True:
        if i >= len(labels):
            return False

        instruction = instructions[instr]
        label = labels[i]

        if start_label != -1:
            if instruction == label.instructions[0].name:
                instr += 1
                
                if instr == len(instructions):
                    a = 0
                    for j in range(start_label, start_label + len(instructions)):
                        if remove[a]:
                            del labels[j]
                        a += 1


                    return True
                
                i += 1
                continue
            else:
                i = start_label + 1
                start_label = -1
            
            continue

        if len(label.instructions) == 0:
            i += 1
            continue

        if instructions[0] == label.instructions[0].name:
            start_label = i
            instr = 1

        i += 1

def process_method(method: krak2.JMethod, instructions: list) -> bool:
    labels = method.code.labels

    start_label = -1
    instr = 0
    i = 0

    while True:
        if i >= len(labels):
            return False

        instruction = instructions[instr]
        label = labels[i]

        if start_label != -1:
            if instruction == label.instructions[0].name:
                instr += 1
                
                if instr == len(instructions):
                    for j in range(0, len(instructions)):
                        del labels[start_label]

                    return True
                
                i += 1
                continue
            else:
                i = start_label + 1
                start_label = -1
            
            continue

        if len(label.instructions) == 0:
            i += 1
            continue

        if instructions[0] == label.instructions[0].name:
            start_label = i
            instr = 1

        i += 1


patterns = []
patterns.append(["ldc", "pop"])
patterns.append(["ldc", "ldc", "pop2"])
patterns.append(["ldc_w", "pop"])
patterns.append(["ldc_w", "ldc_w", "pop2"])
patterns.append(["swap", "swap"])
patterns.append(["dup", "pop"])
patterns.append(["ldc", "invokevirtual", "pop"])
patterns.append(["ldc_w", "invokevirtual", "pop"])
patterns.append(["ldc", "invokevirtual", "dup", "pop2"])
patterns.append(["ldc_w", "invokevirtual", "dup", "pop2"])
patterns.append(["ldc", "ldc_w", "pop2"])
patterns.append(["ldc", "ldc", "swap", "pop", "ldc", "pop2"])
patterns.append(["ldc_w", "ldc_w", "swap", "pop", "ldc_w", "pop2"])

for method in j.methods:
    while True:
        processed = False

        for list in patterns:
            processed = processed or process_method(method, list)
    
        processed = processed or process_method_spec(method, ["dup", "swap"], [False, True])

        if not processed:
            break
#

def yeah(a):
    return a and a + " " or ""

def dft(a: bool, b: str):
    return a and b + " " or ""

sys.stdout = open(output, 'w')

print(f".version {j.vmajor} {j.vminor}")
print(f".class {yeah(j.access)}{dft(j.final, "final")}{dft(j.super, "super")}{dft(j.synthetic, "synthetic")}{dft(j.enum, "enum")}{j.name}")
print(f".super {j.superclass}")

if len(j.implements) > 0:
    for i in range(0, len(j.implements)):
        print(f".implements {j.implements[i]}")

for field in j.fields:
    print(".field "+yeah(field.access)+dft(field.static, "static")+dft(field.final, "final")+dft(field.enum, "enum")+dft(field.synthetic,"synthetic")+field.name+" "+field.jclass +" "+dft(field.attributes, ".fieldattributes"))
    #print(f".field {yeah(field.access)}{dft(field.static, "static")}{dft(field.final, "final")}{dft(field.enum, "enum")}{dft(field.synthetic, "synthetic")} {field.name} {field.jclass} {dft(field.attributes, ".fieldattributes")}")

    if field.attributes:
        for attribute in field.attributes:
            print(f"    .{attribute} {" ".join(field.attributes[attribute])}")
        print(".end fieldattributes")


print()

for method in j.methods:
    code = method.code

    print(f".method {yeah(method.access)}{dft(method.static, "static")}{dft(method.synthetic, "synthetic")}{method.name} : {method.arguments}")
    print(f"    .code stack {code.stack} locals {code.locals}")
    
    for label in code.labels:
        if len(label.instructions) == 0:
            continue

        print(f"L{label.name}:     {label.instructions[0].name} {" ".join(label.instructions[0].arguments)}")

        for instruction in label.instructions[1:]:
            print(f"            {instruction.name} {" ".join(instruction.arguments)}")
        
        if label.catch:
            print()
            print(f"        .catch {" ".join(label.catch)}")

        if label.stack:
            print()

            if label.stack.full:
                print("        .stack full")
                print("            locals " + " ".join(label.stack.locals))
                print("            stack " + " ".join(label.stack.stack))
                print("        .end stack")
            else:
                print("        .stack " + " ".join(label.stack.stack))
        

    print("    .end code")

    if method.signature:
        print(f"    .signature {method.signature}")

    print(".end method")
    print()

if j.innerclasses:
    for jic in j.innerclasses:
        print(jic.v[:-1])

    print(".end innerclasses")

if j.signature:
    print(f".signature {j.signature}")

for enc in j.enclosing:
    print(".enclosing " + " ".join(enc))

if j.bootstrapmethods:
    print()
    print(".bootstrapmethods")
    print()

if len(j.constants) > 0:
    for constant in j.constants:
        print(constant.v[:-1])

print(".end class")