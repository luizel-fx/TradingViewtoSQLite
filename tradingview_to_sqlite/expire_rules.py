import calendar
from datetime import date, timedelta
import holidays

# Mapeamento global de meses
MONTH_CODES = {
    'F': 1, 'G': 2, 'H': 3, 'J': 4, 'K': 5, 'M': 6,
    'N': 7, 'Q': 8, 'U': 9, 'V': 10, 'X': 11, 'Z': 12
}

def _get_month_num(exp_month: str) -> int:
    return MONTH_CODES[exp_month.upper()]

def _is_biz_day(dt: date, cal: holidays.HolidayBase) -> bool:
    """Verifica se é dia útil dado um calendário de feriados."""
    return dt.weekday() < 5 and dt not in cal

def _get_first_biz_day(year: int, month: int, cal: holidays.HolidayBase) -> date:
    dt = date(year, month, 1)
    while not _is_biz_day(dt, cal):
        dt += timedelta(days=1)
    return dt

def _get_last_biz_day(year: int, month: int, cal: holidays.HolidayBase) -> date:
    last_day = calendar.monthrange(year, month)[1]
    dt = date(year, month, last_day)
    while not _is_biz_day(dt, cal):
        dt -= timedelta(days=1)
    return dt

def _get_nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Retorna a data do n-ésimo dia da semana específico (ex: 3ª sexta-feira).
       weekday: 0=Seg, 1=Ter, ..., 4=Sex, 5=Sáb, 6=Dom"""
    dt = date(year, month, 1)
    count = 0
    while count < n:
        if dt.weekday() == weekday:
            count += 1
            if count == n:
                break
        dt += timedelta(days=1)
    return dt

# ==========================================
# REGRAS B3 (BRASIL)
# ==========================================
def b3_first_biz_day(exp_month: str, exp_year: int) -> date:
    """DI1, DOL, WDO, EUR: 1º dia útil do mês de vencimento."""
    return _get_first_biz_day(exp_year, _get_month_num(exp_month), holidays.Brazil(years=exp_year))

def b3_last_biz_day(exp_month: str, exp_year: int) -> date:
    """BGI, ETH: Último dia útil do mês de vencimento."""
    return _get_last_biz_day(exp_year, _get_month_num(exp_month), holidays.Brazil(years=exp_year))

def b3_day_15_next_biz(exp_month: str, exp_year: int) -> date:
    """CCM, DAP, SFI: Dia 15. Se não for útil, próximo dia útil."""
    dt = date(exp_year, _get_month_num(exp_month), 15)
    cal = holidays.Brazil(years=exp_year)
    while not _is_biz_day(dt, cal):
        dt += timedelta(days=1)
    return dt

def b3_ind_expiry(exp_month: str, exp_year: int) -> date:
    """IND, WIN: Quarta-feira mais próxima do dia 15. Se não for útil, próximo."""
    dt = date(exp_year, _get_month_num(exp_month), 15)
    cal = holidays.Brazil(years=exp_year)
    
    # Ajusta para a quarta-feira (weekday == 2) mais próxima
    offset = (2 - dt.weekday()) % 7
    if offset > 3: 
        offset -= 7
    dt += timedelta(days=offset)
    
    while not _is_biz_day(dt, cal):
        dt += timedelta(days=1)
    return dt

def b3_icf_expiry(exp_month: str, exp_year: int) -> date:
    """ICF (Café Arábica): 6º dia útil anterior ao último dia útil do mês."""
    dt = _get_last_biz_day(exp_year, _get_month_num(exp_month), holidays.Brazil(years=exp_year))
    cal = holidays.Brazil(years=exp_year)
    count = 0
    while count < 6:
        dt -= timedelta(days=1)
        if _is_biz_day(dt, cal):
            count += 1
    return dt

# ==========================================
# REGRAS CME / CBOT / NYMEX / COMEX (EUA)
# ==========================================
def us_day_15_prev_biz(exp_month: str, exp_year: int) -> date:
    """ZC, ZS, ZW: Dia 15. Se não for útil, dia útil anterior."""
    dt = date(exp_year, _get_month_num(exp_month), 15)
    cal = holidays.US(years=exp_year)
    while not _is_biz_day(dt, cal):
        dt -= timedelta(days=1)
    return dt

def us_third_friday(exp_month: str, exp_year: int) -> date:
    """ES, NQ: 3ª sexta-feira do mês de vencimento."""
    return _get_nth_weekday(exp_year, _get_month_num(exp_month), weekday=4, n=3)

def us_last_biz_day(exp_month: str, exp_year: int) -> date:
    """SOFR, ZQ: Último dia útil do mês."""
    return _get_last_biz_day(exp_year, _get_month_num(exp_month), holidays.US(years=exp_year))

def us_wti_expiry(exp_month: str, exp_year: int) -> date:
    """CL (WTI): 3 dias úteis antes do dia 25 do mês anterior."""
    month_num = _get_month_num(exp_month)
    target_month = month_num - 1
    target_year = exp_year
    if target_month == 0:
        target_month = 12
        target_year -= 1
        
    dt = date(target_year, target_month, 25)
    cal = holidays.US(years=target_year)
    
    # Se o dia 25 não for útil, a regra base se move para o dia útil anterior antes de contar os 3 dias
    while not _is_biz_day(dt, cal):
        dt -= timedelta(days=1)
        
    count = 0
    while count < 3:
        dt -= timedelta(days=1)
        if _is_biz_day(dt, cal):
            count += 1
    return dt

# ==========================================
# REGRAS ICE / LME (REINO UNIDO E GLOBAIS)
# ==========================================
def uk_brent_expiry(exp_month: str, exp_year: int) -> date:
    """Brent (ICE): Último dia útil do segundo mês anterior."""
    month_num = _get_month_num(exp_month)
    target_month = month_num - 2
    target_year = exp_year
    if target_month <= 0:
        target_month += 12
        target_year -= 1
        
    return _get_last_biz_day(target_year, target_month, holidays.UK(years=target_year))

def uk_third_wednesday(exp_month: str, exp_year: int) -> date:
    """LME Metals, SONIA: 3ª quarta-feira do mês de vencimento."""
    return _get_nth_weekday(exp_year, _get_month_num(exp_month), weekday=2, n=3)

def uk_third_friday(exp_month: str, exp_year: int) -> date:
    """FTSE 100: 3ª sexta-feira do mês de vencimento."""
    return _get_nth_weekday(exp_year, _get_month_num(exp_month), weekday=4, n=3)