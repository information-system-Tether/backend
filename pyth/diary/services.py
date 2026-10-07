from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from diary.calculation import calcportion, calctotals, calcdata, rounddec
from diary.models import baseprod, bio, diarylist, entry, fav, userprod
from diary.schemas import (
    daydyn, dynresp, entrycreate, entryupd, favcreate, healcreate,
    healresp, healupd, prodcreate, produpd, sheetcreate, sheetresp,
    syncdata, syncresp, parsedate)

def safe_parsedate(dt: str | date, allow_future: bool = True) -> date:
    try:
        return parsedate(dt, allow_future=allow_future)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

class healserv:
    @staticmethod
    def applytargets(h: bio, custom_steps: bool = False) -> None:
        targets = calcdata(w=h.weight, h=h.height, age=h.age, sex=h.gender, actlvl=h.activity_level, tgoal=h.target_goal)
        for k, v in targets.items():
            if k == "target_steps" and custom_steps and h.target_steps and h.target_steps > 0:
                continue
            setattr(h, k, v)

    @classmethod
    def to_resp(cls, h: bio) -> healresp:
        vals = {f: getattr(h, f) for f in healcreate.model_fields}
        return healresp(
            id=h.id, min_target_calories=h.min_target_calories, max_target_calories=h.max_target_calories,
            target_proteins=h.target_proteins, target_fats=h.target_fats, target_carbs=h.target_carbs,
            target_water=h.target_water, **vals)

    @classmethod
    def getheal(cls, db: Session, idu: int) -> healresp:
        h = db.scalar(select(bio).where(bio.user_id == idu))
        if h is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль здоровья не найден")
        return cls.to_resp(h)

    @classmethod
    def createheal(cls, db: Session, idu: int, data: healcreate) -> healresp:
        if db.scalar(select(bio).where(bio.user_id == idu)) is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Профиль здоровья для данного пользователя уже создан")
        h = bio(user_id=idu, **data.model_dump())
        cls.applytargets(h, custom_steps=(data.target_steps > 0))
        db.add(h)
        db.commit()
        db.refresh(h)
        return cls.to_resp(h)

    @classmethod
    def updheal(cls, db: Session, idu: int, data: healupd) -> healresp:
        h = db.scalar(select(bio).where(bio.user_id == idu))
        if h is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль здоровья не найден")
        d = data.model_dump(exclude_unset=True)
        for f, val in d.items():
            setattr(h, f, val)
        cls.applytargets(h, custom_steps=("target_steps" in d))
        db.commit()
        db.refresh(h)
        return cls.to_resp(h)

    @staticmethod
    def delheal(db: Session, idu: int) -> None:
        h = db.scalar(select(bio).where(bio.user_id == idu))
        if h is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Профиль здоровья не найден")
        db.delete(h)
        db.commit()

