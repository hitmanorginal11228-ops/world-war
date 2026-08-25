import os, asyncio, random
from decimal import Decimal
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Numeric, Text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

TOKEN = os.getenv("BOT_TOKEN")
DB = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./worldwar.db")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is required")
if DB.startswith("postgres://"): DB = DB.replace("postgres://","postgresql+asyncpg://",1)
elif DB.startswith("postgresql://"): DB = DB.replace("postgresql://","postgresql+asyncpg://",1)

engine = create_async_engine(DB, pool_pre_ping=True)
Session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase): pass

class Player(Base):
    __tablename__="players"
    id: Mapped[int]=mapped_column(primary_key=True)
    tg: Mapped[int]=mapped_column(BigInteger,unique=True,index=True)
    username: Mapped[str|None]=mapped_column(String(100))
    country: Mapped[str]=mapped_column(String(100),default="بدون کشور")
    money: Mapped[Decimal]=mapped_column(Numeric(20,2),default=5000000)
    population: Mapped[int]=mapped_column(BigInteger,default=10000000)
    land: Mapped[int]=mapped_column(Integer,default=1000)
    air: Mapped[int]=mapped_column(Integer,default=100)
    navy: Mapped[int]=mapped_column(Integer,default=25)
    defense: Mapped[int]=mapped_column(Integer,default=50)
    strategic: Mapped[int]=mapped_column(Integer,default=10)
    tanks: Mapped[int]=mapped_column(Integer,default=100)
    artillery: Mapped[int]=mapped_column(Integer,default=100)
    missiles: Mapped[int]=mapped_column(Integer,default=20)
    nuclear: Mapped[int]=mapped_column(Integer,default=0)
    factories: Mapped[int]=mapped_column(Integer,default=5)
    auto_factories: Mapped[int]=mapped_column(Integer,default=1)
    mines: Mapped[int]=mapped_column(Integer,default=1)
    oil: Mapped[int]=mapped_column(Integer,default=1)
    hotels: Mapped[int]=mapped_column(Integer,default=0)
    ports: Mapped[int]=mapped_column(Integer,default=1)
    airports: Mapped[int]=mapped_column(Integer,default=1)
    bases: Mapped[int]=mapped_column(Integer,default=1)
    commander: Mapped[str]=mapped_column(String(100),default="فرمانده ارشد")
    alliance_id: Mapped[int|None]=mapped_column(ForeignKey("alliances.id"))
    last_income: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class Alliance(Base):
    __tablename__="alliances"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(100),unique=True)
    owner: Mapped[int]=mapped_column(BigInteger)
    friendly: Mapped[bool]=mapped_column(Boolean,default=False)

class War(Base):
    __tablename__="wars"
    id: Mapped[int]=mapped_column(primary_key=True)
    attacker: Mapped[int]=mapped_column(BigInteger)
    defender: Mapped[int]=mapped_column(BigInteger)
    active: Mapped[bool]=mapped_column(Boolean,default=True)
    created: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class Loan(Base):
    __tablename__="loans"
    id: Mapped[int]=mapped_column(primary_key=True)
    borrower: Mapped[int]=mapped_column(BigInteger)
    lender: Mapped[int]=mapped_column(BigInteger,default=0)
    amount: Mapped[Decimal]=mapped_column(Numeric(20,2))
    due: Mapped[datetime]=mapped_column(DateTime)
    status: Mapped[str]=mapped_column(String(20),default="active")

class Trade(Base):
    __tablename__="trades"
    id: Mapped[int]=mapped_column(primary_key=True)
    seller: Mapped[int]=mapped_column(BigInteger)
    buyer: Mapped[int]=mapped_column(BigInteger)
    mode: Mapped[str]=mapped_column(String(20))
    amount: Mapped[Decimal]=mapped_column(Numeric(20,2))
    created: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

class Statement(Base):
    __tablename__="statements"
    id: Mapped[int]=mapped_column(primary_key=True)
    player: Mapped[int]=mapped_column(BigInteger)
    text: Mapped[str]=mapped_column(Text)
    created: Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

