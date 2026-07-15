# QIT C++ Proton Shim

AMQP interoperability test shim using Qpid Proton C++.

## Dependencies

### Fedora/RHEL
```bash
sudo dnf install -y qpid-proton-cpp-devel jsoncpp-devel cmake g++
```

### Ubuntu/Debian
```bash
sudo apt install -y libqpid-proton-cpp12-dev libjsoncpp-dev cmake g++
```

## Building

```bash
cd shims/cpp-proton
mkdir -p build
cd build
cmake ..
make
```

The executable will be built as `build/qit-shim-cpp`.

## Usage

Via the wrapper script:
```bash
# Send messages
./shim.sh send --broker amqp://localhost:5672 --queue test.queue \
  --type uint --count 3 \
  --data '[{"index":0,"type":"uint","value":0},{"index":1,"type":"uint","value":42},{"index":2,"type":"uint","value":255}]'

# Receive messages
./shim.sh receive --broker amqp://localhost:5672 --queue test.queue \
  --count 3 --timeout 30
```

## Implementation Notes

- **Type Detection**: Uses `proton::value::type()` which preserves AMQP type information perfectly
- **Type Encoding**: All 18 AMQP primitive types supported
- **Float Encoding**: Hex strings (`0x...`) for exact binary representation
- **Integer Encoding**: Accepts both decimal and hex input
- **UUID Format**: Standard format `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Binary Format**: Hex strings

## Supported Types

All 18 AMQP 1.0 primitive types:
- null, boolean
- ubyte, ushort, uint, ulong
- byte, short, int, long
- float, double
- char, timestamp, uuid
- binary, string, symbol
