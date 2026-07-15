import asyncio
import asyncpg
import socket

async def test():
    # Check what IP localhost resolves to
    print("localhost resolves to:", socket.getaddrinfo('localhost', 5432, socket.AF_UNSPEC, socket.SOCK_STREAM))

    tests = [
        ('127.0.0.1 explicit', {'user': 'ielts', 'password': 'ielts_secret', 'host': '127.0.0.1', 'port': 5432, 'database': 'ieltsdb'}),
        ('::1 explicit', {'user': 'ielts', 'password': 'ielts_secret', 'host': '::1', 'port': 5432, 'database': 'ieltsdb'}),
        ('localhost', {'user': 'ielts', 'password': 'ielts_secret', 'host': 'localhost', 'port': 5432, 'database': 'ieltsdb'}),
        ('no password 127.0.0.1', {'user': 'ielts', 'host': '127.0.0.1', 'port': 5432, 'database': 'ieltsdb'}),
    ]
    for label, kwargs in tests:
        try:
            conn = await asyncpg.connect(**kwargs)
            r = await conn.fetchval('SELECT 1')
            print(f'OK [{label}]:', r)
            await conn.close()
        except Exception as e:
            print(f'FAIL [{label}]:', type(e).__name__, str(e)[:120])

asyncio.run(test())
