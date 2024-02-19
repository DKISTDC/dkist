"""
A pandoc filter which returns only the content between the start of the file
and the second top level heading.
"""
import io
import sys
import json

input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
source = input_stream.read()
doc = json.loads(source)

output_blocks = []
for block in doc["blocks"]:
    if output_blocks and block["t"] == "Header" and block["c"][0] == 1:
        break
        print(block["c"], file=sys.stderr)
    output_blocks.append(block)

doc["blocks"] = output_blocks
sys.stdout.write(json.dumps(doc))
