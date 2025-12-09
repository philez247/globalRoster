"""Seed script to generate realistic dummy dataset for Global Roster."""
import random
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from global_roster.core.db import SessionLocal, engine
from global_roster.models import (
    Base,
    Trader,
    TraderWeeklyPattern,
    TraderPreference,
    TraderRequest,
    TraderSportSkill,
    TraderDaySportPreference,
)
from global_roster.models.trader import UserRole
from global_roster.models.trader_request import TraderRequestKind, TraderRequestEffectType, TraderRequestStatus

# Constants
LOCATIONS = ["DUB", "MEL", "NY"]
SPORTS = ["NBA", "NFL", "MLB", "NHL", "CFB", "CBB", "WNBA"]
SHIFT_TYPES = ["FULL", "EARLY", "MID", "LATE"]
DAYS_OF_WEEK = list(range(7))  # 0=Monday, 6=Sunday

# User roles distribution: 90 USER, 15 OWNER, 10 MANAGER, 5 ADMIN
USER_ROLES = [UserRole.USER] * 90 + [UserRole.OWNER] * 15 + [UserRole.MANAGER] * 10 + [UserRole.ADMIN] * 5
random.shuffle(USER_ROLES)


def clear_existing_data(db: Session):
    """Clear all existing data from tables."""
    db.query(TraderDaySportPreference).delete()
    db.query(TraderSportSkill).delete()
    db.query(TraderRequest).delete()
    db.query(TraderPreference).delete()
    db.query(TraderWeeklyPattern).delete()
    db.query(Trader).delete()
    db.commit()


def create_traders(db: Session, num_traders: int = 120):
    """Create traders with realistic data."""
    traders = []
    today = date.today()
    start_date_min = date(2022, 1, 1)
    
    for i in range(1, num_traders + 1):
        # Name format: "Last, First" -> "Trader, 001"
        first_name = "Trader"
        last_name = f"{i:03d}"
        name = f"{last_name}, {first_name}"
        alias = f"t{i:03d}"
        
        # Location: rotate through DUB, MEL, NY
        location = LOCATIONS[(i - 1) % len(LOCATIONS)]
        
        # Level: random 1-3
        level = random.randint(1, 3)
        
        # Required days per week: 80% get 5, 20% get 4
        required_days_per_week = 5 if random.random() < 0.8 else 4
        
        # Hours per week: random 32-40
        hours_per_week = random.randint(32, 40)
        
        # Start date: random between 2022-01-01 and today
        days_range = (today - start_date_min).days
        start_date = start_date_min + timedelta(days=random.randint(0, days_range))
        
        # User role from shuffled list
        user_role = USER_ROLES[i - 1]
        
        # Primary sport: rotate through SPORTS
        primary_sport = SPORTS[(i - 1) % len(SPORTS)]
        
        # Secondary sport: different from primary
        secondary_sport_idx = (i + 2) % len(SPORTS)
        secondary_sport = SPORTS[secondary_sport_idx]
        
        trader = Trader(
            name=name,
            alias=alias,
            location=location,
            level=level,
            primary_sport=primary_sport,
            secondary_sport=secondary_sport,
            required_days_per_week=required_days_per_week,
            hours_per_week=hours_per_week,
            start_date=start_date,
            is_active=True,
            user_role=user_role,
        )
        traders.append(trader)
        db.add(trader)
    
    db.commit()
    return traders


def create_weekly_patterns(db: Session, traders: list):
    """Create weekly patterns for all traders (28 rows per trader)."""
    for trader in traders:
        for day_of_week in DAYS_OF_WEEK:
            for shift_type in SHIFT_TYPES:
                # Hard block: 5-10% probability
                hard_block = random.random() < random.uniform(0.05, 0.10)
                
                # Weight distribution:
                # 20% -> +1 (preferred)
                # 10% -> -1 (prefer not)
                # rest -> 0 (neutral)
                # If hard_block=True, weight must be 0
                if hard_block:
                    weight = 0
                else:
                    rand = random.random()
                    if rand < 0.20:
                        weight = 1  # preferred
                    elif rand < 0.30:
                        weight = -1  # prefer not
                    else:
                        weight = 0  # neutral
                
                pattern = TraderWeeklyPattern(
                    trader_id=trader.id,
                    day_of_week=day_of_week,
                    shift_type=shift_type,
                    hard_block=hard_block,
                    weight=weight,
                )
                db.add(pattern)
    
    db.commit()


def create_preferences(db: Session, traders: list):
    """Create days-off grouping preferences for all traders."""
    for trader in traders:
        # Weight: randomly chosen from {+2, 0, -2}
        weight = random.choice([-2, 0, 2])
        
        preference = TraderPreference(
            trader_id=trader.id,
            category="DAYS_OFF_GROUPING",
            key="PREFERENCE",
            weight=weight,
        )
        db.add(preference)
    
    db.commit()


