# Docker Broker Status

## Current Status: NOT WORKING

The `/var/lib/artemis-instance/etc-override` volume mount approach from the [official Artemis Docker documentation](https://artemis.apache.org/components/artemis/documentation/latest/docker.html#overriding-files-in-etc-folder) is not working with the `quay.io/artemiscloud/activemq-artemis-broker` image.

## What Was Tried

### Attempt 1: Volume Mount to etc-override (per documentation)
```yaml
volumes:
  - ./etc-override:/var/lib/artemis-instance/etc-override:ro,z
```

**Result**: 
- ✅ File IS mounted and readable at `/var/lib/artemis-instance/etc-override/broker.xml`
- ❌ File is NOT copied to `/home/jboss/broker/etc/broker.xml`
- ❌ Default configuration is used instead

**Why it fails**:
- The artemiscloud image may not implement the etc-override copy mechanism
- Or the copy happens at a different lifecycle point than expected
- No log messages about override being processed

### Attempt 2: Custom Dockerfile with sed script
- Timing issues - broker.xml doesn't exist when entrypoint runs
- Complex to coordinate instance creation and config modification

### Attempt 3: Environment variable flags
- `--autocreate` flag exists but doesn't control routing type (ANY CAST vs MULTICAST)
- Can't configure address-settings via environment variables

## What Works

**Local Artemis**: ✅ TESTED AND WORKING
```bash
export ARTEMIS_HOME=/path/to/artemis
./scripts/setup-local-broker.sh
./artemis-local/bin/artemis run
```

This creates a broker with:
- Auto-create queues for `qit.#` and `test.#` patterns
- ANYCAST routing (queue semantics)
- Persistence disabled

## Next Steps for Docker (Future Work)

### Option A: Use apache/artemis Image Instead
The documentation example uses `apache/artemis:latest-alpine`. Try that image instead of artemiscloud:
```yaml
image: apache/artemis:latest-alpine
```

### Option B: Custom Entrypoint Script
Create a wrapper that:
1. Calls original launcher to create instance
2. Waits for broker.xml to exist
3. Modifies it with sed
4. Starts broker

### Option C: Use Named Volume + Init Container
```yaml
volumes:
  - broker-data:/home/jboss/broker
init:
  # Container that modifies broker.xml before main container starts
```

### Option D: Use Dispatch Router
Qpid Dispatch Router auto-creates queues by default:
```yaml
services:
  dispatch:
    image: quay.io/interconnectedcloud/qdrouterd
```

## Recommendation

**For Phase 2**: Use local Artemis (working, matches Jenkins)

**For CI/CD**: Revisit Docker configuration or use Dispatch Router

## Files in This Directory

- `compose.yaml` - Docker Compose (currently not working as intended)
- `etc-override/broker.xml` - Our custom config (not being applied)
- `Dockerfile.artemis` - Custom image attempt (deprecated)
- `configure-broker.sh` - Init script attempt (timing issues)
- `README_DOCKER_STATUS.md` - This file

## Testing Docker Changes

When making changes:
```bash
# Force clean restart
docker compose -f docker/compose.yaml down -v
docker compose -f docker/compose.yaml up -d
sleep 40

# Check if config was applied
docker exec qit-artemis grep "persistence-enabled\|qit.#" /home/jboss/broker/etc/broker.xml

# Test send/receive
source ../.venv/bin/activate
python ../test_manual.py send
python ../test_manual.py receive
```
