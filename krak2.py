import re

class JInstruction:
    name: str
    arguments: list[str]

    def __str__(self) -> str:
        return f"JInstruction {self.name}"
    
class JStack():
    full: bool
    locals: list[str] | None
    stack: list[str]

class JLabel():
    name: str
    stack: JStack | None
    catch: str | None
    instructions: list[JInstruction]

    def __str__(self) -> str:
        return f"JLabel {self.name}"

class JCode:
    stack: int
    locals: int
    labels: list[JLabel]
    line_number_table: dict[str, str]

    def __str__(self) -> str:
        return f"JCode stack {self.stack} locals {self.locals}"

class JMethod:
    access: str | None
    static: bool
    synthetic: bool
    name: str
    arguments: str
    signature: str | None
    code: JCode

    def __str__(self) -> str:
        return self.name

class JField:
    attributes: dict | None
    access: str | None
    name: str
    static: bool
    final: bool
    enum: bool
    synthetic: bool
    jclass: str

    def __str__(self) -> str:
        return self.name
    
class JConstant: # TODO: finish this
    v: str

class JInnerClass: # TODO: finish this
    v: str

class JClass:
    vmajor: str
    vminor: str
    access: str
    name: str
    signature: str | None
    superclass: str
    enum: bool
    super: bool
    final: bool
    bootstrapmethods: bool
    synthetic: bool
    enclosing: list[str] # i need to make this a class probably
    innerclasses: list[JInnerClass] | None
    implements: list[str]
    constants: list[JConstant]

    sourcefile: str
    fields: list[JField]
    methods: list[JMethod]

    def __str__(self) -> str:
        return self.name

