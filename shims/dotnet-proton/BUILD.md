# .NET Apache Qpid Proton Shim - Build Instructions

## Prerequisites

- .NET SDK 8.0 or later
- Apache Artemis broker (or Docker Compose for containerized testing)

## Installation

### Fedora/RHEL
```bash
sudo dnf install -y dotnet-sdk-8.0
```

### Ubuntu/Debian
```bash
sudo apt-get install -y dotnet-sdk-8.0
```

### Other platforms
Download from: https://dotnet.microsoft.com/download

## Building

```bash
cd shims/dotnet-proton
dotnet restore
dotnet build -c Release
```

## Testing Standalone

### Send Messages
```bash
bin/Release/net8.0/qit-shim-dotnet send \
    --broker amqp://localhost:5672 \
    --queue qit.test \
    --type int \
    --data '[{"index": 0, "value": 42}]'
```

### Receive Messages
```bash
bin/Release/net8.0/qit-shim-dotnet receive \
    --broker amqp://localhost:5672 \
    --queue qit.test \
    --count 1 \
    --timeout 5
```

## Integration with QIT

The shim is automatically discovered by the QIT CLI via `shim.sh` wrapper.

Test with:
```bash
uv run qit test amqp-types --sender dotnet-proton --receiver dotnet-proton --type int
```

## Dependencies

- **Apache.Qpid.Proton.Client** (1.0.0) - Apache Qpid Proton .NET Client Library
- **Newtonsoft.Json** (13.0.3) - JSON serialization
- **System.CommandLine** (2.0.0-beta4) - Command-line parsing

## Architecture

The shim uses the **Apache Qpid Proton .NET Client API**, which provides:
- High-level `IClient`, `IConnection`, `ISender`, `IReceiver` abstractions
- Native AMQP 1.0 type support
- Synchronous and asynchronous APIs

This is different from the lower-level protocol engine in the `Apache.Qpid.Proton` package.

## Type Detection

Type detection uses C# reflection:
```csharp
var typeName = value.GetType().Name;
// "Int32" → "int", "Single" → "float", etc.
```

Float and double values are returned as hex strings for exact comparison:
```csharp
var floatBytes = BitConverter.GetBytes((float)value);
var intVal = BitConverter.ToUInt32(floatBytes, 0);
return $"0x{intVal:x8}";
```

## Known Issues

None currently - the shim passes all basic type tests with 100% compatibility across Python, JavaScript, C++, and .NET implementations.

## References

- GitHub: https://github.com/apache/qpid-proton-dotnet
- NuGet: https://www.nuget.org/packages/Apache.Qpid.Proton.Client
- Apache Qpid: https://qpid.apache.org/proton/
