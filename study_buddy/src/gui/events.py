"""
Study Buddy GUI Event System

This module provides the event system infrastructure for the GUI application.
It implements the Observer pattern for loose coupling between components.

Architecture: Clean Architecture Infrastructure Layer
Dependencies: None (pure domain logic)
"""

import logging
import weakref
from typing import Dict, List, Any, Callable, Union
from dataclasses import dataclass
from enum import Enum


@dataclass
class GlobalEvent:
    """Represents a global application event."""
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: float


class EventBus:
    """
    Global event bus for application-wide communication.
    
    Implements observer pattern for loose coupling between components.
    Follows SOLID principles:
    - SRP: Only handles event publishing and subscription
    - OCP: New event types can be added without modification
    - DIP: Components depend on this abstraction, not concrete implementations
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Union[weakref.WeakMethod, weakref.ref]]] = {}
        self._logger = logging.getLogger(f"{__name__}.EventBus")
    
    def subscribe(self, event_type: str, handler: Callable[[GlobalEvent], None]) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Callback function to handle events
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        # Use weak references for methods, regular storage for functions
        try:
            # Try to create a weak reference for bound methods
            weak_handler = weakref.WeakMethod(handler)
        except TypeError:
            # For functions and other callables, use weakref.ref
            weak_handler = weakref.ref(handler)
        
        self._subscribers[event_type].append(weak_handler)
        self._logger.debug(f"Subscribed to event type: {event_type}")
    
    def publish(self, event: GlobalEvent) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
        """
        self._logger.debug(f"Publishing event: {event.event_type}")
        
        if event.event_type in self._subscribers:
            # Clean up dead weak references and call live ones
            live_handlers = []
            for weak_handler in self._subscribers[event.event_type]:
                handler = weak_handler()
                if handler is not None:
                    try:
                        handler(event)
                        live_handlers.append(weak_handler)
                    except Exception as e:
                        self._logger.error(f"Error in event handler: {e}", exc_info=True)
            
            self._subscribers[event.event_type] = live_handlers
    
    def unsubscribe_all(self, event_type: str) -> None:
        """Remove all subscribers for an event type."""
        if event_type in self._subscribers:
            del self._subscribers[event_type]