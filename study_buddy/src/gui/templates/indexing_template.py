"""
Study Buddy GUI - Indexing Prompt Template

Concrete implementation for generating document indexing/chunking prompts.
Helps users generate AI instructions for document structure analysis.

Architecture: Clean Architecture Layer 4 (Infrastructure - Concrete Strategy)
"""

from typing import List
from .base_template import BasePromptTemplate, TemplateContext, TemplateError


class IndexingTemplate(BasePromptTemplate):
    """
    Prompt template for AI-powered document indexing and chunking.
    
    Generates prompts that instruct AI agents to analyze document structure
    and create intelligent chunks using appropriate strategies.
    """
    
    @property
    def template_name(self) -> str:
        return "Document Indexing"
    
    @property
    def template_description(self) -> str:
        return "Generate AI instructions for document structure analysis and intelligent chunking"
    
    @property
    def required_context(self) -> List[str]:
        return ["document_title", "document_id", "document_type"]
    
    def generate_prompt(self, context: TemplateContext) -> str:
        """Generate document indexing prompt for AI agents."""
        self.validate_context(context)
        
        try:
            # Determine appropriate chunking strategy based on document type
            strategy_recommendations = {
                "pdf": "chapter",  # Books and papers
                "docx": "heading",  # Word documents with headings
                "pptx": "slide",   # PowerPoint presentations
                "md": "heading"    # Markdown documents
            }
            
            recommended_strategy = strategy_recommendations.get(
                context.document_type.lower(), "auto"
            )
            
            prompt = f"""# AI Document Indexing Task

## Objective
Analyze and create intelligent chunks for the document "{context.document_title}" to enable efficient AI-powered summarization and retrieval.

## Step-by-Step Instructions

### Step 1: Analyze Document Structure
First, retrieve the document to understand its structure:

```
get_document(document_id={context.document_id})
```

### Step 2: Select Appropriate Chunking Strategy
Based on the document type ({context.document_type.upper()}) and structure analysis, choose the most appropriate chunking strategy:

**Recommended Strategy:** `{recommended_strategy}`

Available strategies:
- **chapter**: For books and long documents with clear chapter divisions
- **section**: For academic papers with standard sections (Abstract, Introduction, etc.)
- **heading**: For documents with hierarchical headings (H1, H2, etc.)
- **slide**: For PowerPoint presentations (one chunk per slide)
- **auto**: For mixed content or when structure is unclear

### Step 3: Execute Indexing
Index the document using the selected strategy:

```
index_document(
    document_id={context.document_id},
    strategy="{recommended_strategy}"
)
```

### Step 4: Verify Structure
Check the resulting document structure:

```
get_document_structure(document_id={context.document_id})
```

## Quality Guidelines
- Choose strategy that preserves logical content boundaries
- Ensure chunks are neither too small (<100 words) nor too large (>2000 words)
- Verify that chunk titles are meaningful and descriptive
- Confirm that the structure enables effective summarization

## Expected Results
- Document marked as indexed in the system
- Logical chunk structure that facilitates AI summarization
- Clear, descriptive chunk titles
- Appropriate chunk sizes for processing

Begin with Step 1 and proceed systematically through all steps."""
            
            return prompt
            
        except Exception as e:
            raise TemplateError(
                template_name=self.template_name,
                message=f"Failed to generate indexing prompt: {str(e)}",
                context=context
            )