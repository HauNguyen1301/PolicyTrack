import os
import asyncio
from dotenv import load_dotenv
import libsql_client

# --- Load Environment Variables ---
load_dotenv()
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")

# --- Async Test Function ---
async def main():
    if not TURSO_DATABASE_URL or not TURSO_AUTH_TOKEN:
        print("Error: Please ensure TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are in your .env file.")
        return

    print(f"Attempting to connect to: {TURSO_DATABASE_URL}")

    try:
        # Use the http/https protocol for the URL
        # Replace 'libsql://' with 'https://'
        http_url = TURSO_DATABASE_URL.replace("libsql", "https", 1)

        async with libsql_client.create_client(url=http_url, auth_token=TURSO_AUTH_TOKEN) as client:
            print("Connection successful! Executing a test query...")
            print("Connection successful! Executing SELECT * FROM hopdong_baohiem...")
            rs = await client.execute("SELECT id, soHopDong, tenCongTy, HLBH_den FROM hopdong_baohiem ORDER BY id")
            
            # Process and print results with proper encoding
            columns = rs.columns
            results = []
            for row in rs.rows:
                values = [v.decode('utf-8') if isinstance(v, bytes) else v for v in row]
                results.append(dict(zip(columns, values)))

            output_filename = "output.txt"
            print(f"--- Writing Results to {output_filename} ---")
            try:
                with open(output_filename, "w", encoding="utf-8") as f:
                    for item in results:
                        f.write(str(item) + "\n")
                print("---------------------")
                print(f"{len(results)} rows written to {output_filename}.")
                print("Test completed successfully. Please check the content of output.txt.")
            except Exception as e:
                print(f"Failed to write to file: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your TURSO_DATABASE_URL and TURSO_AUTH_TOKEN in the .env file.")
        print("2. Check your internet connection and firewall settings.")
        print("3. Ensure the Turso database is running and accessible.")

# --- Run the Test ---
if __name__ == "__main__":
    # This will run the async main function
    asyncio.run(main())
