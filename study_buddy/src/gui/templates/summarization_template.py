"""
Study Buddy GUI - Summarization Prompt Template

Concrete implementation for generating AI summarization prompts.
This is the core template used for the primary AI workflow.

Architecture: Clean Architecture Layer 4 (Infrastructure - Concrete Strategy)
Pattern: Strategy Pattern implementation for summarization
SOLID: Single Responsibility (summarization prompts only)
"""

from typing import List
from .base_template import BasePromptTemplate, TemplateContext, PromptStyle, FocusArea, TemplateError


class SummarizationTemplate(BasePromptTemplate):
    """
    Prompt template for AI-powered document summarization.
    
    Generates comprehensive prompts that instruct AI agents to:
    1. Retrieve specific chunk content via MCP tools
    2. Generate high-quality summaries with specified style/focus
    3. Save the results back to the database
    
    This template is the core of the AI workflow described in the
    implementation guide's "Prompt Builder" section.
    """
    
    @property
    def template_name(self) -> str:
        return "Summarization"
    
    @property
    def template_description(self) -> str:
        return "Generate AI-powered summaries of document chunks with customizable style and focus areas"
    
    @property
    def required_context(self) -> List[str]:
        return ["document_title", "document_id", "chunk_title", "chunk_id"]
    
    def generate_prompt(self, context: TemplateContext) -> str:
        """
        Generate a comprehensive summarization prompt for AI agents.
        
        This creates a step-by-step prompt that guides the AI through:
        1. Using get_chunk_content MCP tool
        2. Generating appropriate summary 
        3. Using save_summary MCP tool
        
        The prompt follows the workflow pattern from the implementation guide.
        """
        # Validate required context
        self.validate_context(context)
        
        try:
            # Build the comprehensive prompt
            prompt = f"""# AI Document Summarization Task

## Objective
Create a high-quality summary of "{context.chunk_title}" from the document "{context.document_title}" following the specified requirements below.

## Step-by-Step Instructions

### Step 1: Retrieve Content
Use the MCP tool to get the full content of the target chunk:

```
get_chunk_content(chunk_id={context.chunk_id})
```

This will return the complete text content that you need to summarize.

### Step 2: Generate Summary
Create a summary with the following specifications:

**Style Requirements:**
{self._format_style_instructions(context.style)}

**Focus Areas:**
{self._format_focus_instructions(context.focus_areas or [FocusArea.KEY_CONCEPTS])}

**Quality Standards:**
- Use clear, professional language
- Maintain logical flow and structure
- Include specific examples where relevant
- Ensure accuracy to the source material
- Use markdown formatting for better readability

### Step 3: Save Summary
Once you've generated the summary, save it using:

```
save_summary(
    chunk_id={context.chunk_id},
    summary_type="{context.style.value}",
    summary_content="[Your generated summary here in markdown format]",
    model_name="[Your model name, e.g., 'gpt-4', 'claude-3']"
)
```

## Additional Context
- **Document Type:** {context.document_type.upper()}
- **Target Content:** {context.target_description}
- **Summary Style:** {context.style.value.title()}
- **Focus Areas:** {context.focus_areas_text}"""

            # Add user instructions if provided
            if context.user_instructions and context.user_instructions.strip():
                prompt += f"""
                
## Special Instructions
{context.user_instructions.strip()}"""

            prompt += """

## Success Criteria
- ✅ Successfully retrieve chunk content using get_chunk_content
- ✅ Generate summary meeting style and focus requirements  
- ✅ Successfully save summary using save_summary
- ✅ Confirm successful completion with summary ID

Begin with Step 1 and proceed through all steps systematically."""

            return prompt
            
        except Exception as e:
            raise TemplateError(
                template_name=self.template_name,
                message=f"Failed to generate summarization prompt: {str(e)}",
                context=context
            )
    
    def generate_batch_prompt(self, contexts: List[TemplateContext]) -> str:
        """
        Generate a batch summarization prompt for multiple chunks.
        
        Useful for summarizing entire documents or multiple sections.
        
        Args:
            contexts: List of TemplateContext objects for each chunk
            
        Returns:
            Batch summarization prompt
        """
        if not contexts:
            raise ValueError("At least one context required for batch prompt")
        
        # Use first context for document-level information
        primary_context = contexts[0]
        
        prompt = f"""# AI Batch Document Summarization Task

## Objective
Create summaries for {len(contexts)} chunks from "{primary_context.document_title}".

## Batch Processing Instructions

For each chunk listed below, follow this process:
1. Use get_chunk_content(chunk_id=X) to retrieve content
2. Generate summary according to specifications
3. Use save_summary() to store the result
4. Proceed to next chunk

## Target Chunks:
"""
        
        # Add each chunk to the batch
        for i, ctx in enumerate(contexts, 1):
            prompt += f"""
### Chunk {i}: {ctx.chunk_title}
- **Chunk ID:** {ctx.chunk_id}
- **Style:** {ctx.style.value}
- **Focus:** {ctx.focus_areas_text}
"""
        
        prompt += f"""
## Quality Standards
{self._format_style_instructions(primary_context.style)}
{self._format_focus_instructions(primary_context.focus_areas or [FocusArea.KEY_CONCEPTS])}

Process all chunks systematically and confirm completion of each one."""
        
        return prompt