def create_requests(db: Session, traders: list):
    """Create requests for traders."""
    today = date.today()
    date_window_start = today - timedelta(days=30)
    date_window_end = today + timedelta(days=30)
    
    for trader in traders:
        # Number of requests per trader:
        # 70% -> 1 request
        # 20% -> 2 requests
        # 10% -> 3 requests
        rand = random.random()
        if rand < 0.70:
            num_requests = 1
        elif rand < 0.90:
            num_requests = 2
        else:
            num_requests = 3
        
        for _ in range(num_requests):
            # Request type
            request_kind = random.choice([
                TraderRequestKind.REQUEST_OFF_DAY,
                TraderRequestKind.REQUEST_OFF_RANGE,
                TraderRequestKind.REQUEST_IN,
            ])
            
            # Set effect_type based on request_kind
            if request_kind == TraderRequestKind.REQUEST_IN:
                effect_type = TraderRequestEffectType.MANDATORY
            else:  # REQUEST_OFF_DAY or REQUEST_OFF_RANGE
                effect_type = TraderRequestEffectType.UNAVAILABLE
            
            # Date range
            if request_kind == TraderRequestKind.REQUEST_OFF_RANGE:
                # Range: max 3 days
                date_from = date_window_start + timedelta(
                    days=random.randint(0, (date_window_end - date_window_start).days - 3)
                )
                date_to = date_from + timedelta(days=random.randint(1, 3))
            else:
                # Single day
                date_from = date_window_start + timedelta(
                    days=random.randint(0, (date_window_end - date_window_start).days)
                )
                date_to = date_from
            
            # Optional fields
            shift_type = random.choice([None] + SHIFT_TYPES) if random.random() < 0.5 else None
            sport_code = random.choice([None, trader.primary_sport, trader.secondary_sport]) if random.random() < 0.5 else None
            destination = random.choice([None] + LOCATIONS) if random.random() < 0.3 else None
            
            # Reason
            if request_kind == TraderRequestKind.REQUEST_IN:
                reason = "Seed mandatory in shift"
            elif request_kind == TraderRequestKind.REQUEST_OFF_RANGE:
                reason = "Seed request range off"
            else:
                reason = "Seed request day off"
            
            request = TraderRequest(
                trader_id=trader.id,
                request_kind=request_kind.value,
                effect_type=effect_type.value,
                date_from=date_from,
                date_to=date_to,
                shift_type=shift_type,
                sport_code=sport_code,
                destination=destination,
                status=TraderRequestStatus.APPROVED.value,
                reason=reason,
                created_at=datetime.now(),
                approved_at=datetime.now(),
                approved_by="seed_script",
            )
            db.add(request)
    
    db.commit()


def print_summary(db: Session):
    """Print summary statistics."""
    traders = db.query(Trader).all()
    total_traders = len(traders)
    
    # By location
    by_location = {}
    for loc in LOCATIONS:
        by_location[loc] = sum(1 for t in traders if t.location == loc)
    
    # By role
    by_role = {}
    for role in [UserRole.USER, UserRole.OWNER, UserRole.MANAGER, UserRole.ADMIN]:
        by_role[role.value] = sum(1 for t in traders if t.user_role == role)
    
    # Average required_days_per_week
    avg_days = sum(t.required_days_per_week for t in traders) / total_traders if total_traders > 0 else 0
    
    # Total requests
    total_requests = db.query(TraderRequest).count()
    
    print(f"Total traders: {total_traders}")
    print(f"By location: DUB={by_location.get('DUB', 0)}, MEL={by_location.get('MEL', 0)}, NY={by_location.get('NY', 0)}")
    print(f"By role: USER={by_role.get('USER', 0)}, OWNER={by_role.get('OWNER', 0)}, MANAGER={by_role.get('MANAGER', 0)}, ADMIN={by_role.get('ADMIN', 0)}")
    print(f"Average required_days_per_week: {avg_days:.2f}")
    print(f"Total requests: {total_requests}")
    print("Dummy dataset created successfully.")


def main():
    """Main function to seed the database."""
    db = SessionLocal()
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        # Clear existing data
        clear_existing_data(db)
        
        # Create traders
        print("Creating traders...")
        traders = create_traders(db, num_traders=120)
        
        # Create weekly patterns
        print("Creating weekly patterns...")
        create_weekly_patterns(db, traders)
        
        # Create preferences
        print("Creating preferences...")
        create_preferences(db, traders)
        
        # Create requests
        print("Creating requests...")
        create_requests(db, traders)
        
        # Print summary
        print_summary(db)
        
    finally:
        db.close()


if __name__ == "__main__":
    main()

