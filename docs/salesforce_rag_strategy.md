# Salesforce Data Interpretation Strategy using Retrieval-Augmented Generation (RAG)

## 1. Problem Statement
Sara's outreach data for the last six months contains **~126 000 tokens**. This exceeds the context window of even the largest commercially available LLMs (typically 8k–200k tokens). We need a strategy that enables:

1. Efficient retrieval of relevant slices of data at inference time.
2. Accurate, traceable summarisation and interpretation.
3. Low-latency, cost-effective operation for analysts and downstream automation.

## 2. Key Constraints & Requirements

| Category | Requirement |
|----------|-------------|
| Data Volume | 126 k tokens per user, likely to grow. |
| Source Systems | Salesforce (accounts, contacts, activities), Outreach logs, internal notes. |
| Traceability | Show provenance ("why did you answer?" links to raw rows). |
| Security | PHI/PII considerations ⇒ need field-level filtering + row-level auth. |
| Deployment | Existing infra uses Supabase PG, Celery workers, Langfuse tracing. |
| SDKs | Prefer Python; potential use of MCP (Modular Command Pattern) server architecture. |

## 3. Retrieval-Augmented Generation Overview
RAG pipelines add **retrieval** in front of the LLM so only the *most relevant* chunks are injected. Typical components:

1. **Chunker** – splits raw documents into tokens (e.g. 512-1 024 tokens) with overlap.
2. **Embedding Store** – vector DB (Supabase pgvector, Weaviate, Pinecone).
3. **Retriever** – similarity search, hybrid BM25 + vector, metadata filters.
4. **Prompt Builder** – crafts context window with instructions + retrieved chunks.
5. **Generation** – LLM produces answer.

### 3.1 Variants
* **Standard RAG** – single similarity search → single prompt.
* **Hierarchical / Multi-step RAG** – coarse retrieval → refine → final answer (reduces hallucination).
* **Hybrid RAG** – combine sparse (keyword/BM25) and dense (vector) scores.
* **Agentic RAG** – agent iteratively issues search queries & reasoning steps (chain-of-thought outside LLM context).
* **Chunk-graph RAG** – link chunks by entity, chronology, CRM object relationships.

## 4. Options Analysis

| Option | Pros | Cons | Recommended Use |
|--------|------|------|-----------------|
| **Pure RAG Pipeline** (single-pass) | Simple to implement; fast. | Lower reasoning depth; risk of missing edge cases; prompt size spikes. | Quick POC, FAQ bots. |
| **Hierarchical / Map-Reduce Summarisation** | Compresses large sets into hierarchical summaries; mitigates context limits. | Adds compute cost; summary drift possible. | Monthly reports, high-level dashboards. |
| **Hybrid RAG (BM25+Vector)** | Better recall on rare tokens (IDs, abbreviations). | Infrastructure complexity. | CRM data with many unique IDs. |
| **Agentic Workflow** (task-oriented tools) | Complex reasoning; can branch into sub-tasks; supports tool invocation (SQL, API). | Longer latency; agent reliability challenges; needs orchestration layer. | Investigative analysis, KPI deep-dives. |
| **Chatbot-style Recursive Agent** | Natural conversation; incremental context. | Conversation memory management tricky; session state persistence needed. | End-user Q&A support. |
| **MCP Server (Tooling Micro-service)** | Decouples retrieval logic; reusable by many agents/bots. | Extra DevOps surface area. | Organisation-wide retrieval backend. |

## 5. Proposed Architecture
```
┌─────────────────┐   ingest   ┌──────────────┐  embed  ┌───────────────┐
│ Salesforce ETL  │──────────▶│ Chunker      │────────▶│ Vector Store  │
└─────────────────┘            │ + Metadata   │         │ (pgvector)    │
                              └──────────────┘         └───────────────┘
                                     ▲                        │
                                     │ retrieve               │
                                     │                        ▼
                              ┌──────────────┐  ranked   ┌───────────────┐
                              │ Retriever    │──────────▶│ Prompt Builder│
                              │ (hybrid)     │           └───────────────┘
                              └──────────────┘                 │
                                     ▲                        │
                                     │ tools / SQL            │
                     agent plan      │                        ▼
     ┌──────────────┐───────────────▶│  Agent Executor  │
     │ User / Cron  │                │  (LangChain,     │
     └──────────────┘◀───────────────│   CrewAI, etc.)  │
                                     └───────────────┬─┘
                                                     ▼
                                             LLM (OpenAI/Claude)
```

