import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from alembic import command
from alembic.config import Config


def main():
    config = Config(str(ROOT_DIR / 'alembic.ini'))
    command.upgrade(config, 'head')
    print('Migrações aplicadas com sucesso')


if __name__ == '__main__':
    main()
