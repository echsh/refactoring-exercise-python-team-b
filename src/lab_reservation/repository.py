class ReservationRepository:
    def save(self, reservation):
        raise NotImplementedError

    def find_by_id(self, reservation_id):
        raise NotImplementedError

    def find_all(self):
        raise NotImplementedError


class InMemoryReservationRepository(ReservationRepository):
    def __init__(self):
        self.data = []

    def save(self, reservation):
        if reservation not in self.data:
            self.data.append(reservation)

    def find_by_id(self, reservation_id):
        for reservation in self.data:
            if reservation.reservation_id == reservation_id:
                return reservation
        return None

    def find_all(self):
        return self.data
