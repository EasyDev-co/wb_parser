from apps.pars_settings.models import Position, Query

from django.db import transaction


class QueryUpdater:
    @staticmethod
    def update_position(query: Query, updated_position: int) \
            -> tuple[Position | None, bool]:
        """Создаем новую позицию и проверяем упал ли товар"""
        position = Position(
                query=query,
                current_position=updated_position,
                target_position=query.target_position
            )

        return position


def bulk_create_positions(positions: list[Position]):
    with transaction.atomic():
        Position.objects.bulk_create(positions)
