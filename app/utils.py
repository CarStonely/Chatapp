def get_room_id(user1_id, user2_id):
    return f"room:{min(user1_id, user2_id)}:{max(user1_id, user2_id)}"
