"""
Summary prompt generation strategy.

This module implements the strategy for generating AI prompts that create
summaries of documents or chunks, with different detail levels and focus areas.
"""

from typing import Dict, List, Optional, Any
from study_buddy.server.prompts.base_strategy import BasePromptStrategy
from study_buddy.server.models.prompt_result import PromptResult


class SummaryPromptStrategy(BasePromptStrategy):
    """
    Strategy for generating summary prompts.

    This strategy creates prompts that instruct AI agents to:
    1. Retrieve content from specified targets
    2. Analyze and extract key information
    3. Create structured summaries with appropriate detail
    4. Save results back to the database

    Supports both document-level and chunk-level summaries.
    """

    def supports_target_type(self, target_type: str) -> bool:
        """Summary strategy supports both documents and chunks."""
        return target_type in ["document", "chunk"]

    def get_strategy_name(self) -> str:
        """Human-readable strategy name."""
        return "Summary Generation"

    def generate_prompt(
        self,
        target_ids: List[int],
        target_type: str,
        detail_level: str,
        focus_areas: Optional[List[str]] = None,
        custom_instructions: Optional[str] = None,
        output_format: str = "markdown",
    ) -> PromptResult:
        """
        Generate summary prompt for specified targets.

        Creates complete instructions for AI agent to retrieve content,
        analyze it, generate summary, and save results.
        """
        # Validate parameters
        self.validate_parameters(target_ids, target_type, detail_level)

        # Get word count targets
        word_counts = self.get_word_count_target(detail_level)

        # Format focus areas
        focus_text = self.format_focus_areas(focus_areas)

        # Generate the prompt based on target type
        if target_type == "chunk":
            prompt_text = self._generate_chunk_summary_prompt(
                target_ids,
                detail_level,
                word_counts,
                focus_text,
                custom_instructions,
                output_format,
            )
        else:  # document
            prompt_text = self._generate_document_summary_prompt(
                target_ids,
                detail_level,
                word_counts,
                focus_text,
                custom_instructions,
                output_format,
            )

        # Create and return result
        return self.create_prompt_result(
            prompt_text=prompt_text,
            prompt_type="summary",
            detail_level=detail_level,
            target_ids=target_ids,
            target_type=target_type,
            focus_areas=focus_areas,
            metadata={
                "strategy": "summary",
                "word_count_target": word_counts,
                "output_format": output_format,
                "includes_mcp_tools": True,
            },
        )

    def _generate_chunk_summary_prompt(
        self,
        chunk_ids: List[int],
        detail_level: str,
        word_counts: Dict[str, int],
        focus_text: str,
        custom_instructions: Optional[str],
        output_format: str,
    ) -> str:
        """Generate prompt for chunk-level summaries."""

        # Handle single vs multiple chunks
        if len(chunk_ids) == 1:
            chunk_id = chunk_ids[0]
            prompt = f"""# AI Task: Create {detail_level.title()} Summary of Content Chunk

## Context
You are an expert content analyst with access to the Study Buddy MCP server. Your task is to create a {detail_level} summary ({word_counts['min']}-{word_counts['max']} words) of a specific content chunk, focusing on {focus_text}.

## Instructions

### Step 1: Retrieve Content
Use the Study Buddy MCP tool to get the chunk content:
```
get_chunk_content(chunk_id={chunk_id})
```

### Step 2: Analyze Content
Examine the retrieved content and identify:
- Main topics and key concepts
- Important details relevant to: {focus_text}
- Structure and organization
- Core insights and takeaways

### Step 3: Create Summary
Generate a {detail_level} summary with these requirements:
- **Length**: {word_counts['min']}-{word_counts['max']} words
- **Format**: Well-structured {output_format}
- **Focus**: Emphasize {focus_text}
- **Structure**: Use clear headings and sections
- **Tone**: Professional and informative

### Step 4: Save Result
Save your summary using:
```
save_summary(
    chunk_id={chunk_id},
    summary_type="{detail_level}",
    summary_content="[Your complete summary here]",
    model_name="gpt-4"
)
```

## Quality Requirements
- ✅ Stay within word count limits
- ✅ Focus on specified areas: {focus_text}
- ✅ Use proper {output_format} formatting
- ✅ Include key insights and practical information
- ✅ Maintain objective, informative tone

{self._add_custom_instructions(custom_instructions)}

## Success Criteria
Your task is complete when you have:
1. Retrieved the chunk content successfully
2. Created a well-structured summary within word limits  
3. Saved the summary to the database
4. Confirmed successful save operation"""

        else:
            # Multiple chunks - batch processing
            chunk_list = ", ".join(str(cid) for cid in chunk_ids)
            prompt = f"""# AI Task: Create {detail_level.title()} Summaries of Multiple Content Chunks

## Context
You are an expert content analyst with access to the Study Buddy MCP server. Your task is to create {detail_level} summaries ({word_counts['min']}-{word_counts['max']} words each) for {len(chunk_ids)} content chunks, focusing on {focus_text}.

## Target Chunks
Process these chunk IDs: {chunk_list}

## Instructions

### Step 1: Process Each Chunk
For each chunk ID, follow this workflow:

1. **Retrieve Content**:
   ```
   get_chunk_content(chunk_id=[CHUNK_ID])
   ```

2. **Analyze and Summarize**:
   - Identify main topics and key concepts
   - Focus on: {focus_text}
   - Create {detail_level} summary ({word_counts['min']}-{word_counts['max']} words)
   - Use proper {output_format} formatting

3. **Save Summary**:
   ```
   save_summary(
       chunk_id=[CHUNK_ID],
       summary_type="{detail_level}",
       summary_content="[Your summary here]",
       model_name="gpt-4"
   )
   ```

### Step 2: Quality Requirements
Each summary must:
- ✅ Stay within {word_counts['min']}-{word_counts['max']} word limits
- ✅ Focus on specified areas: {focus_text}
- ✅ Use proper {output_format} formatting
- ✅ Include key insights and practical information
- ✅ Maintain objective, informative tone

{self._add_custom_instructions(custom_instructions)}

## Success Criteria
Your task is complete when you have:
1. Processed all {len(chunk_ids)} chunks successfully
2. Created well-structured summaries within word limits
3. Saved all summaries to the database
4. Confirmed all save operations successful"""

        return prompt

    def _generate_document_summary_prompt(
        self,
        document_ids: List[int],
        detail_level: str,
        word_counts: Dict[str, int],
        focus_text: str,
        custom_instructions: Optional[str],
        output_format: str,
    ) -> str:
        """Generate prompt for document-level summaries."""

        if len(document_ids) == 1:
            doc_id = document_ids[0]
            prompt = f"""# AI Task: Create {detail_level.title()} Document Summary

## Context
You are an expert content analyst with access to the Study Buddy MCP server. Your task is to create a {detail_level} summary ({word_counts['min']}-{word_counts['max']} words) of an entire document, focusing on {focus_text}.

## Instructions

### Step 1: Analyze Document Structure
First, understand the document organization:
```
get_document_structure(document_id={doc_id})
```

### Step 2: Review Key Content
Based on the structure, retrieve important sections:
```
get_chunk_content(chunk_id=[RELEVANT_CHUNK_IDS])
```
*Select chunks that best represent the document's main content*

### Step 3: Create Comprehensive Summary
Generate a {detail_level} document summary with these requirements:
- **Length**: {word_counts['min']}-{word_counts['max']} words
- **Format**: Well-structured {output_format}
- **Focus**: Emphasize {focus_text}
- **Scope**: Cover the document's main themes and insights
- **Structure**: Use clear headings and logical flow

### Step 4: Save Result
Save your document summary using:
```
save_summary(
    document_id={doc_id},
    summary_type="{detail_level}",
    summary_content="[Your complete summary here]",
    model_name="gpt-4"
)
```

## Quality Requirements
- ✅ Provide comprehensive document overview
- ✅ Stay within word count limits
- ✅ Focus on specified areas: {focus_text}
- ✅ Use proper {output_format} formatting
- ✅ Include key insights from multiple sections
- ✅ Maintain objective, informative tone

{self._add_custom_instructions(custom_instructions)}

## Success Criteria
Your task is complete when you have:
1. Analyzed the document structure
2. Reviewed key content sections
3. Created a comprehensive summary within word limits
4. Saved the summary to the database
5. Confirmed successful save operation"""

        else:
            # Multiple documents - comparison summary
            doc_list = ", ".join(str(did) for did in document_ids)
            prompt = f"""# AI Task: Create Comparative Analysis of Multiple Documents

## Context
You are an expert content analyst with access to the Study Buddy MCP server. Your task is to create a {detail_level} comparative analysis ({word_counts['min']}-{word_counts['max']} words) of {len(document_ids)} documents, focusing on {focus_text}.

## Target Documents
Analyze these document IDs: {doc_list}

## Instructions

### Step 1: Analyze Each Document
For each document:
1. Get structure: `get_document_structure(document_id=[DOC_ID])`
2. Review key content from representative chunks
3. Identify main themes related to: {focus_text}

### Step 2: Create Comparative Analysis
Generate analysis covering:
- **Common Themes**: Shared concepts across documents
- **Key Differences**: Unique perspectives or approaches
- **Focus Areas**: Detailed analysis of {focus_text}
- **Insights**: Cross-document connections and patterns
- **Summary**: Integrated understanding

### Step 3: Save Results
Create individual summaries for each document if needed, or one comparative summary.

## Quality Requirements
- ✅ Compare and contrast effectively
- ✅ Stay within {word_counts['min']}-{word_counts['max']} word limits
- ✅ Focus on specified areas: {focus_text}
- ✅ Use proper {output_format} formatting
- ✅ Provide balanced coverage of all documents

{self._add_custom_instructions(custom_instructions)}

## Success Criteria
Your task is complete when you have:
1. Analyzed all {len(document_ids)} documents
2. Created comprehensive comparative analysis
3. Saved appropriate summaries to the database
4. Confirmed all operations successful"""

        return prompt

    def _add_custom_instructions(self, custom_instructions: Optional[str]) -> str:
        """Add custom instructions section if provided."""
        if custom_instructions:
            return f"""
## Additional Instructions
{custom_instructions}"""
        return ""
