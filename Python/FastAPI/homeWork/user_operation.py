import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException


app = FastAPI(title="User CRUD API")

# Resolve the data file relative to this module so the path works from any directory.
USERS_FILE = Path(__file__).resolve().parent.parent / "users.json"


def load_users() -> list[dict[str, Any]]:
    with USERS_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_users(users: list[dict[str, Any]]) -> None:
    # Write mode clears the file, so write the full updated list.
    with USERS_FILE.open("w", encoding="utf-8") as file:
        json.dump(users, file)

@app.get("/users")
def get_users():
    # Read on each request so the response includes changes saved by earlier requests.
    return load_users()


@app.get("/users/{user_id}")
def get_user(user_id:int):
    users = load_users()
    for user in users:
        if user["id"]==user_id:
            return user
    # Report a missing ID only after checking the whole list.
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users", status_code=201)
def create_user(user:dict[str,Any]):
    users = load_users()
    requested_user_id = user.get("id")
    if requested_user_id is None:
        # Use the largest ID so gaps in the list do not cause ID collisions.
        user["id"] = max((existing_user["id"] for existing_user in users), default=0) + 1
    else:
        # handling the case where the user provides an ID as string in the request body
        if type(requested_user_id) is not int:
            raise HTTPException(status_code=422, detail="User ID must be an integer")
        # Reject a duplicate before changing the stored records.
        for existing_user in users:
            if existing_user["id"] == requested_user_id:
                raise HTTPException(status_code=409, detail="User already exists")
    users.append(user)
    save_users(users)
    return user

@app.put("/users/{user_id}")
def replace_user(user_id: int, new_user: dict[str, Any]) -> dict[str, Any]:
    users = load_users()
    for index, existing_user in enumerate(users):
        if existing_user["id"] == user_id:
            # The URL determines the ID, and omitted fields disappear on replacement.
            new_user["id"] = user_id
            users[index] = new_user
            save_users(users)
            return new_user
    raise HTTPException(status_code=404, detail="User not found")

@app.patch("/users/{user_id}")   
def patch_user(user_id: int, user_updates: dict[str, Any]) -> dict[str, Any]:
    users = load_users()
    for index, existing_user in enumerate(users):
        if existing_user["id"] == user_id:
            # Keep omitted fields and apply the supplied values at the top level.
            updated_user = existing_user.copy()
            updated_user.update(user_updates)
            # Keep the record ID selected by the URL.
            updated_user["id"] = user_id
            users[index] = updated_user
            save_users(users)
            return updated_user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    users = load_users()
    for index, existing_user in enumerate(users):
        if existing_user["id"] == user_id:
            # Save the remaining list and return the record removed by pop().
            deleted_user = users.pop(index)
            save_users(users)
            return deleted_user
    raise HTTPException(status_code=404, detail="User not found")
