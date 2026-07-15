# Rhea Type Detection Fix

## Problem
Rhea's message decoder automatically "unwraps" AMQP Typed objects to JavaScript primitives, losing type information. This prevented the receiver from detecting whether it received a `uint` vs `int` vs `long`, etc.

## Root Cause
In `/node_modules/rhea/lib/message.js` line 143:
```javascript
msg.body = types.unwrap(section);
```

The `types.unwrap()` function recursively extracts the JavaScript value from Rhea's `Typed` objects, discarding the AMQP type descriptor.

## Solution
**Monkey-patch `types.unwrap()` to capture Typed objects before they're unwrapped.**

### Implementation (in shim.js)
```javascript
const originalUnwrap = rhea.types.unwrap;
let capturedTypedBodies = [];

rhea.types.unwrap = function(o, leave_described) {
    // Capture ALL Typed objects during message decode
    if (o && o.type && o.type.name) {
        capturedTypedBodies.push({
            typeName: o.type.name,
            typeCode: o.type.typecode,
            value: o.value,
            typed: o
        });
    }
    return originalUnwrap.call(this, o, leave_described);
};
```

Then in the `'message'` event handler:
```javascript
connection.on('message', (context) => {
    const capturedList = [...capturedTypedBodies];
    capturedTypedBodies = [];

    const body = context.message.body;  // Already unwrapped

    // Match the Typed object to the body value
    // Search from END (body is typically one of the last unwraps)
    let typedBody = null;
    for (let i = capturedList.length - 1; i >= 0; i--) {
        if (capturedList[i].value === body) {
            typedBody = capturedList[i].typed;
            break;
        }
    }

    // Now typedBody has .type.name = "SmallUint", "Long", etc.
    const decoded = TypeDecoder.decode(typedBody || body);
    ...
});
```

### Type Name Mapping
Rhea uses type names like `SmallUint`, `Uint`, `Uint0` which all map to AMQP `uint`. The TypeDecoder maps these:

```javascript
const nameMap = {
    'Ubyte': 'ubyte',
    'Ushort': 'ushort',
    'Uint': 'uint',
    'SmallUint': 'uint',
    'Uint0': 'uint',
    // ... etc
};
```

## Results
**Before fix**: 35/72 tests passing (48.6%)  
**After fix**: 50/72 tests passing (69.4%)  

All JavaScript type detection issues resolved! Remaining failures are Python-side issues (float infinity handling, binary encoding).

### Type Detection Now Working
- ✅ All numeric types (ubyte, ushort, uint, ulong, byte, short, int, long)
- ✅ Float and double  
- ✅ Char, timestamp, uuid, binary, string, symbol
- ✅ Boolean and null

## Caveats
1. **Monkey-patching**: This modifies Rhea's global `types.unwrap` function. Could affect other Rhea users in the same process (unlikely in our use case).

2. **Matching by value**: When the body value appears multiple times in the message (e.g., `0` in headers AND body), we search backwards to prefer the body. This works because message sections are decoded in order (headers → properties → body).

3. **Not upstream**: This fix is specific to our shim. The proper solution is to contribute to Rhea to expose type descriptors in their API.

## Future Work
Propose to Rhea project:
- Add `message.body_type` property that preserves the AMQP type descriptor
- Or add an option to `message.decode()` like `{preserveTypes: true}`
- Or expose the raw Typed object via `message.raw_body`

## Testing
```bash
# Test specific type
uv run qit test amqp-types --type uint

# Test full matrix
uv run qit test amqp-types
```

All JavaScript ↔ JavaScript and Python ↔ JavaScript type combinations now pass for properly implemented types!
