# start.py
import asyncio
import sys
import runpy

# On Windows, the default asyncio event loop (ProactorEventLoop) has limitations
# when used in threads, which can cause a ValueError.
# Switching to the SelectorEventLoopPolicy resolves this for libraries like libsql_client.
if sys.platform == "win32":
    print("Applying asyncio event loop policy for Windows.")
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

print("Starting the application from main.py...")
# Execute main.py as if it were run directly from the command line
runpy.run_path('main.py', run_name='__main__')
