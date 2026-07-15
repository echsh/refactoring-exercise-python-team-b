import unittest
from datetime import datetime

from lab_reservation.models import EquipmentData, UserData
from lab_reservation.notification import RecordingNotificationService
from lab_reservation.repository import InMemoryReservationRepository
from lab_reservation.reservation_manager import ReservationManager


class ReservationManagerTest(unittest.TestCase):
    def setUp(self):
        ReservationManager.reset_sequence_for_test()
        self.repository = InMemoryReservationRepository()
        self.notification = RecordingNotificationService()
        self.manager = ReservationManager(self.repository, self.notification)

    def test_student_laser_cutter_fee_is_calculated_in_thirty_minute_units(self):
        reservation = self.manager.reserve(
            student("s001", True),
            equipment("laser-01", "LASER_CUTTER"),
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 20),
            False,
            False,
        )

        self.assertEqual("R-0001", reservation.reservation_id)
        self.assertEqual(900, reservation.fee)
        self.assertEqual("RESERVED", reservation.status)

    def test_external_gpu_fee_uses_external_multiplier(self):
        reservation = self.manager.reserve(
            external("x001"),
            equipment("gpu-01", "GPU_SERVER"),
            at(2026, 7, 20, 13, 0),
            at(2026, 7, 20, 14, 0),
            False,
            False,
        )

        self.assertEqual(3000, reservation.fee)

    def test_staff_emergency_reservation_adds_surcharge_and_allows_outside_hours(self):
        reservation = self.manager.reserve(
            staff("f001", True),
            equipment("gpu-01", "GPU_SERVER"),
            at(2026, 7, 20, 6, 0),
            at(2026, 7, 20, 7, 0),
            False,
            True,
        )

        self.assertEqual(3600, reservation.fee)
        self.assertTrue(reservation.emergency)

    def test_non_staff_cannot_make_emergency_reservation(self):
        with self.assertRaises(ValueError):
            self.manager.reserve(
                student("s001", True),
                equipment("gpu-01", "GPU_SERVER"),
                at(2026, 7, 20, 6, 0),
                at(2026, 7, 20, 7, 0),
                False,
                True,
            )

    def test_student_cannot_reserve_longer_than_four_hours(self):
        with self.assertRaises(ValueError):
            self.manager.reserve(
                student("s001", True),
                equipment("gpu-01", "GPU_SERVER"),
                at(2026, 7, 20, 10, 0),
                at(2026, 7, 20, 14, 1),
                False,
                False,
            )

    def test_external_user_cannot_reserve_on_weekend(self):
        with self.assertRaises(ValueError):
            self.manager.reserve(
                external("x001"),
                equipment("gpu-01", "GPU_SERVER"),
                at(2026, 7, 18, 10, 0),
                at(2026, 7, 18, 11, 0),
                False,
                False,
            )

    def test_motion_capture_requires_training(self):
        with self.assertRaises(ValueError):
            self.manager.reserve(
                student("s001", False),
                equipment("mocap-01", "MOTION_CAPTURE"),
                at(2026, 7, 20, 10, 0),
                at(2026, 7, 20, 11, 0),
                False,
                False,
            )

    def test_external_user_cannot_reserve_motion_capture(self):
        with self.assertRaises(ValueError):
            self.manager.reserve(
                external("x001"),
                equipment("mocap-01", "MOTION_CAPTURE"),
                at(2026, 7, 20, 10, 0),
                at(2026, 7, 20, 11, 0),
                False,
                False,
            )

    def test_overlapping_reservation_for_same_equipment_is_rejected(self):
        gpu = equipment("gpu-01", "GPU_SERVER")
        self.manager.reserve(
            student("s001", True),
            gpu,
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )

        with self.assertRaises(RuntimeError):
            self.manager.reserve(
                staff("f001", True),
                gpu,
                at(2026, 7, 20, 10, 30),
                at(2026, 7, 20, 11, 30),
                False,
                False,
            )

    def test_cancelled_reservation_does_not_block_another_reservation(self):
        gpu = equipment("gpu-01", "GPU_SERVER")
        first = self.manager.reserve(
            student("s001", True),
            gpu,
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )
        self.manager.cancel(first.reservation_id, at(2026, 7, 18, 9, 0), False)

        second = self.manager.reserve(
            staff("f001", True),
            gpu,
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )

        self.assertEqual("R-0002", second.reservation_id)

    def test_cancellation_fee_depends_on_time_before_start(self):
        early = self.manager.reserve(
            student("s001", True),
            equipment("laser-01", "LASER_CUTTER"),
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )
        self.assertEqual(
            0, self.manager.cancel(early.reservation_id, at(2026, 7, 18, 10, 0), False)
        )

        late = self.manager.reserve(
            student("s002", True),
            equipment("laser-02", "LASER_CUTTER"),
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )
        self.assertEqual(
            300, self.manager.cancel(late.reservation_id, at(2026, 7, 19, 12, 0), False)
        )

        after_start = self.manager.reserve(
            student("s003", True),
            equipment("laser-03", "LASER_CUTTER"),
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )
        self.assertEqual(
            600,
            self.manager.cancel(
                after_start.reservation_id, at(2026, 7, 20, 10, 5), False
            ),
        )

    def test_notifications_are_optional_and_do_not_change_reservation(self):
        reservation = self.manager.reserve(
            student("s001", True),
            equipment("gpu-01", "GPU_SERVER"),
            at(2026, 7, 20, 13, 0),
            at(2026, 7, 20, 14, 0),
            True,
            False,
        )

        self.assertEqual(1, len(self.notification.sent_messages))
        self.assertEqual(
            "s001:予約を受け付けました: " + reservation.reservation_id + " GPUサーバ",
            self.notification.sent_messages[0],
        )

    def test_filtering_user_reservations_can_exclude_cancelled_reservations(self):
        first = self.manager.reserve(
            student("s001", True),
            equipment("laser-01", "LASER_CUTTER"),
            at(2026, 7, 20, 10, 0),
            at(2026, 7, 20, 11, 0),
            False,
            False,
        )
        self.manager.reserve(
            student("s001", True),
            equipment("gpu-01", "GPU_SERVER"),
            at(2026, 7, 20, 13, 0),
            at(2026, 7, 20, 14, 0),
            False,
            False,
        )
        self.manager.cancel(first.reservation_id, at(2026, 7, 18, 10, 0), False)

        active = self.manager.get_user_reservations("s001", False)
        all_reservations = self.manager.get_user_reservations("s001", True)

        self.assertEqual(1, len(active))
        self.assertEqual(2, len(all_reservations))

    def test_summary_uses_domain_labels_and_can_include_fee(self):
        reservation = self.manager.reserve(
            student("s001", True),
            equipment("gpu-01", "GPU_SERVER"),
            at(2026, 7, 20, 13, 0),
            at(2026, 7, 20, 14, 0),
            False,
            False,
        )

        self.assertEqual(
            "R-0001 GPUサーバ 学生 2026-07-20T13:00 - 2026-07-20T14:00 1000円",
            self.manager.make_summary(reservation, True),
        )


def student(user_id, training_completed):
    user = UserData()
    user.id = user_id
    user.name = "学生" + user_id
    user.type = "STUDENT"
    user.training_completed = training_completed
    user.suspended = False
    user.penalty_points = 0
    return user


def staff(user_id, training_completed):
    user = UserData()
    user.id = user_id
    user.name = "教職員" + user_id
    user.type = "STAFF"
    user.training_completed = training_completed
    user.suspended = False
    user.penalty_points = 0
    return user


def external(user_id):
    user = UserData()
    user.id = user_id
    user.name = "学外" + user_id
    user.type = "EXTERNAL"
    user.training_completed = True
    user.suspended = False
    user.penalty_points = 0
    return user


def equipment(code, equipment_type):
    item = EquipmentData()
    item.code = code
    item.name = code
    item.type = equipment_type
    item.active = True
    return item


def at(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute)


if __name__ == "__main__":
    unittest.main()
