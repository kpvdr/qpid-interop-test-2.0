# Java Apache Qpid ProtonJ2 Shim - Build Instructions

## Prerequisites

- Java JDK 11 or later
- Apache Maven 3.6+
- Apache Artemis broker (or Docker Compose for containerized testing)

## Installation

### Fedora/RHEL
```bash
sudo dnf install -y java-11-openjdk-devel maven
```

### Ubuntu/Debian
```bash
sudo apt-get install -y openjdk-11-jdk maven
```

## Building

```bash
cd shims/java-protonj2
mvn clean package
```

This creates a fat JAR with all dependencies at:
```
target/qit-shim-protonj2.jar
```

## Testing Standalone

### Send Messages
```bash
java -jar target/qit-shim-protonj2.jar send \
    --broker amqp://localhost:5672 \
    --queue qit.test \
    --type int \
    --data '[{"index": 0, "value": 42}]'
```

### Receive Messages
```bash
java -jar target/qit-shim-protonj2.jar receive \
    --broker amqp://localhost:5672 \
    --queue qit.test \
    --count 1 \
    --timeout 5
```

## Integration with QIT

The shim is automatically discovered by the QIT CLI via `shim.sh` wrapper.

Test with:
```bash
uv run qit test amqp-types --sender java-protonj2 --receiver java-protonj2 --type int
```

## Dependencies

- **org.apache.qpid:protonj2-client** (1.1.0) - Apache Qpid ProtonJ2 Client Library
- **com.google.code.gson:gson** (2.10.1) - JSON serialization

## Architecture

The shim uses the **Apache Qpid ProtonJ2 Client API**, which provides:
- High-level `Client`, `Connection`, `Sender`, `Receiver` abstractions
- Native AMQP 1.0 type support with typed wrappers
- Non-blocking and blocking APIs

ProtonJ2 is the successor to qpid-jms and provides direct AMQP 1.0 protocol implementation.

## Type Handling

ProtonJ2 provides excellent type support with specific wrapper classes:
- `UnsignedByte`, `UnsignedShort`, `UnsignedInteger`, `UnsignedLong` for unsigned types
- `Symbol` for AMQP symbols (distinct from strings)
- `Binary` for binary data
- Native Java types for signed integers, float, double, boolean, etc.

Type detection uses instanceof checks:
```java
if (obj instanceof UnsignedByte) return "ubyte";
if (obj instanceof Symbol) return "symbol";
// etc.
```

Float and double values are returned as hex strings for exact comparison:
```java
int bits = Float.floatToRawIntBits(value);
return String.format("0x%08x", bits);
```

## Known Issues

1. **Int vs Char ambiguity**: Both AMQP `int` and `char` types decode to Java `Integer`. 
   Currently defaults to detecting as `char`. This is a limitation of the high-level API
   which doesn't expose AMQP type descriptors on decoded messages.

2. **Java Warnings**: When running with Java 25, you may see warnings about:
   - SLF4J providers (harmless - logging is not required)
   - Unsafe memory access (from Netty library)
   - Restricted method access (from Netty native libraries)
   
   These can be suppressed with the wrapper script which filters stderr.

## Performance

The ProtonJ2 client is high-performance and uses Netty for I/O. Build time is fast (~2 seconds) and the fat JAR approach means no runtime dependency management is needed.

## References

- GitHub: https://github.com/apache/qpid-protonj2
- Maven Central: https://search.maven.org/artifact/org.apache.qpid/protonj2-client
- Apache Qpid: https://qpid.apache.org/proton/
