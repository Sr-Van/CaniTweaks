"""Enums do domínio da aplicação."""
from enum import Enum


class TweakCategory(str, Enum):
    ALL = "Todos"
    LATENCY = "Latência & Vídeo"
    FPS = "Estabilidade de FPS"
    RAM_PROCESSES = "Uso de RAM & Processos"
    DISK_CLEANUP = "Limpeza de Disco"


class TweakStatus(str, Enum):
    INACTIVE = "Inativo"
    ACTIVE = "Ativo"
    PENDING = "Processando..."
    ERROR = "Erro"
