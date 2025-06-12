# CPT Code Categorization Service

## 🎯 Overview

The CPT Code Categorization Service is a sophisticated AI-powered system designed to automatically categorize thousands of Current Procedural Terminology (CPT) codes into meaningful, specialty-specific groupings with human-in-the-loop validation. This service addresses the critical need for healthcare organizations to organize medical procedure codes for mapping tables, analytics, and operational workflows.

## 🚨 Problem Statement

Healthcare organizations face significant challenges in categorizing CPT codes:

- **Scale**: Thousands of procedure codes require classification
- **Specialization**: Different medical specialties need custom categorization schemes
- **Accuracy**: Medical codes demand high precision for billing and compliance
- **Customization**: Generic classification systems don't meet specific organizational needs
- **Manual Effort**: Current Excel-based processes are time-consuming and error-prone
- **Contextual Similarity**: Codes need to be grouped considering medical relationships, not just numerical proximity

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chat Agent    │───▶│  Workflow Engine │───▶│   Human-in-Loop │
│   Interface     │    │  (Classification) │    │   UI Dashboard  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Claims Database │    │  Classification  │    │  Classification │
│  CPT Retrieval  │    │    Storage       │    │   Feedback      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **Data Layer**
- **CPT Codes Database**: Master repository of all CPT codes with descriptions
- **Claims Database**: Historical procedure data filtered by specialty/provider
- **Classification Storage**: Versioned categorization results and schemas
- **Feedback Database**: Human corrections and validation data

#### 2. **Classification Workflow Engine**
Built using the existing Launchpad workflow system with specialized nodes:

##### **Stage 1: Category Generation Node**
- **Input**: Medical specialty (e.g., "Urology", "ENT", "Orthopedics")
- **Process**: LLM generates 6-8 broad, clinically meaningful categories
- **Output**: Category schema with descriptions and inclusion criteria
- **Example Output**:
  ```json
  {
    "specialty": "Urology",
    "categories": [
      {
        "id": "diagnostic_imaging",
        "name": "Diagnostic Imaging & Testing",
        "description": "Cystoscopy, urodynamics, imaging studies",
        "inclusion_criteria": ["diagnostic procedures", "imaging", "testing"]
      },
      {
        "id": "minimally_invasive",
        "name": "Minimally Invasive Procedures",
        "description": "Laparoscopic, robotic, and endoscopic procedures"
      }
      // ... additional categories
    ]
  }
  ```

##### **Stage 2: Code Classification Node**
- **Input**: List of CPT codes + approved category schema
- **Process**: Multi-shot LLM classification with medical context
- **Features**:
  - Batch processing for efficiency
  - Confidence scoring for each classification
  - Similar code clustering for consistency
  - Medical context awareness (anatomical systems, procedure types)
- **Output**: Classified codes with confidence scores and reasoning

##### **Stage 3: Similarity Analysis Node**
- **Input**: Classified codes
- **Process**: Identifies codes that should be grouped together based on:
  - Numerical proximity (sequential CPT codes often related)
  - Semantic similarity in descriptions
  - Historical co-occurrence in claims
- **Output**: Similarity clusters and recommendations

#### 3. **Human-in-the-Loop Interface**
- **Review Dashboard**: Visual interface for validating classifications
- **Batch Operations**: Approve/reject multiple similar codes
- **Manual Override**: Custom categorization with reasoning
- **Feedback Integration**: Corrections feed back into model improvement

#### 4. **API Layer**
RESTful endpoints following Launchpad patterns:
- `GET /api/v1/cpt-categories/{specialty}` - Retrieve categories for specialty
- `POST /api/v1/cpt-classify` - Trigger classification workflow
- `GET /api/v1/cpt-classify/{job_id}` - Check classification status
- `PUT /api/v1/cpt-classify/{job_id}/feedback` - Submit human feedback

## 🔄 Workflow Process

### User Journey Example

1. **Initiation**: User asks chat agent: "Help me categorize procedure codes for a urologist"

2. **Code Retrieval**: System queries claims database for all CPT codes used by urologists

3. **Category Generation**: 
   ```
   Workflow: Generate Urology Categories
   Node 1: Specialty Analysis → Medical Context
   Node 2: Category Generation → 6-8 broad categories
   Node 3: Category Validation → Clinical review prompt
   ```

