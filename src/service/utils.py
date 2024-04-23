def get_targets(position: int) -> tuple[int, int]:
    """Метод для получения страницы и позиции"""
    if position > 100:
        return (position // 100) + 1, position % 100

    return 1, position


def get_clean_position(page: int, position: int) -> int:
    """Метод для получения исходного числа позиции"""
    if page > 1:
        return ((page - 1) * 100) + position

    return (page * 100) + position