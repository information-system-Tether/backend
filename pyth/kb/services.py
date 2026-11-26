from __future__ import annotations
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from kb.models import kbarticle
from kb.schemas import kbcreate, kbresp, kbupd

class kbserv:
    @staticmethod
    def _build_query(
        category: str | None = None,
        block: str | None = None,
        q: str | None = None,
    ):
        stmt = select(kbarticle)
        if q and q.strip():
            words = [w.strip() for w in q.split() if w.strip()]
            for w in words:
                pat = f"%{w}%"
                stmt = stmt.where(
                    or_(
                        kbarticle.question.ilike(pat),
                        kbarticle.answer.ilike(pat),
                        kbarticle.tags.ilike(pat),
                        kbarticle.block.ilike(pat),
                    )
                )
        if category:
            stmt = stmt.where(kbarticle.category == category)
        if block:
            stmt = stmt.where(kbarticle.block == block)
        return stmt

    @staticmethod
    def listarticles(
        db: Session,
        category: str | None = None,
        block: str | None = None,
        q: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[kbarticle], int]:
        base_stmt = kbserv._build_query(category=category, block=block, q=q)
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = db.scalar(count_stmt) or 0

        query = base_stmt.order_by(kbarticle.id)
        if offset > 0:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        return list(db.scalars(query)), total

    @staticmethod
    def listblocks(db: Session) -> list[str]:
        stmt = select(kbarticle.block).where(kbarticle.block.is_not(None)).distinct().order_by(kbarticle.block)
        return [b for b in db.scalars(stmt) if b]

    @staticmethod
    def getarticle(db: Session, aid: int) -> kbarticle:
        a = db.get(kbarticle, aid)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья базы знаний не найдена")
        return a

    @staticmethod
    def search(
        db: Session,
        q: str,
        category: str | None = None,
        block: str | None = None,
        offset: int = 0,
        limit: int | None = None,
    ) -> tuple[list[kbarticle], int]:
        return kbserv.listarticles(
            db=db,
            category=category,
            block=block,
            q=q,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    def createarticle(db: Session, data: kbcreate) -> kbarticle:
        a = kbarticle(**data.model_dump())
        db.add(a)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def updatearticle(db: Session, aid: int, data: kbupd) -> kbarticle:
        a = db.get(kbarticle, aid)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья базы знаний не найдена")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(a, k, v)
        db.commit()
        db.refresh(a)
        return a

    @staticmethod
    def delarticle(db: Session, aid: int) -> None:
        a = db.get(kbarticle, aid)
        if a is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья базы знаний не найдена")
        db.delete(a)
        db.commit()
