# QIT .NET AmqpNetLite Shim

AMQP interoperability test shim using AMQP.Net Lite.

## Dependencies

### Install .NET 8 SDK

**Fedora/RHEL:**
```bash
sudo dnf install -y dotnet-sdk-8.0
```

**Ubuntu/Debian:**
```bash
sudo apt install -y dotnet-sdk-8.0
```

**Manual Installation:**
Download from: https://dotnet.microsoft.com/download/dotnet/8.0

## Building

```bash
cd shims/dotnet-amqpnetlite
dotnet restore
dotnet build -c Release
```

The executable will be built as `bin/Release/net8.0/qit-shim-dotnet.dll`.

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

- **Library**: AMQP.Net Lite 2.4.8
- **Type Detection**: Uses .NET reflection on `GetType().Name` - preserves type information perfectly
- **Type Encoding**: All 18 AMQP primitive types supported
- **Float Encoding**: Hex strings (`0x...`) for exact binary representation
- **Integer Encoding**: Accepts both decimal and hex input
- **UUID Format**: Standard .NET Guid format
- **Binary Format**: Hex strings

## Supported Types

All 18 AMQP 1.0 primitive types:
- null, boolean
- ubyte, ushort, uint, ulong
- byte, short, int, long
- float, double
- char, timestamp, uuid
- binary, string, symbol

## NuGet Packages

- **AMQPNetLite** (2.4.8): AMQP 1.0 client library
- **Newtonsoft.Json** (13.0.3): JSON serialization
- **System.CommandLine** (2.0.0-beta4): CLI parsing

## Project Structure

```
dotnet-amqpnetlite/
├── QitShim.csproj          # Project file
├── src/
│   ├── Program.cs          # Main entry point
│   ├── Sender.cs           # AMQP sender
│   ├── Receiver.cs         # AMQP receiver
│   └── TypeCodec.cs        # Type encoding/decoding
├── shim.sh                 # Wrapper script
└── README.md              # This file
```

## Type Detection

.NET has excellent type preservation. The `TypeCodec.InferType()` method uses reflection:

```csharp
var typeName = obj.GetType().Name;
// "UInt32" → "uint"
// "Int64" → "long"
// etc.
```

This is as reliable as C++ Proton's type detection!

## Expected Test Results

### .NET ↔ .NET
✅ **100% passing** - Perfect type detection, no limitations

### .NET ↔ Python
✅ **High pass rate** - Both preserve types well

### .NET ↔ C++
✅ **High pass rate** - Both have excellent type systems

### .NET ↔ JavaScript
⚠️ **Partial** - Limited by JavaScript/Rhea issues
- .NET → JS: JS can't detect types (known Rhea limitation)
- JS → .NET: ✅ .NET will detect types correctly
