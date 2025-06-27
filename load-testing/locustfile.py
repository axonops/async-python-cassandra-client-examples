from locust import HttpUser, task, between, events
from faker import Faker
import json
import random
import time
from uuid import uuid4
import logging

fake = Faker()
logger = logging.getLogger(__name__)

# Store some user IDs for read operations
created_user_ids = []
created_document_ids = []


class CassandraUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Create some initial data for testing"""
        # Create a few users to ensure we have data to read
        for _ in range(5):
            user_data = {
                "id": str(uuid4()),
                "username": fake.user_name(),
                "email": fake.email(),
                "profile_data": {
                    "bio": fake.text(max_nb_chars=200),
                    "location": fake.city()
                }
            }
            
            with self.client.post(
                "/api/v1/users",
                json=user_data,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    created_user_ids.append(json.loads(response.text)["id"])
    
    @task(3)
    def create_user(self):
        """Create a new user"""
        user_data = {
            "id": str(uuid4()),
            "username": fake.user_name() + str(time.time()),
            "email": fake.email(),
            "profile_data": {
                "bio": fake.text(max_nb_chars=200),
                "location": fake.city(),
                "age": random.randint(18, 80)
            }
        }
        
        with self.client.post(
            "/api/v1/users",
            json=user_data,
            catch_response=True,
            name="POST /api/v1/users"
        ) as response:
            if response.status_code == 200:
                user = json.loads(response.text)
                created_user_ids.append(user["id"])
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(5)
    def get_user(self):
        """Get a random user"""
        if not created_user_ids:
            return
        
        user_id = random.choice(created_user_ids)
        with self.client.get(
            f"/api/v1/users/{user_id}",
            catch_response=True,
            name="GET /api/v1/users/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Remove non-existent user from list
                created_user_ids.remove(user_id)
                response.success()  # 404 is expected behavior
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def list_users(self):
        """List users with pagination"""
        page = random.randint(1, 5)
        page_size = random.choice([10, 20, 50])
        
        with self.client.get(
            f"/api/v1/users?page={page}&page_size={page_size}",
            catch_response=True,
            name="GET /api/v1/users"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def update_user(self):
        """Update a random user"""
        if not created_user_ids:
            return
        
        user_id = random.choice(created_user_ids)
        update_data = {
            "username": fake.user_name() + "_updated",
            "email": fake.email(),
            "profile_data": {
                "bio": fake.text(max_nb_chars=200),
                "location": fake.city(),
                "updated_at": str(time.time())
            }
        }
        
        with self.client.put(
            f"/api/v1/users/{user_id}",
            json=update_data,
            catch_response=True,
            name="PUT /api/v1/users/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def create_document(self):
        """Create a new document"""
        doc_data = {
            "id": str(uuid4()),
            "title": fake.sentence(nb_words=6),
            "content": fake.text(max_nb_chars=2000),
            "tags": [fake.word() for _ in range(random.randint(1, 5))]
        }
        
        with self.client.post(
            "/api/v1/documents",
            json=doc_data,
            catch_response=True,
            name="POST /api/v1/documents"
        ) as response:
            if response.status_code == 200:
                doc = json.loads(response.text)
                created_document_ids.append(doc["id"])
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(3)
    def get_document(self):
        """Get a random document"""
        if not created_document_ids:
            return
        
        doc_id = random.choice(created_document_ids)
        with self.client.get(
            f"/api/v1/documents/{doc_id}",
            catch_response=True,
            name="GET /api/v1/documents/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                created_document_ids.remove(doc_id)
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def batch_create_users(self):
        """Create multiple users in batch"""
        batch_size = random.randint(5, 20)
        users = []
        
        for _ in range(batch_size):
            users.append({
                "id": str(uuid4()),
                "username": fake.user_name() + str(time.time()),
                "email": fake.email(),
                "profile_data": {
                    "bio": fake.text(max_nb_chars=100),
                    "batch": True
                }
            })
        
        with self.client.post(
            "/api/v1/users/batch",
            json=users,
            catch_response=True,
            name="POST /api/v1/users/batch"
        ) as response:
            if response.status_code == 200:
                response.success()
                # Add created IDs to our list
                for user in json.loads(response.text):
                    created_user_ids.append(user["id"])
            else:
                response.failure(f"Failed with status {response.status_code}")


class StreamingUser(HttpUser):
    """User class for testing streaming endpoints"""
    wait_time = between(1, 3)
    
    @task(3)
    def stream_sensor_data(self):
        """Stream sensor data"""
        params = {
            "batch_size": random.choice([50, 100, 200])
        }
        
        with self.client.get(
            "/api/v1/stream/sensor-data",
            params=params,
            stream=True,
            catch_response=True,
            name="GET /api/v1/stream/sensor-data"
        ) as response:
            if response.status_code == 200:
                # Consume the stream
                lines_read = 0
                for line in response.iter_lines():
                    if line:
                        lines_read += 1
                        if lines_read > 1000:  # Limit for testing
                            break
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(2)
    def stream_documents(self):
        """Stream documents"""
        params = {
            "page_size": random.choice([50, 100])
        }
        
        with self.client.get(
            "/api/v1/stream/documents",
            params=params,
            stream=True,
            catch_response=True,
            name="GET /api/v1/stream/documents"
        ) as response:
            if response.status_code == 200:
                # Consume the stream
                lines_read = 0
                for line in response.iter_lines():
                    if line:
                        lines_read += 1
                        if lines_read > 500:  # Limit for testing
                            break
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(1)
    def generate_sensor_data(self):
        """Generate sensor data for streaming tests"""
        count = random.choice([100, 500, 1000])
        
        with self.client.post(
            f"/api/v1/sensor-data/generate/{count}",
            catch_response=True,
            name="POST /api/v1/sensor-data/generate/{count}"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """Simulates a realistic mixed workload"""
    wait_time = between(0.5, 2)
    
    tasks = {
        CassandraUser: 8,  # 80% CRUD operations
        StreamingUser: 2   # 20% streaming operations
    }


# Event handlers for test statistics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logger.info("Load test starting...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    logger.info("Load test complete")
    logger.info(f"Total users created: {len(created_user_ids)}")
    logger.info(f"Total documents created: {len(created_document_ids)}")