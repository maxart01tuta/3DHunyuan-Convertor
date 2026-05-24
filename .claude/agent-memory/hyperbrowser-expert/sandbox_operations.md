# Sandbox Operations

Песочница — изолированная виртуальная машина с собственными файлами, процессами, терминалом и networking.

## Sandboxes API Reference
See: https://docs.hyperbrowser.ai/reference/sdks/python/sessions

## Create a Sandbox

```python
from hyperbrowser import Hyperbrowser
from hyperbrowser.models import CreateSandboxParams, SandboxExposeParams

client = Hyperbrowser(api_key=os.getenv("HYPERBROWSER_API_KEY"))

sandbox = client.sandboxes.create(
    CreateSandboxParams(
        image_name="node",
        region="us-west",
        timeout_minutes=30,
        enable_recording=True,
        exposed_ports=[SandboxExposeParams(port=3000, auth=True)],
    )
)
```

## Execute Commands

```python
# One-shot command
result = sandbox.exec(command="bash", args=["-lc", "node --version"])
print(result.stdout.strip())

# Long-running process
process = sandbox.processes.start(
    SandboxExecParams(
        command="bash",
        args=["-lc", "sleep 30"]
    )
)
print(process.id)
```

## File Operations

```python
# Write text
sandbox.files.write_text("/tmp/file.txt", "hello content")
sandbox.files.write_text("/tmp/file.txt", "\nmore text", append=True)

# Read text
text = sandbox.files.read_text("/tmp/file.txt")

# List files
entries = sandbox.files.list("/tmp", depth=2)

# Watch directory
def on_event(event):
    print(event.type, event.name)

watch = sandbox.files.watch_dir("/tmp/watch", on_event, recursive=True)
watch.stop()
```

## File Upload/Download

```python
# Create upload URL
upload = sandbox.files.upload_url(
    "/tmp/upload.txt",
    one_time=True,
    expires_in_seconds=60,
)
print(upload.method, upload.url)

# Create download URL
download = sandbox.files.download_url(
    "/tmp/file.txt",
    one_time=True,
    expires_in_seconds=60,
)
print(download.url)
```

## Terminal / PTY

```python
from hyperbrowser.models import SandboxTerminalCreateParams

terminal = sandbox.terminal.create(
    SandboxTerminalCreateParams(
        command="bash",
        args=["-l"],
        rows=24,
        cols=80,
        timeout_ms=60000,
    )
)
```

## Snapshots

```python
# Create memory snapshot
snapshot = sandbox.create_memory_snapshot(
    SandboxMemorySnapshotParams(snapshot_name="after-setup")
)

# Start from snapshot
sandbox = client.sandboxes.create(
    CreateSandboxParams(
        snapshot_name="after-setup"
    )
)
```

## Manage Sandboxes

```python
# List sandboxes
response = client.sandboxes.list(
    SandboxListParams(status="active", page=1, limit=20)
)

# List images
images = client.sandboxes.list_images()

# List snapshots
snapshots = client.sandboxes.list_snapshots(
    SandboxSnapshotListParams(limit=10)
)

# Reconnect to running sandbox
sandbox = client.sandboxes.connect("sandbox-id")

# Get sandbox info
detail = sandbox.info()
print(detail.runtime.base_url)

# Stop sandbox
sandbox.stop()
```

## Networking

```python
# Expose port
exposure = sandbox.expose(
    SandboxExposeParams(port=3000, auth=True)
)

# Get exposed URL
url = sandbox.get_exposed_url(3000)

# Unexpose port
sandbox.unexpose(3000)
```
