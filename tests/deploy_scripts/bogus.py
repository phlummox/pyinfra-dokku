"""
a "bogus" deploy script which executes quickly.
"""

from pyinfra              import logger
from pyinfra.operations   import server

logger.info("a bogus, quickly executed ad-hoc command")

server.shell(
    name='Run an ad-hoc command',
    commands='echo "hello world"',
)

