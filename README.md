# ⚡ WinTweaks - Gaming & Performance Optimizer

Utilitário desktop para otimizar o Windows 10/11 (64-bit) focado em jogos e baixa latência, escrito em
Python com interface CustomTkinter e **Clean Architecture (Ports & Adapters)**.

> ⚠️ **Use por sua conta e risco.** Todos os ajustes são reversíveis e o app cria um ponto de
> restauração antes de aplicar em lote, mas alterar configurações do sistema sempre carrega algum risco.

## Recursos

- **21 otimizações reais** (registro, serviços, planos de energia e limpeza de disco) em 5 categorias.
- **Reversão fiel**: o estado original de cada valor é salvo antes de aplicar e restaurado ao reverter.
- **Aplicação atômica**: se uma etapa falha, as anteriores do mesmo tweak são desfeitas.
- **Ponto de restauração** automático antes de lotes e **presets** com aplicação/reversão em um clique.
- Detecção do estado real, busca, filtro por categoria, progresso com cancelamento e relatório de resultados.
- Aviso de reinício pendente (com cancelamento), banner de administrador e exportação de relatório `.txt`.
- Tweaks incompatíveis com a versão do Windows ficam marcados como *Indisponível*.

## Catálogo

| Categoria | Tweaks |
| :-- | :-- |
| Latência & Vídeo | HAGS, desativar FSO, network throttling, algoritmo de Nagle, ASPM do PCIe, resolução de timer global (Win 11) |
| Estabilidade de FPS | Game Mode, power throttling, plano Desempenho Máximo, inicialização rápida |
| Periféricos | Aceleração do mouse, atalhos de teclas de aderência, suspensão seletiva de USB |
| RAM & Processos | Telemetria (DiagTrack), Game DVR, apps patrocinados, apps em segundo plano, pesquisa na web do Menu Iniciar |
| Limpeza de Disco | Temporários, Prefetch/WER/dumps, cache de shaders (ações pontuais, mostram o espaço liberado) |

Presets: **Competitivo**, **Equilibrado**, **Privacidade & Segundo Plano** e **Limpeza Rápida**.

## Como executar

```bash
pip install -r requirements.txt
python run.py
```

O app pede elevação (UAC) ao abrir. Sem administrador, ajustes em `HKLM`, serviços e energia falham com
mensagem clara; os demais continuam funcionando.

Logs e backups ficam em `%LOCALAPPDATA%\WinTweaks` (`wintweaks.log` e `state_backup.json`).

## Testes

```bash
python -m unittest discover -s tests -t .
```

Os testes usam dublês do sistema (registro, serviços, powercfg), exceto um teste de integração que
grava e remove uma chave descartável em `HKCU\Software\WinTweaksTests`.

## Arquitetura

```text
app/
├── domain/      Entidades imutáveis (Tweak, Preset), enums, Result, BatchReport e presets padrão
├── ports/       Contratos: TweakPort, RestorePointPort, SystemPort
├── use_cases/   TweakManager, BatchRunner, PresetsManager, SystemService, status_report
├── adapters/    Implementações para Windows
│   ├── operations/   Operações atômicas reversíveis (registro, serviço, energia, limpeza)
│   ├── catalog/      Catálogo declarativo dos tweaks, um módulo por categoria
│   └── catalog_tweak_adapter.py   TweakPort: backup, rollback, aplicar/reverter/verificar
├── ui/          CustomTkinter: janela, views, componentes e executor de tarefas em segundo plano
└── bootstrap.py Raiz de composição (injeção de dependências e logging)
```

Regras de dependência: `ui → use_cases → ports ← adapters`, com `domain` no centro sem depender de nada.
A interface nunca toca o sistema diretamente e threads de trabalho nunca tocam widgets
(retorno pela fila do `UiTaskRunner`).

### Adicionar um novo tweak

1. Declare o `Tweak` (metadados) e suas operações em um módulo de `app/adapters/catalog/`:
   `ctx.reg(...)` para registro, `DisableServiceOperation`, `PowerSettingOperation` ou uma `ActionOperation`.
2. (Opcional) Inclua o `id` em um preset de `app/domain/presets.py`.
3. Os testes de integridade do catálogo e o teste de ida e volta (aplicar → verificar → reverter) o cobrem
   automaticamente.
