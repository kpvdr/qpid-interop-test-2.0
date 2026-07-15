# Docker Broker Setup - WORKING ✓

## Status: FULLY FUNCTIONAL

The Docker broker setup is working with the official Apache Artemis image.

## Quick Start

```bash
# Start broker
docker compose up -d

# Check it's running
docker compose ps

# View logs
docker compose logs -f artemis

# Test
cd ..
source .venv/bin/activate
python test_manual.py send
python test_manual.py receive

# Stop
docker compose down
```

## Configuration

- **Image**: `apache/artemis:latest-alpine` (official Apache image)
- **Custom config**: `etc-override/broker.xml`
- **Auto-create queues**: Enabled for `qit.#` and `test.#` patterns
- **Routing**: ANYCAST (queue semantics, not topic)
- **Persistence**: Disabled for faster testing

## How the Override Works

Per [official Artemis Docker documentation](https://artemis.apache.org/components/artemis/documentation/latest/docker.html#overriding-files-in-etc-folder):

1. Custom `broker.xml` placed in `etc-override/` directory
2. Directory mounted to `/var/lib/artemis-instance/etc-override/` in container
3. On first start, Artemis copies override files to `/var/lib/artemis-instance/etc/`
4. Broker starts with custom configuration

## Important: Use Correct Image

✅ **WORKS**: `apache/artemis:latest-alpine`  
❌ **DOESN'T WORK**: `quay.io/artemiscloud/activemq-artemis-broker`

The artemiscloud image does not implement the etc-override mechanism.

## Verifying Configuration

```bash
# Check persistence is disabled (should show "false")
docker exec qit-artemis grep "persistence-enabled" /var/lib/artemis-instance/etc/broker.xml

# Check QIT address settings are present
docker exec qit-artemis grep -A3 'match="qit.#"' /var/lib/artemis-instance/etc/broker.xml
```

## Files

- `compose.yaml` - Docker Compose configuration
- `etc-override/broker.xml` - Custom Artemis configuration
- `README.md` - This file

## Troubleshooting

### Config not applied

Force recreation of broker instance:
```bash
docker compose down -v  # Remove volumes
docker compose up -d
```

### Permission issues on SELinux systems

The compose file uses `:z` flag for volume mounts to handle SELinux relabeling.

### Port 5672 already in use

Stop any existing broker:
```bash
docker compose down
# Or if running locally:
./artemis-local/bin/artemis-service stop
```
