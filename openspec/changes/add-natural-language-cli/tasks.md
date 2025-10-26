## 1. Intent Modeling
- [ ] 1.1 Define Pydantic schemas for supported intents (import, report, posting, rule creation, transaction listing)
- [ ] 1.2 Implement validation and normalization steps for parsed parameters

## 2. Parsing Pipeline
- [ ] 2.1 Integrate Pydantic AI orchestrator with provider abstraction (local llama.cpp, OpenAI, Anthropic)
- [ ] 2.2 Implement regex/grammar fallback for common intents without LLM usage
- [ ] 2.3 Add safety filters and confirmation prompts for destructive actions

## 3. CLI Command
- [ ] 3.1 Add `fin ask "<instruction>"` command with preview output and `--explain` flag
- [ ] 3.2 Support dry-run preview before executing actions, requiring explicit confirmation
- [ ] 3.3 Log resolved intents and executions via structured logging

## 4. Quality
- [ ] 4.1 Unit tests for intent parsing and validation
- [ ] 4.2 Integration tests simulating `fin ask` flows across providers/fallbacks
- [ ] 4.3 Documentation covering configuration, supported intents, and safety guidelines