4. **Code Classification**:
   ```
   Workflow: Classify Urology Codes
   Node 1: Batch Preparation → Group codes for processing
   Node 2: LLM Classification → Assign codes to categories
   Node 3: Confidence Scoring → Flag uncertain classifications
   Node 4: Similarity Analysis → Identify related codes
   ```

5. **Human Review**:
   - Present results in intuitive UI
   - Highlight low-confidence classifications
   - Show similar codes for consistency checking
   - Allow bulk operations for efficiency

6. **Feedback Loop**:
   - Store human corrections
   - Update classification model
   - Generate mapping tables and exports

## 📊 Data Structures

### CPT Code Schema
```python
class CPTCode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    description: str
    category: Optional[str] = None
    modifier_codes: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime
```

### Classification Result Schema
```python
class ClassificationResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cpt_code: str = Field(foreign_key="cptcode.code")
    specialty: str
    category_id: str
    category_name: str
    confidence_score: float
    reasoning: str
    workflow_run_id: str
    human_validated: bool = False
    human_feedback: Optional[str] = None
    created_at: datetime
```

### Category Schema
```python
class CategorySchema(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    specialty: str
    schema_version: str
    categories: List[Dict[str, Any]]  # JSON field storing category definitions
    created_by: str  # user or system
    is_active: bool = True
    created_at: datetime
```

## 🛠️ Implementation Plan

### Phase 1: Foundation (Week 1-2)
- [ ] Database schema design and migration
- [ ] Basic workflow nodes implementation
- [ ] CPT code data ingestion pipeline
- [ ] Initial LLM prompt engineering

### Phase 2: Core Classification Engine (Week 3-4)
- [ ] Category generation node with medical specialty awareness
- [ ] Code classification node with batch processing
- [ ] Similarity analysis and clustering algorithms
- [ ] Confidence scoring and uncertainty detection

### Phase 3: Human-in-the-Loop Interface (Week 5-6)
- [ ] Review dashboard with intuitive UX
- [ ] Bulk operations and batch approval workflows
- [ ] Feedback integration and correction tracking
- [ ] Export functionality for mapping tables

### Phase 4: Integration & Testing (Week 7-8)
- [ ] Chat agent integration for natural language queries
- [ ] End-to-end testing with real CPT data
- [ ] Performance optimization for large datasets
- [ ] User acceptance testing with domain experts

### Phase 5: Advanced Features (Week 9-10)
- [ ] Active learning from human feedback
- [ ] Multi-specialty cross-validation
- [ ] Advanced analytics and reporting
- [ ] API documentation and client SDKs

## 🔧 Technical Considerations

### LLM Strategy
- **Primary Model**: GPT-4 for initial classification with medical knowledge
- **Fallback Model**: Claude-3 for cost optimization on bulk operations
- **Specialized Prompts**: Medical terminology and context-aware prompts
- **Few-shot Learning**: Use validated examples to improve accuracy

### Scalability
- **Batch Processing**: Handle thousands of codes efficiently
- **Caching**: Store category schemas and common classifications
- **Async Processing**: Use Celery for long-running classification jobs
- **Database Optimization**: Proper indexing for code lookups and similarity searches

### Quality Assurance
- **Confidence Thresholds**: Flag uncertain classifications for human review
- **Cross-validation**: Compare classifications across similar specialties
- **Audit Trail**: Track all changes and decisions for compliance
- **Version Control**: Maintain schema versions for reproducibility

## 🎨 User Experience Design

### Chat Interface
```
User: "Help me categorize procedure codes for ENT surgery"

Agent: "I'll help you categorize ENT procedure codes. Let me start by analyzing 
your claims database to identify the most common ENT procedures, then generate 
appropriate categories.

🔍 Found 127 unique CPT codes used by ENT specialists
📊 Generating clinical categories...

Here are the suggested categories for ENT procedures:
1. Head & Neck Cancer Surgery
2. Reconstructive Surgery
3. Ear Surgery & Hearing
4. Sinus & Nasal Surgery
5. Throat & Voice Surgery
6. Diagnostic Procedures

Would you like me to proceed with classifying all codes into these categories?"
```

