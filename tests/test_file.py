import pytest
from app import create_app
from app.services.redis_client import redis_client


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    from app import limiter 
    limiter.enabled = False  
    with app.test_client() as client:
        yield client

@pytest.fixture()
def register(client):
    
    client.post("/register", json={
        "email": "sheikh@joyeb.com",
        "password": "123454321"
    })

    
    otp = redis_client.get("otp:sheikh@joyeb.com")

    
    client.post("/verify-otp", json={
        "email": "sheikh@joyeb.com",
        "otp": otp
    })

@pytest.fixture()
def user_token(client, register):
    response = client.post("/login", json={
        "email": "sheikh@joyeb.com",
        "password": "123454321"
    })
    data = response.get_json()
    assert response.status_code == 200, f"Login failed: {data}"
    return data["token"]
def test_login(client,register):
    response=client.post("/login",json={
        "email" : "sheikh@joyeb.com",
        "password" : "123454321"
    })
    assert response.status_code==200
    assert "token" in response.get_json()
def test_login_wrong_pass(client,register):
    response=client.post("/login",json={
        "email" : "sheikh@joyeb.com",
        "password" : "ttttt"
    })
    assert response.status_code==401
def test_add_exp(client,user_token):
    response=client.post("/add",json={
        "title" : "Lunch",
        "amount" : 2000,
        "category" : "Food",
        "date" : "2026-04-12"}, headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==201
def test_add_exp_without_login(client):
    response=client.post("/add",json={
        "title" : "Lunch",
        "amount" : 2000,
        "category" : "Food",
        "date" : "2026-04-12"})
    assert response.status_code==401
def test_view_exp(client,user_token):
    response=client.get("/view", headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==200
def test_search(client,user_token):
    response=client.post("/search",json={
        "category" : "Food"},headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==200
def test_total(client,user_token):
    response=client.get("/view_total",json={
        "title" : "Lunch"},headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==200
def test_delete(client,user_token):
    client.post("/add", json={
        "title": "Lunch",
        "amount": 2000,
        "category": "Food",
        "date": "2026-04-12"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    response=client.delete("/delete",json={
        "title" : "Lunch"},headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==201
def test_logout(client,user_token):
    response=client.post("/logout",headers={"Authorization" : f"Bearer {user_token}"})
    assert response.status_code==200
def test_logout_success(client,user_token):
    client.post("/logout",headers={"Authorization" : f"Bearer {user_token}"})
    response=client.get("/view_total",headers={
            "Authorization" : f"Bearer {user_token}"
        })
    assert response.status_code==401
def test_inputs(client,user_token):
    response=client.post("/add", json={
        "title": "   ",
        "amount": 2000,
        "category": "Food",
        "date": "2026-04-12"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code==422
def test_input_integer(client,user_token):
    response=client.post("/add", json={
        "title": "Lunch   ",
        "amount": -12,
        "category": "Food",
        "date": "2026-04-12"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code==422
def test_search_by_date(client,user_token):
    client.post("/add", json={
        "title": "Lunch   ",
        "amount": 1000,
        "category": "Food",
        "date": "2026-04-12"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    client.post("/add", json={
        "title": "Lunch   ",
        "amount": 1000,
        "category": "Food",
        "date": "2026-04-13"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    response=client.post("/date_range",json={
        "start_date" : "2026-04-12",
        "end_date" : "2026-04-14"
    },
        headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code==200