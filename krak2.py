import re

class JInstruction:
    name: str
    arguments: list[str]

    def __str__(self) -> str:
        return f"JInstruction {self.name}"

class JLabel():
    name: str
    stack: str
    catch: str
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
    access: str
    static: bool
    synthetic: bool
    name: str
    arguments: str
    code: JCode

    def __str__(self) -> str:
        return self.name

class JField:
    access: str | None
    name: str
    final: bool
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
    super: str
    superclass: bool
    innerclasses: list[JInnerClass]
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
        
        tokens = list[str]()
        token = ""
        
        for c in line:
            if c == " ":
                if token != "":
                    tokens.append(token)
                    token = ""
            elif c == "\n":
                tokens.append(token)
            else:
                token += c
        
        return tokens
    
    def parse_innerclasses(self) -> list[JInnerClass]: # im so lazy and im tired i did all of this in 1 day
        innerclasses = list()
        
        while True:
            token = self.read_lex_line()

            match token[0]:
                case ".end":
                    return innerclass
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
        instructions = list()

        tokens = self.read_lex_line()
        if len(tokens) > 0:
            if tokens[0].startswith("L"):
                match len(tokens):
                    case 1: # There is a label
                        pass
                    case 2: # There is instruction
                        instruction = JInstruction()
                        instruction.name = tokens[1]
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

    def parse_label(self) -> JLabel:
        info = self.read_lex_line()
        name = re.match(r"L(.+):", info[0])

        label = JLabel()
        label.name = "MAIN"
        label.instructions = self.parse_instructions()
        if name != None: label.name = name.group(1)
        
        while True:
            stop = self.read_lex_line()
            
            match stop[0]:
                case ".stack":
                    label.stack = stop[1:]    
                case ".catch":
                    label.catch = stop[1:]
                case _:
                    return label

            self.next_line()
    
    def parse_code(self) -> JCode:
        info = self.read_lex_line()

        code = JCode()
        code.stack = info[2]
        code.locals = info[4]
        code.labels = list()

        self.next_line()

        while True:
            line = self.read_lex_line()

            if len(line) == 0:
                continue

            name = re.search(r"L(.+):", line[0])
            
            if name == None:
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
        method.static = False
        method.synthetic = False
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
                    case ".end":
                        return method
            
            self.next_line()

    def parse_class(self) -> JClass:
        jclass = JClass()
        jclass.superclass = False
        jclass.implements = list()
        jclass.fields = list()
        jclass.methods = list()

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

                        match len(info):
                            case 3:
                                pass
                            case 4:
                                if info[2] != "super": print("warning: unhandled class token: ", info[2])
                                else: jclass.superclass = True
                            case _:
                                print("unhandled .class info size")
                                exit(1)
                    case ".super":
                        jclass.super = info[1]
                    case ".implements":
                        if jclass.implements == None:
                            jclass.implements = list[str]()
                        
                        jclass.implements.append(info[1])
                    case ".field":
                        field = JField()
                        field.final = False
                        field.access = None
                        field.name = info[-2]
                        field.jclass = info[-1]

                        match len(info):
                            case 3:
                                pass
                            case 4:
                                field.access = info[1]
                            case 5:
                                field.access = info[1]
                                field.final = info[2] == "final"
                            case _:
                                print("unhandled .field info size: ", info)
                                exit(1)
                        
                        jclass.fields.append(field)
                    case ".method":
                        jclass.methods.append(self.parse_method())
                    case ".innerclasses":
                        jclass.innerclasses = self.parse_innerclasses()
                    case ".bootstrapmethods": # idk what is bootstrapmethod and what are constants in java im just adding this lol
                        jclass.constants = list()
                    case ".const":
                        constant = JConstant()
                        constant.v = self.read_line()

                        jclass.constants.append(constant)
                    case ".sourcefile":
                        jclass.sourcefile = info[1]
                    case ".end":
                        return jclass
                    case " " | "":
                        pass
                    case _:
                        print(f"343: unhandled {info[0]}")
                        exit(1)

            self.next_line()

class Writer: # TODO
    pass
