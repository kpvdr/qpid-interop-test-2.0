# Rhea Shim Known Issues

## 1. Numeric Type Detection Limitation

**Issue**: The Rhea JavaScript library cannot distinguish between different AMQP numeric types after receiving messages.

**Root Cause**: Rhea automatically converts all AMQP numeric types (byte, ubyte, short, ushort, int, uint, long, ulong) to JavaScript's single `number` primitive type. The AMQP type descriptor information that exists on the wire is not exposed through Rhea's API after decoding.

**Impact**: 
- Tests involving uint, int, and other numeric type variations may fail when using the Rhea shim as receiver
- The shim correctly *sends* typed values using `rhea.types.wrap_uint()` etc., but cannot detect them on receive
- This affects cross-shim tests: `python→javascript` and `javascript→javascript` for numeric types

**Comparison with Other Clients**:
- **Python Proton**: Preserves types as distinct Python classes (`ubyte`, `uint`, `int32`, etc.)
- **C++ Proton**: Preserves types via `proton::value::type_id()`
- **Rhea**: Converts to JavaScript primitives, losing type information

**Old QIT v1 Approach**:
The original test suite worked around this by passing the expected type as a command-line argument to the receiver, so it knew what to expect rather than detecting it. This approach was less rigorous - it verified "values match for expected type" but not "receiver can detect the type."

**QIT 2.0 Decision**:
We leave these tests failing to expose the limitation rather than compromising the shim architecture. This serves as documentation and motivation to work with the Rhea project to expose type descriptors in their API.

**Future Resolution**:
- Contribute to Rhea to expose `message.body_type` or similar AMQP type descriptor
- Alternative: Use a different JavaScript AMQP library if one exists that preserves type information
- Fallback: Document the limitation and accept that JavaScript/Rhea cannot fully participate in numeric type interop testing

**Affected Test Cases** (as of 2026-07-14):
- python-proton → javascript-rhea (uint)
- javascript-rhea → javascript-rhea (uint)
- Similar failures expected for: byte, ubyte, short, ushort, int, long, ulong when tested

**Workaround for Users**:
If precise numeric type interoperability is critical for your use case, use Python, C++, Java, or .NET clients which preserve AMQP type information.

---

## 2. 64-bit Integer (long/ulong) Limitation

**Issue**: JavaScript's `Number` type is a 64-bit float, which cannot accurately represent all 64-bit integer values. Large `long` and `ulong` values lose precision or cause range errors.

**Root Cause**: JavaScript has no native 64-bit integer type (BigInt exists but Rhea doesn't use it for AMQP long/ulong types).

**Impact**:
- Values > 2^53 lose precision
- Values outside int32 range cause encoding errors in Rhea
- Tests with large long/ulong values fail

**Example Error**:
```
RangeError [ERR_OUT_OF_RANGE]: The value of "value" is out of range. 
It must be >= -2147483648 and <= 2147483647. Received 2147483648
```

**Resolution**: Rhea would need to use JavaScript BigInt for 64-bit AMQP integers. This is a library enhancement.

---

## 3. Type Detection for Non-Numeric Types

**Issue**: Similar to numeric types, Rhea converts other AMQP types to JavaScript primitives, losing type information:
- `char` → `number` (detected as `long`)
- `symbol` → `string` (detected as `string`)
- `uuid` → `Buffer` (might be detected as `binary`)
- `float` → `number` (detected as `long` or `double`)
- `double` → `number` (detected as `long`)

**Root Cause**: Same as issue #1 - Rhea's API doesn't expose AMQP type descriptors.

**Current Test Status** (2026-07-14):
- 35/72 tests passing (48.6%)
- Most failures are Rhea type detection issues
- Python ↔ Python tests also have some failures (float/double special values, binary encoding)

**Summary**: JavaScript/Rhea can send typed AMQP messages correctly but cannot reliably detect received types. This is a fundamental library limitation.
