import uuid
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, text, case
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from models import Store, DeliveryArea, DeliveryFee, OperatingHours
from store.schemas import (
    StoreInfoResponse, DeliveryAreasResponse, DeliveryAreaResponse,
    DeliveryFeeResponse, OperatingHoursResponse, DeliveryFeeRequest,
    StoreInfoCreate, StoreInfoUpdate, DeliveryAreaCreate, DeliveryAreaUpdate,
    OperatingHoursCreate, OperatingHoursUpdate
)

class StoreService:
    """Store service for store information, delivery areas, and operating hours"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # STORE INFO MANAGEMENT
    # =============================================================================
    
    def get_store_info(self, store_id: str = "main") -> StoreInfoResponse:
        """Get store information"""
        try:
            # For now, we'll return mock data since we don't have store tables yet
            # In a real implementation, this would query the database
            
            # Mock store data
            store_info = {
                "store_id": store_id,
                "store_name": "Labanita Store",
                "store_description": "Your trusted destination for quality products and exceptional service",
                "store_logo": "https://example.com/logo.png",
                "store_banner": "https://example.com/banner.jpg",
                "store_status": "open",
                "contact_info": {
                    "phone": "+1-555-123-4567",
                    "email": "info@labanita.com",
                    "website": "https://labanita.com",
                    "whatsapp": "+1-555-123-4567",
                    "social_media": {
                        "facebook": "https://facebook.com/labanita",
                        "instagram": "https://instagram.com/labanita",
                        "twitter": "https://twitter.com/labanita"
                    }
                },
                "location": {
                    "address": "123 Main Street",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "postal_code": "10001",
                    "latitude": 40.7128,
                    "longitude": -74.0060,
                    "landmark": "Near Central Park"
                },
                "features": [
                    "Free WiFi",
                    "Parking Available",
                    "Wheelchair Accessible",
                    "Customer Service",
                    "Gift Wrapping",
                    "Loyalty Program"
                ],
                "policies": {
                    "return_policy": "30-day return policy",
                    "shipping_policy": "Free shipping on orders over $50",
                    "privacy_policy": "We protect your privacy",
                    "terms_of_service": "Standard terms apply"
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            return StoreInfoResponse(**store_info)
            
        except Exception as e:
            raise ValidationException(f"Failed to get store info: {str(e)}")
    
    def update_store_info(self, store_id: str, update_data: StoreInfoUpdate) -> StoreInfoResponse:
        """Update store information"""
        try:
            # In a real implementation, this would update the database
            # For now, return the updated mock data
            current_info = self.get_store_info(store_id)
            
            # Update fields if provided
            if update_data.store_name:
                current_info.store_name = update_data.store_name
            if update_data.store_description:
                current_info.store_description = update_data.store_description
            if update_data.store_logo:
                current_info.store_logo = update_data.store_logo
            if update_data.store_banner:
                current_info.store_banner = update_data.store_banner
            if update_data.store_status:
                current_info.store_status = update_data.store_status
            if update_data.contact_info:
                current_info.contact_info = update_data.contact_info
            if update_data.location:
                current_info.location = update_data.location
            if update_data.features:
                current_info.features = update_data.features
            if update_data.policies:
                current_info.policies = update_data.policies
            
            current_info.updated_at = datetime.utcnow()
            
            return current_info
            
        except Exception as e:
            raise ValidationException(f"Failed to update store info: {str(e)}")
    
    # =============================================================================
    # DELIVERY AREA MANAGEMENT
    # =============================================================================
    
    def get_delivery_areas(self) -> DeliveryAreasResponse:
        """Get all delivery areas"""
        try:
            # Mock delivery areas data
            areas = [
                {
                    "area_id": "local-001",
                    "area_name": "Local Delivery",
                    "area_type": "local",
                    "description": "Same-day delivery within city limits",
                    "cities": ["New York", "Brooklyn", "Queens"],
                    "postal_codes": ["10001", "10002", "10003", "11201", "11301"],
                    "estimated_delivery_time": "2-4 hours",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "area_id": "regional-001",
                    "area_name": "Regional Delivery",
                    "area_type": "regional",
                    "description": "Next-day delivery to nearby cities",
                    "cities": ["Newark", "Jersey City", "Yonkers"],
                    "postal_codes": ["07101", "07302", "10701"],
                    "estimated_delivery_time": "24-48 hours",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "area_id": "national-001",
                    "area_name": "National Shipping",
                    "area_type": "national",
                    "description": "Standard shipping across the country",
                    "cities": ["Los Angeles", "Chicago", "Houston", "Phoenix"],
                    "postal_codes": ["90001", "60601", "77001", "85001"],
                    "estimated_delivery_time": "3-7 business days",
                    "is_active": True,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]
            
            # Build response objects
            area_responses = [DeliveryAreaResponse(**area) for area in areas]
            
            # Calculate summary
            total_count = len(areas)
            active_areas = len([a for a in areas if a["is_active"]])
            
            coverage_summary = {}
            for area in areas:
                area_type = area["area_type"]
                coverage_summary[area_type] = coverage_summary.get(area_type, 0) + 1
            
            return DeliveryAreasResponse(
                areas=area_responses,
                total_count=total_count,
                active_areas=active_areas,
                coverage_summary=coverage_summary
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get delivery areas: {str(e)}")
    
    def get_delivery_area_by_id(self, area_id: str) -> DeliveryAreaResponse:
        """Get delivery area by ID"""
        try:
            # Get all areas and find the one with matching ID
            areas_response = self.get_delivery_areas()
            
            for area in areas_response.areas:
                if area.area_id == area_id:
                    return area
            
            raise NotFoundException(f"Delivery area with ID {area_id} not found")
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get delivery area: {str(e)}")
    
    # =============================================================================
    # DELIVERY FEE MANAGEMENT
    # =============================================================================
    
    def calculate_delivery_fee(self, request: DeliveryFeeRequest) -> DeliveryFeeResponse:
        """Calculate delivery fee for a specific area and order"""
        try:
            # Get delivery area
            area = self.get_delivery_area_by_id(request.area_id)
            
            # Mock delivery fee calculation
            # In a real implementation, this would use complex business logic
            
            base_fee = 5.99  # Base delivery fee
            final_fee = base_fee
            is_free_delivery = False
            free_delivery_threshold = 50.00
            
            # Check if order qualifies for free delivery
            if request.order_amount >= free_delivery_threshold:
                final_fee = 0.00
                is_free_delivery = True
            
            # Apply express delivery surcharge
            if request.is_express:
                final_fee += 3.99
            
            # Calculate based on weight if provided
            if request.order_weight:
                if request.order_weight > 5.0:  # Over 5kg
                    final_fee += 2.99
            
            # Build calculation details
            calculation_details = {
                "base_fee": base_fee,
                "order_amount": request.order_amount,
                "free_delivery_threshold": free_delivery_threshold,
                "express_surcharge": 3.99 if request.is_express else 0.0,
                "weight_surcharge": 2.99 if request.order_weight and request.order_weight > 5.0 else 0.0,
                "final_calculation": f"Base: ${base_fee} + Express: ${3.99 if request.is_express else 0.0} + Weight: ${2.99 if request.order_weight and request.order_weight > 5.0 else 0.0}"
            }
            
            # Build applied discounts
            applied_discounts = []
            if is_free_delivery:
                applied_discounts.append({
                    "type": "free_delivery",
                    "description": f"Free delivery for orders over ${free_delivery_threshold}",
                    "amount": base_fee
                })
            
            return DeliveryFeeResponse(
                area_id=area.area_id,
                area_name=area.area_name,
                fee_type="free_above_threshold",
                base_fee=base_fee,
                final_fee=final_fee,
                currency="USD",
                calculation_details=calculation_details,
                free_delivery_threshold=free_delivery_threshold,
                estimated_delivery_time=area.estimated_delivery_time,
                is_free_delivery=is_free_delivery,
                applied_discounts=applied_discounts
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to calculate delivery fee: {str(e)}")
    
    # =============================================================================
    # OPERATING HOURS MANAGEMENT
    # =============================================================================
    
    def get_operating_hours(self, store_id: str = "main") -> OperatingHoursResponse:
        """Get store operating hours"""
        try:
            # Mock operating hours data
            # In a real implementation, this would query the database
            
            # Get current time
            now = datetime.utcnow()
            current_time = now.time()
            current_day = now.strftime("%A").lower()
            
            # Mock weekly schedule
            weekly_schedule = [
                {
                    "day": "monday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(9, 0), "end_time": time(12, 0), "is_break": False},
                        {"start_time": time(13, 0), "end_time": time(18, 0), "is_break": False}
                    ],
                    "special_notes": None,
                    "is_holiday": False
                },
                {
                    "day": "tuesday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(9, 0), "end_time": time(12, 0), "is_break": False},
                        {"start_time": time(13, 0), "end_time": time(18, 0), "is_break": False}
                    ],
                    "special_notes": None,
                    "is_holiday": False
                },
                {
                    "day": "wednesday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(9, 0), "end_time": time(12, 0), "is_break": False},
                        {"start_time": time(13, 0), "end_time": time(18, 0), "is_break": False}
                    ],
                    "special_notes": None,
                    "is_holiday": False
                },
                {
                    "day": "thursday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(9, 0), "end_time": time(12, 0), "is_break": False},
                        {"start_time": time(13, 0), "end_time": time(18, 0), "is_break": False}
                    ],
                    "special_notes": None,
                    "is_holiday": False
                },
                {
                    "day": "friday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(9, 0), "end_time": time(12, 0), "is_break": False},
                        {"start_time": time(13, 0), "end_time": time(18, 0), "is_break": False}
                    ],
                    "special_notes": "Extended hours until 8 PM",
                    "is_holiday": False
                },
                {
                    "day": "saturday",
                    "is_open": True,
                    "time_slots": [
                        {"start_time": time(10, 0), "end_time": time(16, 0), "is_break": False}
                    ],
                    "special_notes": "Weekend hours",
                    "is_holiday": False
                },
                {
                    "day": "sunday",
                    "is_open": False,
                    "time_slots": [],
                    "special_notes": "Closed on Sundays",
                    "is_holiday": False
                }
            ]
            
            # Determine if store is currently open
            is_currently_open = False
            next_open_time = None
            
            # Find current day schedule
            current_day_schedule = None
            for day_schedule in weekly_schedule:
                if day_schedule["day"] == current_day:
                    current_day_schedule = day_schedule
                    break
            
            if current_day_schedule and current_day_schedule["is_open"]:
                # Check if current time falls within any time slot
                for time_slot in current_day_schedule["time_slots"]:
                    if time_slot["start_time"] <= current_time <= time_slot["end_time"]:
                        is_currently_open = True
                        break
                
                # If not currently open, find next open time
                if not is_currently_open:
                    for time_slot in current_day_schedule["time_slots"]:
                        if current_time < time_slot["start_time"]:
                            next_open_time = datetime.combine(now.date(), time_slot["start_time"])
                            break
            
            # If no next open time today, find next open day
            if not next_open_time:
                next_open_time = self._find_next_open_time(weekly_schedule, now)
            
            # Mock special hours and holidays
            special_hours = [
                {
                    "date": "2024-12-25",
                    "description": "Christmas Day",
                    "is_open": False,
                    "notes": "Store closed for Christmas"
                },
                {
                    "date": "2024-12-24",
                    "description": "Christmas Eve",
                    "is_open": True,
                    "time_slots": [{"start_time": "09:00", "end_time": "15:00"}],
                    "notes": "Early closing for Christmas Eve"
                }
            ]
            
            holidays = [
                {
                    "date": "2024-12-25",
                    "name": "Christmas Day",
                    "is_open": False
                },
                {
                    "date": "2024-01-01",
                    "name": "New Year's Day",
                    "is_open": False
                }
            ]
            
            return OperatingHoursResponse(
                store_id=store_id,
                store_name="Labanita Store",
                current_status="open" if is_currently_open else "closed",
                is_currently_open=is_currently_open,
                next_open_time=next_open_time,
                weekly_schedule=weekly_schedule,
                special_hours=special_hours,
                holidays=holidays,
                timezone="America/New_York",
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get operating hours: {str(e)}")
    
    def _find_next_open_time(self, weekly_schedule: List[Dict], current_time: datetime) -> Optional[datetime]:
        """Find the next time the store will be open"""
        try:
            # Start from tomorrow
            check_date = current_time.date() + timedelta(days=1)
            
            # Check next 7 days
            for _ in range(7):
                day_name = check_date.strftime("%A").lower()
                
                # Find schedule for this day
                day_schedule = None
                for schedule in weekly_schedule:
                    if schedule["day"] == day_name:
                        day_schedule = schedule
                        break
                
                if day_schedule and day_schedule["is_open"] and day_schedule["time_slots"]:
                    # Return first time slot of the day
                    first_slot = day_schedule["time_slots"][0]
                    return datetime.combine(check_date, first_slot["start_time"])
                
                check_date += timedelta(days=1)
            
            return None
            
        except Exception:
            return None
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def get_store_status(self) -> Dict[str, Any]:
        """Get current store status summary"""
        try:
            store_info = self.get_store_info()
            operating_hours = self.get_operating_hours()
            delivery_areas = self.get_delivery_areas()
            
            return {
                "store_name": store_info.store_name,
                "current_status": store_info.store_status,
                "is_currently_open": operating_hours.is_currently_open,
                "next_open_time": operating_hours.next_open_time,
                "delivery_areas_count": delivery_areas.total_count,
                "active_delivery_areas": delivery_areas.active_areas,
                "last_updated": datetime.utcnow()
            }
            
        except Exception as e:
            raise ValidationException(f"Failed to get store status: {str(e)}")