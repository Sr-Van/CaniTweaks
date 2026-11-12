"""Enums do domínio da aplicação."""
from enum import Enum


class TweakCategory(str, Enum):
    """Categorias usadas para agrupar e filtrar os tweaks."""

    ALL = "Todos"
    LATENCY = "Latência & Vídeo"
    FPS = "Estabilidade de FPS"
    INPUT = "Periféricos"
    RAM_PROCESSES = "RAM & Processos"
    DISK_CLEANUP = "Limpeza de Disco"


class TweakStatus(str, Enum):
    """Estado de um tweak no sistema operacional."""

    INACTIVE = "Inativo"
    ACTIVE = "Ativo"
    PENDING = "Processando..."
    ERROR = "Erro"
    UNKNOWN = "Desconhecido"
    UNSUPPORTED = "Indisponível"


class TweakKind(str, Enum):
    """Define se o tweak é um ajuste reversível ou uma ação pontual."""

    TOGGLE = "toggle"  # Pode ser aplicado e revertido (ex.: chave de registro).
    ACTION = "action"  # Executa uma vez e não tem reversão (ex.: limpeza de disco).


class RiskLevel(str, Enum):
    """Nível de risco percebido de um tweak, exibido ao usuário."""

    LOW = "Baixo"
    MEDIUM = "Moderado"
    HIGH = "Alto"


class OutcomeKind(str, Enum):
    """Resultado de um tweak dentro de uma execução em lote."""

    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"
