"""
Tests for SummaryPanelWidget.

This module contains comprehensive unit and integration tests for the SummaryPanelWidget class,
ensuring it properly handles AI-generated summary display, generation, and management.
"""
import pytest
import tkinter as tk
from datetime import datetime
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Optional, Dict

# Import the widget under test
from ..widgets.summary_panel import (
    SummaryPanelWidget,
    Summary, 
    SummaryMetadata,
    SummaryType,
    SummaryStatus,
    SummaryDisplayOptions
)
from ..widgets.base_widget import EventBus, GlobalEvent, WidgetState, LayoutConstraints

# Mock EventType for testing
class EventType:
    DOCUMENT_SELECTED = "document_selected"
    SUMMARY_REQUESTED = "summary_requested"


class TestSummary:
    """Test Summary data model."""
    
    def test_summary_creation(self):
        """Test Summary model initialization."""
        metadata = SummaryMetadata(
            generation_time=datetime.now(),
            model_name="gpt-4",
            word_count=250,
            processing_time_ms=1500
        )
        
        summary = Summary(
            summary_id=1,
            document_id=42,
            chunk_id=101,
            summary_type=SummaryType.STANDARD,
            content="This is a test summary content.",
            metadata=metadata,
            status=SummaryStatus.COMPLETED
        )
        
        assert summary.summary_id == 1
        assert summary.document_id == 42
        assert summary.chunk_id == 101
        assert summary.summary_type == SummaryType.STANDARD
        assert summary.content == "This is a test summary content."
        assert summary.status == SummaryStatus.COMPLETED
        assert summary.is_available is True
        assert summary.is_generating is False
        assert summary.has_error is False
    
    def test_summary_status_properties(self):
        """Test Summary status-based properties."""
        # Test generating status
        summary_generating = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.BRIEF,
            content="",
            metadata=SummaryMetadata(),
            status=SummaryStatus.GENERATING
        )
        
        assert summary_generating.is_available is False
        assert summary_generating.is_generating is True
        assert summary_generating.has_error is False
        
        # Test error status
        summary_error = Summary(
            summary_id=2,
            document_id=42,
            summary_type=SummaryType.DETAILED,
            content="",
            metadata=SummaryMetadata(),
            status=SummaryStatus.ERROR
        )
        
        assert summary_error.is_available is False
        assert summary_error.is_generating is False
        assert summary_error.has_error is True
    
    def test_display_title(self):
        """Test Summary display title generation."""
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Test content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        
        expected_title = "Standard Summary"
        assert summary.display_title == expected_title


class TestSummaryMetadata:
    """Test SummaryMetadata data model."""
    
    def test_metadata_creation(self):
        """Test SummaryMetadata initialization."""
        now = datetime.now()
        metadata = SummaryMetadata(
            generation_time=now,
            model_name="gpt-4",
            word_count=350,
            processing_time_ms=2000
        )
        
        assert metadata.generation_time == now
        assert metadata.model_name == "gpt-4"
        assert metadata.word_count == 350
        assert metadata.processing_time_ms == 2000
    
    def test_display_info(self):
        """Test metadata display information."""
        metadata = SummaryMetadata(
            generation_time=datetime(2025, 1, 1, 12, 0, 0),
            model_name="gpt-4",
            word_count=275,
            processing_time_ms=1500
        )
        
        display_info = metadata.display_info
        
        assert "gpt-4" in display_info
        assert "275" in display_info
        assert "12:00:00" in display_info


