from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.crud.charity_projects as crud
from app.models import CharityProject, Donation
from app.schemas.charity_projects import ProjectUpdate


def get_current_time() -> datetime:
    """Получение текущих даты и времени."""
    return datetime.now()


async def check_name_duplicate(
        name: str,
        session: AsyncSession,
) -> None:
    """Проверка имени проекта на уникальность."""
    room_id = await crud.crud_charity_projects.get_project_by_name(
        name=name, session=session
    )
    if room_id is not None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Проект с таким именем уже существует!",
        )


async def check_project_exists(
        project_id: int,
        session: AsyncSession,
) -> CharityProject:
    """Проверка проекта по id."""
    project = await crud.crud_charity_projects.get(project_id, session)
    if project is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Проект {project_id} не найден!",
        )
    return project


async def check_project_before_update(
        project: CharityProject,
        project_id: int,
        obj_in: ProjectUpdate,
        session: AsyncSession,
) -> None:
    """Проверка проекта перед обновлением."""
    await check_project_exists(project_id, session)
    if project.fully_invested is True or project.close_date:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Закрытый проект нельзя редактировать!",
        )
    if obj_in.name is not None and obj_in.name != project.name:
        await check_name_duplicate(
            name=obj_in.name, session=session
        )
    if obj_in.full_amount and project.invested_amount > obj_in.full_amount:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=(f"Новая сумма проекта {obj_in.full_amount} не может быть"
                    " меньше внесенной - {project.invested_amount}!",)
        )


async def check_project_before_delete(project_id, session) -> CharityProject:
    """Проверка проекта перед удалением."""
    project = await check_project_exists(project_id, session)
    if project.invested_amount > 0:
        await crud.crud_charity_projects.close_project(project, session)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="В проект были внесены средства, не подлежит удалению!",
        )
    return project


async def invest_it(
        session: AsyncSession,
) -> None:
    """Функция инвестирования."""
    project_objs = await session.execute(
        select(CharityProject)
        .where(CharityProject.close_date.is_(None))
        .order_by(asc(CharityProject.create_date))
    )
    project_objs = project_objs.scalars().all()

    project_sum = await session.execute(
        select(
            func.sum(CharityProject.full_amount),
            func.sum(CharityProject.invested_amount),
        ).where(CharityProject.close_date.is_(None))
    )
    project_sum = project_sum.fetchall()
    project_full = 0 if project_sum[0][0] is None else project_sum[0][0]
    project_invested = (0 if project_sum[0][1] is None
                        else project_sum[0][1])

    to_invest = project_full - project_invested

    donation_objs = await session.execute(
        select(Donation)
        .where(Donation.close_date.is_(None))
        .order_by(asc(Donation.create_date))
    )
    donation_objs = donation_objs.scalars().all()

    donation_sum = await session.execute(
        select(
            func.sum(Donation.full_amount), func.sum(Donation.invested_amount)
        ).where(Donation.close_date.is_(None))
    )
    donation_sum = donation_sum.fetchall()
    donation_full = 0 if donation_sum[0][0] is None else donation_sum[0][0]
    donation_invested = (0 if donation_sum[0][1] is None
                         else donation_sum[0][1])

    to_be_invested = donation_full - donation_invested

    for project in project_objs:
        if to_be_invested > 0 and to_invest > 0:
            project_to_invest = project.full_amount - project.invested_amount
            if project_to_invest <= to_be_invested:
                setattr(project, "invested_amount", project.full_amount)
                setattr(project, "close_date", get_current_time())
                setattr(project, "fully_invested", True)
                to_invest = to_invest - project_to_invest
                to_be_invested = to_be_invested - project_to_invest
                session.add(project)
            else:
                setattr(
                    project,
                    "invested_amount",
                    project.invested_amount + to_be_invested,
                )
                session.add(project)
                break
        else:
            break
    to_be_invested = donation_full - donation_invested
    to_invest = project_full - project_invested
    to_be_invested = min(to_be_invested, to_invest)

    for donation in donation_objs:
        donation_to_be_invested = \
            (donation.full_amount - donation.invested_amount)
        if donation_to_be_invested <= to_be_invested:
            setattr(donation, "invested_amount", donation.full_amount)
            setattr(donation, "close_date", get_current_time())
            setattr(donation, "fully_invested", True)
            to_be_invested = to_be_invested - donation_to_be_invested
            session.add(donation)

        else:
            setattr(
                donation,
                "invested_amount",
                donation.invested_amount + to_be_invested,
            )
            session.add(donation)
            break

    await session.commit()
