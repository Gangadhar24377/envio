# Next Steps for Envio

## Current Status: Phase 1 Complete ✅

- Week 1: CLI commands (init, prompt, doctor, install)
- Week 2: Rich TUI (timestamps, tables, progress bars)
- Week 3: Polish (RAM detection, --optimize-for, CI workflow)
- Self-Healing: Wired with 3-attempt retry loop

---

## Immediate Fixes (Before Phase 2)

### 1. Conda Support Fix
**Status:** Needs Fix
**Issue:** `conda activate` in subprocess scripts doesn't work
**Solution:** Use `conda run -n {env_name}` instead of `conda activate`
**Files:** `src/envio/core/script_generator.py`

### 2. README Clarity
**Status:** In Progress
**Issue:** Setup instructions unclear for new users
**Solution:** Add separate sections for Installing Envio vs Using Envio
**Files:** `README.md`

---

## Phase 2: Reproducibility Engine

### Feature 1: Ghost-Town Repo Resurrection
**Priority:** High
**Effort:** High
**Impact:** Very High

**What it does:**
```bash
# Scan dead GitHub repos and generate working environment
envio resurrect https://github.com/old/dead-repo
# Or scan local directory
envio resurrect ./old-project
```

**Implementation:**
1. Scan Python files for imports using `ast` module
2. Detect deprecated syntax patterns (infer timeline of codebase)
3. Query PyPI for compatible versions
4. Generate working requirements.txt
5. Create environment with `envio init` under the hood

**Files to Create:**
- `src/envio/commands/resurrect.py`
- `src/envio/analysis/import_analyzer.py`
- `src/envio/analysis/syntax_detector.py`

**Testing:**
```bash
# Test with a known dead repo
envio resurrect https://github.com/huggingface/transformers-old
```

---

### Feature 2: Local LLM (Ollama) Support
**Priority:** Medium
**Effort:** Medium
**Impact:** High

**What it does:**
```bash
# Use local model instead of OpenAI API
envio --model ollama/llama3 prompt "set up pytorch environment"
```

**Implementation:**
1. Add Ollama client to `llm/client.py`
2. Detect if Ollama is running (`ollama list`)
3. Fall back to local if API key not set
4. Support multiple providers (Ollama, llama.cpp, etc.)

**Files to Modify:**
- `src/envio/llm/client.py` - Add Ollama support
- `src/envio/cli.py` - Add `--model` flag

**Testing:**
```bash
# Install Ollama first
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3

# Test with Envio
envio --model ollama/llama3 doctor
```

---

### Feature 3: AI Containerization
**Priority:** Medium
**Effort:** High
**Impact:** High

**What it does:**
```bash
# Generate optimized Dockerfile
envio containerize --base python:3.11-slim
```

**Implementation:**
1. Analyze environment dependencies
2. Generate multi-stage Dockerfile
3. Optimize layer caching
4. Include only required system dependencies

**Files to Create:**
- `src/envio/commands/containerize.py`
- `src/envio/container/dockerfile_generator.py`

**Testing:**
```bash
# Create environment
envio init

# Generate Dockerfile
envio containerize --output Dockerfile

# Build and run
docker build -t my-app .
docker run my-app
```

---

### Feature 4: Semantic Environment Diffing
**Priority:** Low
**Effort:** Medium
**Impact:** Medium

**What it does:**
```bash
# Compare environments and explain changes
envio diff env1 env2
```

**Implementation:**
1. Parse requirements from both environments
2. Compare versions and dependencies
3. Use AI to explain changes in plain English
4. Show breaking changes and migration steps

**Files to Create:**
- `src/envio/commands/diff.py`
- `src/envio/analysis/environment_differ.py`

**Testing:**
```bash
# Create two environments
envio init --name env1
envio install requests flask --name env2

# Compare
envio diff env1 env2
```

---

## Phase 3: Team & Enterprise Workflows

