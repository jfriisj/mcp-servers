#!/usr/bin/env python3
"""
Test file for SOLID analysis with some violations
"""

class BadClass:
    """A class that violates SRP by doing too many things"""
    
    def __init__(self):
        self.data = []
        self.file_path = "data.txt"
    
    def add_data(self, item):
        """Add data to collection"""
        self.data.append(item)
    
    def save_to_file(self):
        """Save data to file - this violates SRP"""
        with open(self.file_path, 'w') as f:
            for item in self.data:
                f.write(str(item) + '\n')
    
    def send_email_notification(self):
        """Send email - another SRP violation"""
        print("Email sent")
    
    def calculate_statistics(self):
        """Calculate stats - yet another responsibility"""
        if not self.data:
            return 0
        return len(self.data)