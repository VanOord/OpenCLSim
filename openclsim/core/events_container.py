"""EventsContainer provide a basic class for managing information which has to be stored in an object."""
import simpy


class EventsContainer(simpy.FilterStore):
    """
    EventsContainer provide a basic class for managing information which has to be stored in an object.

    It is a generic container, which has a default behavior, but can be used for storing arbitrary objects.

    Parameters
    ----------
    store_capacity
        Number of stores that can be contained by the multicontainer
    """

    def __init__(self, env, store_capacity: int = 1, *args, **kwargs):
        super().__init__(env, capacity=store_capacity)
        self._env = env
        self._get_available_events = {}
        self._put_available_events = {}

    def initialize_container(self, initials):
        """Initialize method used for MultiContainers."""
        for item in initials:
            assert "id" in item
            assert "capacity" in item
            assert "level" in item

            item["reservation"] = {}

            super().put(item)

    def get_available(self, amount, id_="default"):
        if self.get_level(id_) >= amount:
            return self._env.event().succeed()

        available_event = self._get_available_events.get(id_, {}).get(amount)
        if available_event:
            return available_event

        new_event = self._env.event()
        self._get_available_events.setdefault(id_, {})[amount] = new_event
        return new_event

    def get_capacity(self, id_="default"):
        if self.items is None:
            return 0
        res = [item["capacity"] for item in self.items if item["id"] == id_]
        if isinstance(res, list) and len(res) > 0:
            return res[0]
        return 0

    def get_level(self, id_="default"):
        if self.items is None:
            return 0
        res = [item["level"] for item in self.items if item["id"] == id_]
        if isinstance(res, list) and len(res) > 0:
            return res[0]
        return 0

    def put_available(self, amount, id_="default"):
        if self.get_capacity(id_) - self.get_level(id_) >= amount:
            return self._env.event().succeed()

        available_event = self._put_available_events.get(id_, {}).get(amount)
        if available_event:
            return available_event

        new_event = self._env.event()
        self._put_available_events.setdefault(id_, {})[amount] = new_event
        return new_event

    def get_empty_event(self, start_event=False, id_="default"):
        if not start_event:
            return self.put_available(self.get_capacity(id_), id_)
        elif start_event.triggered:
            return self.put_available(self.get_capacity(id_), id_)
        else:
            return self._env.event()

    def get_full_event(self, start_event=False, id_="default"):
        if not start_event:
            return self.get_available(self.get_capacity(id_), id_)
        elif start_event.triggered:
            return self.get_available(self.get_capacity(id_), id_)
        else:
            return self._env.event()

    def put(self, amount, id_="default", activity_id=None):
        assert self.put_available(amount=amount, id_=id_).triggered

        store_status = super().get(lambda state: state["id"] == id_).value
        store_status["level"] = store_status["level"] + amount
        if activity_id and activity_id in store_status["reservation"]:
            del store_status["reservation"][activity_id]

        put_event = super().put(store_status)
        put_event.callbacks.append(self.put_callback)
        return put_event

    def put_callback(self, event, id_="default"):
        if isinstance(event, simpy.resources.store.StorePut):
            if "id" in event.item:
                id_ = event.item["id"]
        if id_ in self._get_available_events:
            for amount in sorted(self._get_available_events[id_]):
                if self.get_level(id_) >= amount:
                    if id_ in self._get_available_events:
                        self._get_available_events[id_][amount].succeed()
                        del self._get_available_events[id_][amount]
                else:
                    return

    def get(self, amount, id_="default", activity_id=None):
        assert self.get_available(amount=amount, id_=id_).triggered

        store_status = super().get(lambda state: state["id"] == id_).value
        store_status["level"] = store_status["level"] - amount
        if activity_id and activity_id in store_status["reservation"]:
            del store_status["reservation"][activity_id]

        get_event = super().put(store_status)
        get_event.callbacks.append(self.get_callback)
        return get_event

    def get_callback(self, event, id_="default"):
        if isinstance(event, simpy.resources.store.StorePut):
            if "id" in event.item:
                id_ = event.item["id"]
        if id_ in self._put_available_events:
            for amount in sorted(self._put_available_events[id_]):
                if self.get_capacity(id_) - self.get_level(id_) >= amount:
                    if id_ in self._put_available_events:
                        self._put_available_events[id_][amount].succeed()
                        del self._put_available_events[id_][amount]
                else:
                    return

    def get_reservation(self, activity_id, amount, id_="default"):
        store_status = super().get(lambda state: state["id"] == id_).value

        new_store_status = store_status.copy()
        new_store_status["reservation"][activity_id] = -amount

        new_level = new_store_status["level"] + sum(
            new_store_status["reservation"].values()
        )

        if new_level >= 0:
            return super().put(new_store_status), True
        else:
            return super().put(store_status), False

    def put_reservation(self, activity_id, amount, id_="default"):
        store_status = super().get(lambda state: state["id"] == id_).value

        new_store_status = store_status.copy()
        new_store_status["reservation"][activity_id] = amount

        new_level = new_store_status["level"] + sum(
            new_store_status["reservation"].values()
        )
        if new_store_status["capacity"] >= new_level:
            return super().put(new_store_status), True
        else:
            return super().put(store_status), False

    @property
    def container_list(self):
        container_ids = []
        if len(self.items) > 0:
            container_ids = [item["id"] for item in self.items]
        return container_ids
