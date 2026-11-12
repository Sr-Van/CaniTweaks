"""Execução de trabalho em segundo plano com retorno seguro para a thread da interface."""
import logging
import queue
import threading
import tkinter
from typing import Any, Callable, List, Optional

logger = logging.getLogger(__name__)

_POLL_INTERVAL_MS = 40


class UiTaskRunner:
    """Roda funções em threads e entrega os resultados na thread principal do Tk.

    Widgets do Tk não são thread-safe: threads de trabalho nunca tocam na interface,
    apenas enfileiram callbacks que são executados aqui, na thread principal.

    Também controla o estado "ocupado" global, impedindo operações concorrentes sobre o sistema.
    """

    def __init__(self, root: tkinter.Misc):
        self._root = root
        self._callbacks: "queue.Queue[Callable[[], None]]" = queue.Queue()
        self._busy = False
        self._busy_listeners: List[Callable[[bool], None]] = []
        self._pump()

    @property
    def is_busy(self) -> bool:
        return self._busy

    def subscribe_busy(self, listener: Callable[[bool], None]) -> None:
        """Registra um callback chamado sempre que o estado ocupado mudar."""
        self._busy_listeners.append(listener)

    def post(self, callback: Callable[[], None]) -> None:
        """Agenda `callback` para rodar na thread da interface (seguro de qualquer thread)."""
        self._callbacks.put(callback)

    def run(
        self,
        work: Callable[[], Any],
        on_done: Callable[[Any], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Executa `work` em segundo plano sem bloquear nem reservar o estado ocupado."""
        def target():
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - repassa qualquer falha à interface
                logger.exception("Erro em tarefa em segundo plano")
                self.post(lambda: self._deliver_error(on_error, exc))
            else:
                self.post(lambda: on_done(result))

        threading.Thread(target=target, daemon=True).start()

    def run_exclusive(
        self,
        work: Callable[[], Any],
        on_done: Callable[[Any], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> bool:
        """Como `run`, mas só inicia se nada estiver em execução. Retorna False se estava ocupado."""
        if self._busy:
            return False
        self._set_busy(True)

        def finish(result: Any) -> None:
            self._set_busy(False)
            on_done(result)

        def fail(exc: Exception) -> None:
            self._set_busy(False)
            self._deliver_error(on_error, exc)

        self.run(work, finish, fail)
        return True

    @staticmethod
    def _deliver_error(handler: Optional[Callable[[Exception], None]], exc: Exception) -> None:
        if handler:
            handler(exc)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for listener in self._busy_listeners:
            listener(busy)

    def _pump(self) -> None:
        """Executa os callbacks pendentes e se reagenda enquanto a janela existir."""
        try:
            while True:
                self._callbacks.get_nowait()()
        except queue.Empty:
            pass
        try:
            self._root.after(_POLL_INTERVAL_MS, self._pump)
        except tkinter.TclError:
            pass  # Janela encerrada.
