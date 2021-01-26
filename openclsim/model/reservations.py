"""Base classes for the openclsim reservations."""

from .shift_amount_activity import ShiftAmountActivity


class SubProcessesReservation:
    """Mixin for the activities that want to reserve the shift amout quantities of their subprocesses."""

    def __init__(self, *args, **kwargs):
        """Class constructor."""
        super().__init__(*args, **kwargs)

    def reserve_sub_processes(self):
        reservations = []
        for sub_process in self.sub_processes:
            if hasattr(sub_process, "sub_processes"):
                reservations.extend(sub_process.reserve_sub_processes())

            if (
                isinstance(sub_process, ShiftAmountActivity)
                and sub_process.amount is not None
            ):
                get_reservation, passed = sub_process.origin.container.get_reservation(
                    sub_process.id, sub_process.amount, sub_process.id_
                )
                assert passed, "Not a valid reservation"
                (
                    put_reservation,
                    passed,
                ) = sub_process.destination.container.put_reservation(
                    sub_process.id, sub_process.amount, sub_process.id_
                )
                assert passed, "Not a valid reservation"
                reservations.extend([get_reservation, put_reservation])

        return reservations
