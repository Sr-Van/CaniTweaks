# Contexto do Projeto: Windows PC Tweaks (Gaming & Performance)

> **Documento de Especificação Arquitetural e Funcional**  
> Consolidado através do processo de `/brainstorming` com aplicação de **Clean Architecture (Ports & Adapters)**.

---

## 1. Visão Geral e Propósito

O **Windows PC Tweaks** é um utilitário desktop moderno, leve, rápido e portátil para Windows 10 e Windows 11 (64-bit). Seu objetivo é otimizar as configurações do sistema operacional voltadas para **jogos (especialmente jogos competitivos/FPS)** e responsividade geral da máquina, sem recorrer a práticas nocivas ("snake oil"), sem quebrar o Windows Update e sem risco de banimento por sistemas anti-cheat (como Riot Vanguard, Easy Anti-Cheat ou BattlEye).

O aplicativo é desenvolvido em **Python 3.11+**, utiliza interface gráfica em **CustomTkinter** (tema escuro estilo Fluent/Windows 11) e é distribuído como um executável autônomo (`.exe`) portátil, dispensando instalação do Python na máquina do usuário final.

---

## 2. Decision Log (Brainstorming Consolidado)

| ID | Tópico | Decisão Tomada | Justificativa Técnica |
| :--- | :--- | :--- | :--- |
| **DEC-01** | **Segurança & Reversibilidade** | Reversão individual + Ponto de Restauração automático | Protege a integridade do Windows contra falhas e permite que o usuário desfaça qualquer ajuste individualmente ou reverta todo o sistema. |
| **DEC-02** | **Stack Tecnológica** | Python 3 + CustomTkinter + módulos nativos Win32 | Atende à preferência por Python; interface nativa leve e moderna; acesso direto a `winreg`, `ctypes` e `subprocess`; packaging via PyInstaller com manifest UAC. |
| **DEC-03** | **Estrutura da GUI** | Menu Lateral com 2 abas ("Otimizações" e "Presets") | Garante visual limpo; permite filtrar tweaks por categoria na aba principal e oferece perfis de 1 clique na aba de presets. |
| **DEC-04** | **Execução & Feedback** | Multithreading assíncrono + Barra de Progresso + Diálogo de Reinício | Impede travamento ("congelamento") da interface gráfica durante operações demoradas de disco/registro e notifica se um tweak necessita de reinicialização. |

---

## 3. Escopo e Não-Objetivos

### Escopo Incluído (In-Scope)
- Elevação automática de privilégios de Administrador (UAC) na inicialização.
- Criação de Ponto de Restauração do Windows via WMI / PowerShell antes de operações em lote.
- Detecção dinâmica do estado de cada tweak (Ativo / Inativo / Desconhecido).
- Aplicação e Reversão atômica para cada tweak individual.
- Botão "Aplicar Todos" que processa todos os tweaks ativos ou filtrados.
- Presets prontos para aplicação rápida de perfis pré-configurados.
- Limpeza segura de arquivos temporários e caches com exibição do espaço liberado.

### Não-Objetivos Explícitos (Out-of-Scope)
- **NÃO** desativar componentes críticos: Windows Update, Windows Defender ou drivers de áudio/rede/Bluetooth.
- **NÃO** modificar arquivos de jogos protegidos ou injetar DLLs na memória (zero risco anti-cheat).
- **NÃO** aplicar modificações de registro arriscadas ou não documentadas.
- **NÃO** realizar overclock de hardware ou controle de ventoinhas.

---

## 4. Catálogo Curado de Tweaks & Categorias Reais

Cada ajuste foi validado contra a documentação do Windows e os melhores projetos open-source (Optimizer, Chris Titus WinUtil, AtlasOS):

### Categoria: `LATÊNCIA / INPUT LAG`
1. **Hardware-Accelerated GPU Scheduling (HAGS)**
   - *Impacto*: Reduz a latência de comunicação entre CPU e GPU na fila de quadros.
   - *Mecanismo*: Registro `HKLM\SYSTEM\CurrentControlSet\Control\GraphicsDrivers` (`HwSchMode = 2`).
   - *Exige Reinício*: Sim.
