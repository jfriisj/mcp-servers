"""
Study Buddy GUI - Search Prompt Template

Concrete implementation for generating document search prompts.
Helps users create AI instructions for intelligent document search and retrieval.

Architecture: Clean Architecture Layer 4 (Infrastructure - Concrete Strategy)
"""

from typing import List
from .base_template import BasePromptTemplate, TemplateContext, TemplateError


class SearchTemplate(BasePromptTemplate):
    """
    Prompt template for AI-powered document search operations.
    
    Generates prompts that instruct AI agents to search through
    documents and provide relevant results with context.
    """
    
    @property
    def template_name(self) -> str:
        return "Document Search"
    
    @property
    def template_description(self) -> str:
        return "Generate AI instructions for intelligent document search and content retrieval"
    
    @property
    def required_context(self) -> List[str]:
        return ["document_title"]  # More flexible requirements for search
    
    def generate_prompt(self, context: TemplateContext) -> str:
        """Generate document search prompt for AI agents."""
        self.validate_context(context)
        
        try:
            # Base search prompt
            prompt = f"""# AI Document Search Task

## Objective
Search through documents in the Study Buddy system to find relevant content based on the specified query and criteria.

## Search Instructions

### Step 1: Execute Search
Use the search functionality to find relevant content:

```
search_documents(
    query="[ENTER YOUR SEARCH QUERY HERE]",
    filters={{
        "file_type": "{context.document_type if hasattr(context, 'document_type') and context.document_type else 'all'}",
        "indexed": true
    }},
    limit=20
)
```

### Step 2: Analyze Results
Review the search results to identify:
- Most relevant documents and chunks
- Key passages that match the query
- Related content that might be useful
- Overall patterns in the results

### Step 3: Provide Contextual Summary
Create a summary of findings that includes:
- **Relevance Ranking**: Order results by relevance to the query
- **Key Insights**: Main points discovered across the results
- **Source Attribution**: Clear references to specific documents and chunks
- **Follow-up Suggestions**: Recommendations for deeper exploration

## Search Quality Guidelines
- Use specific, focused search terms
- Consider synonyms and related concepts
- Look for both direct matches and conceptual relevance
- Evaluate result quality and relevance
- Provide clear source attribution for all findings

## Output Format
Structure your response as:

1. **Search Summary**
   - Query used: [search terms]
   - Results found: [number of matches]
   - Top relevance score: [if available]

2. **Key Findings**
   - [Most relevant finding with source]
   - [Second most relevant finding with source]
   - [Additional relevant findings...]

3. **Recommended Next Steps**
   - [Suggestions for deeper analysis]
   - [Related search queries to try]
   - [Specific documents to explore further]

Begin by formulating your search query and executing the search."""

            # Add specific document context if available
            if hasattr(context, 'document_id') and context.document_id:
                prompt += f"""

## Specific Document Context
Focus your search within or related to: "{context.document_title}" (ID: {context.document_id})

You may want to combine document-specific searches with broader queries to find related content across the entire document collection."""

            return prompt
            
        except Exception as e:
            raise TemplateError(
                template_name=self.template_name,
                message=f"Failed to generate search prompt: {str(e)}",
                context=context
            )