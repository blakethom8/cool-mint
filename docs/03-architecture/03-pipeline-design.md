# Workflow Design and Implementation

The workflow system in GenAI Launchpad provides a structured way to implement AI workflows. This guide explains how to design, implement, and register workflows for processing through the Celery worker system.

## Workflow Architecture

### Registry System (registry.py)

The WorkflowRegistry acts as a central hub for managing different workflow implementations:

```python
class WorkflowRegistry:
    workflows: Dict[str, Type[Workflow]] = {
        "support": CustomerSupportWorkflow,
        "content": ContentAnalysisWorkflow,
    }

    @staticmethod
    def get_workflow_type(event: EventSchema) -> str:
        # Implement your routing logic
        if "support" in event.data.get("type"):
            return "support"
        return "content"
```

This registry:

- Maps event types to specific workflow implementations
- Provides dynamic workflow selection based on event attributes
- Enables easy addition of new workflow types

## Creating Workflows

### Basic Workflow Structure

A typical workflow consists of multiple nodes arranged in a DAG:

```python
class ContentAnalysisWorkflow(Workflow):
   workflow_schema = WorkflowSchema(
      description="Analyzes content using AI",
      start=GuardrailsNode,
      nodes=[
         NodeConfig(
            node=GuardrailsNode,
            connections=[ExtractNode],
            parallel_nodes=[FilterContentNode, FilterSQLInjectionNode, FilterSpamNode]
         ),
         NodeConfig(node=ExtractNode, connections=[AnalyzeNode]),
         NodeConfig(node=AnalyzeNode, connections=[RouterNode]),
         NodeConfig(
            node=RouterNode,
            connections=[SummarizeNode, TranslateNode],
            is_router=True
         ),
         NodeConfig(node=SummarizeNode, connections=[FormatNode]),
         NodeConfig(node=TranslateNode, connections=[FormatNode]),
         NodeConfig(node=FormatNode, connections=[])
      ]
   )
```

### Node Types and Implementation

1. **Basic Processing Node**:
```python
class ExtractNode(Node):
    def process(self, context: TaskContext) -> TaskContext:
        # Extract text from input
        text = context.event.data.get("content")
        context.nodes[self.node_name] = {"extracted_text": text}
        return context
```

2. **LLM Node**:
```python
class AnalyzeNode(LLMNode):
    class ContextModel(BaseModel):
        text: str
        analysis_type: str

    class ResponseModel(BaseModel):
        sentiment: str
        key_points: List[str]

    def get_context(self, task_context: TaskContext) -> ContextModel:
        return self.ContextModel(
            text=task_context.nodes["ExtractNode"]["extracted_text"],
            analysis_type=task_context.event.data.get("analysis_type")
        )

    def create_completion(self, context: ContextModel) -> ResponseModel:
        llm = LLMFactory("openai")
        prompt = PromptManager.get_prompt(
            "extract",
            workflow="support",
        )
        return llm.create_completion(
            response_model=self.ResponseModel,
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": f"# New data:\n{context.model_dump()}",
                },
            ],
        )

    def process(self, task_context: TaskContext) -> TaskContext:
        context = self.get_context(task_context)
        response = self.create_completion(context)
        task_context.nodes[self.node_name] = response
        return task_context
```

4. **Parallel Node**:
The nodes to be executed in parallel are defined in the workflow schema.
```python
class GuardrailsNode(ParallelNode):
    def process(self, task_context: TaskContext) -> TaskContext:
        self.execute_nodes_in_parallel(task_context)
        return task_context
```

3. **Router Node**:
```python
class ContentRouter(BaseRouter):
    def __init__(self):
        self.routes = [
            SummaryRoute(),
            TranslationRoute()
        ]
        self.fallback = SummaryRoute()

class SummaryRoute(RouterNode):
    def determine_next_node(self, context: TaskContext) -> Optional[Node]:
        if context.event.data.get("action") == "summarize":
            return SummarizeNode()
        return None
```

## Worker Integration

The Celery worker (tasks.py) handles workflow execution:

```python
@celery_app.task(name="process_incoming_event")
def process_incoming_event(event_id: str):
    with db_session() as session:
        # Get event from database
        event = repository.get(id=event_id)
        
        # Determine and execute workflow
        workflow = WorkflowRegistry.get_workflow(event)
        result = workflow.run(event)
        
        # Store results
        event.task_context = result.model_dump()
        repository.update(event)
```

## Workflow Design Best Practices

### 1. Node Granularity

Design nodes with single responsibilities:
```python
# Good: Focused node
class SentimentNode(LLMNode):
    def process(self, context: TaskContext) -> TaskContext:
        # Only handles sentiment analysis
        return context

# Avoid: Too many responsibilities
class AnalysisNode(LLMNode):
    def process(self, context: TaskContext) -> TaskContext:
        # Handles sentiment, entities, translation, etc.
        return context
```

### 2. Data Flow

Maintain clear data dependencies:
```python
class SummarizeNode(LLMNode):
    def get_context(self, task_context: TaskContext) -> ContextModel:
        # Clearly specify data requirements
        return self.ContextModel(
            text=task_context.nodes["ExtractNode"]["text"],
            style=task_context.nodes["AnalyzeNode"]["tone"]
        )
```

### 3. Router Placement

Place routers at decision points:
```python
workflow_schema = WorkflowSchema(
    start=ValidateNode,
    nodes=[
        NodeConfig(node=ValidateNode, connections=[RouterNode]),
        NodeConfig(
            node=RouterNode,
            connections=[ProcessA, ProcessB],
            is_router=True
        )
    ]
)
```

### 4. Error Handling

