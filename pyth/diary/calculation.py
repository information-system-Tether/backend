from abc import ABC, abstractmethod
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

dec2 = Decimal("0.01")
dec1 = Decimal("0.1")

def rounddec(val: Decimal, pl: Decimal = dec2) -> Decimal:
    return val.quantize(pl, rounding=ROUND_HALF_UP)

class goalstrat(ABC):
    @property
    @abstractmethod
    def calcfactor(self) -> Decimal:
        pass

    @abstractmethod
    def prot1kg(self, actlvl: int) -> Decimal:
        pass

    @abstractmethod
    def fat1kg(self, actlvl: int) -> Decimal:
        pass

    @abstractmethod
    def calcsteps(self, basesteps: int) -> int:
        pass

class losewstrat(goalstrat):
    @property
    def calcfactor(self) -> Decimal:
        return Decimal("0.80")
    def prot1kg(self, actlvl: int) -> Decimal:
        protmap = {1: Decimal("1.6"), 2: Decimal("1.8"), 3: Decimal("2.0"), 4: Decimal("2.2"), 5: Decimal("2.2")}
        return protmap.get(actlvl, Decimal("1.8"))
    def fat1kg(self, actlvl: int) -> Decimal:
        return Decimal("0.8") if actlvl <= 2 else Decimal("0.9")
    def calcsteps(self, basesteps: int) -> int:
        return basesteps + 2500

class moremstrat(goalstrat):
    @property
    def calcfactor(self) -> Decimal:
        return Decimal("1.15")
    def prot1kg(self, actlvl: int) -> Decimal:
        protmap = {1: Decimal("1.5"), 2: Decimal("1.7"), 3: Decimal("1.9"), 4: Decimal("2.1"), 5: Decimal("2.2")}
        return protmap.get(actlvl, Decimal("1.8"))
    def fat1kg(self, actlvl: int) -> Decimal:
        return Decimal("1.0") if actlvl <= 2 else Decimal("1.1")
    def calcsteps(self, basesteps: int) -> int:
        return min(basesteps, 8000)

class recompstrat(goalstrat):
    @property
    def calcfactor(self) -> Decimal:
        return Decimal("0.95")
    def prot1kg(self, actlvl: int) -> Decimal:
        protmap = {1: Decimal("1.6"), 2: Decimal("1.8"), 3: Decimal("2.0"), 4: Decimal("2.2"), 5: Decimal("2.2")}
        return protmap.get(actlvl, Decimal("1.8"))
    def fat1kg(self, actlvl: int) -> Decimal:
        return Decimal("0.9") if actlvl <= 2 else Decimal("1.0")
    def calcsteps(self, basesteps: int) -> int:
        return basesteps + 1500

class maintstrat(goalstrat):
    @property
    def calcfactor(self) -> Decimal:
        return Decimal("1.00")
    def prot1kg(self, actlvl: int) -> Decimal:
        protmap = {1: Decimal("1.0"), 2: Decimal("1.3"), 3: Decimal("1.5"), 4: Decimal("1.8"), 5: Decimal("2.0")}
        return protmap.get(actlvl, Decimal("1.3"))
    def fat1kg(self, actlvl: int) -> Decimal:
        return Decimal("1.0")
    def calcsteps(self, basesteps: int) -> int:
        return basesteps

_STRATS: dict[int, goalstrat] = {
    1: losewstrat(),
    2: moremstrat(),
    3: recompstrat(),
    4: maintstrat()}

def getgoal(tgoal: int = 4) -> goalstrat:
    strat = _STRATS.get(tgoal)
    return strat if strat is not None else maintstrat()

def calcbmr(w: Decimal = None, h: Decimal = None, age: int = None, sex: str = "m", **kw) -> Decimal:
    weight = kw.get("weight", w)
    height_m = kw.get("height_m", h)
    gender = kw.get("gender", sex)
    base = (Decimal("10") * weight) + (Decimal("625") * height_m) - (Decimal("5") * Decimal(age))
    gendercheck = gender.lower()
    if gendercheck == "m":
        return base + Decimal("5")
    elif gendercheck == "f":
        return base - Decimal("161")
    return base - Decimal("78")

