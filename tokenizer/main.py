import sys


USAGE_MESSAGE = "usage: python main.py <file>"
HELP_MESSAGE = f"""{USAGE_MESSAGE}

Tokenize source code from <file> and print one token per line:
  (<type>, <value>, <line>:<col>)
where <type> is IDENT, KEYWORD, INT, FLOAT, STRING, OP or SEP.

On an invalid character prints
  <file>:<line>:<col>: lexical: <message>
and exits with code 1."""

class LexicalException(Exception):
    def __init__(self, line, col, text) -> None:
        super().__init__(f"{line}:{col}: lexical: {text}")
        self.line = line
        self.col = col
        self.text = text


class Lexer():
    operators = {"+", "-", "*", "/", "=", "<", ">"}
    keywords = {"if", "else", "while", "return", "for", "def"}
    separators = {"(", ")", "{", "}", ",", ";"}

    def __init__(self, text) -> None:
        self.text = text
        self.len = len(text)
        self.col = 1
        self.line = 1
        self.pos = 0


    def peek(self):
        return self.text[self.pos] if self.pos < self.len else ""


    def advance(self):
        c = self.text[self.pos]

        if c == "\n":
            self.line +=1
            self.col = 0
            
        self.col += 1
        self.pos += 1
        
        return c


    def read_while(self, pred):
        start = self.pos
        while self.peek() and pred(self.peek()):
            self.advance()
            
        return self.text[start:self.pos]


    def read_word(self):
        start_line, start_col = self.line, self.col
        token = self.read_while(lambda c: c.isalnum() or c == "_")

        if token in self.keywords:
            return ("KEYWORD", token, start_line, start_col)

        return ("IDENT", token, start_line, start_col)
        
        
    def read_number(self):
        start_line, start_col = self.line, self.col
        token = self.read_while(lambda c: c.isdigit())

        if self.peek() == ".":
            token += self.advance()
            token += self.read_while(lambda c: c.isdigit())

            return ("FLOAT", token, start_line, start_col)

        return ("INT", token, start_line, start_col)
        

    def read_string(self):
        start_line, start_col = self.line, self.col
        token = self.advance()
        token += self.read_while(lambda c: c != '"')

        if not self.peek():
            raise LexicalException(start_line, start_col, "unterminated string literal")
            
        token += self.advance()

        return ("STRING", token, start_line, start_col)
        
        
    def read_op(self):
        start_line, start_col = self.line, self.col
        token = self.advance()
        
        if token in {"=", "<", ">"} and self.peek() in {"="}:
            token += self.advance()

        return ("OP", token, start_line, start_col)


    def read_sep(self):
        start_line, start_col = self.line, self.col
        token = self.advance()

        return ("SEP", token, start_line, start_col)
        

    def read_comment(self):
        self.read_while(lambda c: c != "\n")


    def tokens(self):
        while self.peek():
            c = self.peek()

            if c == "\n":
                self.advance()

            elif c.isspace():
                self.advance()
                
            elif c.isdigit():
                yield self.read_number()

            elif c == '"':
                yield self.read_string()

            elif c.isalpha() or c == "_":
                yield self.read_word()

            elif c in self.operators:
                yield self.read_op()

            elif c in self.separators:
                yield self.read_sep()

            elif c == "#":
                self.read_comment()

            else:
                raise LexicalException(self.line, self.col, f"unexpected character '{c}'")


    def tokenize(self):
        return list(self.tokens())


def main():
    if len(sys.argv) < 2:
        print(HELP_MESSAGE, file=sys.stderr)
        sys.exit(2)
    elif len(sys.argv) > 2:
        print(USAGE_MESSAGE, file=sys.stderr)
        sys.exit(2)
    else:
        file_name = sys.argv[1]

        try:
            with open(file_name, "r", encoding="utf-8") as file:
                text = file.read()
                lexer = Lexer(text)

                try:
                    tokens = lexer.tokenize()
                    for token in tokens:
                        type, value, line, col = token
                        
                        print(f"({type}, {value}, {line}:{col})")
                        
                except LexicalException as le:
                    exception_message = f"{file_name}:{le}"

                    print(exception_message, file=sys.stderr)
                    sys.exit(1)
                    
        except (OSError, UnicodeDecodeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()