### Review Dashboard Mockup
```
┌─────────────────────────────────────────────────────────────────┐
│ CPT Classification Review - ENT Surgery                        │
├─────────────────────────────────────────────────────────────────┤
│ Progress: 89/127 codes reviewed (70%)                          │
│                                                                 │
│ 🔴 High Priority (12 codes need review)                       │
│ 🟡 Medium Confidence (23 codes)                               │
│ 🟢 High Confidence (54 codes approved)                        │
│                                                                 │
│ Current Code: 31240 - Nasal/sinus endoscopy, surgical         │
│ Suggested Category: Sinus & Nasal Surgery (85% confidence)     │
│                                                                 │
│ Similar Codes in this Category:                                │
│ • 31254 - Ethmoidectomy, endoscopic                          │
│ • 31255 - Ethmoidectomy, endoscopic, total                   │
│ • 31267 - Nasal/sinus endoscopy, with removal of tissue      │
│                                                                 │
│ [✓ Approve] [✗ Reject] [✏️ Edit Category] [⏭️ Skip]           │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites
- Existing GenAI Launchpad installation
- Access to CPT code database or API
- Claims data with procedure codes by specialty
- LLM API keys (OpenAI/Anthropic)

### Quick Start
1. **Install Dependencies**:
   ```bash
   pip install sqlmodel pandas scikit-learn textdistance
   ```

2. **Database Setup**:
   ```bash
   alembic revision --autogenerate -m "Add CPT classification tables"
   alembic upgrade head
   ```

3. **Initialize Workflow**:
   ```python
   from app.workflows.cpt_classification import CPTClassificationWorkflow
   
   workflow = CPTClassificationWorkflow()
   result = workflow.classify_specialty("Urology")
   ```

## 🎯 Success Metrics

### Accuracy Metrics
- **Classification Accuracy**: >90% human validation rate
- **Consistency**: <5% disagreement on similar codes
- **Coverage**: 100% of specialty codes classified

### Efficiency Metrics
- **Processing Speed**: <2 minutes per 100 codes
- **Human Review Time**: <30 seconds per uncertain code
- **Batch Operations**: 80% of codes approved in bulk

### User Experience Metrics
- **Time Savings**: 75% reduction vs. Excel-based process
- **User Satisfaction**: >4.5/5 rating on usability
- **Adoption Rate**: 90% of target users active monthly

## 🔮 Future Enhancements

### Advanced AI Features
- **Multi-modal Classification**: Include procedure images/videos
- **Temporal Analysis**: Track code usage trends over time
- **Cross-specialty Learning**: Share insights between specialties
- **Automated Validation**: Reduce human review requirements

### Integration Opportunities
- **EHR Integration**: Direct import from electronic health records
- **Billing Systems**: Export classifications to revenue cycle systems
- **Analytics Platforms**: Feed categorized data to business intelligence
- **Regulatory Compliance**: Automated compliance checking

### Scalability Improvements
- **Distributed Processing**: Handle enterprise-scale datasets
- **Real-time Classification**: Instant categorization for new codes
- **Multi-tenant Support**: Isolated environments for different organizations
- **API Ecosystem**: Third-party integration capabilities

## 📞 Next Steps

### Immediate Actions (This Week)
1. **Architecture Review**: Validate this approach with medical domain experts
2. **Data Assessment**: Evaluate available CPT code and claims data sources
3. **Prototype Planning**: Define MVP scope for initial validation
4. **Team Alignment**: Assign development resources and timeline

### Technical Decisions Needed
- **LLM Provider Selection**: Cost vs. accuracy trade-offs
- **UI Framework**: React/Vue for dashboard development
- **Data Sources**: Internal vs. external CPT code databases
- **Deployment Strategy**: Cloud vs. on-premise considerations

### Stakeholder Involvement
- **Medical Experts**: Clinical validation of categories and logic
- **End Users**: UX feedback and workflow optimization
- **IT/Security**: Infrastructure and compliance requirements
- **Business Analysts**: ROI measurement and success criteria

---

*This document represents our comprehensive plan for building the CPT Code Categorization Service. The architecture is designed to be iterative and adaptable based on real-world testing and user feedback.*