Implement robust error handling:
```python
class ProcessingNode(Node):
    def process(self, context: TaskContext) -> TaskContext:
        try:
            result = self.process_data(context)
            context.nodes[self.node_name] = {"status": "success", "data": result}
        except Exception as e:
            context.nodes[self.node_name] = {
                "status": "error",
                "error": str(e)
            }
        return context
```

## Workflow Organization

Structure your workflows folder:
```
workflows/
├── __init__.py
├── registry.py
├── support/
│   ├── __init__.py
│   ├── nodes.py
│   └── workflow.py
└── content/
    ├── __init__.py
    ├── nodes.py
    └── workflow.py
```

## Testing Workflows

Create comprehensive tests:
```python
def test_content_workflow():
    # Create test event
    event = EventSchema(type="content_analysis", data={...})
    
    # Initialize workflow
    workflow = ContentAnalysisWorkflow()
    
    # Run workflow
    result = workflow.run(event)
    
    # Assert expected results
    assert "AnalyzeNode" in result.nodes
    assert result.nodes["AnalyzeNode"]["sentiment"] == "positive"
```

Remember that well-designed workflows are:

- Easy to understand
- Maintainable
- Testable
- Reusable
- Error-resistant

The workflow system provides the structure - your implementation provides the intelligence.

## Workflow Strategy: Single vs. Multiple

### When to Use a Single Workflow

A single workflow is often sufficient when:

1. **Common Processing Flow**: Your application handles variations of the same basic workflow:
```python
class ContentWorkflow(Workflow):
    workflow_schema = WorkflowSchema(
        start=ValidateNode,
        nodes=[
            NodeConfig(node=ValidateNode, connections=[RouterNode]),
            NodeConfig(
                node=RouterNode, 
                connections=[
                    TextAnalysisNode,
                    ImageAnalysisNode,
                    AudioAnalysisNode
                ],
                is_router=True
            ),
            # All paths converge to common processing
            NodeConfig(node=TextAnalysisNode, connections=[EnrichmentNode]),
            NodeConfig(node=ImageAnalysisNode, connections=[EnrichmentNode]),
            NodeConfig(node=AudioAnalysisNode, connections=[EnrichmentNode]),
            NodeConfig(node=EnrichmentNode, connections=[StorageNode]),
        ]
    )
```

2. **Branching Logic**: When differences can be handled through routing:
```python
class RouterNode(BaseRouter):
    def determine_next_node(self, context: TaskContext) -> Node:
        content_type = context.event.data.get("type")
        return {
            "text": TextAnalysisNode(),
            "image": ImageAnalysisNode(),
            "audio": AudioAnalysisNode()
        }.get(content_type, TextAnalysisNode())
```

3. **Shared Context**: When different processes need access to the same context:
```python
class EnrichmentNode(Node):
    def process(self, context: TaskContext) -> TaskContext:
        # Access results from any previous node
        analysis_results = context.nodes.get(
            f"{context.metadata['analysis_type']}AnalysisNode"
        )
        # Enrich with common logic
        return context
```

### When to Use Multiple Workflows

Consider multiple workflows when:

1. **Distinct Business Domains**:
```python
class CustomerSupportWorkflow(Workflow):
    # Handle customer inquiries
    workflow_schema = WorkflowSchema(...)

class ContentModerationWorkflow(Workflow):
    # Handle content moderation
    workflow_schema = WorkflowSchema(...)
```

2. **Different Security Requirements**:
```python
class PublicWorkflow(Workflow):
    # Public-facing processing
    workflow_schema = WorkflowSchema(...)

class InternalWorkflow(Workflow):
    # Internal, privileged processing
    workflow_schema = WorkflowSchema(...)
```

3. **Completely Different Workflows**:
```python
class DocumentProcessingWorkflow(Workflow):
    # Document-specific workflow
    workflow_schema = WorkflowSchema(
        nodes=[
            NodeConfig(node=OCRNode),
            NodeConfig(node=ClassificationNode),
            # ...
        ]
    )

class ChatWorkflow(Workflow):
    # Conversational workflow
    workflow_schema = WorkflowSchema(
        nodes=[
            NodeConfig(node=ContextNode),
            NodeConfig(node=ResponseNode),
            # ...
        ]
    )
```

### Hybrid Approach

You can also use a hybrid approach where you have multiple workflows that share common components:

```python
# Shared nodes module
class CommonNodes:
    class ValidationNode(Node):
        def process(self, context: TaskContext) -> TaskContext:
            # Common validation logic
            return context

# Multiple workflows using shared components
class Workflow1(Workflow):
    workflow_schema = WorkflowSchema(
        start=CommonNodes.ValidationNode,
        nodes=[
            NodeConfig(node=CommonNodes.ValidationNode),
            NodeConfig(node=CustomNode1)
        ]
    )

class Workflow2(Workflow):
    workflow_schema = WorkflowSchema(
        start=CommonNodes.ValidationNode,
        nodes=[
            NodeConfig(node=CommonNodes.ValidationNode),
            NodeConfig(node=CustomNode2)
        ]
    )
```

### Decision Framework

When deciding on workflow structure, consider:

1. **Complexity Management**:
   - Single Workflow: When variations are minimal
   - Multiple Workflows: When complexity becomes hard to manage in one workflow

2. **Maintenance**:
   - Single Workflow: Easier to maintain when logic is related
   - Multiple Workflows: Better when different teams manage different workflows

3. **Performance**:
   - Single Workflow: Can optimize shared resources
   - Multiple Workflows: Can scale different workflows independently

4. **Security**:
   - Single Workflow: When security context is uniform
   - Multiple Workflows: When different security contexts are needed

Remember: Start with a single workflow and split only when necessary. It's easier to split a workflow later than to combine multiple workflows.