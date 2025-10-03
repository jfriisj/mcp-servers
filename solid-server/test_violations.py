"""
Test file with various SOLID principle violations for demonstration purposes.
This file intentionally violates SOLID principles to test the analyzer.
"""

import json
from typing import List, Dict, Any


# SRP Violation - Employee class doing too many things
class Employee:
    def __init__(self, name: str, salary: float):
        self.name = name
        self.salary = salary
    
    # Business logic
    def calculate_pay(self) -> float:
        return self.salary
    
    def calculate_bonus(self) -> float:
        return self.salary * 0.1
    
    # Data persistence - violates SRP
    def save_to_database(self) -> None:
        print(f"Saving {self.name} to database")
    
    def load_from_database(self, employee_id: int) -> None:
        print(f"Loading employee {employee_id}")
    
    # Reporting - violates SRP  
    def generate_report(self) -> str:
        return f"Employee Report: {self.name}, Salary: {self.salary}"
    
    def export_to_json(self) -> str:
        return json.dumps({"name": self.name, "salary": self.salary})
    
    # UI/Display logic - violates SRP
    def display_info(self) -> None:
        print(f"Name: {self.name}")
        print(f"Salary: ${self.salary:,.2f}")
    
    def format_for_display(self) -> Dict[str, Any]:
        return {
            "display_name": self.name.upper(),
            "formatted_salary": f"${self.salary:,.2f}"
        }


# OCP Violation - must modify this function to add new shape types
def calculate_area(shape_type: str, **kwargs) -> float:
    if shape_type == "circle":
        return 3.14159 * kwargs["radius"] ** 2
    elif shape_type == "rectangle":
        return kwargs["width"] * kwargs["height"]
    elif shape_type == "triangle":
        return 0.5 * kwargs["base"] * kwargs["height"]
    elif shape_type == "square":
        return kwargs["side"] ** 2
    # Must add new elif for each shape type - violates OCP
    else:
        raise ValueError(f"Unknown shape type: {shape_type}")


# OCP Violation - type checking instead of polymorphism
def process_animal(animal):
    if isinstance(animal, Dog):
        return f"Walking the dog: {animal.bark()}"
    elif isinstance(animal, Cat):
        return f"Playing with cat: {animal.meow()}"
    elif isinstance(animal, Bird):
        return f"Bird is flying: {animal.fly()}"
    else:
        return "Unknown animal type"


class Animal:
    pass


class Dog(Animal):
    def bark(self):
        return "Woof!"


class Cat(Animal):
    def meow(self):
        return "Meow!"


class Bird(Animal):
    def fly(self):
        return "Flying!"


# LSP Violation - Bird can't fly
class Penguin(Bird):
    def fly(self):
        raise NotImplementedError("Penguins can't fly!")  # LSP violation


# LSP Violation - Rectangle/Square problem
class Rectangle:
    def __init__(self, width: float, height: float):
        self._width = width
        self._height = height
    
    def set_width(self, width: float):
        self._width = width
    
    def set_height(self, height: float):
        self._height = height
    
    def area(self) -> float:
        return self._width * self._height


class Square(Rectangle):
    def __init__(self, side: float):
        super().__init__(side, side)
    
    def set_width(self, width: float):
        # Violates LSP - changes both dimensions unexpectedly
        self._width = width
        self._height = width  # Side effect not expected by client code
    
    def set_height(self, height: float):
        # Violates LSP - changes both dimensions unexpectedly  
        self._width = height
        self._height = height  # Side effect not expected by client code


# ISP Violation - Fat interface
class Worker:
    def work(self):
        pass
    
    def eat(self):
        pass
    
    def sleep(self):
        pass
    
    def take_vacation(self):
        pass
    
    def attend_meeting(self):
        pass
    
    def file_taxes(self):
        pass
    
    def drive_to_work(self):
        pass
    
    def use_computer(self):
        pass
    
    def answer_phone(self):
        pass
    
    def write_reports(self):
        pass