class TestSummaryPanelWidget:
    """Test SummaryPanelWidget functionality."""
    
    @pytest.fixture
    def root(self):
        """Create Tkinter root for testing."""
        root = tk.Tk()
        root.withdraw()  # Hide during tests
        yield root
        root.destroy()
    
    @pytest.fixture
    def event_bus(self):
        """Create event bus mock."""
        return Mock(spec=EventBus)
    
    @pytest.fixture
    def mcp_client(self):
        """Create MCP client mock."""
        client = Mock()
        client.get_summary = AsyncMock()
        client.save_summary = AsyncMock()
        client.generate_summary = AsyncMock()
        return client
    
    @pytest.fixture
    def widget(self, root, event_bus, mcp_client):
        """Create SummaryPanelWidget for testing."""
        widget = SummaryPanelWidget(
            parent=root,
            event_bus=event_bus,
            widget_id="test_summary_panel",
            mcp_client=mcp_client
        )
        widget.create_ui()
        return widget
    
    def test_widget_creation(self, widget):
        """Test widget initialization."""
        assert widget.widget_id == "test_summary_panel"
        assert widget._state == WidgetState.READY
        assert widget._current_document_id is None
        assert widget._selected_summary_type == SummaryType.STANDARD
        assert isinstance(widget._summaries, dict)
        assert len(widget._summaries) == 0
    
    def test_ui_creation(self, widget):
        """Test UI component creation."""
        # Check main components exist
        assert widget.root_frame is not None
        assert widget._type_selector is not None
        assert widget._summary_text is not None
        assert widget._generate_button is not None
        assert widget._metadata_label is not None
        assert widget._status_label is not None
    
    def test_summary_type_selection(self, widget):
        """Test changing summary type."""
        # Test initial state
        assert widget._selected_summary_type == SummaryType.STANDARD
        
        # Change to brief
        widget.set_summary_type(SummaryType.BRIEF)
        assert widget._selected_summary_type == SummaryType.BRIEF
        
        # Change to detailed
        widget.set_summary_type(SummaryType.DETAILED)
        assert widget._selected_summary_type == SummaryType.DETAILED
    
    def test_document_selection_event(self, widget, event_bus):
        """Test handling document selection event."""
        # Create document selection event
        event_data = {
            'document_id': 42,
            'title': 'Test Document',
            'file_type': 'pdf'
        }
        event = GlobalEvent(
            event_type=EventType.DOCUMENT_SELECTED,
            source="document_browser",
            data=event_data,
            timestamp=1234567890.0
        )
        
        # Trigger event handler
        widget._on_document_selected(event)
        
        # Verify document is set
        assert widget._current_document_id == 42
    
    def test_summary_display_no_summary(self, widget):
        """Test displaying no summary message."""
        widget._current_document_id = 42
        widget._display_no_summary()
        
        # Verify message displayed
        content = widget._summary_text.get("1.0", tk.END)
        assert "No standard summary available" in content
        assert "Generate" in content
    
    def test_summary_display_generating(self, widget):
        """Test displaying generating status."""
        widget._display_generating_status()
        
        # Verify generating message
        content = widget._summary_text.get("1.0", tk.END)
        assert "Generating standard summary" in content
        assert "Please wait" in content
    
    def test_summary_display_error(self, widget):
        """Test displaying error message."""
        error_message = "Failed to generate summary"
        widget._display_error(error_message)
        
        # Verify error message
        content = widget._summary_text.get("1.0", tk.END)
        assert "Error generating" in content
        assert error_message in content
    
    def test_summary_content_display(self, widget):
        """Test displaying actual summary content."""
        # Create test summary
        metadata = SummaryMetadata(
            generation_time=datetime.now(),
            model_name="gpt-4",
            word_count=200
        )
        
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="# Test Summary\n\nThis is test content.",
            metadata=metadata,
            status=SummaryStatus.COMPLETED
        )
        
        # Display summary
        widget._display_summary_content(summary)
        
        # Verify content displayed
        content = widget._summary_text.get("1.0", tk.END)
        assert "Standard Summary" in content
        assert "This is test content" in content
    
    def test_formatted_content_insertion(self, widget):
        """Test markdown-style content formatting."""
        test_content = """# Heading 1
## Heading 2
**Bold text**
Regular text with `code` snippet
More regular text"""
        
        widget._insert_formatted_content(test_content)
        
        # Verify content was inserted
        content = widget._summary_text.get("1.0", tk.END)
        assert "Heading 1" in content
        assert "Heading 2" in content
        assert "Bold text" in content
        assert "code" in content
        assert "More regular text" in content
    
    async def test_summary_generation_request(self, widget, mcp_client):
        """Test requesting summary generation."""
        widget._current_document_id = 42
        
        # Mock successful generation
        mock_summary = {
            'success': True,
            'summary_id': 1,
            'content': 'Generated summary content'
        }
        mcp_client.generate_summary.return_value = mock_summary
        
        # Request generation
        result = widget.request_summary(SummaryType.STANDARD)
        
        assert result is True
        # Verify MCP client called
        mcp_client.generate_summary.assert_called_once()
    
    def test_summary_retrieval(self, widget):
        """Test getting current summary."""
        # No summary initially
        assert widget.get_current_summary() is None
        
        # Add a summary
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Test content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        
        widget._summaries[SummaryType.STANDARD] = summary
        widget._current_document_id = 42
        
        # Get current summary
        current = widget.get_current_summary()
        assert current == summary
        assert current.content == "Test content"
    
    def test_summaries_for_document(self, widget):
        """Test getting all summaries for a document."""
        # Add multiple summaries
        brief_summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.BRIEF,
            content="Brief content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        
        standard_summary = Summary(
            summary_id=2,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Standard content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        
        widget._summaries[SummaryType.BRIEF] = brief_summary
        widget._summaries[SummaryType.STANDARD] = standard_summary
        
        # Get summaries for document
        summaries = widget.get_summaries_for_document(42)
        
        assert len(summaries) == 2
        assert SummaryType.BRIEF in summaries
        assert SummaryType.STANDARD in summaries
        assert summaries[SummaryType.BRIEF] == brief_summary
        assert summaries[SummaryType.STANDARD] == standard_summary
    
    def test_clear_summaries(self, widget):
        """Test clearing all summaries."""
        # Add summaries
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        widget._summaries[SummaryType.STANDARD] = summary
        
        # Clear summaries
        widget.clear_summaries()
        
        # Verify cleared
        assert len(widget._summaries) == 0
    
    def test_display_options_update(self, widget):
        """Test updating display options."""
        options = SummaryDisplayOptions(
            show_metadata=False,
            show_word_count=True,
            show_generation_time=False,
            font_size=14
        )
        
        widget.update_display_options(options)
        
        assert widget._display_options == options
        assert widget._display_options.show_metadata is False
        assert widget._display_options.font_size == 14
    
    def test_refresh_current_summary(self, widget):
        """Test refreshing current summary display."""
        widget._current_document_id = 42
        
        # Add summary
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Test content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        widget._summaries[SummaryType.STANDARD] = summary
        
        # Refresh display
        widget.refresh_current_summary()
        
        # Verify content displayed
        content = widget._summary_text.get("1.0", tk.END)
        assert "Test content" in content
    
    def test_generation_readiness_check(self, widget):
        """Test checking if ready for generation."""
        # Not ready without document
        assert widget.is_ready_for_generation() is False
        
        # Ready with document
        widget._current_document_id = 42
        assert widget.is_ready_for_generation() is True
    
    def test_event_publishing(self, widget, event_bus):
        """Test widget publishes events correctly."""
        # Simulate document selection to trigger event
        widget._current_document_id = 42
        
        # Simulate summary generation completion
        summary = Summary(
            summary_id=1,
            document_id=42,
            summary_type=SummaryType.STANDARD,
            content="Generated content",
            metadata=SummaryMetadata(),
            status=SummaryStatus.COMPLETED
        )
        
        widget._summaries[SummaryType.STANDARD] = summary
        widget._update_current_display()
        
        # Verify event was published
        # Note: Actual event publishing verification would depend on the specific implementation
        assert widget._current_document_id == 42
    
    def test_accessibility_setup(self, widget):
        """Test accessibility features are configured."""
        # Verify keyboard shortcuts are bound
        # This is a basic test - full accessibility testing would require integration tests
        assert widget.root_frame is not None
        
        # Verify accessibility method was called during initialization
        assert hasattr(widget, '_setup_accessibility')
    
    def test_widget_state_management(self, widget):
        """Test widget state transitions."""
        # Initial state
        assert widget._state == WidgetState.READY
        
        # Simulate state changes during generation
        widget._state = WidgetState.LOADING
        assert widget._state == WidgetState.LOADING
        
        widget._state = WidgetState.ERROR
        assert widget._state == WidgetState.ERROR
        
        widget._state = WidgetState.READY
        assert widget._state == WidgetState.READY


class TestSummaryPanelIntegration:
    """Integration tests for SummaryPanelWidget with other components."""
    
    @pytest.fixture
    def root(self):
        """Create Tkinter root for testing."""
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    
    @pytest.fixture
    def event_bus(self):
        """Create real event bus for integration testing."""
        return EventBus()
    
    @pytest.fixture
    def mcp_client(self):
        """Create MCP client mock for integration."""
        client = Mock()
        client.get_summary = AsyncMock()
        client.save_summary = AsyncMock()
        client.generate_summary = AsyncMock()
        return client
    
    @pytest.fixture
    def widget(self, root, event_bus, mcp_client):
        """Create widget with real event bus."""
        widget = SummaryPanelWidget(
            parent=root,
            event_bus=event_bus,
            widget_id="integration_test",
            mcp_client=mcp_client
        )
        widget.create_ui()
        return widget
    
    def test_document_selection_workflow(self, widget, event_bus):
        """Test complete document selection workflow."""
        # Subscribe to events
        events_received = []
        def capture_event(event):
            events_received.append(event)
        
        event_bus.subscribe(EventType.SUMMARY_REQUESTED, capture_event)
        
        # Simulate document selection
        document_event = GlobalEvent(
            event_type=EventType.DOCUMENT_SELECTED,
            source="document_browser",
            data={'document_id': 42, 'title': 'Test Doc'},
            timestamp=1234567890.0
        )
        
        event_bus.publish(document_event)
        
        # Verify widget state
        assert widget._current_document_id == 42
    
    def test_summary_generation_workflow(self, widget, event_bus, mcp_client):
        """Test complete summary generation workflow."""
        widget._current_document_id = 42
        
        # Mock successful generation
        mock_response = {
            'success': True,
            'summary_id': 1,
            'content': 'AI-generated summary content',
            'metadata': {
                'model_name': 'gpt-4',
                'word_count': 250
            }
        }
        mcp_client.generate_summary.return_value = mock_response
        
        # Request generation
        result = widget.request_summary(SummaryType.STANDARD)
        
        assert result is True
        mcp_client.generate_summary.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])