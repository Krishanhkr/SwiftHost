import os
import json
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta

# Mocked imports for demonstration since these would require actual API keys
# In a real implementation, you would need to install and configure these properly
class MockOpenAI:
    def __init__(self, api_key=None):
        self.chat = MockChatCompletions()

class MockChatCompletions:
    def create(self, model, messages):
        # This is a mock implementation that returns fake data based on the prompt
        content = messages[0]["content"]
        if "user entries" in content:
            return MockResponse(generate_mock_users(50))
        elif "credentials" in content:
            return MockResponse(generate_mock_credentials())
        else:
            return MockResponse({"error": "Unknown request"})

class MockResponse:
    def __init__(self, content):
        self.choices = [MockChoice(content)]

class MockChoice:
    def __init__(self, content):
        self.message = MockMessage(json.dumps(content))

class MockMessage:
    def __init__(self, content):
        self.content = content

def generate_mock_users(count):
    faker = Faker()
    users = []
    corporate_domains = ["acme.com", "example.org", "techinc.co", "dataflow.net", "cloudpeak.io"]
    
    for _ in range(count):
        domain_type = random.random()
        if domain_type < 0.3:  # 30% gmail
            email_domain = "gmail.com"
        elif domain_type < 0.7:  # 40% corporate
            email_domain = random.choice(corporate_domains)
        else:  # 30% other
            email_domain = faker.domain_name()
            
        # Job titles with realistic distribution
        job_titles = [
            "Software Engineer", "Project Manager", "Data Analyst", 
            "Marketing Specialist", "HR Coordinator", "Systems Administrator",
            "Product Manager", "Business Analyst", "UX Designer",
            "Customer Support Specialist", "Sales Representative"
        ]
        
        # Date formats with intentional inconsistency
        if random.random() < 0.5:
            date_format = faker.date_this_decade().strftime("%m/%d/%Y")
        else:
            date_format = faker.date_this_decade().strftime("%d-%m-%Y")
            
        # Password patterns (15% with reuse patterns)
        if random.random() < 0.15:
            # Simulate password reuse with minor variations
            base_password = faker.password(length=8)
            password = f"{base_password}{random.choice(['!', '1', '123', '@'])}"
        else:
            password = faker.password(length=random.randint(8, 14))
            
        users.append({
            "id": faker.uuid4(),
            "name": faker.name(),
            "email": f"{faker.user_name()}@{email_domain}",
            "job_title": random.choice(job_titles),
            "registration_date": date_format,
            "last_login": faker.date_time_this_month().isoformat(),
            "password_hash": f"$2a$10${faker.md5()}",
            "password_hint": password if random.random() < 0.05 else None  # 5% have plaintext passwords as "hints"
        })
    
    return users

def generate_mock_credentials():
    faker = Faker()
    return {
        "ssh_keys": [faker.sha256() for _ in range(5)],
        "aws_tokens": [f"AWS_{faker.pystr(20)}" for _ in range(3)],
        "db_connections": [{
            "host": faker.ipv4(),
            "user": faker.user_name(),
            "password": faker.password(length=12),
            "database": faker.word()
        } for _ in range(random.randint(2, 5))]
    }

# Mock for StyleGAN3 image generation
def mock_generate_image(seed=None, truncation=0.7, target_size=(512, 512)):
    # In a real implementation, this would use StyleGAN3 to generate an actual image
    # Here we just return a placeholder for the image data
    if seed is None:
        seed = random.randint(0, 10000)
    return {
        "seed": seed,
        "size": target_size,
        "format": "PNG",
        "data": f"mock_image_data_{seed}_{truncation}"
    }

