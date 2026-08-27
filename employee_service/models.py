from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Date
from datetime import date

db = SQLAlchemy()

class Employee(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(unique=True , nullable=False)
    position: Mapped[str] = mapped_column(nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    salary: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(nullable=False)
    department_id: Mapped[int] = mapped_column(nullable=False)