class prodserv:
    @staticmethod
    def listbase(db: Session) -> list[baseprod]:
        return list(db.scalars(select(baseprod).order_by(baseprod.name)))

    @staticmethod
    def syncbase(db: Session, prods: list[prodcreate]) -> int:
        cnt = 0
        for p in prods:
            item = db.scalar(select(baseprod).where(baseprod.name == p.name))
            if item:
                for k, v in p.model_dump().items():
                    setattr(item, k, v)
            else:
                db.add(baseprod(**p.model_dump()))
            cnt += 1
        db.commit()
        return cnt

    @staticmethod
    def getprod(db: Session, idu: int, base_product_id: int | None = None, user_product_id: int | None = None, idbase: int | None = None, iduser: int | None = None) -> baseprod | userprod:
        bid = base_product_id if base_product_id is not None else idbase
        uid = user_product_id if user_product_id is not None else iduser
        if (bid is None) == (uid is None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Необходимо указать ровно один идентификатор продукта (base_product_id или user_product_id)")
        if bid is not None:
            p = db.get(baseprod, bid)
        else:
            p = db.scalar(select(userprod).where(userprod.id == uid, userprod.user_id == idu))
        if p is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")
        return p

    @staticmethod
    def createpr(db: Session, idu: int, data: prodcreate, idemp: str | None = None, idempotency_key: str | None = None) -> userprod:
        k = idemp if idemp is not None else idempotency_key
        if k:
            old = db.scalar(select(userprod).where(userprod.user_id == idu, userprod.idempotency_key == k))
            if old:
                return old
        p = userprod(user_id=idu, idempotency_key=k, **data.model_dump())
        db.add(p)
        try:
            db.commit()
            db.refresh(p)
            return p
        except IntegrityError:
            db.rollback()
            if k:
                old = db.scalar(select(userprod).where(userprod.user_id == idu, userprod.idempotency_key == k))
                if old:
                    return old
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Конфликт при создании продукта. Продукт с такими параметрами уже существует.")

    @staticmethod
    def listpr(db: Session, idu: int) -> list[userprod]:
        return list(db.scalars(select(userprod).where(userprod.user_id == idu)))

    @staticmethod
    def updatepr(db: Session, idu: int, idp: int, data: produpd) -> userprod:
        p = db.scalar(select(userprod).where(userprod.id == idp, userprod.user_id == idu))
        if p is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        db.commit()
        db.refresh(p)
        return p

    @staticmethod
    def delpr(db: Session, idu: int, idp: int) -> None:
        p = db.scalar(select(userprod).where(userprod.id == idp, userprod.user_id == idu))
        if p is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")
        for f in list(db.scalars(select(fav).where(fav.user_id == idu, fav.user_product_id == idp))):
            db.delete(f)
        db.delete(p)
        db.commit()

    @staticmethod
    def listfav(db: Session, idu: int) -> list[fav]:
        return list(db.scalars(select(fav).where(fav.user_id == idu)))

    @classmethod
    def addfav(cls, db: Session, idu: int, data: favcreate) -> fav:
        cls.getprod(db, idu, data.base_product_id, data.user_product_id)
        old = db.scalar(select(fav).where(fav.user_id == idu, fav.base_product_id == data.base_product_id, fav.user_product_id == data.user_product_id))
        if old:
            return old
        f = fav(user_id=idu, **data.model_dump())
        db.add(f)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Продукт уже в избранном")
        db.refresh(f)
        return f

    @staticmethod
    def delfav(db: Session, idu: int, idf: int) -> None:
        f = db.scalar(select(fav).where(fav.id == idf, fav.user_id == idu))
        if f is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись избранного не найдена")
        db.delete(f)
        db.commit()

class diaryserv:
    @staticmethod
    def to_resp(s: diarylist, rows: list[entry]) -> sheetresp:
        totals = calctotals(rows)
        return sheetresp(
            id=s.id, user_id=s.user_id, sheet_date=s.sheet_date, weight=s.weight,
            total_calories=totals["total_calories"], total_fats=totals["total_fats"],
            total_proteins=totals["total_proteins"], total_carbs=totals["total_carbs"],
            total_water=totals["total_water"], entries=rows)

    @classmethod
    def listsheets(cls, db: Session, idu: int) -> list[sheetresp]:
        sheets = list(db.scalars(select(diarylist).where(diarylist.user_id == idu).options(selectinload(diarylist.entries)).order_by(diarylist.sheet_date.desc())))
        return [cls.to_resp(s, s.entries) for s in sheets]

    @classmethod
    def getsheet(cls, db: Session, idu: int, dt: str) -> sheetresp:
        parsed = safe_parsedate(dt)
        s = db.scalar(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date == parsed).options(selectinload(diarylist.entries)))
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лист дневника за указанную дату не найден")
        return cls.to_resp(s, s.entries)

    @classmethod
    def createsheet(cls, db: Session, idu: int, data: sheetcreate) -> sheetresp:
        if db.scalar(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date == data.sheet_date)):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Лист дневника на эту дату уже существует")
        s = diarylist(user_id=idu, **data.model_dump())
        db.add(s)
        db.commit()
        db.refresh(s)
        return cls.to_resp(s, [])

    @classmethod
    def updatesheet(cls, db: Session, idu: int, dt: str, w: Decimal | None) -> sheetresp:
        parsed = safe_parsedate(dt)
        s = db.scalar(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date == parsed).options(selectinload(diarylist.entries)))
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лист не найден")
        if w is not None:
            s.weight = w
        db.commit()
        db.refresh(s)
        return cls.to_resp(s, s.entries)

    @classmethod
    def delsheet(cls, db: Session, idu: int, dt: str) -> None:
        parsed = safe_parsedate(dt)
        s = db.scalar(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date == parsed))
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Лист дневника за указанную дату не найден")
        db.delete(s)
        db.commit()

    @staticmethod
    def createentry(db: Session, idu: int, dt: str, data: entrycreate) -> entry:
        parsed = safe_parsedate(dt)
        s = db.scalar(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date == parsed))
        if not s:
            s = diarylist(user_id=idu, sheet_date=parsed)
            db.add(s)
            db.commit()
            db.refresh(s)

        if data.base_product_id is not None or data.user_product_id is not None:
            p = prodserv.getprod(db, idu, data.base_product_id, data.user_product_id)
            grams = data.quantity_grams or Decimal("100")
            nutr = calcportion(
                grams=grams,
                cals100=p.calories, prots100=p.proteins,
                fats100=p.fats, carbs100=p.carbs)
            ptype = p.product_type
            wtr = rounddec(grams / Decimal("1000")) if ptype == "beverages" else Decimal("0")
            e = entry(
                sheet_id=s.id, base_product_id=data.base_product_id, user_product_id=data.user_product_id,
                quantity_grams=grams, title=data.title or p.name, description=data.description or p.description,
                calories=nutr["calories"], proteins=nutr["proteins"], fats=nutr["fats"], carbs=nutr["carbs"],
                water=wtr,
                product_type=ptype)
        else:
            ptype = data.product_type.value if hasattr(data.product_type, "value") else (data.product_type or "other")
            grams = data.quantity_grams
            if grams is not None:
                nutr = calcportion(
                    grams=grams,
                    cals100=data.calories,
                    prots100=data.proteins or Decimal("0"),
                    fats100=data.fats or Decimal("0"),
                    carbs100=data.carbs or Decimal("0"))
                cals = nutr["calories"]
                prots = nutr["proteins"]
                fats = nutr["fats"]
                carbs = nutr["carbs"]
                wtr = rounddec(grams / Decimal("1000")) if ptype == "beverages" else Decimal("0")
            else:
                cals = data.calories
                prots = data.proteins or Decimal("0")
                fats = data.fats or Decimal("0")
                carbs = data.carbs or Decimal("0")
                wtr = Decimal("0")

            e = entry(
                sheet_id=s.id, base_product_id=None, user_product_id=None,
                title=data.title or "Перекус", description=data.description, quantity_grams=grams,
                calories=cals, proteins=prots, fats=fats, carbs=carbs,
                water=wtr,
                product_type=ptype)
        db.add(e)
        db.commit()
        db.refresh(e)
        return e

    @staticmethod
    def updateentry(db: Session, idu: int, ide: int, data: entryupd) -> entry:
        e = db.scalar(select(entry).join(diarylist).where(entry.id == ide, diarylist.user_id == idu))
        if e is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")

        is_prod = e.base_product_id is not None or e.user_product_id is not None
        if is_prod and data.quantity_grams is not None:
            e.quantity_grams = data.quantity_grams
            p = prodserv.getprod(db, idu, e.base_product_id, e.user_product_id)
            nutr = calcportion(
                grams=e.quantity_grams, cals100=p.calories,
                prots100=p.proteins, fats100=p.fats, carbs100=p.carbs)
            e.calories = nutr["calories"]
            e.proteins = nutr["proteins"]
            e.fats = nutr["fats"]
            e.carbs = nutr["carbs"]
            e.water = rounddec(e.quantity_grams / Decimal("1000")) if e.product_type == "beverages" else Decimal("0")
        elif not is_prod and data.quantity_grams is not None and e.quantity_grams and e.quantity_grams > 0:
            ratio = data.quantity_grams / e.quantity_grams
            if data.calories is None and e.calories is not None:
                e.calories = rounddec(e.calories * ratio)
            if data.proteins is None and e.proteins is not None:
                e.proteins = rounddec(e.proteins * ratio)
            if data.fats is None and e.fats is not None:
                e.fats = rounddec(e.fats * ratio)
            if data.carbs is None and e.carbs is not None:
                e.carbs = rounddec(e.carbs * ratio)
            e.quantity_grams = data.quantity_grams
            e.water = rounddec(e.quantity_grams / Decimal("1000")) if e.product_type == "beverages" else Decimal("0")

        for k, v in data.model_dump(exclude_unset=True).items():
            if k == "quantity_grams" and (is_prod or (e.quantity_grams and e.quantity_grams > 0)):
                continue
            if k == "product_type" and v is not None:
                val = v.value if hasattr(v, "value") else v
                setattr(e, k, val)
                if val == "beverages" and e.quantity_grams:
                    e.water = rounddec(e.quantity_grams / Decimal("1000"))
                elif val != "beverages":
                    e.water = Decimal("0")
            else:
                setattr(e, k, v)

        if e.product_type == "beverages" and e.quantity_grams and (e.water is None or e.water == 0):
            e.water = rounddec(e.quantity_grams / Decimal("1000"))

        db.commit()
        db.refresh(e)
        return e

    @staticmethod
    def delentry(db: Session, idu: int, ide: int) -> None:
        e = db.scalar(select(entry).join(diarylist).where(entry.id == ide, diarylist.user_id == idu))
        if e is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Запись не найдена")
        db.delete(e)
        db.commit()

    @staticmethod
    def getdyn(db: Session, idu: int, start_date_str: str | None = None, end_date_str: str | None = None, d1: str | None = None, d2: str | None = None) -> dynresp:
        start_val = d1 or start_date_str
        end_val = d2 or end_date_str
        today = date.today()
        end_dt = parsedate(end_val) if end_val else today
        start_dt = parsedate(start_val) if start_val else (end_dt - timedelta(days=30))
        if start_dt > end_dt:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Начальная дата (start_date) не может быть позже конечной (end_date)")

        sheets = list(db.scalars(select(diarylist).where(diarylist.user_id == idu, diarylist.sheet_date >= start_dt, diarylist.sheet_date <= end_dt).options(selectinload(diarylist.entries)).order_by(diarylist.sheet_date.asc())))
        b = db.scalar(select(bio).where(bio.user_id == idu))
        tc = ((b.min_target_calories + b.max_target_calories) / Decimal("2")) if b and b.max_target_calories else None

        days: list[daydyn] = []
        cals, prots, fats, carbs, water = Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")

        for s in sheets:
            totals = calctotals(s.entries)
            cals += totals["total_calories"]
            prots += totals["total_proteins"]
            fats += totals["total_fats"]
            carbs += totals["total_carbs"]
            water += totals["total_water"]
            days.append(daydyn(
                sheet_date=s.sheet_date, weight=s.weight, total_calories=totals["total_calories"],
                total_proteins=totals["total_proteins"], total_fats=totals["total_fats"],
                total_carbs=totals["total_carbs"], total_water=totals["total_water"],
                entries_count=len(s.entries)))

        cnt = len(days)
        div = Decimal(cnt) if cnt > 0 else Decimal("1")
        weights = [s.weight for s in sheets if s.weight is not None]
        avg_weight = rounddec(sum(weights) / Decimal(len(weights))) if weights else None
        return dynresp(
            start_date=start_dt, end_date=end_dt, days_count=cnt,
            average_calories=rounddec(cals / div),
            average_proteins=rounddec(prot_sum := prots / div),
            average_fats=rounddec(fats / div),
            average_carbs=rounddec(carbs / div),
            average_water=rounddec(water / div),
            average_weight=avg_weight,
            target_calories=rounddec(tc) if tc else None,
            days=days)

    @classmethod
    def getsync(cls, db: Session, idu: int) -> syncresp:
        b = db.scalar(select(bio).where(bio.user_id == idu))
        pr = list(db.scalars(select(userprod).where(userprod.user_id == idu)))
        f = list(db.scalars(select(fav).where(fav.user_id == idu)))
        sheets = cls.listsheets(db, idu)
        return syncresp(health=healserv.to_resp(b) if b else None, products=pr, favorites=f, sheets=sheets)

    @classmethod
    def syncuser(cls, db: Session, idu: int, data: syncdata) -> None:
        if data.health:
            b = db.scalar(select(bio).where(bio.user_id == idu))
            hd = data.health.model_dump(exclude_unset=True)
            if b is None:
                b = bio(user_id=idu, **hd)
                healserv.applytargets(b, custom_steps=("target_steps" in hd))
                db.add(b)
            else:
                for k, v in hd.items():
                    setattr(b, k, v)
                healserv.applytargets(b, custom_steps=("target_steps" in hd))
        db.commit()