# ISP Violation - Robot forced to implement human-only methods
class Robot(Worker):
    def work(self):
        return "Robot working"
    
    def eat(self):
        raise NotImplementedError("Robots don't eat")  # Forced to implement
    
    def sleep(self):
        raise NotImplementedError("Robots don't sleep")  # Forced to implement
    
    def take_vacation(self):
        raise NotImplementedError("Robots don't take vacation")  # Forced
    
    def attend_meeting(self):
        pass  # Empty implementation - interface bloat
    
    def file_taxes(self):
        pass  # Empty implementation - interface bloat
    
    def drive_to_work(self):
        pass  # Empty implementation - interface bloat
    
    def use_computer(self):
        return "Using computer"
    
    def answer_phone(self):
        pass  # Empty implementation - interface bloat
    
    def write_reports(self):
        pass  # Empty implementation - interface bloat


# DIP Violation - High-level module depends on low-level module
class EmailService:  # Low-level module
    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email to {to}: {subject}")


class SMSService:  # Low-level module
    def send_sms(self, to: str, message: str):
        print(f"Sending SMS to {to}: {message}")


class NotificationManager:  # High-level module
    def __init__(self):
        # DIP violation - directly instantiating concrete classes
        self.email_service = EmailService()
        self.sms_service = SMSService()
    
    def send_notification(self, notification_type: str, to: str, message: str):
        # DIP violation - depending on concrete implementations
        if notification_type == "email":
            self.email_service.send_email(to, "Notification", message)
        elif notification_type == "sms":
            self.sms_service.send_sms(to, message)


# DIP Violation - OrderProcessor directly creates dependencies
class DatabaseConnection:
    def save(self, data):
        print(f"Saving to database: {data}")


class PaymentProcessor:
    def process_payment(self, amount):
        print(f"Processing payment: ${amount}")


class OrderProcessor:
    def __init__(self):
        # DIP violations - creating own dependencies
        self.db = DatabaseConnection()
        self.payment = PaymentProcessor()
    
    def process_order(self, order_data, payment_amount):
        # Tight coupling to concrete classes
        self.payment.process_payment(payment_amount)
        self.db.save(order_data)


# Additional SRP violation - very long method
class ReportGenerator:
    def generate_complex_report(self, data: List[Dict]) -> str:
        """This method is way too long and does too many things - SRP violation."""
        # Data validation
        if not data:
            return "No data provided"
        
        # Data cleaning
        cleaned_data = []
        for item in data:
            if "name" in item and "value" in item:
                cleaned_item = {
                    "name": item["name"].strip().title(),
                    "value": float(item["value"]) if str(item["value"]).replace('.', '').isdigit() else 0.0
                }
                cleaned_data.append(cleaned_item)
        
        # Statistical calculations
        total = sum(item["value"] for item in cleaned_data)
        average = total / len(cleaned_data) if cleaned_data else 0
        maximum = max(item["value"] for item in cleaned_data) if cleaned_data else 0
        minimum = min(item["value"] for item in cleaned_data) if cleaned_data else 0
        
        # Sorting and ranking
        sorted_data = sorted(cleaned_data, key=lambda x: x["value"], reverse=True)
        top_performers = sorted_data[:5]
        bottom_performers = sorted_data[-5:]
        
        # HTML generation
        html_report = "<html><head><title>Report</title></head><body>"
        html_report += f"<h1>Data Analysis Report</h1>"
        html_report += f"<p>Total Records: {len(cleaned_data)}</p>"
        html_report += f"<p>Total Value: ${total:,.2f}</p>"
        html_report += f"<p>Average Value: ${average:,.2f}</p>"
        html_report += f"<p>Maximum Value: ${maximum:,.2f}</p>"
        html_report += f"<p>Minimum Value: ${minimum:,.2f}</p>"
        
        html_report += "<h2>Top Performers</h2><ul>"
        for item in top_performers:
            html_report += f"<li>{item['name']}: ${item['value']:,.2f}</li>"
        html_report += "</ul>"
        
        html_report += "<h2>Bottom Performers</h2><ul>"
        for item in bottom_performers:
            html_report += f"<li>{item['name']}: ${item['value']:,.2f}</li>"
        html_report += "</ul>"
        html_report += "</body></html>"
        
        return html_report