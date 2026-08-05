# Demo Server

This local server gives reviewers one browser entry point for manual testing.

Q1 supports:

- text-based web calling
- microphone speech recognition when the browser supports it
- browser speech playback
- audio recording save to `evidence/q1/recordings/`
- transcript history

## Run

```powershell
python .\src\server.py --host 127.0.0.1 --port 8088
```

Then open:

- `http://127.0.0.1:8088/`
- `http://127.0.0.1:8088/q1`
- `http://127.0.0.1:8088/q2`
- `http://127.0.0.1:8088/q3`
- `http://127.0.0.1:8088/q4`
