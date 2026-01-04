# rmdbg

rmdbg is a command-line tool that removes debugger statements from your source code.

It is currently restricted to Python source code with pdb and ipdb debugger statements.

Before:

```python
print("Hello, world!")
import pdb; pdb.set_trace()

for i in range(10):
    print(i)

import ipdb

ipdb.set_trace()

print("Done")
```

After:

```python
print("Hello, world!")

for i in range(10):
    print(i)


print("Done")
```

## Installation

```bash
git clone https://github.com/osolmaz/rmdbg
cd rmdbg
cargo install --path .
```

## Usage

```bash
cd /path/to/your/project
rmdbg .
```
