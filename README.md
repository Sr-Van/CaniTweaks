# ⚡ WinTweaks - Gaming & Performance Optimizer

Utilitário desktop moderno para otimização do Windows focado em jogos e redução de latência, desenvolvido em Python com interface CustomTkinter seguindo **Clean Architecture**.

---

## 🚀 Como Executar a Demonstração (Preview)

Certifique-se de que os pacotes necessários estejam instalados:

```bash
pip install -r requirements.txt
```

Para iniciar a janela da aplicação:

```bash
python run.py
```

---

## 📁 Estrutura de Arquitetura

O projeto foi organizado em camadas desacopladas:

- **`app/domain/`**: Entidades puras (`Tweak`, `Preset`) e Enums (`TweakCategory`, `TweakStatus`).
- **`app/ports/`**: Contratos/Interfaces abstratas (`TweakPort`).
- **`app/adapters/`**: Implementações de baixo nível (atualmente `FakeTweakAdapter` com catálogo demonstrativo).
- **`app/use_cases/`**: Orquestração das regras de negócio (`TweakManager`, `PresetsManager`).
- **`app/ui/`**: Interface CustomTkinter moderna com suporte a modo escuro, filtros e multithreading.
