from datetime import datetime

def format_date(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")

def get_medal(index: int) -> str:
    medals = ["🥇", "🥈", "🥉"]
    return medals[index] if index < 3 else f"{index+1}."

def mask_username(username: str, code_name: str = None) -> str:
    if code_name:
        return f"🐾 {code_name}"
    elif username:
        return f"@{username}"
    else:
        return "Студент"