COUNTRIES = """افغانستان|آلبانی|الجزایر|آرژانتین|استرالیا|اتریش|بلژیک|برزیل|بلغارستان|کانادا|شیلی|چین|کلمبیا|کرواسی|کوبا|دانمارک|مصر|فنلاند|فرانسه|آلمان|یونان|هند|اندونزی|ایران|عراق|ایرلند|ایتالیا|ژاپن|قزاقستان|کنیا|کره جنوبی|مکزیک|مراکش|هلند|نیوزیلند|نروژ|پاکستان|پرو|لهستان|پرتغال|رومانی|روسیه|عربستان سعودی|صربستان|سنگاپور|اسپانیا|سوئد|سوئیس|ترکیه|اوکراین|امارات متحده عربی|بریتانیا|ایالات متحده|ونزوئلا|ویتنام|آفریقای جنوبی|مصر|مغولستان|تایلند|مالزی|فیلیپین|چک|اسلواکی|مجارستان|بلاروس|گرجستان|ارمنستان|آذربایجان|قطر|کویت|اردن|لبنان|عمان|بحرین|تونس|لیبی|اتیوپی|نیجریه|غنا|کنیا|تانزانیا|اوگاندا|آنگولا|موزامبیک|زیمبابوه|شیلی|بولیوی|اکوادور|اروگوئه|پاراگوئه|کاستاریکا|پاناما|کوبا|جامائیکا|ایسلند|لوکزامبورگ|اسلوونی|کره شمالی""".split("|")

def fmt(n): return f"{Decimal(n):,.0f}"

async def player(s,tg,user=None):
    p=(await s.execute(select(Player).where(Player.tg==tg))).scalar_one_or_none()
    if not p:
        p=Player(tg=tg,username=user); s.add(p); await s.commit()
    return p

def menu():
    b=InlineKeyboardBuilder()
    for t,d in [
        ("🌍 کشور من","country"),("💼 دارایی‌ها","assets"),("⚔️ جنگ/صلح","war"),
        ("📜 بیانیه","statement"),("💰 اقتصاد","economy"),("🪖 ارتش","army"),
        ("🏭 صنعت و سازه","build"),("⛏️ منابع","resources"),("👑 فرمانده","commander"),
        ("🤝 اتحادها","alliance"),("🏦 وام","loan"),("🚢 تجارت دریایی","sea"),
        ("✈️ تجارت هوایی","air"),("👥 دعوت دوستان","invite"),("🔄 تغییر کشور","change")
    ]: b.button(text=t,callback_data=d)
    b.adjust(2)
    return b.as_markup()

async def start(m:Message):
    async with Session() as s:
        p=await player(s,m.from_user.id,m.from_user.username)
        await m.answer(f"🌍 <b>WORLD WAR</b>\n\nکشور: <b>{p.country}</b>\n💰 خزانه: {fmt(p.money)}\n\nیک بخش را انتخاب کن.",reply_markup=menu(),parse_mode="HTML")

