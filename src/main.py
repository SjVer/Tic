#!/usr/bin/python3

from lex import *
from emit import *
from parse import *
import sys, argparse, os, tempfile

def main(file, output, compiler):
    print("AttempLang Compiler")
    
    temp = tempfile.NamedTemporaryFile(suffix=".c", mode="w+t")

    with open(file, 'r') as inputFile:
        input = inputFile.read()

    # Initialize the lexer, emitter, and parser.
    lexer = Lexer(input)
    emitter = Emitter(temp)
    parser = Parser(lexer, emitter)

    print("Parsing file.")
    parser.program() # Start the parser.
    emitter.writeFile() # Write the output to file.
    print("Parsing complete.")
    
    print("Compiling file.")
    
    # make sure dirs exist
    if not os.path.exists(os.path.dirname(output)):
        os.mkdir(os.path.dirname(output))
    
    os.system(f"{compiler} {temp.name} -o {output}")
    temp.close()
    print("Compiling completed.")
    
if __name__ == '__main__':
    
    if '--version' in sys.argv:
        print("AttemptLang compiler version 1.0 by Sjoerd Vermeulen")
        sys.exit(0)

    parser = argparse.ArgumentParser('attemptlang', description='AttemptLang compiler', usage='%(prog)s [-v] input\n -h/--help: show help message')
    parser.add_argument('input', type=str, help='input script (program passed in as ".Al" file)')
    parser.add_argument('-o', '--output', dest='file', action='store', help='specify the output file')
    parser.add_argument('-c', '--compiler', dest='compiler', default='/usr/bin/gcc', action='store', help='specify the c compiler (gcc by default)')
    parser.add_argument('-v', '--verbose', action='store_true', default=0, help='verbose compiling')
    parser.add_argument('--version', action='store_true', help='print version info')

    args = parser.parse_args()
    
    if args.file == None:
        outfile = os.path.join(os.getcwd(), "bin", os.path.splitext(os.path.basename(args.input))[0])
    else:
        outfile = args.file
        if not os.path.exists(os.path.dirname(outfile)):
            print(f"Error: Output directory '{os.path.dirname(outfile)}' does not exist")
            sys.exit(1)
    
    if not os.path.exists(args.compiler):
        print(f"Error: Compiler '{args.compiler}' not found")
        sys.exit(1)
    
    main(args.input, outfile, args.compiler)
    
    
    
    
    
    
    
    
    
    
    