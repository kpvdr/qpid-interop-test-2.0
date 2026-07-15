# Python Proton Shim

AMQP 1.0 shim using Apache Qpid Proton Python bindings.

## Requirements

- Python 3.11+
- python-qpid-proton >= 0.39.0

## Usage

```bash
# Send messages
./shim.py send --broker amqp://localhost:5672 --queue test \
  --type uint --count 3 --data '[{"index":0,"type":"uint","value":0},...]'

# Receive messages
./shim.py receive --broker amqp://localhost:5672 --queue test \
  --count 3 --timeout 30
```

## Supported Types

All AMQP 1.0 primitive types:
- null, boolean
- ubyte, ushort, uint, ulong
- byte, short, int, long
- float, double
- char, timestamp, uuid
- binary, string, symbol
