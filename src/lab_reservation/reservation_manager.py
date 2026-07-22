from datetime import time

from .common_util import CommonUtil
from .models import ReservationData


class ReservationManager:
    no = 1
    MAX_MINUTES_BY_USER_TYPE = {"STUDENT": 240, "STAFF": 480, "EXTERNAL": 120}
    OPENING_TIME = time(8, 0)
    CLOSING_TIME = time(22, 0)

    def __init__(self, repository, notification_service):
        self.repository = repository
        self.notification_service = notification_service

    def reserve(
        self,
        user,
        equipment,
        start_at,
        end_at,
        send_notification,
        emergency,
    ):
        if user is None:
            raise ValueError("user is required")
        if equipment is None:
            raise ValueError("equipment is required")
        if (
            CommonUtil.empty(user.id)
            or CommonUtil.empty(user.name)
            or CommonUtil.empty(user.type)
        ):
            raise ValueError("invalid user")
        if (
            CommonUtil.empty(equipment.code)
            or CommonUtil.empty(equipment.name)
            or CommonUtil.empty(equipment.type)
        ):
            raise ValueError("invalid equipment")

        if start_at is None or end_at is None:
            raise ValueError("start and end are required")
        if end_at <= start_at:
            raise ValueError("end must be after start")
        if start_at.date() != end_at.date():
            raise ValueError("reservation must be within one day")

        if user.suspended:
            raise RuntimeError("user is suspended")
        if user.penalty_points >= 3:
            raise RuntimeError("too many penalty points")
        if not equipment.active:
            raise RuntimeError("equipment is inactive")

        minutes = int((end_at - start_at).total_seconds() // 60)
        max_minutes = ReservationManager.MAX_MINUTES_BY_USER_TYPE.get(user.type)
        if max_minutes is None:
            raise ValueError(f"unknown user type: {user.type}")
        if minutes > max_minutes:
            raise ValueError(f"{user.type.lower()} reservation is too long")

        if emergency:
            if user.type != "STAFF":
                raise ValueError("only staff can make emergency reservations")
        else:
            if start_at.time() < ReservationManager.OPENING_TIME or end_at.time() > ReservationManager.CLOSING_TIME:
                raise ValueError("outside operating hours")

        if user.type == "EXTERNAL":
            if start_at.weekday() in (5, 6):
                raise ValueError("external users cannot reserve on weekends")

        if equipment.type == "MOTION_CAPTURE":
            if not user.training_completed:
                raise ValueError("training is required")
            if user.type == "EXTERNAL":
                raise ValueError("external users cannot use motion capture")
        elif equipment.type != "LASER_CUTTER" and equipment.type != "GPU_SERVER":
            raise ValueError(f"unknown equipment type: {equipment.type}")

        all_reservations = self.repository.find_all()
        for existing in all_reservations:
            if (
                existing.equipment_code == equipment.code
                and existing.status != "CANCELLED"
            ):
                if start_at < existing.end_at and end_at > existing.start_at:
                    raise RuntimeError("reservation overlaps existing reservation")

        result = ReservationData()
        result.reservation_id = f"R-{ReservationManager.no:04d}"
        ReservationManager.no += 1
        result.user_id = user.id
        result.user_name = user.name
        result.user_type = user.type
        result.equipment_code = equipment.code
        result.equipment_name = equipment.name
        result.equipment_type = equipment.type
        result.start_at = start_at
        result.end_at = end_at
        result.emergency = emergency
        result.status = "RESERVED"
        result.fee = CommonUtil.calculate_fee(
            user.type, equipment.type, start_at, end_at, emergency
        )
        result.cancellation_fee = 0
        self.repository.save(result)

        if send_notification:
            self.notification_service.send(
                user.id,
                "予約を受け付けました: "
                + result.reservation_id
                + " "
                + CommonUtil.equipment_label(equipment.type),
            )

        return result

    def cancel(self, reservation_id, cancelled_at, send_notification):
        if CommonUtil.empty(reservation_id):
            raise ValueError("reservation id is required")
        if cancelled_at is None:
            raise ValueError("cancelled time is required")

        reservation = self.repository.find_by_id(reservation_id)
        if reservation is None:
            raise ValueError("reservation not found")
        if reservation.status == "CANCELLED":
            raise RuntimeError("reservation is already cancelled")

        minutes_before_start = int(
            (reservation.start_at - cancelled_at).total_seconds() // 60
        )
        if minutes_before_start >= 24 * 60:
            cancellation_fee = 0
        elif minutes_before_start > 0:
            cancellation_fee = reservation.fee // 2
        else:
            cancellation_fee = reservation.fee

        reservation.status = "CANCELLED"
        reservation.cancellation_fee = cancellation_fee
        self.repository.save(reservation)

        if send_notification:
            self.notification_service.send(
                reservation.user_id,
                "予約をキャンセルしました: "
                + reservation.reservation_id
                + " キャンセル料="
                + str(cancellation_fee)
                + "円",
            )

        return cancellation_fee

    def get_user_reservations(self, user_id, include_cancelled):
        result = []
        for reservation in self.repository.find_all():
            if reservation.user_id == user_id:
                if include_cancelled:
                    result.append(reservation)
                else:
                    if reservation.status != "CANCELLED":
                        result.append(reservation)
        return result

    def make_summary(self, reservation, include_fee):
        equipment = CommonUtil.equipment_label(reservation.equipment_type)
        user_type = CommonUtil.user_label(reservation.user_type)

        text = (
            reservation.reservation_id
            + " "
            + equipment
            + " "
            + user_type
            + " "
            + reservation.start_at.isoformat(timespec="minutes")
            + " - "
            + reservation.end_at.isoformat(timespec="minutes")
        )
        if include_fee:
            text += " " + str(reservation.fee) + "円"
        return text

    @staticmethod
    def reset_sequence_for_test():
        ReservationManager.no = 1