async def callbacks(c:CallbackQuery):
    async with Session() as s:
        p=await player(s,c.from_user.id,c.from_user.username)
        d=c.data

        if d=="assets":
            text=(f"💼 <b>دارایی‌های {p.country}</b>\n\n💰 {fmt(p.money)}\n👥 جمعیت: {p.population:,}\n"
            f"🪖 زمینی: {p.land:,}\n✈️ هوایی: {p.air:,}\n🚢 دریایی: {p.navy:,}\n🛡️ پدافند: {p.defense:,}\n"
            f"🎯 استراتژیک: {p.strategic:,}\n🛡️ تانک: {p.tanks:,}\n💥 توپخانه: {p.artillery:,}\n🚀 موشک: {p.missiles:,}\n☢️ هسته‌ای: {p.nuclear:,}\n"
            f"🏭 کارخانه: {p.factories}\n🚗 خودرو: {p.auto_factories}\n⛏️ معدن: {p.mines}\n🛢️ نفت: {p.oil}\n"
            f"🏨 هتل: {p.hotels}\n🚢 بندر: {p.ports}\n✈️ فرودگاه: {p.airports}\n🏰 پایگاه: {p.bases}\n👑 فرمانده: {p.commander}")
            await c.message.edit_text(text,reply_markup=menu(),parse_mode="HTML")

        elif d=="country":
            await c.message.edit_text(f"🌍 کشور: <b>{p.country}</b>\n👑 فرمانده: {p.commander}\n💰 {fmt(p.money)}",reply_markup=menu(),parse_mode="HTML")

        elif d=="economy":
            income=p.population*2+p.mines*50000+p.oil*80000+p.factories*100000+p.hotels*25000+p.auto_factories*70000
            await c.message.edit_text(f"💰 <b>اقتصاد</b>\nدرآمد روزانه تقریبی: {fmt(income)}\n\nمنابع و صنعت روی درآمد اثر می‌گذارند.",reply_markup=menu(),parse_mode="HTML")

        elif d=="army":
            b=InlineKeyboardBuilder()
            for t,x in [("🪖 +100 زمینی","buy:land"),("✈️ +1 هوایی","buy:air"),("🚢 +1 دریایی","buy:navy"),("🛡️ +1 پدافند","buy:def"),("🎯 +1 استراتژیک","buy:strat"),("🛡️ +10 تانک","buy:tank"),("💥 +10 توپخانه","buy:art"),("🚀 +1 موشک","buy:missile"),("☢️ +1 آیتم هسته‌ای","buy:nuke")]:
                b.button(text=t,callback_data=x)
            b.adjust(2)
            await c.message.edit_text("🪖 <b>مدیریت نیروها</b>\nهمه موارد در این پروژه آیتم‌های بازی هستند.",reply_markup=b.as_markup(),parse_mode="HTML")

        elif d=="build":
            b=InlineKeyboardBuilder()
            for t,x in [("🏭 کارخانه","build:factory"),("🚗 صنعت خودرو","build:auto"),("⛏️ معدن","build:mine"),("🛢️ نفت","build:oil"),("🏨 هتل","build:hotel"),("🚢 بندر","build:port"),("✈️ فرودگاه","build:airport"),("🏰 پایگاه","build:base")]:
                b.button(text=t,callback_data=x)
            b.adjust(2); await c.message.edit_text("🏭 <b>ساخت‌وساز</b>",reply_markup=b.as_markup(),parse_mode="HTML")

        elif d=="resources":
            await c.message.edit_text(f"⛏️ معدن: {p.mines}\n🛢️ نفت: {p.oil}\n🏭 کارخانه: {p.factories}\n🚗 خودرو: {p.auto_factories}",reply_markup=menu())

        elif d=="commander":
            await c.message.answer("برای تعیین فرمانده بنویس: /commander نام فرمانده")

        elif d=="war":
            b=InlineKeyboardBuilder(); b.button(text="⚔️ اعلان جنگ",callback_data="war:declare"); b.button(text="🕊️ صلح",callback_data="war:peace"); b.button(text="🌍 کشورها","countries"); b.adjust(1)
            await c.message.edit_text("⚔️ <b>جنگ و دیپلماسی</b>\nبرای هدف از دستور /war استفاده کن.",reply_markup=b.as_markup(),parse_mode="HTML")

        elif d=="statement": await c.message.answer("📜 /statement متن بیانیه")

        elif d=="alliance":
            b=InlineKeyboardBuilder(); b.button(text="🤝 ساخت اتحاد",callback_data="ally:create"); b.button(text="💙 اتحاد دوستانه","ally:friendly"); b.button(text="📋 فهرست","ally:list"); b.adjust(1)
            await c.message.edit_text("🤝 <b>اتحادها</b>",reply_markup=b.as_markup(),parse_mode="HTML")

        elif d=="loan": await c.message.answer("🏦 /loan مبلغ — سقف 100,000,000 و سررسید 2 روز")

        elif d in ("sea","air"):
            mode="دریایی" if d=="sea" else "هوایی"
            await c.message.answer(f"{'🚢' if d=='sea' else '✈️'} /trade {mode} @username مبلغ")

        elif d=="invite":
            me=await c.bot.me()
            await c.message.edit_text(f"👥 لینک دعوت:\nhttps://t.me/{me.username}?start=ref_{p.tg}\n\nپاداش دعوت را می‌توان در مرحله بعد تنظیم کرد.",reply_markup=menu())

        elif d=="change":
            b=InlineKeyboardBuilder()
            for i,x in enumerate(COUNTRIES):
                b.button(text=x,callback_data=f"country:{i}")
            b.adjust(3); await c.message.edit_text("🌍 کشور جدید را انتخاب کن:",reply_markup=b.as_markup())

        elif d.startswith("country:"):
            name=COUNTRIES[int(d.split(":")[1])]
            taken=(await s.execute(select(Player).where(Player.country==name))).scalar_one_or_none()
            if taken and taken.tg!=p.tg: await c.answer("این کشور قبلاً گرفته شده.",show_alert=True)
            else:
                p.country=name; await s.commit()
                await c.message.edit_text(f"✅ کشور انتخاب شد: <b>{name}</b>",reply_markup=menu(),parse_mode="HTML")

        elif d.startswith("buy:"):
            k=d.split(":")[1]
            vals={"land":(100000,"land",100),"air":(500000,"air",1),"navy":(1200000,"navy",1),"def":(800000,"defense",1),"strat":(1500000,"strategic",1),"tank":(1000000,"tanks",10),"art":(700000,"artillery",10),"missile":(2500000,"missiles",1),"nuke":(20000000,"nuclear",1)}
            cost,attr,q=vals[k]
            if p.money<cost: await c.answer("بودجه کافی نیست.",show_alert=True)
            else: p.money-=cost; setattr(p,attr,getattr(p,attr)+q); await s.commit(); await c.answer("خرید انجام شد.")

        elif d.startswith("build:"):
            k=d.split(":")[1]
            vals={"factory":(5000000,"factories"),"auto":(10000000,"auto_factories"),"mine":(8000000,"mines"),"oil":(15000000,"oil"),"hotel":(1500000,"hotels"),"port":(12000000,"ports"),"airport":(10000000,"airports"),"base":(20000000,"bases")}
            cost,attr=vals[k]
            if p.money<cost: await c.answer("بودجه کافی نیست.",show_alert=True)
            else: p.money-=cost; setattr(p,attr,getattr(p,attr)+1); await s.commit(); await c.answer("ساخت انجام شد.")

        elif d=="countries":
            await c.message.answer("🌍 برای دیدن/انتخاب کشورها از «تغییر کشور» استفاده کن.")

        elif d=="ally:create": await c.message.answer("/alliance نام_اتحاد")
        elif d=="ally:friendly": await c.message.answer("/friendly کشور")
        elif d=="ally:list":
            aa=(await s.execute(select(Alliance))).scalars().all()
            await c.message.answer("\n".join(f"🤝 {a.name} {'💙' if a.friendly else '⚔️'}" for a in aa) or "اتحادی وجود ندارد.")
        elif d=="war:declare": await c.message.answer("/war @username")
        elif d=="war:peace": await c.message.answer("/peace @username")
        await c.answer()