### Feature 1: GitHub Action (CI Guardian)
**Priority:** High (after Phase 2)
**Effort:** High
**Impact:** Very High

**What it does:**
- Analyzes PRs that modify dependencies
- Tests resolution without installing
- Calculates "bloat score"
- Comments on PR with suggestions

**Implementation:**
1. Create GitHub Action Docker container
2. Add `envio analyze` command for CI
3. Add bloat score calculation
4. Create action.yml for GitHub Marketplace

**Testing:**
```yaml
# .github/workflows/envio.yml
- uses: your-org/envio-action@v1
  with:
    api-key: ${{ secrets.OPENAI_API_KEY }}
```

---

### Feature 2: CVE Security Profiling
**Priority:** Medium
**Effort:** High
**Impact:** High

**What it does:**
```bash
# Scan for vulnerabilities
envio audit --severity critical
```

**Implementation:**
1. Query OSV database (https://osv.dev)
2. Query GitHub Advisory Database
3. Cross-reference with installed packages
4. Report CVEs with severity and fix versions

**Files to Create:**
- `src/envio/commands/audit.py`
- `src/envio/security/cve_scanner.py`
- `src/envio/security/vulnerability_db.py`

**Testing:**
```bash
# Install vulnerable package
envio install requests==2.25.0

# Scan for CVEs
envio audit
```

---

### Feature 3: Cost Estimation
**Priority:** Low
**Effort:** Medium
**Impact:** Medium

**What it does:**
```bash
# Estimate cloud compute costs
envio cost --provider aws --region us-east-1
```

**Implementation:**
1. Map packages to compute requirements
2. Query cloud pricing APIs
3. Estimate monthly costs based on workload
4. Compare providers (AWS, GCP, Azure)

**Files to Create:**
- `src/envio/commands/cost.py`
- `src/envio/pricing/cloud_estimator.py`

**Testing:**
```bash
# Estimate costs for ML environment
envio install torch transformers
envio cost --provider aws
```

---

## Documentation Tasks

### Update README.md
- [x] Add prerequisites section
- [x] Add troubleshooting section
- [x] Add GitHub Actions secret setup
- [ ] Add "Installing Envio" vs "Using Envio" separation
- [ ] Add `.env` file creation steps
- [ ] Add FAQ section

### Update docs/PROGRESS.md
- [ ] Add Phase 1 completion summary
- [ ] Add Phase 2 progress tracking
- [ ] Add Phase 3 planning

### Create CONTRIBUTING.md
- [ ] Code style guide
- [ ] Testing instructions
- [ ] Pull request template

---

## CI/CD Tasks

### GitHub Actions Workflow
- [x] Basic linting and testing
- [ ] Add coverage reporting
- [ ] Add deployment pipeline
- [ ] Add changelog generation

### Pre-commit Hooks
- [x] Ruff linting
- [x] Ruff formatting
- [ ] MyPy type checking (enabled but may have errors)
- [ ] Security scanning

---

## Testing Strategy

### Unit Tests
- [ ] Test each agent independently
- [ ] Test FastResolver with known conflicts
- [ ] Test SelfHealingLoop with mock errors

### Integration Tests
- [ ] Test full CLI flow (init → install → activate)
- [ ] Test with real packages
- [ ] Test on multiple platforms (Windows, Linux, macOS)

### Performance Tests
- [ ] Benchmark resolution speed (uv vs pip)
- [ ] Measure AI healing latency
- [ ] Test with 100+ packages

---

## Prioritization Matrix

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Conda Fix | Low | Medium | **Now** |
| Ghost-Town | High | Very High | **Next** |
| Local LLM | Medium | High | **Next** |
| GitHub Action | High | Very High | **After Phase 2** |
| CVE Audit | High | High | **After Phase 2** |
| Containerization | High | High | **Phase 2** |
| Cost Estimation | Medium | Medium | **Phase 3** |

---

*Last Updated: March 24, 2026*