2. **Desativar Otimizações de Tela Inteira Globais (Disable FSO)**
   - *Impacto*: Reduz o input lag de sobreposição do DWM em jogos executados em tela cheia exclusiva.
   - *Mecanismo*: Registro `HKCU\System\GameConfigStore` (`GameDVR_FSEBehavior = 2`, `GameDVR_FSEBehaviorMode = 2`).
   - *Exige Reinício*: Não (ou relog).
3. **Desativação do Algoritmo de Nagle (Network Throttling)**
   - *Impacto*: Desativa a agregação de pacotes TCP e o limitador de rede multimídia, reduzindo picos de ping/latência em jogos online.
   - *Mecanismo*: `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile` (`NetworkThrottlingIndex = 0xFFFFFFFF`, `SystemResponsiveness = 0`).
   - *Exige Reinício*: Sim.

### Categoria: `ESTABILIDADE DE FPS & 1% LOWS`
4. **Habilitar Windows Game Mode**
   - *Impacto*: Aloca prioridade de threads de CPU e GPU para o processo do jogo em execução, evitando que tarefas em segundo plano roubem ciclos de clock.
   - *Mecanismo*: `HKCU\Software\Microsoft\GameBar` (`AutoGameModeEnabled = 1`).
   - *Exige Reinício*: Não.
5. **Desativar Power Throttling de CPU**
   - *Impacto*: Impede que o agendador do Windows limite artificialmente threads de segundo plano ou jogos para economizar energia.
   - *Mecanismo*: `HKLM\SYSTEM\CurrentControlSet\Control\Power\PowerThrottling` (`PowerThrottlingOff = 1`).
   - *Exige Reinício*: Sim.
6. **Ativar Plano de Energia "Desempenho Máximo" (Ultimate Performance)**
   - *Impacto*: Reduz micro-travamentos (1% lows) mantendo os núcleos do processador sempre em estado de alta prontidão (C-States / P-States mínimos).
   - *Mecanismo*: Execução de `powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61` e ativação via GUID.
   - *Exige Reinício*: Não.

### Categoria: `USO DE RAM & PROCESSOS`
7. **Desativar Telemetria e Diagnósticos em Segundo Plano (DiagTrack)**
   - *Impacto*: Libera de 150MB a 350MB de RAM e reduz I/O de disco causado por coleta periódica de logs da Microsoft.
   - *Mecanismo*: Desativação e parada dos serviços `DiagTrack` e `dmwappushservice`.
   - *Exige Reinício*: Não.
8. **Desativar Xbox Game DVR / Captura em Segundo Plano**
   - *Impacto*: Desliga a gravação contínua em buffer de RAM/disco que consome recursos de GPU e memória mesmo quando não solicitada.
   - *Mecanismo*: `HKCU\System\GameConfigStore` (`GameDVR_Enabled = 0`) e `HKLM\SOFTWARE\Policies\Microsoft\Windows\GameDVR` (`AllowGameDVR = 0`).
   - *Exige Reinício*: Não.
9. **Desativar Sugestões e Apps Patrocinados Automáticos**
   - *Impacto*: Impede o download silencioso de bloatwares da Windows Store em segundo plano.
   - *Mecanismo*: `HKCU\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager` (`SilentInstalledAppsEnabled = 0`, `SystemPaneSuggestionsEnabled = 0`).
   - *Exige Reinício*: Não.

### Categoria: `LIMPEZA DE DISCO & CACHE`
10. **Limpeza de Arquivos Temporários do Usuário e do Sistema**
    - *Impacto*: Libera gigabytes de espaço em disco e remove arquivos obsoletos de compiladores/jogos em `%TEMP%` e `C:\Windows\Temp`.
    - *Mecanismo*: Remoção segura com tratamento de exceções para arquivos em uso.