async def statement(m):
    text=m.text.partition(" ")[2].strip()
    if not text: return await m.answer("/statement متن")
    async with Session() as s:
        p=await player(s,m.from_user.id,m.from_user.username); s.add(Statement(player=p.tg,text=text)); await s.commit()
    await m.answer(f"📜 <b>بیانیه {p.country}</b>\n\n{text}",parse_mode="HTML")

async def commander(m):
    name=m.text.partition(" ")[2].strip()[:100]
    if not name: return await m.answer("/commander نام")
    async with Session() as s:
        p=await player(s,m.from_user.id,m.from_user.username); p.commander=name; await s.commit()
    await m.answer(f"👑 فرمانده تعیین شد: <b>{name}</b>",parse_mode="HTML")

async def alliance(m):
    name=m.text.partition(" ")[2].strip()[:100]
    if not name:return await m.answer("/alliance نام")
    async with Session() as s:
        p=await player(s,m.from_user.id,m.from_user.username)
        a=Alliance(name=name,owner=p.tg); s.add(a); await s.flush(); p.alliance_id=a.id; await s.commit()
    await m.answer(f"🤝 اتحاد <b>{name}</b> ساخته شد.",parse_mode="HTML")

async def friendly(m):
    await m.answer("💙 پیشنهاد اتحاد دوستانه ثبت شد. نسخه بعدی می‌تواند تأیید دوطرفه و مدت قرارداد را اضافه کند.")

async def loan(m):
    try: amount=Decimal(m.text.split()[1])
    except: return await m.answer("/loan 10000000")
    if amount<=0 or amount>100000000:return await m.answer("حداکثر وام: 100,000,000")
    async with Session() as s:
        p=await player(s,m.from_user.id,m.from_user.username); p.money+=amount
        s.add(Loan(borrower=p.tg,amount=amount,due=datetime.now(timezone.utc)+timedelta(days=2))); await s.commit()
    await m.answer(f"🏦 {fmt(amount)} به حساب بازی اضافه شد؛ سررسید ۲ روز.")

async def income_loop():
    while True:
        try:
            async with Session() as s:
                ps=(await s.execute(select(Player))).scalars().all(); now=datetime.now(timezone.utc)
                for p in ps:
                    if now-p.last_income>=timedelta(days=1):
                        inc=p.population*2+p.mines*50000+p.oil*80000+p.factories*100000+p.hotels*25000+p.auto_factories*70000
                        p.money+=Decimal(inc); p.last_income=now
                await s.commit()
        except Exception as e: print("income:",e)
        await asyncio.sleep(3600)

async def main():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    bot=Bot(TOKEN); dp=Dispatcher()
    dp.message.register(start,CommandStart())
    dp.message.register(statement,Command("statement"))
    dp.message.register(commander,Command("commander"))
    dp.message.register(alliance,Command("alliance"))
    dp.message.register(friendly,Command("friendly"))
    dp.message.register(loan,Command("loan"))
    dp.callback_query.register(callbacks)
    asyncio.create_task(income_loop())
    print("WORLD WAR BOT ONLINE")
    await dp.start_polling(bot)

if __name__=="__main__": asyncio.run(main())