class Parser:
    jclass: JClass
    
    lines: list[str]
    line: int

    def __init__(self, f):
        self.line = 0

        with open(f) as out:
            self.lines = out.readlines()

    def next_line(self):
        self.line += 1

    def read_line(self):
        return self.lines[self.line]
    
    def read_lex_line(self):
        line = self.read_line()
        
        tokens = []
        token = ""
        
        for c in line:
            match c:
                case " ":
                    if token != "":
                        tokens.append(token)
                        token = ""
                case "\n":
                    tokens.append(token)
                    return tokens
                case _:
                    token += c
        
        return tokens
    
    def parse_innerclasses(self) -> list[JInnerClass]: # im so lazy and im tired i did all of this in 1 day
        innerclasses = []
        
        while True:
            token = self.read_lex_line()

            match token[0]:
                case ".end":
                    return innerclasses
                case _:
                    innerclass = JInnerClass()
                    innerclass.v = self.read_line()
                    
                    innerclasses.append(innerclass)

            self.next_line()
    
    def parse_line_number_table(self) -> dict[str, str]:
        line_number_table: dict[str, str] = dict()

        while True:
            info = self.read_lex_line()

            if len(info) < 1:
                continue

            match info[0]:
                case ".linenumbertable":
                    pass
                case ".end":
                    return line_number_table
                case _:
                    line_number_table[info[0]] = info[1]
            
            self.next_line()

    def parse_instructions(self) -> list[JInstruction]:
        instructions = []

        tokens = self.read_lex_line()
        if len(tokens) > 0:
            if tokens[0].startswith("L"):
                match len(tokens):
                    case 1: # There is a label
                        pass
                    case 2: # There is instruction
                        instruction = JInstruction()
                        instruction.name = tokens[1]
                        instruction.arguments = []
                        instructions.append(instruction)
                    case _:
                        instruction = JInstruction()
                        instruction.name = tokens[1]
                        instruction.arguments = tokens[2:]
                        instructions.append(instruction)
                
                self.next_line()        

        while True:
            tokens = self.read_lex_line()
            
            if len(tokens) == 0:
                pass
            else:
                if tokens[0].startswith("L") or tokens[0].startswith("."):
                    return instructions

                instruction = JInstruction()
                instruction.name = tokens[0]

                if len(tokens) > 1:
                    instruction.arguments = tokens[1:]

            self.next_line()

    def parse_stack(self) -> JStack:
        info = self.read_lex_line()
        
        stack = JStack()
        stack.full = info[1] == "full"
        
        if info[1] != "full":
            stack.stack = info[1:]
            return stack
        
        self.next_line()

        while True:
            line = self.read_lex_line()

            if len(line) > 0:
                match line[0]:
                    case "locals":
                        stack.locals = line[1:]
                    case "stack":
                        stack.stack = line[1:]
                    case ".end":
                        return stack

            self.next_line()

    def parse_label(self) -> JLabel:
        info = self.read_lex_line()

        while len(info[0]) == "":
            info = self.read_lex_line()

        name = re.match(r"L(.+):", info[0])

        label = JLabel()
        label.name = "MAIN"
        label.catch = None
        label.stack = None
        label.instructions = self.parse_instructions()
        if name != None: label.name = name.group(1)
        
        while True:
            stop = self.read_lex_line()
            
            match stop[0]:
                case ".stack":
                    label.stack = self.parse_stack()  
                case ".catch":
                    label.catch = stop[1:]
                case ".end":
                    return label
                case "":
                    pass
                case _:
                    return label

            self.next_line()
    
    def parse_code(self) -> JCode:
        info = self.read_lex_line()

        code = JCode()
        code.stack = info[2]
        code.locals = info[4]
        code.labels = []

        self.next_line()

        while True:
            line = self.read_lex_line()

            if len(line) == 0:
                continue

            name = re.match(r"L(.+):", line[0])
            
            if not name:
                match line[0]:
                    case ".linenumbertable":
                        code.line_number_table = self.parse_line_number_table()
                    case ".end":
                        return code
                    case _:
                        code.labels.append(self.parse_label())
                        continue
            else:
                code.labels.append(self.parse_label())
                continue
            
            self.next_line()
    
    def parse_method(self) -> JMethod:
        info = self.read_lex_line()
        
        method = JMethod()
        method.access = None
        method.static = False
        method.synthetic = False
        method.signature = None
        method.name = info[-3]
        method.arguments = info[-1]

        for token in info[1:]:
            match token:
                case "private":
                    method.access = token
                case "public":
                    method.access = token
                case "static":
                    method.static = True
                case "synthetic":
                    method.synthetic = True
                case _:
                    break
        
        self.next_line()

        while True:
            line = self.read_lex_line()

            if len(line) > 0:
                match line[0]:
                    case ".code":
                        method.code = self.parse_code()
                    case ".signature":
                        method.signature = line[1]
                    case ".end":
                        return method
                    case _:
                        print("UNHANDLED")
                        print(line)
                        break
            
            self.next_line()

    def parse_attributes(self) -> dict:
        attributes = {}
        
        self.next_line()

        while True:
            line = self.read_lex_line()

            if len(line) > 0:
                match line[0]:
                    case ".signature":
                        attributes["signature"] = line[1:]
                    case ".end":
                        return attributes
                    case _:
                        print("unhandled attribute")
                        print(line)

                        exit(1)

            self.next_line()

    def parse_class(self) -> JClass:
        jclass = JClass()
        jclass.signature = None
        jclass.innerclasses = None
        jclass.bootstrapmethods = False
        jclass.synthetic = False
        jclass.super = False
        jclass.final = False
        jclass.enum = False
        jclass.constants = []
        jclass.enclosing = []
        jclass.implements = []
        jclass.fields = []
        jclass.methods = []

        while True:
            info = self.read_lex_line()

            if len(info) > 0:
                match info[0]:
                    case ".version":
                        jclass.vmajor = info[1]
                        jclass.vminor = info[2]
                    case ".class":
                        jclass.access = info[1]
                        jclass.name = info[-1]

                        for token in info[1:-1]:
                            match token:
                                case "private":
                                    jclass.access = token
                                case "public":
                                    jclass.access = token
                                case "final":
                                    jclass.final = True
                                case "super":
                                    jclass.super = True
                                case "synthetic":
                                    jclass.synthetic = True
                                case "enum":
                                    jclass.enum = True
                                case _:
                                    print("warning: unhandled token in .class - ", token)
                                    break
                    case ".super":
                        jclass.superclass = info[1]
                    case ".implements":
                        if jclass.implements == None:
                            jclass.implements = list[str]()
                        
                        jclass.implements.append(info[1])
                    case ".field":
                        field = JField()
                        field.attributes = None
                        field.access = None
                        field.final = False
                        field.enum = False
                        field.static = False
                        field.synthetic = False

                        field.jclass = info[-1]
                        field.name = info[-2]

                        for token in info[1:]:
                            match token:
                                case ".fieldattributes":
                                    field.jclass = info[-2]
                                    field.name  = info[-3]
                                    field.attributes = self.parse_attributes()
                                case "private":
                                    field.access = token
                                case "public":
                                    field.access = token
                                case "static":
                                    field.static = True
                                case "final":
                                    field.final = True
                                case "synthetic":
                                    field.synthetic = True
                                case "enum":
                                    field.enum = True
                                case " ":
                                    pass
                                case _:
                                    print("warning: unhandled token in .field - ", token)
                                                            
                        jclass.fields.append(field)
                    case ".method":
                        jclass.methods.append(self.parse_method())
                    case ".innerclasses":
                        jclass.innerclasses = self.parse_innerclasses()
                    case ".bootstrapmethods":
                        jclass.bootstrapmethods = True
                    case ".const":
                        constant = JConstant()
                        constant.v = self.read_line()

                        jclass.constants.append(constant)
                    case ".enclosing":
                        jclass.enclosing.append(info[1:])
                    case ".signature":
                        jclass.signature = info[1]
                    case ".sourcefile":
                        jclass.sourcefile = info[1]
                    case ".end":
                        return jclass
                    case " " | "":
                        pass
                    case _:
                        print(info)
                        print(f"385: unhandled {info[0]}")
                        exit(1)

            self.next_line()

class Writer:
    pass