11. **Limpeza de Cache de Pré-busca (Prefetch) e Logs de Erro**
    - *Impacto*: Reduz a fragmentação e tamanho da pasta `Prefetch` e esvazia relatórios acumulados do Windows Error Reporting (`WER`).
    - *Mecanismo*: Limpeza da pasta `C:\Windows\Prefetch` e `C:\ProgramData\Microsoft\Windows\WER`.

---

## 5. Presets Definidos

1. **Preset 1: "Competitivo / FPS Máximo"**
   - *Foco*: Máxima estabilidade de quadros e menor latência.
   - *Tweaks Ativados*: HAGS, Disable FSO, Network Throttling, Game Mode, Desativar Power Throttling, Desempenho Máximo, Desativar Game DVR.
2. **Preset 2: "Equilibrado (Gamer & Uso Geral)"**
   - *Foco*: Ganho perceptível de fluidez preservando todos os efeitos visuais e serviços multimídia do Windows.
   - *Tweaks Ativados*: Game Mode, Desempenho Máximo, Desativar Telemetria, Desativar Bloatware Automático.
3. **Preset 3: "Limpeza Rápida de Disco"**
   - *Foco*: Liberação imediata de armazenamento sem alterar configurações de registro do sistema.
   - *Tweaks Ativados*: Limpeza de Pastas Temporárias, Limpeza de Prefetch & Crash Dumps.

---

## 6. Arquitetura de Software (Clean Architecture / Ports & Adapters)

O sistema segue os princípios de separação estrita de responsabilidades: o **Domínio** e os **Casos de Uso** não sabem nada sobre a interface gráfica (CustomTkinter) nem dependem diretamente de chamadas de baixo nível, permitindo testes unitários e modularidade.

```
                              ┌────────────────────────────────────────┐
                              │           PRESENTATION (UI)            │
                              │     CustomTkinter / Threading Worker   │
                              └───────────────────┬────────────────────┘
                                                  │
                                                  ▼
                              ┌────────────────────────────────────────┐
                              │            USE CASES (APP)             │
                              │  - ApplyTweakUseCase                   │
                              │  - RevertTweakUseCase                  │
                              │  - BatchApplyUseCase (Progress/Status) │
                              │  - ApplyPresetUseCase                  │
                              └───────┬────────────────────────┬───────┘
                                      │                        │
                    ┌─────────────────▼─────────┐   ┌──────────▼─────────────────┐
                    │       DOMAIN LAYER        │   │        PORTS (INTERFACES)  │
                    │ - Entity: Tweak           │   │ - TweakActionPort          │
                    │ - Entity: Preset          │   │ - SystemRestorePort        │
                    │ - Enums: Category, Status │   │ - WindowsEnvironmentPort   │
                    └───────────────────────────┘   └──────────┬─────────────────┘
                                                               │
                                      ┌────────────────────────┴───────────────┐
                                      │                                        │
                                      ▼                                        ▼
                       ┌─────────────────────────────┐         ┌──────────────────────────────┐
                       │   ADAPTERS (REGISTRY/SYS)   │         │    ADAPTERS (WMI/SERVICES)   │
                       │ - WindowsRegistryAdapter    │         │ - WindowsServiceAdapter      │
                       │ - DiskCleanAdapter          │         │ - SystemRestoreAdapter       │
                       └─────────────────────────────┘         └──────────────────────────────┘
```

### Estrutura de Diretórios Recomendada