class HoneypotData:
    def __init__(self):
        self.faker = Faker()
        self.client = MockOpenAI(api_key=os.getenv("OPENAI_KEY", "mock_key"))
        
    def _gpt_generate(self, prompt):
        try:
            response = self.client.chat.create(
                model="gpt-4-turbo",
                messages=[{"role": "system", "content": f"""
                    Generate realistic fake {prompt} data for cybersecurity honeypot.
                    Include minor imperfections (typos, inconsistent formats).
                    Output as JSON array.
                """}]
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Error generating data with GPT: {e}")
            # Fallback to local generation
            if "user entries" in prompt:
                return generate_mock_users(50)
            elif "credentials" in prompt:
                return generate_mock_credentials()
            else:
                return {"error": "Failed to generate data"}

    def generate_users(self, count=50):
        return self._gpt_generate(f"""
            {count} user entries with:
            - Realistic email addresses (30% @gmail, 40% corporate domains)
            - Plausible job titles matching industry distributions
            - Mixed date formats (MM/DD/YYYY vs DD-MM-YYYY)
            - 15% entries with password reuse patterns
        """)

    def generate_fake_credentials(self):
        return {
            "ssh_keys": [self.faker.sha256() for _ in range(5)],
            "aws_tokens": [f"AWS_{self.faker.pystr(20)}" for _ in range(3)],
            "db_connections": [{
                "host": self.faker.ipv4(),
                "user": self.faker.user_name(),
                "password": self.faker.password(length=12),
                "database": self.faker.word()
            } for _ in range(random.randint(2, 5))]
        }

    def generate_deepfake_image(self):
        return mock_generate_image(
            seed=np.random.randint(0, 10000),
            truncation=0.7,
            target_size=(512, 512)
        )
        
    def generate_financial_data(self, count=20):
        transactions = []
        for _ in range(count):
            transaction_type = random.choice(["deposit", "withdrawal", "transfer", "payment"])
            amount = round(random.uniform(10, 10000), 2)
            
            # Add some realistic transaction data with occasional errors
            transaction = {
                "id": self.faker.uuid4(),
                "type": transaction_type,
                "amount": amount,
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "status": random.choices(
                    ["completed", "pending", "failed"], 
                    weights=[0.85, 0.1, 0.05]
                )[0],
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
            }
            
            # Add transaction-specific fields
            if transaction_type == "transfer":
                transaction["source_account"] = f"ACCT-{self.faker.numerify('#####')}"
                transaction["destination_account"] = f"ACCT-{self.faker.numerify('#####')}"
            elif transaction_type == "payment":
                transaction["merchant"] = self.faker.company()
                transaction["category"] = random.choice(["retail", "entertainment", "food", "utilities"])
                
            transactions.append(transaction)
            
        return transactions
        
    def generate_system_logs(self, count=30):
        log_types = ["access", "error", "system", "security"]
        log_levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        services = ["web-server", "database", "auth-service", "api-gateway", "cron"]
        
        logs = []
        for _ in range(count):
            log_type = random.choice(log_types)
            service = random.choice(services)
            
            # Generate appropriate message based on log type
            if log_type == "access":
                path = random.choice([
                    "/api/v1/users", "/login", "/admin", "/dashboard", 
                    "/api/v1/transactions", "/settings", "/profile"
                ])
                method = random.choice(["GET", "POST", "PUT", "DELETE"])
                status = random.choice([200, 200, 200, 201, 400, 401, 403, 404, 500])
                message = f"{method} {path} {status}"
                level = "INFO" if status < 400 else "WARNING" if status < 500 else "ERROR"
                
            elif log_type == "error":
                errors = [
                    "Connection refused", "Timeout exceeded", "Unauthorized access",
                    "Invalid input", "Database query failed", "Resource not found"
                ]
                message = random.choice(errors)
                level = random.choices(["WARNING", "ERROR", "CRITICAL"], weights=[0.3, 0.6, 0.1])[0]
                
            elif log_type == "system":
                messages = [
                    "System started", "System shutdown", "Backup completed",
                    "Cache cleared", "Memory usage: {}%".format(random.randint(10, 95)),
                    "CPU usage: {}%".format(random.randint(5, 100))
                ]
                message = random.choice(messages)
                level = "INFO" if "started" in message or "completed" in message else "WARNING" if "usage" in message and random.randint(50, 100) > 80 else "INFO"
                
            else:  # security
                messages = [
                    "Login attempt failed", "Brute force attack detected", 
                    "File permission changed", "Suspicious activity detected",
                    "New SSH key added", "Firewall rule updated"
                ]
                message = random.choice(messages)
                level = random.choices(["WARNING", "ERROR", "CRITICAL"], weights=[0.5, 0.3, 0.2])[0]
            
            timestamp = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59)
            )
            
            logs.append({
                "timestamp": timestamp.isoformat(),
                "service": service,
                "type": log_type,
                "level": level,
                "message": message,
                "host": self.faker.ipv4() if random.random() < 0.7 else "localhost"
            })
            
        # Sort logs by timestamp
        logs.sort(key=lambda x: x["timestamp"])
        return logs 