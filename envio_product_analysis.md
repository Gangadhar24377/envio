# Envio — Product Analysis & Feature Roadmap

> What the product is, what it should be, and exactly how to get there.

---

## My Honest Take on the Product

**Envio is solving a real problem.** Setting up Python environments — especially for ML with CUDA — is genuinely painful. The AI-powered self-healing angle is novel and marketable. The [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752) command is a killer feature idea that no competitor has.

**But the project has a credibility gap.** The docs describe a product that is more mature than what actually ships. Features are coded but not connected. The vision is excellent; the execution is at ~40%.

**Star potential: High.** If the gap between docs and reality is closed, this could genuinely be a Top-500 Python GitHub project. The space is hot (uv, rye, pixi are trending), and "AI-native" is the right positioning.

---

## 🚨 Docs vs Reality Audit

Your [PROGRESS.md](file:///c:/Users/ganga/Documents/envio/docs/PROGRESS.md) claims features that **don't exist in the actual CLI**:

| Claimed Feature | In Docs? | In Code? | Wired into CLI? |
|----------------|----------|----------|-----------------|
| `envio list` — List all venvs | ✅ PROGRESS.md | ❌ | ❌ |
| `envio activate` — Show activation cmd | ✅ PROGRESS.md | ❌ | ❌ |
| `envio remove` — Remove packages | ✅ PROGRESS.md | ❌ | ❌ |
| Shell injection protection ([sanitize.py](file:///c:/Users/ganga/Documents/envio/src/envio/utils/sanitize.py)) | ✅ PROGRESS.md | ✅ Exists | ❌ Not imported in [cli.py](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py) |
| [find_package_for_import()](file:///c:/Users/ganga/Documents/envio/src/envio/analysis/package_mapping.py#85-128) (package mapping) | ✅ PROGRESS.md | ✅ Exists | ❌ Not used in [init](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#448-543) or [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752) |
| Tenacity retry on LLM calls | ✅ PROGRESS.md | ✅ In [client.py](file:///c:/Users/ganga/Documents/envio/src/envio/llm/client.py) | ✅ Works |
| 78 tests passing | ✅ PROGRESS.md | ⚠️ Test files exist | ❓ Never verified |
| Singleton SystemProfiler | ✅ PROGRESS.md | ❌ Each class creates new | ❌ |
| Semantic version comparison | ✅ PROGRESS.md | ❌ Still string comparison in `cli.py:131` | ❌ |

> [!CAUTION]
> This is the **biggest problem** for open-source credibility. If a contributor reads PROGRESS.md, then looks at the code, they'll lose trust immediately. Either implement the claimed features or remove the claims.

---

## Competitive Landscape

Where envio sits among existing tools:

| Tool | Focus | AI? | Self-Healing? | Hardware-Aware? | Resurrect Old Repos? |
|------|-------|-----|---------------|-----------------|---------------------|
| **pip** | Package installer | ❌ | ❌ | ❌ | ❌ |
| **uv** | Fast pip replacement | ❌ | ❌ | ❌ | ❌ |
| **conda** | Scientific computing | ❌ | ❌ | ❌ | ❌ |
| **poetry** | Dependency management | ❌ | ❌ | ❌ | ❌ |
| **pixi** | Multi-language env mgr | ❌ | ❌ | ❌ | ❌ |
| **rye** | Python project mgr | ❌ | ❌ | ❌ | ❌ |
| **pdm** | PEP 582 support | ❌ | ❌ | ❌ | ❌ |
| **hatch** | Build + env manager | ❌ | ❌ | ❌ | ❌ |
| **envio** | AI-native orchestrator | ✅ | ✅ | ✅ | ✅ |

**Envio's moat**: No other tool combines AI resolution + hardware awareness + legacy repo resurrection. This is a genuine differentiator — but only if the features actually work end-to-end.

---

## Code Exists But Isn't Connected

These modules are built but float in isolation:

| Module | What It Does | Why It's Not Wired In |
|--------|-------------|----------------------|
| [sanitize.py](file:///c:/Users/ganga/Documents/envio/src/envio/utils/sanitize.py) | `shlex.quote()` for package names, path validation | [cli.py](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py) never imports or calls it |
| [package_mapping.py](file:///c:/Users/ganga/Documents/envio/src/envio/analysis/package_mapping.py) | Maps `cv2` → `opencv-python` via PyPI | [init](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#448-543) and [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752) don't use it |
| [command_construction_agent.py](file:///c:/Users/ganga/Documents/envio/src/envio/agents/command_construction_agent.py) | LLM-powered command generation | Never imported anywhere |
| [package_lookup.py](file:///c:/Users/ganga/Documents/envio/src/envio/tools/package_lookup.py) | PyPI/Conda package lookup | Never imported |
| [serper_search.py](file:///c:/Users/ganga/Documents/envio/src/envio/tools/serper_search.py) | Web search tool | `DependencyResolver._search_web()` duplicates this inline |
| Test files (8 files) | Unit tests for analysis, core, LLM, resolution | Never run in CI with `continue-on-error: true` masking failures |

### Impact of Wiring These In

If you just **connected what already exists**, you'd immediately get:
- ✅ Shell injection protection (security)
- ✅ Proper import→package resolution for [init](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#448-543) and [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752)  
- ✅ Test confidence (run and fix the 78 tests)
- ✅ Deduplication of search logic

---

## Feature Proposals — What Would Make This Great

### Tier 1: Wire-and-Ship (1-2 days each, massive impact)

| # | Feature | Why It Matters |
|---|---------|---------------|
| 1 | **Wire [sanitize.py](file:///c:/Users/ganga/Documents/envio/src/envio/utils/sanitize.py) into CLI** | Security — blocks shell injection attacks |
| 2 | **Wire [package_mapping.py](file:///c:/Users/ganga/Documents/envio/src/envio/analysis/package_mapping.py) into [init](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#448-543) and [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752)** | Makes the flagship commands actually work for real repos (`cv2`, `PIL`, `sklearn`) |
| 3 | **Fix and run the existing tests** | Proves the code works; enables CI to catch regressions |
| 4 | **Add `envio list` / `envio remove`** | Basic env management — claimed in docs, users expect it |
| 5 | **Fix the version blocklist** | Use `packaging.version.Version` — it's a 5-line fix |

### Tier 2: High-Impact Features (1-2 weeks each)

| # | Feature | Why It Matters |
|---|---------|---------------|
| 6 | **`--dry-run` flag** | Let users preview without side effects — essential for trust |
| 7 | **`envio lock` — Generate lockfile** | Reproducible environments. Output a `envio.lock` file |
| 8 | **`envio export` — Output formats** | Export as [requirements.txt](file:///c:/Users/ganga/Documents/envio/requirements.txt), [pyproject.toml](file:///c:/Users/ganga/Documents/envio/pyproject.toml), `Dockerfile`, `devcontainer.json` |
| 9 | **Ollama/local LLM support** | LiteLLM already supports it, just needs a `--model` flag and docs |
| 10 | **`envio audit` — Security scanning** | Integrate `pip-audit`. One command vulnerability check |
| 11 | **Interactive confirmation mode** | Show the install plan, ask "Proceed? [Y/n]" before execution |
| 12 | **Apple Silicon / MPS detection** | M-series Macs are everywhere now. Detect and suggest [torch](file:///c:/Users/ganga/Documents/envio/src/envio/core/system_profiler.py#248-269) with MPS |

### Tier 3: Differentiating Features (2-4 weeks each)

| # | Feature | Why It Matters |
|---|---------|---------------|
| 13 | **`envio containerize`** | Generate optimized multi-stage Dockerfiles from environment |
| 14 | **`envio diff env1 env2`** | AI-powered semantic diffing between environments |
| 15 | **GitHub Action** | Auto-analyze PRs that change dependencies |
| 16 | **Environment templates** | `envio create --template ml-pytorch`, `--template web-fastapi` |
| 17 | **`envio doctor --fix`** | Auto-install missing tools (uv, conda) |
| 18 | **Token/cost dashboard** | Track LLM API usage per session |
| 19 | **VS Code extension** | Sidebar panel, right-click "Envio: Create Environment" |
| 20 | **Plugin system** | Let community extend envio with custom resolvers, exporters |

---

## What Makes a Top GitHub Open-Source Project

Based on projects that get 1K+ stars:

### 1. **One-Liner Wow Factor**

People star projects they can try in 30 seconds:

```bash
# This should work TODAY, not after 5 setup steps
pip install envio && envio prompt "pytorch with cuda"
```

Right now, envio requires: clone → install → activate venv → create .env → set API key. That's **5 friction points** before someone can try it. You need:
- Publish to PyPI (`pip install envio`)
- Graceful degradation without API key (use [uv](file:///c:/Users/ganga/Documents/envio/src/envio/resolution/fast_resolver.py#130-165) fast path only)
- A 30-second getting started experience

### 2. **GIFs in README**

The #1 thing that gets stars is a **terminal recording** (using [asciinema](https://asciinema.org/) or [vhs](https://github.com/charmbracelet/vhs)) showing:
- The beautiful Rich TUI in action
- Self-healing fixing a conflict in real-time
- [resurrect](file:///c:/Users/ganga/Documents/envio/src/envio/cli.py#735-752) analyzing an old repo

Your TUI is beautiful. **Show it.**

### 3. **Focused Scope**

Your [ROADMAP.md](file:///c:/Users/ganga/Documents/envio/docs/ROADMAP.md), [IMPROVEMENTS.md](file:///c:/Users/ganga/Documents/envio/docs/IMPROVEMENTS.md), [next_steps.md](file:///c:/Users/ganga/Documents/envio/next_steps.md), [plan.md](file:///c:/Users/ganga/Documents/envio/docs/plan.md), and [PROGRESS.md](file:///c:/Users/ganga/Documents/envio/docs/PROGRESS.md) describe 5 different visions of the same project. That's **5 planning docs with overlapping, contradictory content**. This signals indecision.

Consolidate into ONE doc: [ROADMAP.md](file:///c:/Users/ganga/Documents/envio/docs/ROADMAP.md). Delete the rest.

### 4. **Working Tests in CI**

Remove `continue-on-error: true` from the CI config. If tests fail, fix them. A green CI badge in the README is the #1 trust signal.

### 5. **The "Why Not X?" Section**

Your README needs a section answering: *"Why not just use uv/poetry/conda?"*

The answer is: **Envio doesn't replace uv — it wraps it with intelligence.** uv is the engine, envio is the autopilot. Make this crystal clear.

---

## Documentation Overhaul Needed

| Current Problem | Fix |
|----------------|-----|
| 5 overlapping planning docs | Consolidate into single [ROADMAP.md](file:///c:/Users/ganga/Documents/envio/docs/ROADMAP.md) |
| `yourusername` placeholder in clone URL | Replace with actual GitHub username |
| No GIFs/screenshots | Add terminal recordings |
| No badges | Add CI, PyPI, License, Python version badges |
| No "Why Envio?" section | Add comparison with alternatives |
| No PyPI publication | Publish to PyPI so `pip install envio` works |
| [PROGRESS.md](file:///c:/Users/ganga/Documents/envio/docs/PROGRESS.md) claims unimplemented features | Align with reality or implement |
| No `SECURITY.md` | Add vulnerability reporting policy |
| No issue/PR templates | Add `.github/ISSUE_TEMPLATE/` |
| Internal dev notes in `docs/` | Separate user-facing docs from internal planning |

---

## Suggested 8-Week Sprint Plan

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| **1** | Wire & Fix | Connect [sanitize.py](file:///c:/Users/ganga/Documents/envio/src/envio/utils/sanitize.py), [package_mapping.py](file:///c:/Users/ganga/Documents/envio/src/envio/analysis/package_mapping.py). Fix version blocklist. Delete junk files. Run & fix tests. |
| **2** | CLI Completeness | Add `envio list`, `envio remove`, `--dry-run`. Add interactive confirmation. |
| **3** | Publish & Polish | Publish to PyPI. Record terminal GIFs. Consolidate docs into single ROADMAP. Add README badges. |
| **4** | Local LLM + Offline | Add `--model` flag for Ollama. Graceful offline mode (uv-only path). |
| **5** | Security | Wire `envio audit` (pip-audit integration). Add `SECURITY.md`. |
| **6** | Export & Templates | `envio export dockerfile`. `envio create --template ml-pytorch`. |
| **7** | Apple Silicon + Testing | MPS detection. Expand test coverage to 80%+. Remove `continue-on-error`. |
| **8** | GitHub Action MVP | `envio analyze` for CI. Basic PR bot for dependency changes. |

---

## The Single Most Important Thing to Do Next

> **Wire the existing code together and make it actually work end-to-end.**

You have [sanitize.py](file:///c:/Users/ganga/Documents/envio/src/envio/utils/sanitize.py) but don't use it. You have [package_mapping.py](file:///c:/Users/ganga/Documents/envio/src/envio/analysis/package_mapping.py) but don't use it. You have tests but don't run them. You have docs that describe features that don't exist. 

Close the gap between what's written and what works. That single action will transform this from a promising prototype into a shippable product.
