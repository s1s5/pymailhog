import asyncio
import pymailhog

try:
    asyncio.run(pymailhog.main())
except KeyboardInterrupt:
    print('stop server')

