def validate_year_input(text: str) -> int | None:
    """
    Проверяет, что текст — это год в диапазоне от 1900 до 2025.
    Возвращает число или None, если невалидно.
    """
    try:
        year = int(text)
        if 1990 <= year <= 2025:
            return year
    except ValueError:
        pass
    return None

