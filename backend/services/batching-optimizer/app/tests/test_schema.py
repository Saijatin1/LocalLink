from datetime import datetime

from app.schemas.batch_request import BatchRequest

payload = {
    "orders": [
        {
            "order_id": "O1",
            "vendor_location": {
                "latitude": 17.45,
                "longitude": 78.38
            },
            "customer_location": {
                "latitude": 17.46,
                "longitude": 78.40
            },
            "ready_time": datetime.now().isoformat(),
            "preparation_time": 10,
            "priority": 1
        }
    ],
    "riders": [
        {
            "rider_id": "R1",
            "current_location": {
                "latitude": 17.44,
                "longitude": 78.41
            },
            "capacity": 3,
            "current_load": 0,
            "available": True
        }
    ]
}

request = BatchRequest.model_validate(payload)

print(request)