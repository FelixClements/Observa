from typing import Any, Generic, Iterable, Optional, Sequence, TypeVar, Callable
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from plexpy.db.models import Base


ModelT = TypeVar('ModelT', bound=Base)


@dataclass
class DataTableParams:
    draw: int
    start: int = 0
    length: int = 25
    search: Optional[str] = None
    order: list[dict[str, Any]] = field(default_factory=list)
    columns: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DataTableResponse:
    draw: int
    recordsTotal: int
    recordsFiltered: int
    data: list[dict[str, Any]]


class DataTableQueryBuilder:
    def __init__(
        self,
        model: type[Base],
        session: Session,
    ):
        self.model = model
        self.session = session
        self.searchable_columns: list = []
        self.orderable_columns: dict[str, Any] = {}

    def add_searchable(self, *columns: Any) -> 'DataTableQueryBuilder':
        self.searchable_columns.extend(columns)
        return self

    def add_orderable(self, name: str, column: Any) -> 'DataTableQueryBuilder':
        self.orderable_columns[name] = column
        return self

    def execute(
        self,
        params: DataTableParams,
        formatter: Optional[Callable[[Any], dict]] = None,
    ) -> DataTableResponse:
        query = select(self.model)

        if params.search:
            search_filters = [
                col.ilike(f"%{params.search}%")
                for col in self.searchable_columns
            ]
            query = query.where(or_(*search_filters))

        total_query = select(func.count()).select_from(query.subquery())
        total = self.session.execute(total_query).scalar()
        recordsTotal = total or 0

        if params.search:
            recordsFiltered = recordsTotal
        else:
            recordsFiltered = recordsTotal

        if params.order:
            for order_item in params.order:
                col_idx = int(order_item['column'])
                direction = order_item['dir']
                col_name = params.columns[col_idx].get('data')

                if col_name and col_name in self.orderable_columns:
                    col = self.orderable_columns[col_name]
                    if direction == 'desc':
                        query = query.order_by(col.desc())
                    else:
                        query = query.order_by(col.asc())

        query = query.offset(params.start).limit(params.length)

        result = self.session.execute(query)
        rows = result.scalars().all()

        data = [
            formatter(row) if formatter else self._default_formatter(row)
            for row in rows
        ]

        return DataTableResponse(
            draw=params.draw,
            recordsTotal=recordsTotal,
            recordsFiltered=recordsFiltered,
            data=data,
        )

    def _default_formatter(self, row: Any) -> dict:
        return {
            c.name: getattr(row, c.name, None)
            for c in row.__table__.columns
        }


class ExtendedRepository(Generic[ModelT]):
    model: Optional[type[ModelT]] = None

    def __init__(self, session: Session):
        self.session = session

    def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        return instance

    def add_all(self, instances: Iterable[ModelT]) -> list[ModelT]:
        instance_list = list(instances)
        self.session.add_all(instance_list)
        return instance_list

    def delete(self, instance: ModelT) -> None:
        self.session.delete(instance)

    def get(self, model: type[ModelT], primary_key: Any) -> Optional[ModelT]:
        return self.session.get(model, primary_key)

    def get_by_id(self, primary_key: Any) -> Optional[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        return self.session.get(self.model, primary_key)

    def list_all(self) -> Sequence[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        return self.session.execute(select(self.model)).scalars().all()

    def first_by(self, **filters: Any) -> Optional[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        stmt = select(self.model).filter_by(**filters).limit(1)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_by(self, **filters: Any) -> Sequence[ModelT]:
        if self.model is None:
            raise ValueError("Repository model is not set")
        stmt = select(self.model).filter_by(**filters)
        return self.session.execute(stmt).scalars().all()

    def count(self) -> int:
        if self.model is None:
            raise ValueError("Repository model is not set")
        result = self.session.execute(
            select(func.count()).select_from(self.model)
        ).scalar()
        return result or 0

    def exists(self, **filters: Any) -> bool:
        if self.model is None:
            raise ValueError("Repository model is not set")
        stmt = select(self.model).filter_by(**filters).limit(1)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result is not None

    def update(self, instance: ModelT) -> ModelT:
        self.session.flush()
        return instance

    def create_datatable_builder(self) -> DataTableQueryBuilder:
        if self.model is None:
            raise ValueError("Repository model is not set")
        return DataTableQueryBuilder(self.model, self.session)

    def datatable_query(
        self,
        params: DataTableParams,
        searchable_columns: list = None,
        orderable_columns: dict[str, Any] = None,
        formatter: Callable[[Any], dict] = None,
        extra_filters: list = None,
    ) -> DataTableResponse:
        builder = self.create_datatable_builder()

        if searchable_columns:
            builder.add_searchable(*searchable_columns)

        if orderable_columns:
            for name, col in orderable_columns.items():
                builder.add_orderable(name, col)

        query = select(self.model)

        if extra_filters:
            for f in extra_filters:
                query = query.where(f)

        if params.order:
            for order_item in params.order:
                col_idx = int(order_item['column'])
                direction = order_item['dir']
                col_name = params.columns[col_idx].get('data')

                if col_name and col_name in builder.orderable_columns:
                    col = builder.orderable_columns[col_name]
                    if direction == 'desc':
                        query = query.order_by(col.desc())
                    else:
                        query = query.order_by(col.asc())

        total_query = select(func.count()).select_from(self.model)
        recordsTotal = self.session.execute(total_query).scalar() or 0

        filtered_query = query
        if params.search:
            search_filters = [
                col.ilike(f"%{params.search}%")
                for col in builder.searchable_columns
            ]
            filtered_query = filtered_query.where(or_(*search_filters))

        if params.search or extra_filters:
            recordsFiltered = self.session.execute(
                select(func.count()).select_from(filtered_query.subquery())
            ).scalar() or 0
        else:
            recordsFiltered = recordsTotal

        query = query.offset(params.start).limit(params.length)

        result = self.session.execute(query)
        rows = result.scalars().all()

        data = [
            formatter(row) if formatter else self._default_formatter(row)
            for row in rows
        ]

        return DataTableResponse(
            draw=params.draw,
            recordsTotal=recordsTotal,
            recordsFiltered=recordsFiltered,
            data=data,
        )

    def _default_formatter(self, row: Any) -> dict:
        return {
            c.name: getattr(row, c.name, None)
            for c in row.__table__.columns
        }


class Repository(ExtendedRepository[ModelT]):
    def __init__(self, session: Session):
        super().__init__(session)
