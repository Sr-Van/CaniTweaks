"""Script facilitador para rodar a aplicação a partir da raiz."""
import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import main

if __name__ == "__main__":
    main()