def actmult(actlvl: int) -> Decimal:
    coeff = {
        1: Decimal("1.2"),
        2: Decimal("1.375"),
        3: Decimal("1.55"),
        4: Decimal("1.7"),
        5: Decimal("1.9")}
    return coeff.get(actlvl, Decimal("1.2"))

def calcbasesteps(actlvl: int) -> int:
    basestepsforday = {
        1: 6000,
        2: 8000,
        3: 10000,
        4: 12500,
        5: 15000}
    return basestepsforday.get(actlvl, 8000)

def calcdata(w: Decimal = None, h: Decimal = None, age: int = None, sex: str = "m", actlvl: int = 1, tgoal: int = 4, **kw) -> dict[str, Any]:
    weight = kw.get("weight", w)
    height_m = kw.get("height_m", h)
    gender = kw.get("gender", sex)
    level = kw.get("activity_level", actlvl)
    goal_val = kw.get("target_goal", tgoal)

    strat = getgoal(goal_val)
    bmr = calcbmr(weight, height_m, age, gender)
    tdee = bmr * actmult(level)
    esttdee = tdee * strat.calcfactor

    prot1kg = strat.prot1kg(level)
    fat1kg = strat.fat1kg(level)
    proteins = prot1kg * weight
    fats = fat1kg * weight

    protcals = proteins * Decimal("4")
    fatcals = fats * Decimal("9")
    balancecarbs = esttdee - protcals - fatcals

    carbs = max(balancecarbs / Decimal("4"), Decimal("50.0"))
    avgcals = protcals + fatcals + (carbs * Decimal("4"))

    spread = max(Decimal("200"), min(avgcals * Decimal("0.10"), Decimal("500")))
    halfspread = spread / Decimal("2")
    mincals = avgcals - halfspread
    maxcals = avgcals + halfspread

    water = weight * Decimal("0.033")
    basesteps = calcbasesteps(level)
    tsteps = strat.calcsteps(basesteps)

    return {
        "min_target_calories": rounddec(mincals),
        "max_target_calories": rounddec(maxcals),
        "target_proteins": rounddec(proteins),
        "target_fats": rounddec(fats),
        "target_carbs": rounddec(carbs),
        "target_water": rounddec(water),
        "target_steps": tsteps}

def calcportion(grams: Decimal = None, cals100: Decimal = None, prots100: Decimal = None, fats100: Decimal = None, carbs100: Decimal = None, **kw) -> dict[str, Decimal]:
    g = kw.get("quantity_grams", grams)
    c = kw.get("calories_per_100g", cals100)
    p = kw.get("proteins_per_100g", prots100)
    f = kw.get("fats_per_100g", fats100)
    cb = kw.get("carbs_per_100g", carbs100)
    k = g / Decimal("100")
    return {
        "calories": rounddec(c * k),
        "proteins": rounddec(p * k),
        "fats": rounddec(f * k),
        "carbs": rounddec(cb * k)}

def calctotals(rows: list[Any] = None, **kw) -> dict[str, Decimal]:
    entries = kw.get("entries", rows) or []
    cals, prots, fats, carbs, water = Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")
    for r in entries:
        if r.calories:
            cals += r.calories
        if r.proteins:
            prots += r.proteins
        if r.fats:
            fats += r.fats
        if r.carbs:
            carbs += r.carbs
        if getattr(r, "product_type", None) == "beverages" and r.quantity_grams:
            water += r.quantity_grams / Decimal("1000")
    return {
        "total_calories": rounddec(cals),
        "total_proteins": rounddec(prots),
        "total_fats": rounddec(fats),
        "total_carbs": rounddec(carbs),
        "total_water": rounddec(water)}

