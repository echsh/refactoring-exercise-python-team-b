class UserData:
    def __init__(self):
        self.id = None
        self.name = None
        self.type = None
        self.training_completed = False
        self.suspended = False
        self.penalty_points = 0


class EquipmentData:
    def __init__(self):
        self.code = None
        self.name = None
        self.type = None
        self.active = False


class ReservationData:
    def __init__(self):
        self.reservation_id = None
        self.user_id = None
        self.user_name = None
        self.user_type = None
        self.equipment_code = None
        self.equipment_name = None
        self.equipment_type = None
        self.start_at = None
        self.end_at = None
        self.emergency = False
        self.status = None
        self.fee = 0
        self.cancellation_fee = 0
