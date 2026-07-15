from datetime import datetime

from .models import EquipmentData, UserData
from .notification import RecordingNotificationService
from .repository import InMemoryReservationRepository
from .reservation_manager import ReservationManager


def main():
    repository = InMemoryReservationRepository()
    notification = RecordingNotificationService()
    manager = ReservationManager(repository, notification)

    student = UserData()
    student.id = "u001"
    student.name = "山田花子"
    student.type = "STUDENT"
    student.training_completed = True

    gpu = EquipmentData()
    gpu.code = "gpu-01"
    gpu.name = "GPU Server 01"
    gpu.type = "GPU_SERVER"
    gpu.active = True

    reservation = manager.reserve(
        student,
        gpu,
        datetime(2026, 7, 20, 13, 0),
        datetime(2026, 7, 20, 14, 20),
        True,
        False,
    )

    print(manager.make_summary(reservation, True))
    print(notification.sent_messages)


if __name__ == "__main__":
    main()
