from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep, require
from app.api.v1.settings._helpers import _school_id, _require_houses
from app.core.permissions import Permission
from app.models.academic import House
from app.models.school import School
from app.models.staff import PositionPermission, StaffMember, StaffPosition
from app.models.user import User, UserRole
from app.schemas.settings import (
    HouseCreate, HouseUpdate, HouseResponse,
    UserAccountResponse, UserAccountUpdate,
)
from app.schemas.staff import PositionCreate, PositionUpdate, PositionResponse

router = APIRouter()


# ── Positions ─────────────────────────────────────────────────────────────────

def _position_to_response(pos: StaffPosition) -> PositionResponse:
    return PositionResponse(
        id=pos.id,
        name=pos.name,
        code=pos.code,
        is_system_template=pos.is_system_template,
        is_active=pos.is_active,
        permissions=[p.permission_key for p in pos.permissions if p.granted],
    )


@router.get("/positions", response_model=list[PositionResponse],
            dependencies=[require(Permission.MANAGE_USERS)])
async def list_positions(user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    rows = list(await session.scalars(
        select(StaffPosition)
        .where(
            (StaffPosition.school_id == school_id) | (StaffPosition.school_id.is_(None))
        )
        .options(selectinload(StaffPosition.permissions))
        .order_by(StaffPosition.is_system_template.desc(), StaffPosition.name)
    ))
    return [_position_to_response(p) for p in rows]


@router.post("/positions", response_model=PositionResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_USERS)])
async def create_position(body: PositionCreate, user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)

    duplicate = await session.scalar(
        select(StaffPosition).where(
            StaffPosition.school_id == school_id,
            StaffPosition.code == body.code,
        )
    )
    if duplicate:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Position code '{body.code}' already exists")

    pos = StaffPosition(
        school_id=school_id,
        name=body.name,
        code=body.code.upper(),
        is_system_template=False,
        created_by=user.id,
    )
    session.add(pos)
    await session.flush()

    for perm_key in body.permissions:
        session.add(PositionPermission(position_id=pos.id, permission_key=perm_key, granted=True))

    await session.commit()
    await session.refresh(pos, ["permissions"])
    return _position_to_response(pos)


@router.patch("/positions/{pos_id}", response_model=PositionResponse,
              dependencies=[require(Permission.MANAGE_USERS)])
async def update_position(
    pos_id: UUID, body: PositionUpdate, user: CurrentUser, session: SessionDep
):
    pos = await session.scalar(
        select(StaffPosition)
        .where(StaffPosition.id == pos_id, StaffPosition.school_id == _school_id(user))
        .options(selectinload(StaffPosition.permissions))
    )
    if not pos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Position not found")
    if pos.is_system_template:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot modify system positions")

    if body.name is not None:
        pos.name = body.name
    if body.is_active is not None:
        pos.is_active = body.is_active

    if body.permissions is not None:
        for pp in pos.permissions:
            await session.delete(pp)
        await session.flush()
        for perm_key in body.permissions:
            session.add(PositionPermission(position_id=pos.id, permission_key=perm_key, granted=True))

    await session.commit()
    await session.refresh(pos, ["permissions"])
    return _position_to_response(pos)


@router.delete("/positions/{pos_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_USERS)])
async def delete_position(pos_id: UUID, user: CurrentUser, session: SessionDep):
    pos = await session.scalar(
        select(StaffPosition)
        .where(StaffPosition.id == pos_id, StaffPosition.school_id == _school_id(user))
    )
    if not pos:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Position not found")
    if pos.is_system_template:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot delete system positions")
    await session.delete(pos)
    await session.commit()


# ── User Accounts ─────────────────────────────────────────────────────────────

def _user_to_response(u: User) -> UserAccountResponse:
    staff_name: str | None = None
    if u.staff_member:
        staff_name = u.staff_member.full_name
    roles = [ur.role.name for ur in (u.user_roles or []) if ur.role]
    return UserAccountResponse(
        id=u.id,
        email=u.email,
        is_active=u.is_active,
        is_verified=u.is_verified,
        must_change_password=u.must_change_password,
        last_login_at=u.last_login_at,
        staff_name=staff_name,
        roles=roles,
    )


@router.get("/users", response_model=list[UserAccountResponse],
            dependencies=[require(Permission.MANAGE_USERS)])
async def list_school_users(user: CurrentUser, session: SessionDep):
    school_id = _school_id(user)
    rows = await session.scalars(
        select(User)
        .where(User.school_id == school_id)
        .options(
            selectinload(User.staff_member),
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
        .order_by(User.created_at.desc())
    )
    return [_user_to_response(u) for u in rows]


@router.patch("/users/{target_user_id}", response_model=UserAccountResponse,
              dependencies=[require(Permission.MANAGE_USERS)])
async def update_school_user(
    target_user_id: UUID, body: UserAccountUpdate, user: CurrentUser, session: SessionDep
):
    target = await session.scalar(
        select(User)
        .where(User.id == target_user_id, User.school_id == _school_id(user))
        .options(
            selectinload(User.staff_member),
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
    )
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target.id == user.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot modify your own account here")
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.must_change_password is not None:
        target.must_change_password = body.must_change_password
    await session.commit()
    await session.refresh(target, ["staff_member", "user_roles"])
    return _user_to_response(target)


# ── Houses ────────────────────────────────────────────────────────────────────

@router.get("/houses", response_model=list[HouseResponse],
            dependencies=[require(Permission.MANAGE_HOUSES)])
async def list_houses(user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_houses(school)
    rows = await session.scalars(
        select(House)
        .where(House.school_id == _school_id(user))
        .options(selectinload(House.housemaster))
        .order_by(House.name)
    )
    return [HouseResponse.model_validate(h) for h in rows]


@router.post("/houses", response_model=HouseResponse, status_code=201,
             dependencies=[require(Permission.MANAGE_HOUSES)])
async def create_house(body: HouseCreate, user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_houses(school)
    if body.housemaster_id:
        hm = await session.scalar(
            select(StaffMember).where(
                StaffMember.id == body.housemaster_id,
                StaffMember.school_id == _school_id(user),
            )
        )
        if not hm:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")
    house = House(school_id=_school_id(user), **body.model_dump())
    session.add(house)
    await session.commit()
    await session.refresh(house, ["housemaster"])
    return HouseResponse.model_validate(house)


@router.patch("/houses/{house_id}", response_model=HouseResponse,
              dependencies=[require(Permission.MANAGE_HOUSES)])
async def update_house(house_id: UUID, body: HouseUpdate, user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_houses(school)
    house = await session.scalar(
        select(House)
        .where(House.id == house_id, House.school_id == _school_id(user))
        .options(selectinload(House.housemaster))
    )
    if not house:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "House not found")
    if "housemaster_id" in body.model_fields_set and body.housemaster_id:
        hm = await session.scalar(
            select(StaffMember).where(
                StaffMember.id == body.housemaster_id,
                StaffMember.school_id == _school_id(user),
            )
        )
        if not hm:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Staff member not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(house, field, value)
    await session.commit()
    await session.refresh(house, ["housemaster"])
    return HouseResponse.model_validate(house)


@router.delete("/houses/{house_id}", status_code=204,
               dependencies=[require(Permission.MANAGE_HOUSES)])
async def delete_house(house_id: UUID, user: CurrentUser, session: SessionDep):
    school = await session.get(School, _school_id(user))
    _require_houses(school)
    house = await session.scalar(
        select(House).where(House.id == house_id, House.school_id == _school_id(user))
    )
    if not house:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "House not found")
    await session.delete(house)
    await session.commit()