```text
pc-tweaks/
├── context.md                    # Especificação e arquitetura do projeto
├── README.md                     # Instruções de execução e build
├── requirements.txt              # Dependências (customtkinter, pillow, pyinstaller)
├── build.py                      # Script de compilação em .exe (PyInstaller)
├── app/
│   ├── __init__.py
│   ├── main.py                   # Ponto de entrada (validação de UAC e inicialização da UI)
│   ├── domain/                   # Camada de Entidades e Regras de Negócio Puras
│   │   ├── __init__.py
│   │   ├── entities.py           # Classes Tweak, Preset
│   │   └── enums.py              # TweakCategory, TweakStatus, RiskLevel
│   ├── ports/                    # Interfaces abstratas (Contratos)
│   │   ├── __init__.py
│   │   ├── tweak_port.py         # Interface de ação (apply, revert, is_applied)
│   │   └── restore_port.py       # Interface de criação de Ponto de Restauração
│   ├── use_cases/                # Casos de Uso da Aplicação
│   │   ├── __init__.py
│   │   ├── tweak_manager.py      # Coordena catálogo, detecção e execução
│   │   ├── apply_batch.py        # Aplicação em lote com callbacks de progresso
│   │   └── presets_manager.py    # Gerencia aplicação dos perfis
│   ├── adapters/                 # Implementações concretas de Sistema Operacional
│   │   ├── __init__.py
│   │   ├── registry_adapter.py   # Manipulação segura de winreg (HKLM / HKCU)
│   │   ├── services_adapter.py   # Controle de serviços via sc.exe / subprocess
│   │   ├── restore_adapter.py    # Ponto de restauração via WMI / PowerShell
│   │   ├── disk_clean_adapter.py # Limpeza de arquivos temporários e contagem de bytes
│   │   └── tweaks_catalog.py     # Definição e registro de todos os tweaks suportados
│   └── ui/                       # Apresentação gráfica (CustomTkinter)
│       ├── __init__.py
│       ├── app_window.py         # Janela principal e controle de abas
│       ├── views/
│       │   ├── tweaks_view.py    # Lista de tweaks, filtros e "Aplicar Todos"
│       │   └── presets_view.py   # Cards dos perfis pré-definidos
│       └── components/
│           ├── tweak_card.py     # Card individual com tag, status e botão
│           └── progress_modal.py # Diálogo de progresso não-bloqueante
```

---

## 7. Requisitos Não-Funcionais & Empacotamento

1. **Privilégios de Administrador (UAC Elevation)**:
   - O `main.py` utiliza `ctypes.windll.shell32.IsUserAnAdmin()`. Caso não esteja elevado, reinicia o processo solicitando elevação através de `ShellExecuteEx` com o verbo `runas`.
2. **Proteção e atomicidade**:
   - Falhas individuais na escrita de chaves de registro não abortam a execução geral; erros são capturados e reportados no status do card.
3. **Distribuição em Executável (`.exe`)**:
   - Compilação via **PyInstaller** configurado com:
     - `--onedir` ou `--onefile` (recomendado `--onefile` com manifest `requireAdministrator`).
     - `--noupx` para evitar alertas heurísticos de packers no Windows Defender.
     - Ícone personalizado e metadados de versão preenchidos para aumentar a reputação do binário.

---

## 8. Plano de Implementação (Roadmap)

- **Fase 1: Núcleo de Domínio, Ports e Adapters de Baixo Nível**
  - Criação das entidades, enums e contratos de ports.
  - Implementação do `WindowsRegistryAdapter`, `ServicesAdapter`, `DiskCleanAdapter` e `SystemRestoreAdapter`.
  - Implementação do catálogo com os 11 tweaks curados e suas regras de reversão.
- **Fase 2: Camada de Casos de Uso e Gestão de Estado**
  - Implementação do `TweakManager` (leitura de status em tempo real).
  - Implementação do `BatchApplyUseCase` com suporte a callbacks de progresso para a UI.
  - Implementação da lógica de perfis no `PresetsManager`.
- **Fase 3: Interface Gráfica Moderna (CustomTkinter)**
  - Construção da janela principal com tema escuro e menu lateral.
  - Desenvolvimento dos cards com tags de categoria coloridas e botão Aplicar/Reverter.
  - Integração assíncrona com `threading.Thread` para garantir 100% de fluidez.
  - Implementação da aba de Presets e do diálogo de conclusão/reinicialização.
- **Fase 4: Empacotamento e Testes**
  - Criação do script de build automatizado (`build.py`).
  - Testes em ambiente limpo de Windows 10/11.
  - Geração do executável final testado e documentado.