### 5.1 Key Design Decisions
1. **pgvector in Supabase** – Leverage current Postgres; one less service.
2. **Hybrid Retriever** – pgvector + `pg_trgm`/`tsvector` for keyword recall.
3. **Metadata-Aware Filters** – e.g., `WHERE owner = 'Sara' AND date > NOW() - 180d`.
4. **Agent Toolkit** – expose SQL, summarise, drill-down tools.
5. **Langfuse Tracing** – already integrated; retain for observability.

## 6. RAG Techniques Catalogue

### 6.1 Chunking Strategies
* **Fixed-size tokens** (512/1 024) with 15-20 % overlap.
* **Semantic chunking** by email thread, CRM activity, task.
* **Entity-centric**: group by `LeadId`, `AccountId`.

### 6.2 Indexing & Embeddings
* OpenAI `text-embedding-3-small` (fast, 1k dims) or local models (Instructor, E5).
* Store additional vectors: `title`, `participants`, `object_type` for weighted fusion.

### 6.3 Retrieval Enhancements
* **Max-marginal Relevance (MMR)** to reduce redundancy.
* **Self-ask**: agent crafts follow-up query when initial context insufficient.
* **Temporal decay** boosting recent interactions.
* **Feedback-driven re-ranking** using session clicks.

### 6.4 Summarisation Patterns
1. **Map-Reduce** – summarise chunks → aggregate.
2. **Refine** – iterative summary where each chunk updates previous.
3. **Sliding Window** – ordered summarisation for chronological narratives.
4. **Segment-aware** – summarise per object (Opportunity) then assemble.

### 6.5 Agent Patterns
* **ReACT** – reason + act loops (search, fetch, summarise).
* **MRKL** – modular router + tool-solver architecture.
* **Plan-and-execute** – high-level plan node then executor workers (CrewAI pattern).
* **Memory-aided conversation** – persistent vector memory per user session.

## 7. Implementation Phases
1. **POC (2 wks)**
   * Chunk ~10 % of data.
   * Store in pgvector.
   * Build simple retrieval endpoint (FastAPI) + LLM summariser.
2. **MVP (4 wks)**
   * Full data ingestion pipeline via Airflow/Celery.
   * Deploy Hybrid Retriever, expose MCP-style `/search` tool.
   * Add LangChain agent with SQL + Search tools.
3. **Alpha Agent (4 wks)**
   * Agentic workflow for "Generate monthly outreach effectiveness report".
   * Hierarchical summarisation; output Markdown + JSON.
4. **Beta & Hardening**
   * Fine-tune retrieval parameters; add caching, rate-limits.
   * Automated evaluations (retrieval precision, factual consistency).

## 8. Tooling Recommendations
| Layer | Suggested Library/Service | Notes |
|-------|---------------------------|-------|
| Embedding | OpenAI, HuggingFace Inference Endpoints | Choose based on cost vs accuracy. |
| Vector DB | `pgvector` on Supabase | Consolidates infra. |
| Retriever | `langchain.retrievers.MultiVectorRetriever`, `LlamaIndex` | Hybrid support. |
| Agent | LangChain AgentExecutor, CrewAI, Autogen | Depends on complexity. |
| API Layer | FastAPI / MCP server | Provide `/retrieve`, `/summary`, `/evaluate`. |
| Observability | Langfuse, OpenTelemetry | Already partially in repo. |

## 9. Evaluation Metrics
* **Retrieval** – Recall@k, MRR, nDCG.
* **Answer Quality** – ROUGE/BLEU vs baseline, human grading.
* **Latency** – P95 < 5 s for interactive chat.
* **Cost per 1 000 requests** – embeddings + LLM tokens.
* **Hallucination rate** – tracked via feedback interface.

## 10. Recommendations
1. **Start with Hybrid RAG** using pgvector + BM25.
2. **Deploy as a thin MCP-style micro-service** so both agent workflows and chatbots reuse retrieval.
3. **Layer Agentic Workflow** for complex reporting tasks; keep chatbot interface lightweight.
4. **Iteratively add hierarchical summarisation** for long-horizon outputs (quarterly, annual).
5. **Instrument with Langfuse** from day 1 to track failure modes.

## 11. Next Steps
- [ ] Set up `salesforce_rag` Supabase schema + pgvector extension.
- [ ] Prototype chunker & embedding loader script.
- [ ] Implement FastAPI `/search` & `/summarise` endpoints.
- [ ] Draft LangChain agent with `SearchTool` & `SQLTool`.
- [ ] Internal demo with Sara's last-month outreach.

---
*Prepared by the AI assistant – July 2025* 