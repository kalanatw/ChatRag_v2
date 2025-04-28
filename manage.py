#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import uvicorn
import signal

uvicorn_server = None

def run_document_fastapi():
    global uvicorn_server
    uvicorn_server = uvicorn.Server(
        config=uvicorn.Config(
            "ChatRAG.document_db_service_pgvector_rerank:app",
            host="127.0.0.1",
            port=8201,
            reload=True
        )
    )
    uvicorn_server.run()

def signal_handler(signum, frame):
    if uvicorn_server:
        uvicorn_server.should_exit = True
    sys.exit(0)

def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ChatRAG.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Check if the command is 'runserver' and not in reload mode
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver' and not os.environ.get('RUN_MAIN'):
        # Start FastAPI server in a separate thread
        thread1 = threading.Thread(target=run_document_fastapi)
        thread1.start()

        # Handle termination signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    # Run Django server
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
